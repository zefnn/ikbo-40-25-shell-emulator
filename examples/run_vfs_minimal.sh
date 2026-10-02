#!/usr/bin/env bash
# Минимальный VFS: один файл, без папок.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --vfs examples/vfs_minimal.csv
