#!/usr/bin/env bash
# Все параметры заданы через YAML-файл конфигурации, без CLI-флагов.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --config examples/config.yaml
