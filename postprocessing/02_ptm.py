#!/usr/bin/env python3
"""OVITO PTM analysis for every trajectory. Uses RMSD cutoff 0.15 to match the Ti paper."""
from pathlib import Path
import numpy as np
import pandas as pd
from common import find_cases, cell_lengths_from_ovito
from ovito.io import import_file
from ovito.modifiers import PolyhedralTemplateMatchingModifier

RMSD_CUTOFF=0.15


def analyze(meta):
    d=meta['dir']; traj=d/'output'/'trajectory.lammpstrj'; post=d/'post'
    if not traj.exists():
        print(f"SKIP {meta['label']}: no trajectory")
        return
    post.mkdir(exist_ok=True)
    pipeline=import_file(str(traj), multiple_frames=True)
    ptm=PolyhedralTemplateMatchingModifier(rmsd_cutoff=RMSD_CUTOFF, output_rmsd=True)
    pipeline.modifiers.append(ptm)
    rows=[]; lz0=None
    for f in range(pipeline.source.num_frames):
        data=pipeline.compute(f)
        _,_,lz=cell_lengths_from_ovito(data)
        if lz0 is None: lz0=lz
        strain=(lz0-lz)/lz0
        st=np.asarray(data.particles['Structure Type'])
        rmsd=np.asarray(data.particles['RMSD'])
        n=len(st)
        counts={k:int(np.count_nonzero(st==v)) for k,v in {'Other':0,'FCC':1,'HCP':2,'BCC':3}.items()}
        row={
            'frame':f, 'timestep':int(data.attributes.get('Timestep',f)), 'strain':strain,
            'other_fraction':counts['Other']/n, 'fcc_fraction':counts['FCC']/n,
            'hcp_fraction':counts['HCP']/n, 'bcc_fraction':counts['BCC']/n,
            'mean_ptm_rmsd':float(np.mean(rmsd)),
        }
        rows.append(row)
    pd.DataFrame(rows).to_csv(post/'ptm_fractions.csv',index=False)
    print(f"OK PTM: {meta['label']} ({len(rows)} frames)")

if __name__=='__main__':
    for m in find_cases(): analyze(m)
