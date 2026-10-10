#!/usr/bin/env bash
# Этап 4: демонстрация команды clear — после неё экран пустеет.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --vfs examples/vfs_stage4.csv \
    --script examples/stage4_clear.txt
