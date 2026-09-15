#!/usr/bin/env python3
"""Generate publication-style project figures from included processed results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from common import find_cases

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
FIG.mkdir(exist_ok=True)
AGG = Path(__file__).resolve().parent / 'aggregate'
cases = {m['short']: m for m in find_cases()}


def mech(key):
    return pd.read_csv(cases[key]['dir'] / 'post' / 'mechanics_processed.csv')


def ptm(key):
    return pd.read_csv(cases[key]['dir'] / 'post' / 'ptm_fractions.csv')


def soapd(key):
    return pd.read_csv(cases[key]['dir'] / 'post' / 'soap_distance.csv')


def finish(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Wrote', path)


# Main Fig. 1: mechanical response (size + rate)
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for k in ['4k_1e9', '32k_1e9', '108k_1e9']:
    d = mech(k)
    ax[0].plot(100*d.strain, d.sigma_zz_GPa, label=cases[k]['label'].split(',')[0])
ax[0].set(xlabel='Compressive strain (%)', ylabel='Axial stress (GPa)',
          title=r'System-size comparison at $10^9$ s$^{-1}$')
ax[0].legend()
for k in ['108k_1e9', '108k_1e10']:
    d = mech(k)
    rate = r'$10^9$ s$^{-1}$' if k.endswith('1e9') else r'$10^{10}$ s$^{-1}$'
    ax[1].plot(100*d.strain, d.sigma_zz_GPa, label=rate)
ax[1].set(xlabel='Compressive strain (%)', ylabel='Axial stress (GPa)',
          title='Strain-rate comparison (108k atoms)')
ax[1].legend()
finish(fig, FIG/'Fig1_mechanical_response.png')

# Main Fig. 2: PTM size effect
fig, axs = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
fields = [('hcp_fraction','HCP'), ('fcc_fraction','FCC'), ('bcc_fraction','BCC'), ('other_fraction','Other')]
for a, (field, title) in zip(axs.ravel(), fields):
    for k in ['4k_1e9', '32k_1e9', '108k_1e9']:
        d = ptm(k)
        a.plot(100*d.strain, 100*d[field], label=cases[k]['label'].split(',')[0])
    a.set_title(title)
    a.set_ylabel('PTM-classified fraction (%)')
    a.set_xlabel('Compressive strain (%)')
axs[0,0].legend()
finish(fig, FIG/'Fig2_ptm_size_effect.png')

# Main Fig. 3: SOAP MDS map
md = pd.read_csv(AGG/'soap_mds_map.csv')
fig, ax = plt.subplots(figsize=(7,5))
markers = {'4k_1e9':'o', '32k_1e9':'s', '108k_1e9':'^', '108k_1e10':'D'}
norm = Normalize(vmin=float(100*md.strain.min()), vmax=float(100*md.strain.max()))
sc = None
for k, g in md.groupby('case'):
    sc = ax.scatter(g.mds1, g.mds2, c=100*g.strain, norm=norm,
                    s=28, marker=markers.get(k,'o'), label=cases[k]['label'])
cb = fig.colorbar(sc, ax=ax)
cb.set_label('Compressive strain (%)')
qfile = AGG/'soap_mds_quality.json'
qtxt = ''
if qfile.exists():
    q = json.loads(qfile.read_text())
    qtxt = f"\nStress-1 = {q['kruskal_stress_1']:.4f}; distance r = {q['distance_pearson_r']:.5f}"
ax.set(xlabel='MDS coordinate 1', ylabel='MDS coordinate 2',
       title='SOAP structural map' + qtxt)
ax.legend(fontsize=8)
finish(fig, FIG/'Fig3_soap_mds_map.png')

# Main Fig. 4: SOAP distance from equilibrated reference
fig, ax = plt.subplots(1, 2, figsize=(10,4))
for k in ['4k_1e9', '32k_1e9', '108k_1e9']:
    d = soapd(k)
    ax[0].plot(100*d.strain, d.soap_distance_from_ref, label=cases[k]['label'].split(',')[0])
ax[0].set(xlabel='Compressive strain (%)', ylabel='SOAP distance from 0% state',
          title='System-size comparison')
ax[0].legend()
for k in ['108k_1e9', '108k_1e10']:
    d = soapd(k)
    rate = r'$10^9$ s$^{-1}$' if k.endswith('1e9') else r'$10^{10}$ s$^{-1}$'
    ax[1].plot(100*d.strain, d.soap_distance_from_ref, label=rate)
ax[1].set(xlabel='Compressive strain (%)', ylabel='SOAP distance from 0% state',
          title='Strain-rate comparison')
ax[1].legend()
finish(fig, FIG/'Fig4_soap_distance.png')

# Main Fig. 5: coupled transition for primary 108k/1e9 case
k = '108k_1e9'
m = mech(k); p = ptm(k); s = soapd(k)
metrics = json.loads((cases[k]['dir']/'post'/'metrics.json').read_text())
y = 100*metrics['yield_strain']
fig, axs = plt.subplots(3, 1, figsize=(7,8), sharex=True)
axs[0].plot(100*m.strain, m.sigma_zz_GPa, linewidth=1.0, alpha=0.7, label='Raw')
axs[0].plot(100*m.strain, m.sigma_zz_smooth_GPa, linewidth=1.6, label='0.5% strain-window smooth')
axs[0].set_ylabel('Axial stress (GPa)'); axs[0].legend(fontsize=8)
axs[1].plot(100*p.strain, 100*p.hcp_fraction); axs[1].set_ylabel('PTM HCP fraction (%)')
axs[2].plot(100*s.strain, s.soap_distance_from_ref); axs[2].set_ylabel('SOAP distance'); axs[2].set_xlabel('Compressive strain (%)')
for a in axs:
    a.axvline(y, linestyle='--', linewidth=1)
    a.grid(alpha=0.2)
axs[0].set_title(rf'Coupled transition: 108k Ti at $10^9$ s$^{{-1}}$; mechanical peak at {y:.2f}%')
finish(fig, FIG/'Fig5_coupled_transition.png')

# S1: temperature equilibration
fig, axs = plt.subplots(2, 2, figsize=(10,7), sharex=False)
for a, k in zip(axs.ravel(), ['4k_1e9','32k_1e9','108k_1e9','108k_1e10']):
    d = pd.read_csv(cases[k]['dir']/'output'/'equilibration.csv')
    a.plot(d.time_ps, d.temp_K)
    a.axhline(300.0, linestyle='--', linewidth=1)
    a.set_title(cases[k]['label']); a.set_xlabel('Time (ps)'); a.set_ylabel('Temperature (K)')
finish(fig, FIG/'FigS1_equilibration_temperature.png')

# S2: PTM rate effect
fig, axs = plt.subplots(2, 2, figsize=(10,7), sharex=True)
for a, (field,title) in zip(axs.ravel(), fields):
    for k in ['108k_1e9','108k_1e10']:
        d = ptm(k)
        rate = r'$10^9$ s$^{-1}$' if k.endswith('1e9') else r'$10^{10}$ s$^{-1}$'
        a.plot(100*d.strain, 100*d[field], label=rate)
    a.set_title(title); a.set_ylabel('PTM-classified fraction (%)'); a.set_xlabel('Compressive strain (%)')
axs[0,0].legend()
finish(fig, FIG/'FigS2_ptm_rate_effect.png')

# S3: exploratory anomaly detector, if previously computed.
af = AGG/'anomaly_scores.csv'
if af.exists():
    d = pd.read_csv(af)
    fig, ax = plt.subplots(figsize=(7,4))
    for k, g in d.groupby('case'):
        ax.plot(100*g.strain, g.anomaly_fraction, label=cases[k]['label'])
    ax.set(xlabel='Compressive strain (%)', ylabel='Anomalous sampled environments (fraction)',
           title='Exploratory Isolation Forest: departure from <=10% elastic training manifold')
    ax.legend(fontsize=8)
    finish(fig, FIG/'FigS3_anomaly_detector_exploratory.png')

# S4: transient temperature during deformation for 108k rate comparison
fig, ax = plt.subplots(figsize=(7,4))
for k in ['108k_1e9','108k_1e10']:
    d = pd.read_csv(cases[k]['dir']/'output'/'mechanics.csv')
    rate = r'$10^9$ s$^{-1}$' if k.endswith('1e9') else r'$10^{10}$ s$^{-1}$'
    ax.plot(100*d.strain, d.temp_K, label=rate)
ax.axhline(300.0, linestyle='--', linewidth=1)
ax.set_xlim(10, 22)
ax.set(xlabel='Compressive strain (%)', ylabel='Instantaneous temperature (K)',
       title='Transient plastic heating near the transition (108k atoms)')
ax.legend()
finish(fig, FIG/'FigS4_temperature_near_yield.png')

# S5: equilibration pressure components; iso NPT targets mean/hydrostatic pressure.
fig, axs = plt.subplots(2, 2, figsize=(10,7), sharex=False)
for a, k in zip(axs.ravel(), ['4k_1e9','32k_1e9','108k_1e9','108k_1e10']):
    d = pd.read_csv(cases[k]['dir']/'output'/'equilibration.csv')
    a.plot(d.time_ps, d.press_bar, label='P')
    a.plot(d.time_ps, d.pxx_bar, label='Pxx', alpha=0.75)
    a.plot(d.time_ps, d.pyy_bar, label='Pyy', alpha=0.75)
    a.plot(d.time_ps, d.pzz_bar, label='Pzz', alpha=0.75)
    a.axhline(0.0, linestyle='--', linewidth=0.8)
    a.set_title(cases[k]['label']); a.set_xlabel('Time (ps)'); a.set_ylabel('Pressure (bar)')
axs[0,0].legend(fontsize=8, ncol=2)
finish(fig, FIG/'FigS5_equilibration_pressure.png')
