"""Loopback-only management plane, separate from the inference/relay API."""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import __version__, providers, secret
from .store import LOG_COLUMNS,keep_default
from .tunnel import Tunnel
from .connection_test import probe
from .handoff import integration
from .windows import startup_enabled, set_startup


class ManagementServer:
    def __init__(self, store, runtime, api, relay=None, on_shutdown=None, preview=False):
        self.store, self.runtime, self.api, self.relay = store, runtime, api, relay
        self.on_shutdown = on_shutdown or (lambda: None)
        self.preview = preview
        self.tunnel = Tunnel()
        self.token = secrets.token_urlsafe(32)
        self.auth = {}
        self.auth_checking = False
        self.auth_lock = threading.Lock()
        self.mutation_lock = threading.Lock()
        self.test_lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass

            def reply(self, status, value, content_type="application/json; charset=utf-8"):
                raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                try: self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError): pass

            def do_GET(self): self.dispatch(False)
            def do_POST(self): self.dispatch(True)

            def dispatch(self, post):
                # Host validation also blocks DNS rebinding. No CORS is exposed.
                if self.headers.get("Host") != f"127.0.0.1:{owner.port}":
                    return self.reply(403, {"error": "管理台僅允許本機存取。"})
                origin = self.headers.get("Origin")
                if origin and origin != owner.origin:
                    return self.reply(403, {"error": "不允許跨來源管理操作。"})
                path = urlsplit(self.path).path
                assets = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/platform.js": ("platform.js", "text/javascript; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/integration.js": ("integration.js", "text/javascript; charset=utf-8"),
                          "/style.css": ("style.css", "text/css; charset=utf-8")}
                if not post and path in assets:
                    name, mime = assets[path]
                    return self.reply(200, (Path(__file__).parent / "web" / name).read_bytes(), mime)
                supplied = self.headers.get("Authorization", "")
                if not secrets.compare_digest(supplied.encode(), ("Bearer " + owner.token).encode()):
                    return self.reply(401, {"error": "管理連線已失效，請從 Bridge 捷徑重新開啟。"})
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    if not post:
                        if path == "/manage/state": return self.reply(200, owner.state())
                        if path == "/manage/handoff": return self.reply(200, integration(owner.store,query.get('model',[None])[0]))
                        if path == "/manage/logs":
                            return self.reply(200, {"logs": owner.logs(query)})
                        if path == "/manage/export":
                            stream = io.StringIO(newline="")
                            writer = csv.DictWriter(stream, fieldnames=LOG_COLUMNS)
                            writer.writeheader()
                            # Prevent spreadsheet formulas in user-defined model slugs.
                            for row in owner.logs(query, limit=10000):
                                writer.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v) for k, v in row.items()})
                            return self.reply(200, stream.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8")
                    else:
                        if self.headers.get("Transfer-Encoding"):
                            raise ValueError("不支援此傳輸格式。")
                        length = int(self.headers.get("Content-Length", "0"))
                        if not 0 < length <= 65536: raise ValueError("管理請求大小無效。")
                        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                            raise ValueError("請使用 JSON。")
                        self.connection.settimeout(5)
                        raw = self.rfile.read(length)
                        if len(raw) != length: raise ValueError("請求不完整。")
                        data = json.loads(raw)
                        if not isinstance(data, dict): raise ValueError("請求格式無效。")
                        if path == "/manage/test-connection":
                            return self.reply(200, owner.test_connection(data))
                        with owner.mutation_lock:
                            result = owner.action(path, data)
                        return self.reply(200, result)
                    self.reply(404, {"error": "找不到管理端點。"})
                except (ValueError, TypeError, KeyError, UnicodeError):
                    self.reply(400, {"error": "資料無效，請確認名稱、模型、HTTPS 網址與數值範圍；Relay 需先完成裝置配對。"})
                except OSError:
                    self.reply(400, {"error": "操作未完成，請檢查本機權限與執行設定。"})
                except Exception:
                    self.reply(500, {"error": "管理操作未完成，請重新整理後再試。"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_port
        self.origin = f"http://127.0.0.1:{self.port}"
        self.url = self.origin + "/#session=" + self.token
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="bridge-management")

    def start(self):
        self.thread.start()
        self.refresh_auth()
        if self.store.get("tunnel_name") and self.store.get("public_url"):
            try: self.tunnel.start(self.store.get("tunnel_name"))
            except ValueError: pass

    def stop(self):
        self.tunnel.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def refresh_auth(self):
        with self.auth_lock:
            if self.auth_checking: return
            self.auth_checking = True
        def check():
            try:
                values = {p: providers.status(p, self.store) for p in ("claude", "codex")}
                with self.auth_lock: self.auth = values
            finally:
                with self.auth_lock: self.auth_checking = False
        threading.Thread(target=check, daemon=True, name="bridge-auth-status").start()

    def state(self):
        settings = {k: self.store.get(k) for k in ("public_url", "tunnel_name", "port", "retention_days", "timeout_s", "claude_path", "codex_path", "models", "relay_enabled")}
        with self.store.lock:
            counts = dict(self.store.db.execute("select status,count(*) from requests group by status"))
        keys = self.store.keys()
        with self.auth_lock:
            auth = {p: {"ready": bool(s.get("ready"))} for p, s in self.auth.items()}
            checking = self.auth_checking
        return {"version": __version__, "preview": self.preview, "accepting": self.store.get("accepting"), "settings": settings,
                "endpoint": (settings["public_url"] or f"http://127.0.0.1:{self.api.port}") + "/api/v1",
                "local_port": self.api.port, "startup": startup_enabled(self.store.directory), "keys": keys,
                "counts": counts, "auth": auth, "auth_checking": checking,
                "tunnel": self.tunnel.state, "relay": self.relay.state if self.relay else "未啟用",
                "logs": self.store.logs(limit=6)}

    def logs(self, query, limit=500):
        return self.store.logs(query.get("status", [""])[0], query.get("provider", [""])[0], limit=limit)

    def test_connection(self, data):
        # Network waits must not hold the management mutation lock.
        provider, model, key = data.get('provider'), data.get('model'), data.get('key')
        if provider not in {'claude', 'codex'} or not isinstance(model, str): raise ValueError()
        if not isinstance(key, str) or not key.strip() or len(key) > 256: raise ValueError()
        key = key.strip()
        with self.mutation_lock:
            endpoint = (self.store.get('public_url') or f'http://127.0.0.1:{self.api.port}') + '/api/v1'
            if data.get('endpoint') != endpoint: raise ValueError()
            if not any(m['id'] == model and m['provider'] == provider for m in self.store.get('models')): raise ValueError()
        result = {'provider': provider, 'model': model, 'endpoint': endpoint, 'success': False,
                  'elapsed_ms': 0, 'http_status': None}
        identity = self.store.authenticate(key)
        if not identity:
            return {**result, 'code': 'invalid_key', 'message': '金鑰無效或已撤銷；未送出測試請求。'}
        if provider not in identity['providers']:
            return {**result, 'code': 'scope_denied', 'message': '這把金鑰未開放此模型來源；未送出測試請求。'}
        if not self.test_lock.acquire(blocking=False):
            return {**result, 'code': 'busy', 'message': '另一個連線測試仍在執行，請稍後再試。'}
        try: return {**result, **probe(endpoint, model, key)}
        finally: self.test_lock.release()

    def action(self, path, data):
        if path == "/manage/accepting":
            if type(data.get("accepting")) is not bool: raise ValueError()
            self.store.set("accepting", data["accepting"])
        elif path == "/manage/auth": self.refresh_auth()
        elif path == "/manage/keys/create":
            allowed = data.get("providers", ["claude", "codex"])
            if not isinstance(allowed, list) or not all(isinstance(p, str) for p in allowed): raise ValueError()
            kid, token = self.store.create_key(data["label"], allowed, int(data.get("rpm", 30)))
            return {"id": kid, "token": token}
        elif path in {"/manage/keys/revoke", "/manage/keys/rotate"}:
            kid = data["id"]
            if not any(k["id"] == kid and not k["revoked_ts"] for k in self.store.keys()): raise ValueError()
            if path.endswith("rotate"):
                new_id, token = self.store.rotate(kid)
                self.runtime.cancel_key(kid)
                return {"id": new_id, "token": token}
            self.store.revoke(kid)
            self.runtime.cancel_key(kid)
        elif path == "/manage/logs/clear": self.store.prune(all_finished=True)
        elif path == "/manage/settings": self.save_settings(data)
        elif path == "/manage/pair":
            if not isinstance(data.get("key"), str): raise ValueError()
            secret.save(self.store.directory, data["key"])
        elif path == "/manage/tunnel/start": self.tunnel.start(self.store.get("tunnel_name"))
        elif path == "/manage/tunnel/stop": self.tunnel.stop()
        elif path == "/manage/shutdown": self.on_shutdown()
        else: raise ValueError()
        return {"ok": True}

    def save_settings(self, data):
        names = ("public_url", "tunnel_name", "claude_path", "codex_path")
        values = {}
        for name in names:
            if not isinstance(data.get(name), str): raise ValueError()
            values[name] = data[name].strip()
        for name, low, high in (("port", 1024, 65535), ("retention_days", 1, 365), ("timeout_s", 10, 1800)):
            values[name] = int(data[name])
            if not low <= values[name] <= high: raise ValueError()
        if values["public_url"]:
            url = urlsplit(values["public_url"])
            _ = url.port  # Reject malformed ports before persisting values.
            if url.scheme != "https" or not url.hostname or url.path not in {"", "/"} or url.query or url.fragment or url.username or url.password:
                raise ValueError()
            values["public_url"] = values["public_url"].rstrip("/")
        models = data.get("models")
        if not isinstance(models, list) or not 1 <= len(models) <= 100: raise ValueError()
        clean = []
        for m in models:
            if not isinstance(m, dict) or m.get("provider") not in {"claude", "codex"}: raise ValueError()
            if not isinstance(m.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:-]{0,120}", m["id"]): raise ValueError()
            if not isinstance(m.get("native"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,100}", m["native"]): raise ValueError()
            clean.append({k: m[k] for k in ("id", "provider", "native")})
        if len({m["id"] for m in clean}) != len(clean): raise ValueError()
        if type(data.get("startup")) is not bool or type(data.get("relay_enabled")) is not bool: raise ValueError()
        if data["relay_enabled"] and (not values["public_url"] or not secret.load(self.store.directory)): raise ValueError()
        values.update(models=clean, default_model=keep_default(clean,self.store.get('default_model')), relay_enabled=data["relay_enabled"])
        old_url, old_relay = self.store.get("public_url"), self.store.get("relay_enabled")
        if data["startup"] != startup_enabled(self.store.directory): set_startup(data["startup"], self.store.directory)
        with self.store.lock, self.store.db:
            self.store.db.executemany("insert or replace into settings values (?,?)", [(k, json.dumps(v)) for k, v in values.items()])
        self.store.prune()
        if self.relay and (old_relay != values["relay_enabled"] or old_url != values["public_url"]):
            self.relay.stop()
            if values["relay_enabled"]: self.relay.start()
