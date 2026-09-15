#!/usr/bin/env python3
"""Exploratory ML analysis: elastic-state Isolation Forest transfer test.

Trains ONLY on 32k, 1e9 s^-1 local SOAP environments at strain <=10%, then evaluates
all cases. This avoids random atom/frame leakage across train and test trajectories.
Higher anomaly_score and anomaly_fraction indicate departure from the <=10% elastic training manifold.
This is an out-of-distribution diagnostic, not a validated plastic-yield or precursor detector.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from common import find_cases

OUT=Path(__file__).resolve().parent/'aggregate'; OUT.mkdir(exist_ok=True)
cases=find_cases(); train=[m for m in cases if m['short']=='32k_1e9']
if not train: raise SystemExit('32k_1e9 case not found')
train=train[0]; train_file=train['dir']/'post'/'soap_local_samples.npz'
if not train_file.exists():
    raise SystemExit('soap_local_samples.npz is not included in the compact GitHub package. Recompute it with 03_soap.py after generating trajectories, then rerun this optional analysis.')
z=np.load(train_file)
X=z['descriptors'].astype(np.float32); s=z['strain']
Xtrain=X[s<=0.10]
# Cap training size for speed but keep a deterministic subset.
rng=np.random.default_rng(42)
if len(Xtrain)>30000: Xtrain=Xtrain[rng.choice(len(Xtrain),30000,replace=False)]
model=IsolationForest(n_estimators=300,contamination=0.02,random_state=42,n_jobs=-1)
model.fit(Xtrain)
rows=[]
for meta in cases:
    f=meta['dir']/'post'/'soap_local_samples.npz'
    if not f.exists(): continue
    z=np.load(f); X=z['descriptors'].astype(np.float32); frame=z['frame']; strain=z['strain']
    score=-model.decision_function(X)  # larger = more anomalous
    pred=model.predict(X)              # -1 = anomaly
    for fr in np.unique(frame):
        mask=frame==fr
        rows.append({'case':meta['short'],'label':meta['label'],'frame':int(fr),
                     'strain':float(np.mean(strain[mask])),
                     'anomaly_score_mean':float(np.mean(score[mask])),
                     'anomaly_fraction':float(np.mean(pred[mask]==-1))})
pd.DataFrame(rows).to_csv(OUT/'anomaly_scores.csv',index=False)
print(f'Wrote {OUT}/anomaly_scores.csv')
