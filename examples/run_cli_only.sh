#!/usr/bin/env bash
# Все параметры заданы через командную строку, без конфигурационного файла.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --vfs examples/vfs.csv \
    --log examples/shellemu_log.xml \
    --script examples/startup.txt
