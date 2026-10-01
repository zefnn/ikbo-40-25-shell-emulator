#!/usr/bin/env bash
# Конфиг задаёт один VFS, но CLI-флаг --vfs должен победить (приоритет CLI).
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu \
    --config examples/config.yaml \
    --vfs examples/vfs_override.csv
