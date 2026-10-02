#!/usr/bin/env bash
# Путь к VFS не существует — демонстрирует сообщение об ошибке загрузки
# из-за отсутствия файла, приложение не падает.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --vfs examples/no_such_vfs.csv
