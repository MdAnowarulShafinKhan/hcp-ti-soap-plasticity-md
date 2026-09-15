#!/usr/bin/env bash
set -euo pipefail
LMP_BIN="${LMP_BIN:-lmp}"
mkdir -p output
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OMP_DYNAMIC=FALSE
printf 'Running one-GPU KOKKOS job with %s\n' "$LMP_BIN"
mpirun -np 1 --bind-to none "$LMP_BIN" \
  -k on g 1 \
  -sf kk \
  -pk kokkos newton on neigh half neigh/thread off gpu/aware off \
  -in in.ti_compression.lmp | tee output/stdout.kokkos.txt
