#!/usr/bin/env bash
set -euo pipefail

# HCP Ti starting structures used in this project
# Lattice parameters:
#   a = 2.95 Angstrom
#   c = 4.68 Angstrom
#
# Orientation:
#   H1 = [10-10]
#   H2 = [1-210]
#   H3 = [0001]

atomsk --create hcp 2.95 4.68 Ti orient [10-10] [1-210] [0001] \
  -orthogonal-cell -duplicate 10 10 10 Ti_4k.lmp

atomsk --create hcp 2.95 4.68 Ti orient [10-10] [1-210] [0001] \
  -orthogonal-cell -duplicate 20 20 20 Ti_32k.lmp

atomsk --create hcp 2.95 4.68 Ti orient [10-10] [1-210] [0001] \
  -orthogonal-cell -duplicate 30 30 30 Ti_108k.lmp

echo "Finished generating HCP Ti structures."
