#!/usr/bin/env bash
# Этап 5: mkdir и mv над VFS в памяти + стартовый скрипт со всеми режимами
# и ошибками. CSV-файл при этом не меняется — правки живут только в памяти.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --vfs examples/vfs_stage4.csv \
    --script examples/stage5_startup.txt
