#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -e ".[dev]"

rm -rf build dist

pyinstaller yomitan-fishaudio-bridge.spec --noconfirm --clean

echo
echo "== Готово =="
ls -la dist/
echo
echo "Запуск без Python:"
echo "  ./dist/yomitan-fishaudio-bridge"
