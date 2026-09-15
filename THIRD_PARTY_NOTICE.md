# Third-party data and potential notice

## Ti MEAM potential

The files `potentials/library.meam` and `potentials/Ti.meam` correspond to the Ti MEAM potential developed by Young-Min Kim, Byeong-Joo Lee, and M. I. Baskes:

> Y.-M. Kim, B.-J. Lee, M. I. Baskes, "Modified embedded-atom method interatomic potentials for Ti and Zr," *Physical Review B* **74**, 014101 (2006). DOI: 10.1103/PhysRevB.74.014101.

The model metadata identifies the OpenKIM/NIST entry `MEAM_LAMMPS_KimLeeBaskes_2006_Ti__MO_472654156677_001`, DOI `10.25950/f8f658f3`.

The original model-package license text is preserved as `potentials/POTENTIAL_LICENSE` (GNU LGPL v2.1). The accompanying `kimspec.edn`, `kimprovenance.edn`, and citation file are retained for provenance.

This repository does **not** claim authorship of the interatomic potential.

## Initial structures

`Ti_4k.lmp`, `Ti_32k.lmp`, and `Ti_108k.lmp` are ideal HCP Ti starting structures generated for this project. The crystal orientation is H1=[10-10], H2=[1-210], H3=[0001], with the [0001] c-axis aligned with the simulation z direction. The structures use HCP lattice parameters a = 2.95 Å and c = 4.68 Å and contain 4,000, 32,000, and 108,000 atoms, respectively.

The structures are included directly in the repository so that the molecular-dynamics workflow can be reproduced without an external file store.

## Project code

No project-wide software license is asserted by this package. Add a repository license only after deciding how you want your own scripts to be licensed; do not replace the potential model's original license notice.
