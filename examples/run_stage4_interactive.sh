#!/usr/bin/env bash
# Этап 4: та же VFS, но без скрипта — можно вводить команды руками.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --vfs examples/vfs_stage4.csv
