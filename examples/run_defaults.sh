#!/usr/bin/env bash
# Без единого параметра — показывает встроенные значения по умолчанию
# (прежде всего log_path) в отладочном выводе при запуске.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu
