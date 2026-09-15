#!/usr/bin/env bash
set -euo pipefail
LMP_BIN="${LMP_BIN:-lmp}"
NP="${NP:-16}"
mkdir -p output
printf 'Running CPU MPI job with %s using %s ranks\n' "$LMP_BIN" "$NP"
mpirun -np "$NP" "$LMP_BIN" -in in.ti_compression.lmp | tee output/stdout.cpu.txt
