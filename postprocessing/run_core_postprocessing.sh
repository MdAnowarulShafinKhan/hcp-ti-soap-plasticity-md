#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
python3 00_validate_inputs.py
python3 01_mechanics.py
# 02_ptm.py and 03_soap.py require raw trajectory.lammpstrj files.
# Run them after fresh MD simulations if you want to recompute descriptors from atoms.
# The repository already contains the processed PTM and global SOAP products used in the figures.
python3 04_build_soap_map.py
python3 06_make_figures.py
python3 07_build_summary_workbook.py
