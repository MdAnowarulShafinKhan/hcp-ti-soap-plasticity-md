#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
python3 05_anomaly_detection_optional.py
python3 06_make_figures.py
