#!/usr/bin/env bash
# Повреждённый VFS (невалидный base64) — демонстрирует сообщение об
# ошибке загрузки из-за неверного формата, приложение не падает.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --vfs examples/vfs_bad.csv
