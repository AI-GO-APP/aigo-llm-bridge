from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import uuid

DEFAULT_MODELS = [
    {"id": "anthropic/claude-haiku-4.5", "provider": "claude", "native": "claude-haiku-4-5-20251001"},
    {"id": "openai/gpt-6-astra", "provider": "codex", "native": "gpt-6-astra"},
]
from .capacity import STANDARD_CONCURRENCY, DEFAULT_KEY_RPM
from .execution_budget import TIMING_COLUMNS

DEFAULTS = {"port": 8920, "accepting": True, "retention_days": 30, "timeout_s": 180, "inference_workers": STANDARD_CONCURRENCY,
            "inference_pending": STANDARD_CONCURRENCY,
            "public_url": "", "default_model": DEFAULT_MODELS[1]["id"], "models": DEFAULT_MODELS,
            "claude_path": "", "codex_path": "", "tunnel_kind": "none", "tunnel_name": "", "relay_enabled":False}
DEFAULTS.update(device_id="",cloudflare_account_id="",cloudflare_worker_name="")
LOG_COLUMNS = ("id", "key_id", "model", "provider", "created_ts", "started_ts", "finished_ts",
               "status", "http_status", "error_code", "duration_ms", "input_bytes", "output_bytes",
               "prompt_tokens", "completion_tokens", "cost_usd", "pricing_model", "pricing_fetched_ts", "cached_tokens", "cache_write_tokens", "reasoning_tokens",
               "protocol", "question_count", "calls_started", "calls_completed", "billing_complete")
LOG_COLUMNS += TIMING_COLUMNS


def keep_default(models,current):
    if any(m['id']==current for m in models):return current
    return next((m['id'] for m in models if m['provider']=='codex'),models[0]['id'])


class Store:
    def __init__(self, directory, *, startup=True):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt": self.directory.chmod(0o700)
        self.path = self.directory / "bridge.sqlite"
        if os.name != "nt":
            fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
            os.close(fd)
            self.path.chmod(0o600)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("pragma journal_mode=WAL")
        self.db.execute("pragma secure_delete=ON")
        self.db.executescript("""
            create table if not exists settings (name text primary key, value text not null);
            create table if not exists api_keys (
              id text primary key, label text not null, prefix text not null, digest text not null unique,
              created_ts real not null, revoked_ts real, providers text not null, rpm integer not null);
            create table if not exists requests (
              id text primary key, key_id text, model text, provider text, created_ts real,
              started_ts real, finished_ts real, status text, http_status integer, error_code text,
              duration_ms integer, input_bytes integer, output_bytes integer, prompt_tokens integer,
              completion_tokens integer);
            create index if not exists requests_time on requests(created_ts);
        """)
        columns={row[1] for row in self.db.execute('pragma table_info(requests)')}
        for name,kind in (('cost_usd','real'),('pricing_model','text'),('pricing_fetched_ts','real'),('client_request_id','text'),('request_digest','text'),('cached_tokens','integer'),('cache_write_tokens','integer'),('reasoning_tokens','integer'),
                          ('protocol','text'),('question_count','integer'),('calls_started','integer'),('calls_completed','integer'),('billing_complete','integer'),
                          *((name,'integer') for name in TIMING_COLUMNS)):
            if name not in columns:self.db.execute(f'alter table requests add column {name} {kind}')
        self.db.execute("create unique index if not exists request_dedupe on requests(key_id,client_request_id) where client_request_id is not null")
        # Installation identity belongs to this device profile, never to a CLI login.
        self.db.execute("insert or ignore into settings values ('device_id',?)",(json.dumps(uuid.uuid4().hex),))
        # A restart never replays an unknown request: no request bodies are on disk.
        if startup:
            self.db.execute("update requests set status='interrupted',http_status=503,error_code='process_restarted',finished_ts=? where status in ('queued','running')", (time.time(),))
        self.db.commit()
        if startup: self.prune()

    def get(self, name):
        with self.lock:
            row = self.db.execute("select value from settings where name=?", (name,)).fetchone()
            if row is None and name=='inference_pending':
                # Preserve older profiles' explicit capacity until an owner opts into queueing.
                row=self.db.execute("select value from settings where name='inference_workers'").fetchone()
        return json.loads(row[0]) if row else json.loads(json.dumps(DEFAULTS[name]))

    def set(self, name, value):
        if name not in DEFAULTS:
            raise ValueError("Unknown setting")
        with self.lock:
            self.db.execute("insert or replace into settings values (?,?)", (name, json.dumps(value)))
            self.db.commit()

    def create_key(self, label, providers=("claude", "codex"), rpm=DEFAULT_KEY_RPM):
        label = str(label).strip()
        providers = sorted(set(providers))
        if not label or len(label) > 60 or not providers or set(providers)-{"claude", "codex"} or not 1 <= int(rpm) <= 600:
            raise ValueError("請填 1–60 字名稱、至少一個來源，以及 1–600 的每分鐘上限。")
        kid = uuid.uuid4().hex
        token = "sk-br-" + secrets.token_hex(4) + "-" + secrets.token_urlsafe(32)
        with self.lock:
            self.db.execute("insert into api_keys values (?,?,?,?,?,null,?,?)",
                            (kid, label, token[:15], hashlib.sha256(token.encode()).hexdigest(), time.time(), json.dumps(providers), int(rpm)))
            self.db.commit()
        return kid, token

    def authenticate(self, token):
        if not token or len(token) > 256:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            row = self.db.execute("select id,label,prefix,providers,rpm from api_keys where digest=? and revoked_ts is null", (digest,)).fetchone()
        if not row:
            return None
        out = dict(row)
        out["providers"] = json.loads(out["providers"])
        return out

    def keys(self):
        with self.lock:
            return [dict(r) for r in self.db.execute("select id,label,prefix,created_ts,revoked_ts,providers,rpm from api_keys order by created_ts desc")]

    def revoke(self, kid):
        with self.lock:
            self.db.execute("update api_keys set revoked_ts=? where id=? and revoked_ts is null", (time.time(), kid))
            self.db.commit()

    def rotate(self, kid):
        with self.lock:
            row = self.db.execute("select * from api_keys where id=? and revoked_ts is null", (kid,)).fetchone()
            if row is None:
                raise ValueError("這把 key 已撤銷或不存在。")
            # One transaction: a failure never leaves the old key revoked alone.
            token = "sk-br-" + secrets.token_hex(4) + "-" + secrets.token_urlsafe(32)
            new_id = uuid.uuid4().hex
            with self.db:
                self.db.execute("insert into api_keys values (?,?,?,?,?,null,?,?)", (new_id, row["label"], token[:15], hashlib.sha256(token.encode()).hexdigest(), time.time(), row["providers"], row["rpm"]))
                self.db.execute("update api_keys set revoked_ts=? where id=?", (time.time(), kid))
        return new_id, token

    def insert_request(self, row, request_identity=None):
        if set(row)-set(LOG_COLUMNS):
            raise ValueError("Content is forbidden in request metadata")
        if request_identity:
            row={**row,'client_request_id':request_identity[0],'request_digest':request_identity[1]}
        with self.lock:
            self.db.execute(f"insert into requests ({','.join(row)}) values ({','.join('?' for _ in row)})", tuple(row.values()))
            self.db.commit()

    def update_request(self, rid, **changes):
        if set(changes)-set(LOG_COLUMNS):
            raise ValueError("Content is forbidden in request metadata")
        with self.lock:
            self.db.execute(f"update requests set {','.join(k+'=?' for k in changes)} where id=?", (*changes.values(), rid))
            self.db.commit()

    def request(self, rid, kid):
        with self.lock:
            row = self.db.execute("select * from requests where id=? and key_id=?", (rid, kid)).fetchone()
        return dict(row) if row else None

    def logs(self, status="", provider="", limit=500):
        clauses, args = [], []
        for column, value in (("status", status), ("provider", provider)):
            if value:
                clauses.append(column+"=?")
                args.append(value)
        query = "select "+','.join(LOG_COLUMNS)+" from requests" + (" where "+" and ".join(clauses) if clauses else "") + " order by created_ts desc limit ?"
        with self.lock:
            return [dict(r) for r in self.db.execute(query, (*args, min(10000, int(limit))))]

    def prune(self, all_finished=False):
        with self.lock:
            if all_finished:
                self.db.execute("delete from requests where status not in ('queued','running')")
            else:
                self.db.execute("delete from requests where created_ts<? and status not in ('queued','running')", (time.time()-self.get("retention_days")*86400,))
            self.db.commit()

    def export(self, path, **filters):
        with Path(path).open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=LOG_COLUMNS)
            writer.writeheader()
            writer.writerows(self.logs(limit=10000, **filters))

    def close(self):
        with self.lock:
            self.db.close()
