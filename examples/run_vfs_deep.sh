#!/usr/bin/env bash
# VFS с 3 уровнями вложенности, плюс стартовый скрипт со всеми командами
# и обоими видами ошибок — самый полный демонстрационный сценарий.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --vfs examples/vfs_deep.csv \
    --script examples/startup.txt
