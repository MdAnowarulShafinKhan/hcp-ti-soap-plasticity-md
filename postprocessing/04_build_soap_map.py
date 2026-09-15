#!/usr/bin/env python3
"""Build combined SOAP structural map, reference distances, and MDS quality metrics."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.manifold import MDS
from common import find_cases

OUT = Path(__file__).resolve().parent / 'aggregate'
OUT.mkdir(exist_ok=True)

vecs = []
rows = []
for meta in find_cases():
    post = meta['dir'] / 'post'
    f = post / 'soap_global.npz'
    m = post / 'soap_frames.csv'
    if not (f.exists() and m.exists()):
        print(f"SKIP {meta['label']}: SOAP results missing")
        continue
    G = np.load(f)['descriptors'].astype(float)
    G /= np.maximum(np.linalg.norm(G, axis=1, keepdims=True), 1e-15)
    fm = pd.read_csv(m)
    if len(G) != len(fm):
        raise ValueError(f"{meta['label']}: SOAP vector/frame count mismatch")
    ref = G[0]
    dist = np.sqrt(np.clip(2.0 - 2.0 * (G @ ref), 0.0, None))
    out = fm.copy()
    out['case'] = meta['short']
    out['label'] = meta['label']
    out['soap_distance_from_ref'] = dist
    out.to_csv(post / 'soap_distance.csv', index=False)
    for i in range(len(G)):
        vecs.append(G[i])
        rows.append({
            'case': meta['short'],
            'label': meta['label'],
            'frame': int(fm.iloc[i].frame),
            'strain': float(fm.iloc[i].strain),
        })

if not vecs:
    raise SystemExit('No SOAP outputs found. Run 03_soap.py first.')

X = np.vstack(vecs)
D = np.sqrt(np.clip(2.0 - 2.0 * (X @ X.T), 0.0, None))

mds = MDS(
    n_components=2,
    dissimilarity='precomputed',
    random_state=42,
    n_init=8,
    max_iter=1000,
)
Y = mds.fit_transform(D)

df = pd.DataFrame(rows)
df['mds1'] = Y[:, 0]
df['mds2'] = Y[:, 1]
df.to_csv(OUT / 'soap_mds_map.csv', index=False)
np.save(OUT / 'soap_distance_matrix.npy', D)

# Quantify how faithfully the 2-D embedding preserves SOAP-space distances.
DY = np.sqrt(np.sum((Y[:, None, :] - Y[None, :, :]) ** 2, axis=2))
mask = np.triu(np.ones(D.shape, dtype=bool), k=1)
d0 = D[mask]
d2 = DY[mask]
valid = np.isfinite(d0) & np.isfinite(d2)
d0 = d0[valid]
d2 = d2[valid]

stress1 = float(np.sqrt(np.sum((d0 - d2) ** 2) / np.sum(d0 ** 2)))
pearson_r = float(np.corrcoef(d0, d2)[0, 1])
quality = {
    'n_frames': int(len(df)),
    'kruskal_stress_1': stress1,
    'distance_pearson_r': pearson_r,
    'description': 'Quality of 2-D MDS representation relative to normalized SOAP distances.'
}
(OUT / 'soap_mds_quality.json').write_text(json.dumps(quality, indent=2))

print(f"Wrote {OUT/'soap_mds_map.csv'} with {len(df)} frames")
print(f"MDS Stress-1={stress1:.6f}; distance Pearson r={pearson_r:.6f}")
