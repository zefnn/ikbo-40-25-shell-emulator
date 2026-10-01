#!/usr/bin/env bash
# Путь к стартовому скрипту не существует — демонстрирует сообщение об
# ошибке исполнения стартового скрипта, само приложение при этом не падает.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --script examples/no_such_script.txt
