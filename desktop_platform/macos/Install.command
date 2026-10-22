#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")/../.."
if ! command -v python3 >/dev/null; then
  echo '請先安裝 Python 3.10 以上。'
  exit 1
fi
python3 desktop_platform/macos/install.py
read -r -p '按 Enter 關閉' _answer
