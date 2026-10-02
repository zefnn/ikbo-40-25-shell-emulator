#!/usr/bin/env bash
# Несколько файлов и папок на верхнем уровне.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --vfs examples/vfs_several.csv
