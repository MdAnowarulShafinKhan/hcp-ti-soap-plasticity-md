from pathlib import Path
import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIM_ROOT = PROJECT_ROOT / "simulations"


def find_cases():
    out=[]
    for d in sorted(SIM_ROOT.iterdir()):
        if d.is_dir() and (d/"metadata.json").exists():
            meta=json.loads((d/"metadata.json").read_text())
            meta["dir"]=d
            out.append(meta)
    return out


def read_csv(path):
    path=Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def cell_lengths_from_ovito(data):
    M=np.asarray(data.cell)
    a,b,c=M[:,0],M[:,1],M[:,2]
    return float(np.linalg.norm(a)), float(np.linalg.norm(b)), float(np.linalg.norm(c))
