# Audit findings and limitations

This GitHub-ready package was rebuilt from the completed simulation/post-processing archive and then revalidated locally. No new molecular-dynamics production simulation was run.

## Corrections applied during the audit

1. **Mechanical smoothing was corrected and re-executed.** The uploaded `01_mechanics.py` targeted a 0.5% strain window but silently fell back to unsmoothed data if SciPy could not be imported. The uploaded regenerated metrics therefore reported `method: none`. In this package SciPy is a required dependency; `01_mechanics.py` fails explicitly if it is unavailable. The mechanical metrics and Fig. 5 were regenerated with strain-normalized Savitzky-Golay smoothing.
2. **Per-case KOKKOS launchers were corrected.** All `run_kokkos_gpu.sh` files now use `newton on neigh half neigh/thread off gpu/aware off`, matching the MEAM requirement for Newton pair on.
3. **The top-level 3080 Ti runner was simplified.** The stale comment claiming a different 4k Newton profile was removed; all four runs now use the same valid MEAM/KOKKOS setting.
4. **Core vs optional post-processing was separated.** The core runner no longer executes the Isolation Forest automatically.
5. **MDS embedding quality is quantified.** `04_build_soap_map.py` now writes `soap_mds_quality.json`; the current 208-frame map has Stress-1 = 0.006706 and pairwise-distance Pearson r = 0.999947.
6. **The Isolation Forest is explicitly exploratory.** Its signal is interpreted as departure from the <=10% elastic training manifold, not as a validated yield/precursor detector.
7. **Additional diagnostics were added.** Temperature-vs-strain and equilibration pressure-component figures expose transient plastic heating and the distinction between hydrostatic and directional pressure under isotropic NPT.
8. **Repository hygiene was fixed.** Accidental `-p` folders, `Zone.Identifier`, `__pycache__`, stale root logs, raw restart files, raw trajectories, and the stale pre-run manifest are not included. A new manifest is generated for this package.

## Scientific limitations

- Four trajectories are analyzed: three sizes at 1e9 s^-1 and one 108k case at 1e10 s^-1. There are no independent stochastic replicas, so the repository does not claim statistical convergence.
- The systems are ideal periodic single crystals. The peak stress near 16.6-16.8 GPa should be treated as a defect-free mechanical peak/yield proxy, not conventional engineering yield strength.
- MD strain rates are very high compared with most experiments.
- PTM values are local template classifications. `Other` means a local neighborhood did not meet an enabled template under the selected RMSD threshold; it is not itself a thermodynamic phase.
- SOAP distance from the equilibrated 0% reference measures descriptor-space change, not a monotonic disorder parameter. Affine elastic strain contributes strongly before the transition.
- Isotropic NPT equilibration drives the *average/hydrostatic* diagonal pressure toward the target while scaling all box directions together; individual diagonal pressure components remain nonzero in these anisotropic HCP cells.
- Plastic deformation produces transient heating despite the thermostat. The 108k runs reach approximately 357 K near 15.79% strain at 1e9 s^-1 and 406 K near 18.2% strain at 1e10 s^-1.

## Large-file policy

Raw trajectories and restart binaries are intentionally not stored in the repository. The 108k trajectory files are about 178 MB each, which exceeds GitHub's 100 MiB regular-file limit. The 32k trajectory is about 52 MB, which triggers GitHub's large-file warning. All LAMMPS inputs, initial structures, potential files, scalar mechanics/equilibration outputs, selected equilibrated/final data states, processed PTM/SOAP products, figures, and tables are included. Thus the external Drive folder is not required to understand the results or reproduce the workflows; full trajectories can be regenerated from the included inputs.
