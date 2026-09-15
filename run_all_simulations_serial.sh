#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
for d in "$ROOT"/simulations/01_Ti4k_1e9 "$ROOT"/simulations/02_Ti32k_1e9 "$ROOT"/simulations/03_Ti108k_1e9 "$ROOT"/simulations/04_Ti108k_1e10; do
  echo "=== $(basename "$d") ==="
  (cd "$d" && ./run_cpu.sh)
done
