#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$ROOT/simulations"
LMP_BIN="${LMP_BIN:-}"
if [[ -z "$LMP_BIN" ]]; then
  if command -v lmp_gpu >/dev/null 2>&1; then LMP_BIN="$(command -v lmp_gpu)";
  elif command -v lmp >/dev/null 2>&1; then LMP_BIN="$(command -v lmp)";
  else echo "ERROR: lmp_gpu/lmp not found. Set LMP_BIN=/path/to/lmp_gpu"; exit 1; fi
fi
MPI_BIN="${MPI_BIN:-mpirun}"
GPU_ID="${GPU_ID:-0}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="$GPU_ID"
export OMP_NUM_THREADS=1
export OMP_DYNAMIC=FALSE
unset CUDA_LAUNCH_BLOCKING 2>/dev/null || true
KOKKOS_ARGS=(-k on g 1 -sf kk -pk kokkos newton on neigh half neigh/thread off gpu/aware off)
MPI_ARGS=(-np 1 --bind-to none)
SIMULATIONS=(01_Ti4k_1e9 02_Ti32k_1e9 03_Ti108k_1e9 04_Ti108k_1e10)
for sim in "${SIMULATIONS[@]}"; do
  d="$SIM_ROOT/$sim"
  mkdir -p "$d/output"
  if [[ "${FORCE_RERUN:-0}" != "1" && -s "$d/output/final.restart" ]]; then
    echo "=== $sim already completed; skipping ==="
    continue
  fi
  echo "=== STARTING $sim ==="
  (cd "$d" && "$MPI_BIN" "${MPI_ARGS[@]}" "$LMP_BIN" "${KOKKOS_ARGS[@]}" -in in.ti_compression.lmp 2>&1 | tee output/stdout.kokkos.3080ti.txt)
  if [[ ! -s "$d/output/final.restart" ]]; then echo "ERROR: $sim did not create output/final.restart"; exit 1; fi
  echo "=== COMPLETED $sim ==="
done
