#!/usr/bin/env python3
"""Compute sampled local SOAP and frame-averaged SOAP for every trajectory.

Design choices for deadline-feasible analysis:
- 1000 fixed atom IDs per case (or all atoms if smaller), tracked across frames.
- Ti only, periodic SOAP, r_cut=5.0 A, n_max=6, l_max=6, sigma=0.5 A.
- Local vectors are stored float32 for the optional anomaly detector.
- The mean SOAP vector for each frame is L2-normalized for structural distances/MDS.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from common import find_cases, cell_lengths_from_ovito
from ovito.io import import_file
from ase import Atoms
from dscribe.descriptors import SOAP

N_SAMPLE=1000
SEED=20260915
SOAP_KW=dict(species=['Ti'], periodic=True, r_cut=5.0, n_max=6, l_max=6,
             sigma=0.5, average='off', sparse=False, dtype='float32')


def to_ase(data):
    M=np.asarray(data.cell)
    cell=M[:,:3].T  # OVITO stores cell vectors as columns; ASE expects rows.
    pos=np.asarray(data.particles.positions)
    atoms=Atoms(symbols=['Ti']*len(pos), positions=pos, cell=cell, pbc=tuple(data.cell.pbc))
    return atoms


def analyze(meta):
    d=meta['dir']; traj=d/'output'/'trajectory.lammpstrj'; post=d/'post'
    if not traj.exists():
        print(f"SKIP {meta['label']}: no trajectory")
        return
    post.mkdir(exist_ok=True)
    pipe=import_file(str(traj), multiple_frames=True)
    first=pipe.compute(0)
    ids0=np.asarray(first.particles['Particle Identifier'],dtype=np.int64)
    rng=np.random.default_rng(SEED)
    sample_ids=np.sort(rng.choice(ids0,size=min(N_SAMPLE,len(ids0)),replace=False))
    soap=SOAP(**SOAP_KW)
    feature_count=soap.get_number_of_features()
    global_vecs=[]; local_vecs=[]; local_frame=[]; local_strain=[]; local_id=[]; rows=[]
    lz0=None
    for f in range(pipe.source.num_frames):
        data=pipe.compute(f)
        _,_,lz=cell_lengths_from_ovito(data)
        if lz0 is None: lz0=lz
        strain=(lz0-lz)/lz0
        ids=np.asarray(data.particles['Particle Identifier'],dtype=np.int64)
        # Map persistent sampled IDs to current array indices.
        order=np.argsort(ids); sorted_ids=ids[order]
        loc=np.searchsorted(sorted_ids,sample_ids)
        valid=(loc < len(sorted_ids)) & (sorted_ids[np.minimum(loc,len(sorted_ids)-1)]==sample_ids)
        centers=order[loc[valid]]
        sid=sample_ids[valid]
        atoms=to_ase(data)
        X=np.asarray(soap.create(atoms, centers=centers, n_jobs=1),dtype=np.float32)
        g=X.mean(axis=0).astype(np.float64)
        norm=np.linalg.norm(g)
        if norm>0: g/=norm
        global_vecs.append(g.astype(np.float32))
        local_vecs.append(X)
        local_frame.append(np.full(len(X),f,dtype=np.int32))
        local_strain.append(np.full(len(X),strain,dtype=np.float32))
        local_id.append(sid.astype(np.int64))
        rows.append({'frame':f,'timestep':int(data.attributes.get('Timestep',f)),'strain':strain,'n_sample':len(X)})
        print(f"  {meta['short']}: frame {f+1}/{pipe.source.num_frames}, strain={100*strain:.2f}%")
    G=np.vstack(global_vecs)
    L=np.vstack(local_vecs)
    np.savez_compressed(post/'soap_global.npz', descriptors=G)
    np.savez_compressed(post/'soap_local_samples.npz', descriptors=L,
                        frame=np.concatenate(local_frame), strain=np.concatenate(local_strain),
                        atom_id=np.concatenate(local_id))
    pd.DataFrame(rows).to_csv(post/'soap_frames.csv',index=False)
    config={'sample_atoms':int(len(sample_ids)), 'sample_seed':SEED, 'feature_count':int(feature_count), **SOAP_KW}
    # dtype isn't JSON serializable as a NumPy object here; SOAP_KW contains strings/numbers only.
    (post/'soap_config.json').write_text(json.dumps(config,indent=2))
    print(f"OK SOAP: {meta['label']} -> {G.shape[0]} global frames, {L.shape[0]} local environments")

if __name__=='__main__':
    for m in find_cases(): analyze(m)
