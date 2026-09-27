#!/usr/bin/env python3
"""把一個目錄部署成 AI GO Hosted App:第一次建立,之後開新 deployment;上傳 → 輪詢到 active / failed。

  python tools/deploy_hosted.py --slug <slug> --src <dir> [--name 顯示名稱] [--files a,b,c]

- 沒給 --files 就打包 <dir> 下所有檔案,排除 .git、__pycache__、node_modules、tests、out、*.pyc、
  .env 與 test_*.py。打包後會列出清單並確認 Dockerfile 在裡面(沒有 Dockerfile 平台會把整包當靜態站,
  部署「成功」但所有路由 404)。
- 建立 Hosted App 需要登入 session(不能用 Deploy Token);憑證見 tools/aigo_api.py。
- ⚠️ slug 命中既有 app = 重新部署;沒命中 = 建立新 app。Hosted 子網域是全平台共用的。
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aigo_api import client, items  # noqa: E402

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "tests", "out", ".pytest_cache", ".venv"}


def collect(src: Path, only: list[str] | None) -> list[Path]:
    if only:
        return [src / name for name in only]
    out = []
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if path.is_dir() or set(rel.parts) & EXCLUDE_DIRS:
            continue
        if path.suffix == ".pyc" or path.name.startswith("test_") or path.name.endswith(".env"):
            continue
        out.append(path)
    return out


def tarball(src: Path, files: list[Path]) -> bytes:
    names = [f.relative_to(src).as_posix() for f in files]
    if "Dockerfile" not in names:
        raise SystemExit("打包清單裡沒有 Dockerfile —— 平台會把整包當成靜態站。請確認 --src 指向服務根目錄")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for f, name in zip(files, names):
            tar.add(f, arcname=name)
    print("打包:", ", ".join(names))
    return buf.getvalue()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--name")
    ap.add_argument("--files", help="逗號分隔;省略則打包整個目錄")
    ap.add_argument("--wait", type=int, default=1200, help="最多等幾秒")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    payload = tarball(src, collect(src, args.files.split(",") if args.files else None))

    with client() as c:
        existing = next((a for a in items(c.get("/api/v1/hosted-apps").json()) if a.get("slug") == args.slug), None)
        if existing:
            app_id = existing["id"]
            r = c.post(f"/api/v1/hosted-apps/{app_id}/deployments", json={})
        else:
            r = c.post("/api/v1/hosted-apps",
                       json={"name": args.name or args.slug, "slug": args.slug, "create_deployment": True})
        if r.status_code >= 300:
            print("建立/開部署失敗:", r.status_code, r.text[:1500])
            return 1
        data = r.json()
        app_id = existing["id"] if existing else data.get("id")
        dep = data.get("latest_deployment") or data
        dispatch = dep.get("dispatch") or data.get("dispatch") or {}
        dep_id = dep.get("id") or dep.get("deployment_id")
        print(f"app={app_id} deployment={dep_id} {'(重新部署)' if existing else '(新建)'}")

        up = httpx.post(dispatch["deployd_upload_url"],
                        headers={"Authorization": "Bearer " + dispatch["upload_token"]},
                        files={"tarball": ("src.tar.gz", payload, "application/gzip")}, timeout=300)
        if up.status_code >= 300:
            print("上傳失敗:", up.status_code, up.text[:500])
            return 1
        dep_id = (up.json() or {}).get("deployment_id") or dep_id

        started, status = time.time(), ""
        while time.time() - started < args.wait:
            d = c.get(f"/api/v1/hosted-apps/{app_id}/deployments/{dep_id}").json()
            if d.get("status") != status:
                status = d.get("status")
                print(f"[{int(time.time() - started):>4}s] {status} {d.get('failure_reason') or ''}")
            if status in ("active", "failed", "superseded"):
                break
            time.sleep(10)

        if status != "active":
            logs = c.get(f"/api/v1/hosted-apps/{app_id}/deployments/{dep_id}/logs").json()
            for line in (logs.get("lines") or [])[-40:]:
                print("  ", line if isinstance(line, str) else json.dumps(line, ensure_ascii=False)[:300])
            # 原因放在最後一行:建置日誌的尾巴常是空行或 buildkit 收尾訊息,只看結尾會以為沒事
            # 共用池租戶的常見原因是配額:每個執行個體的記憶體上限是平台常數,部署時新舊兩個會同時存在
            print(f"部署失敗({status}):{d.get('failure_reason') or '見上方日誌'}")
            return 1
        detail = c.get(f"/api/v1/hosted-apps/{app_id}").json()
        print("完成:", json.dumps({k: detail.get(k) for k in ("id", "slug", "visibility", "url", "app_url")},
                                  ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
