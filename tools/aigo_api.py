"""AI GO 平台 API 的最小連線層(部署工具共用)。

憑證來源,依序:
  1. 環境變數 AIGO_BASE_URL + AIGO_TOKEN(已取得的 access token)
  2. 已安裝的 aigo-builder skill 的 aigo_auth(自動登入、快取、換新 token)
     位置:環境變數 AIGO_SKILL_SCRIPTS,否則 ~/.claude/skills/aigo-builder/scripts
     工作區:環境變數 AIGO_WORKSPACE(含 .aigo/config.json 的目錄),否則目前目錄

AIGO_BASE_URL 必須是租戶空間 https://<your-tenant>.ai-go.app —— 打 apex 會回與「密碼錯誤」同形的 401。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx


def _from_skill() -> tuple[str, str]:
    scripts = Path(os.environ.get("AIGO_SKILL_SCRIPTS") or Path.home() / ".claude/skills/aigo-builder/scripts")
    if not (scripts / "aigo_auth.py").exists():
        raise SystemExit(
            "找不到憑證:請設定 AIGO_BASE_URL 與 AIGO_TOKEN,或安裝 aigo-builder skill 並設定工作區"
        )
    sys.path.insert(0, str(scripts))
    import aigo_auth  # type: ignore

    workspace = os.environ.get("AIGO_WORKSPACE", ".")
    return aigo_auth.resolve_base_url(workspace), aigo_auth.get_token(workspace)


def credentials() -> tuple[str, str]:
    base, token = os.environ.get("AIGO_BASE_URL", ""), os.environ.get("AIGO_TOKEN", "")
    if base and token:
        return base.rstrip("/"), token
    return _from_skill()


def client(timeout: float = 120) -> httpx.Client:
    base, token = credentials()
    return httpx.Client(base_url=base, headers={"Authorization": f"Bearer {token}"}, timeout=timeout)


def items(payload) -> list:
    """列表端點有時回陣列、有時回 {items: [...]}。"""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "data", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []
