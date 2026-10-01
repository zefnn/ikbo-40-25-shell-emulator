#!/usr/bin/env bash
# Намеренно сломанный YAML — демонстрирует сообщение об ошибке чтения конфига.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 -m shellemu --config examples/bad_config.yaml
