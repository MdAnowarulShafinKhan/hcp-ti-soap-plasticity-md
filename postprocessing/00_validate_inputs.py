#!/usr/bin/env python3
"""Static sanity checks for supplied LAMMPS data and potential files."""
from pathlib import Path
import re, json
from common import find_cases

def check_data(path, expected):
    txt=path.read_text(errors='replace')
    m=re.search(r'^\s*(\d+)\s+atoms\s*$',txt,re.M)
    if not m: raise ValueError(f'No atom count in {path}')
    n=int(m.group(1))
    if n!=expected: raise ValueError(f'{path}: expected {expected}, got {n}')
    if 'Atoms # atomic' not in txt: raise ValueError(f'{path}: not atomic style')
    return n

for m in find_cases():
    d=m['dir']; n=check_data(d/m['data_file'],m['atoms'])
    lib=(d/'library.meam').read_text(); prm=(d/'Ti.meam').read_text()
    assert "'Ti'" in lib and "'hcp'" in lib
    assert 'nn2(1,1) = 1' in prm and 're(1,1) = 2.9200' in prm and 'rc = 4.8' in prm
    print(f"OK {m['folder'] if 'folder' in m else d.name}: {n} atoms, Ti 2NN-MEAM files present")
