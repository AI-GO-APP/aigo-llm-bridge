"""tools/scan_secrets.py 的規則。

假金鑰都在執行時拼出來,這個測試檔本身才不會被掃描器擋下。
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("scan_secrets", ROOT / "tools" / "scan_secrets.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

FILL = "A1b2C3d4E5f6G7h8J9k0" * 3

SHOULD_HIT = [
    "sk-" + "or-v1-" + FILL,
    "sk-" + "ant-api03-" + FILL,
    "gh" + "p_" + FILL,
    "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "-----BEGIN " + "RSA PRIVATE KEY-----",
    "BRIDGE_KEY__" + "SALES_APP=" + FILL,
    "OPENROUTER_API_KEY" + '="' + FILL + '"',
    "ey" + "J" + FILL + ".ey" + "J" + FILL + "." + FILL,
]

SHOULD_PASS = [
    "OPENROUTER_API_KEY=sk-or-...",
    "BRIDGE_KEY__<SOURCE>=<value>",
    "BRIDGE_KEY=...",
    "Authorization: Bearer <token>",
    "print(f\"BRIDGE_KEY__{source}={secrets.token_urlsafe(32)}\")",
    "OPENROUTER_API_KEY=mock",
]


@pytest.mark.parametrize("line", SHOULD_HIT)
def test_hits(line):
    assert scan.scan_line("x:1", line)


@pytest.mark.parametrize("line", SHOULD_PASS)
def test_placeholders_pass(line):
    assert scan.scan_line("x:1", line) == []


def test_allow_marker():
    assert scan.scan_line("x:1", SHOULD_HIT[0] + "  # " + scan.ALLOW) == []


@pytest.mark.parametrize("name,forbidden", [
    ("bridge.env", True), (".env", True), (".env.local", True), (".banned-terms", True),
    ("worker.json", True), ("server.pem", True),
    ("bridge.env.example", False), ("package.json", False), ("envs.py", False),
])
def test_forbidden_names(name, forbidden):
    hit = bool(scan.FORBIDDEN_NAMES.match(name)) and not scan.FORBIDDEN_OK.search(name)
    assert hit is forbidden


def test_repo_is_clean():
    assert scan.scan_tracked() == []
