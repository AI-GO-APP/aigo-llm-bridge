#!/usr/bin/env python3
"""建立(或補齊)Bridge 需要的五張平台自建表(jobs、workers、enrollments、usage、prefs)。

  python tools/provision_tables.py            # 只列出計畫,不動任何東西
  python tools/provision_tables.py --apply    # 真的建表 / 補欄位
  python tools/provision_tables.py --prefix biz_bridge_ --apply

- 表是**租戶級**資源:同租戶的所有 app 看得到同一批表。跑之前先確認沒有同語意的表
  (這支會列出名稱相近的既有表)。
- 實體名建立後**永不可改**,所以用「兩步命名法」:先以英文實體名建立,再把顯示名改成中文。
  建立後若實體名與預期不同(例如被加了流水號)就停下來,不要將就用下去。
- 需要 `datacenter.schema_write`(或 `system.admin`)權限;403 時請租戶管理員照印出的規格代建。
- 可重跑:已存在的表只補缺的欄位。
- 憑證見 tools/aigo_api.py。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "hosted"))
from aigo_api import client, items  # noqa: E402
from bridge.store import SCHEMA, AigoStore  # noqa: E402

TABLE_LABELS = {"jobs": "LLM Bridge 工單", "workers": "LLM Bridge 電腦", "enrollments": "LLM Bridge 綁定碼",
                "usage": "LLM Bridge 用量", "prefs": "LLM Bridge 優先順序"}
FIELD_LABELS = {
    "lookup_key": "查詢鍵", "owner": "擁有者", "source": "來源 app", "provider": "後端", "model": "模型",
    "status": "狀態", "worker_key": "worker", "session": "對話 id", "request_json": "請求(暫存)",
    "partial_text": "逐段文字", "result_json": "結果", "error_json": "錯誤", "attempts": "嘗試次數",
    "created_ts": "建立時間(epoch 秒)", "lease_until_ts": "租約到期(epoch 秒)", "done_ts": "完成時間(epoch 秒)",
    "key_hash": "設備鑰匙雜湊", "name": "名稱", "os": "作業系統", "version": "版本", "models": "可用模型",
    "last_seen_ts": "最後心跳(epoch 秒)", "code_hash": "綁定碼雜湊", "expires_ts": "到期(epoch 秒)",
    "used_ts": "使用時間(epoch 秒)", "served_by": "實際回答的模型", "http_status": "HTTP 狀態", "stream": "串流",
    "prompt_tokens": "輸入 token", "completion_tokens": "輸出 token", "cost_usd": "成本(美元)",
    "duration_ms": "耗時(毫秒)", "priority": "優先使用(local / cloud)", "updated_ts": "更新時間(epoch 秒)",
}


def physical_fields(logical: str) -> dict[str, str]:
    return {AigoStore.FIELD_MAP.get(name, name): ftype for name, ftype in SCHEMA[logical].items()}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="biz_bridge_")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.prefix.startswith("biz_"):
        print("⚠ 平台慣例:自建表實體名一律 biz_ 開頭。確定要用其他前綴嗎?(繼續執行)")

    with client() as c:
        resp = c.get("/api/v1/data-center/tables")
        if resp.status_code >= 400:
            print("讀不到租戶的表清單:", resp.status_code, resp.text[:200])
            return 1
        existing = {t["physical_name"]: t for t in items(resp.json())}
        similar = sorted(n for n in existing if "bridge" in n or "llm" in n)
        print(f"租戶現有 {len(existing)} 張自建表;名稱相近的:{similar or '無'}")

        for logical in SCHEMA:
            table = args.prefix + logical
            wanted = physical_fields(logical)
            if table in existing:
                have = {f["physical_name"] for f in existing[table].get("fields") or []}
                missing = {k: v for k, v in wanted.items() if k not in have}
                print(f"\n{table}:已存在,缺 {len(missing)} 個欄位 {sorted(missing) or ''}")
                if not args.apply:
                    continue
                for name, ftype in missing.items():
                    r = c.post(f"/api/v1/data-center/tables/{table}/fields",
                               json={"display_name": name, "field_type": ftype})
                    if r.status_code >= 300:
                        print(f"  ✗ 加欄 {name}:{r.status_code} {r.text[:200]}")
                        return 1
                    c.patch(f"/api/v1/data-center/tables/{table}/fields/{name}",
                            json={"display_name": FIELD_LABELS.get(name, name)})
                    print(f"  ✓ 加欄 {name}({ftype})")
                continue

            print(f"\n{table}:要新建,{len(wanted)} 個欄位")
            for name, ftype in wanted.items():
                print(f"  {name:<18} {ftype:<8} {FIELD_LABELS.get(name, '')}")
            if not args.apply:
                continue
            r = c.post("/api/v1/data-center/tables", json={
                "display_name": table,
                "fields": [{"display_name": n, "field_type": t} for n, t in wanted.items()]})
            if r.status_code == 403:
                print("  ✗ 403:帳號缺 datacenter.schema_write。請租戶管理員照上面的規格代建(先用英文實體名建立)")
                return 1
            if r.status_code >= 300:
                print(f"  ✗ 建表失敗:{r.status_code} {r.text[:300]}")
                return 1
            created = r.json()
            if created.get("physical_name") != table:
                print(f"  ✗ 實體名是 {created.get('physical_name')},不是預期的 {table}。表還沒有資料,請確認後刪掉重建")
                return 1
            got = {f["physical_name"] for f in created.get("fields") or []}
            wrong = sorted(set(wanted) - got)
            if wrong:
                print(f"  ✗ 這些欄位的實體名不如預期:{wrong}。請確認後刪表重建")
                return 1
            # 第二步:顯示名改中文(實體名不變)
            c.patch(f"/api/v1/data-center/tables/{table}", json={"display_name": TABLE_LABELS[logical]})
            for name in wanted:
                c.patch(f"/api/v1/data-center/tables/{table}/fields/{name}",
                        json={"display_name": FIELD_LABELS.get(name, name)})
            print(f"  ✓ 已建立並設定中文顯示名({TABLE_LABELS[logical]})")

    if not args.apply:
        print("\n(只是計畫;加 --apply 才會動手)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
