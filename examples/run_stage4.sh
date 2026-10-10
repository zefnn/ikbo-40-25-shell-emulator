#!/usr/bin/env bash
# Этап 4: VFS с вложенностью, скрытыми файлами и файлами разных размеров
# + стартовый скрипт со всеми режимами ls/cd/cat/tail и обработкой ошибок.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --vfs examples/vfs_stage4.csv \
    --script examples/stage4_startup.txt
