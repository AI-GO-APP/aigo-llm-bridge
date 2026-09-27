"""執行期設定:全部從環境變數讀(Hosted App 的「環境變數」)。

必要
  BRIDGE_KEY__<SOURCE>      每個呼叫端一把金鑰;SOURCE 用大寫英數底線(例 BRIDGE_KEY__SALES_APP)
  BRIDGE_SESSION_SECRET     簽 session token 與內部簽章用;沒設就由所有 source 金鑰衍生(換金鑰會讓舊 token 失效)

後端(至少一個)
  ANTHROPIC_API_KEY         anthropic/* 用
  OPENROUTER_API_KEY        openrouter/* 用
  (local/* 不需要金鑰,靠使用者本人的 worker)

選填
  BRIDGE_DEFAULT_MODEL      沒有前綴的 model 要路由到哪裡(例 anthropic/claude-opus-5);未設 = 400
  BRIDGE_SYNC_TIMEOUT       同步呼叫最多等幾秒,預設 20(Server Action 經 egress 的硬牆是 30 秒)
  BRIDGE_TABLE_PREFIX       自建表名稱前綴,預設 bridge_
  BRIDGE_STORE_PROMPTS      1 = 把提示與回應原文存進工單表(除錯用),預設不存
  BRIDGE_ANTHROPIC_FALLBACKS off = 不對 claude-opus-5 / claude-fable-5-1 帶拒答後備
  BRIDGE_STORE              aigo(預設,容器內用平台自建表)或 memory(單機開發與測試)
  BRIDGE_PUBLIC_URL         對外網址(寫進 worker 安裝說明);沒設就由 AIGO_HOSTED_APP_SLUG 推
平台注入(不用自己設)
  AIGO_PLATFORM_API_URL、AIGO_API_TOKEN、AIGO_HOSTED_APP_SLUG
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field

VERSION = "0.1.0-dev"
_SOURCE_RE = re.compile(r"^BRIDGE_KEY__([A-Z0-9_]{1,40})$")


@dataclass(frozen=True)
class Settings:
    source_keys: dict[str, str] = field(default_factory=dict)
    session_secret: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    default_model: str = ""
    sync_timeout_s: float = 20.0
    table_prefix: str = "bridge_"
    store_prompts: bool = False
    anthropic_fallbacks: bool = True
    store_backend: str = "aigo"
    public_url: str = ""
    aigo_api_url: str = ""
    aigo_api_token: str = ""
    worker_heartbeat_ttl_s: int = 90
    lease_s: int = 60
    claim_wait_s: float = 25.0
    session_ttl_max_s: int = 3600
    version: str = VERSION


def _flag(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() not in ("0", "off", "false", "no")


def load(env: dict[str, str] | None = None) -> Settings:
    env = dict(os.environ if env is None else env)
    keys = {}
    for name, value in env.items():
        match = _SOURCE_RE.match(name)
        if match and value.strip():
            keys[match.group(1)] = value.strip()
    secret = env.get("BRIDGE_SESSION_SECRET", "").strip()
    if not secret and keys:
        joined = "|".join(f"{k}={keys[k]}" for k in sorted(keys))
        secret = hashlib.sha256(("bridge-session|" + joined).encode()).hexdigest()
    slug = env.get("AIGO_HOSTED_APP_SLUG", "").strip()
    public = env.get("BRIDGE_PUBLIC_URL", "").strip().rstrip("/") or (
        f"https://{slug}.deploy.ai-go.app" if slug else "")
    try:
        sync_timeout = float(env.get("BRIDGE_SYNC_TIMEOUT", "20") or 20)
    except ValueError:
        sync_timeout = 20.0
    return Settings(
        source_keys=keys,
        session_secret=secret,
        anthropic_api_key=env.get("ANTHROPIC_API_KEY", "").strip(),
        openrouter_api_key=env.get("OPENROUTER_API_KEY", "").strip(),
        default_model=env.get("BRIDGE_DEFAULT_MODEL", "").strip(),
        sync_timeout_s=max(1.0, min(sync_timeout, 280.0)),
        table_prefix=env.get("BRIDGE_TABLE_PREFIX", "bridge_").strip() or "bridge_",
        store_prompts=_flag(env.get("BRIDGE_STORE_PROMPTS"), False),
        anthropic_fallbacks=_flag(env.get("BRIDGE_ANTHROPIC_FALLBACKS"), True),
        store_backend=(env.get("BRIDGE_STORE", "aigo").strip() or "aigo").lower(),
        public_url=public,
        aigo_api_url=env.get("AIGO_PLATFORM_API_URL", "").strip().rstrip("/"),
        aigo_api_token=env.get("AIGO_API_TOKEN", "").strip(),
    )
