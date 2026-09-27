#!/usr/bin/env python3
"""設定 Hosted App 的執行期環境變數(安全版:先讀現況,只合併你給的 key,其餘設定原樣送回)。

  python tools/hosted_env.py --slug <slug> --env-file path/to/values.env [--show]

平台的 PUT /runtime-settings 是**全量替換**:省略 env_vars 會清空、省略 always_on 會關常駐、
省略 persistent_disk 會卸載持久碟。所以這支一律先 GET 現況,只覆寫 env-file 裡有的 key,
其餘欄位照原值送回。

`resources`(每個 app 的 CPU/記憶體上限)只有專屬節點租戶能設,共用池租戶送了會 403,
所以預設**不送**;專屬節點租戶要保留自訂值時加 --keep-resources。

env_vars 有兩種回傳形狀(物件,或 [{key, value}] 陣列),照原形狀送回。
錯誤回應的 detail 可能回顯輸入值,所以只印欄位位置與訊息。

env-file 格式:KEY=VALUE 一行一個,# 開頭為註解。值不會被印出來。
--show 只列出現有的 key 與常駐設定,不寫入。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aigo_api import client, items  # noqa: E402


def read_env(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--env-file")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--keep-resources", action="store_true", help="專屬節點租戶:保留現有 resources")
    args = ap.parse_args()

    with client() as c:
        app = next((a for a in items(c.get("/api/v1/hosted-apps").json()) if a.get("slug") == args.slug), None)
        if not app:
            print("找不到這個 slug 的 Hosted App")
            return 1
        path = f"/api/v1/hosted-apps/{app['id']}/runtime-settings"
        current = c.get(path).json()
        raw_env = current.get("env_vars") or {}
        as_list = isinstance(raw_env, list)
        env = {i.get("key"): i.get("value") for i in raw_env if i.get("key")} if as_list else dict(raw_env)
        print("現有 key:", sorted(env),
              "| always_on:", current.get("always_on"), "| persistent_disk:", current.get("persistent_disk"))
        if args.show or not args.env_file:
            return 0

        updates = read_env(Path(args.env_file))
        merged = {**env, **updates}
        body = {
            "env_vars": [{"key": k, "value": v} for k, v in merged.items()] if as_list else merged,
            # 一律標 runtime:標 build 的值會寫進映像與建置日誌
            "env_availability": {**(current.get("env_availability") or {}), **{k: "runtime" for k in updates}},
            "always_on": bool(current.get("always_on")),
            "persistent_disk": bool(current.get("persistent_disk")),
        }
        if args.keep_resources and current.get("resources") is not None:
            body["resources"] = current["resources"]
        r = c.put(path, json=body)
        try:
            data = r.json()
        except ValueError:
            data = {}
        print("寫入:", r.status_code, "| 更新的 key:", sorted(updates), "| apply_state:",
              data.get("apply_state") if isinstance(data, dict) else None)
        if r.status_code >= 300:
            detail = data.get("detail") if isinstance(data, dict) else None
            for item in detail if isinstance(detail, list) else [detail]:
                print("  ", (item.get("loc"), item.get("msg")) if isinstance(item, dict) else str(item)[:160])
            return 1
        print("提醒:env 傳播到新 revision 需要數分鐘;用 /healthz 的版本標記或依賴那顆 env 的路徑確認後再判定")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
