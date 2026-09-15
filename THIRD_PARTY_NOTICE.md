# Third-party data and potential notice

## Ti MEAM potential

The files `potentials/library.meam` and `potentials/Ti.meam` correspond to the Ti MEAM potential developed by Young-Min Kim, Byeong-Joo Lee, and M. I. Baskes:

> Y.-M. Kim, B.-J. Lee, M. I. Baskes, "Modified embedded-atom method interatomic potentials for Ti and Zr," *Physical Review B* **74**, 014101 (2006). DOI: 10.1103/PhysRevB.74.014101.

The model metadata identifies the OpenKIM/NIST entry `MEAM_LAMMPS_KimLeeBaskes_2006_Ti__MO_472654156677_001`, DOI `10.25950/f8f658f3`.

The original model-package license text is preserved as `potentials/POTENTIAL_LICENSE` (GNU LGPL v2.1). The accompanying `kimspec.edn`, `kimprovenance.edn`, and citation file are retained for provenance.

This repository does **not** claim authorship of the interatomic potential.

## Initial structures

`Ti_4k.lmp`, `Ti_32k.lmp`, and `Ti_108k.lmp` were supplied as project inputs and correspond to the HCP Ti geometries used for the size-series study. Their orientation is H1=[10-10], H2=[1-210], H3=[0001]. They are included because the repository is intended to remain reproducible without an external file store.

## Project code

No project-wide software license is asserted by this package. Add a repository license only after deciding how you want your own scripts to be licensed; do not replace the potential model's original license notice.
