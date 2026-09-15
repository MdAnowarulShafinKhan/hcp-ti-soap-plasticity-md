from pathlib import Path
import json
import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

ROOT=Path(__file__).resolve().parents[1]
SIM=ROOT/'simulations'
RES=ROOT/'results'; RES.mkdir(exist_ok=True)
case_dirs=[SIM/'01_Ti4k_1e9',SIM/'02_Ti32k_1e9',SIM/'03_Ti108k_1e9',SIM/'04_Ti108k_1e10']

mech_rows=[]; eq_rows=[]; ptm_rows=[]; soap_rows=[]; diag_rows=[]
for d in case_dirs:
    meta=json.loads((d/'metadata.json').read_text())
    met=json.loads((d/'post'/'metrics.json').read_text())
    case=meta['label']
    sm=met['smoothing']; eq=met['equilibration']
    mech_rows.append({
        'case':case,'atoms':meta['atoms'],'strain_rate_s^-1':meta['strain_rate_s-1'],
        'elastic_modulus_GPa_2-10%':met['elastic_modulus_GPa_fit_2to10pct'],
        'yield_strain_%':met['yield_strain_percent'],'yield_stress_GPa':met['yield_stress_GPa'],
        'stress_drop_GPa_next_3%':met['stress_drop_GPa_next_3pct'],
        'flow_stress_mean_GPa_20-25%':met['flow_stress_mean_GPa_20to25pct'],
        'flow_stress_std_GPa_20-25%':met['flow_stress_std_GPa_20to25pct'],
        'smoothing_method':sm['method'],'smoothing_target_%':sm['target_width_percent'],
        'smoothing_points':sm['window_points'],'smoothing_effective_span_%':sm['effective_span_percent'],
    })
    eq_rows.append({'case':case,'T_mean_K_final20ps':eq['T_mean_K'],'T_std_K':eq['T_std_K'],
                    'P_hydro_mean_bar':eq['P_mean_bar'],'P_hydro_std_bar':eq['P_std_bar'],
                    'Pxx_mean_bar':eq['Pxx_mean_bar'],'Pyy_mean_bar':eq['Pyy_mean_bar'],'Pzz_mean_bar':eq['Pzz_mean_bar']})
    p=pd.read_csv(d/'post'/'ptm_fractions.csv').sort_values('strain')
    i_min=p['hcp_fraction'].idxmin(); rmin=p.loc[i_min]
    # first clear HCP loss >1 percentage point
    onset=p[p['hcp_fraction']<0.99]
    onset_str=float(onset.iloc[0]['strain']*100) if len(onset) else np.nan
    r25=p.iloc[(p['strain']-0.25).abs().argmin()]
    ptm_rows.append({'case':case,'PTM_HCP_loss_onset_%_HCP<99%':onset_str,
                     'minimum_HCP_%':100*rmin['hcp_fraction'],'strain_at_min_HCP_%':100*rmin['strain'],
                     'HCP_at_25%_%':100*r25['hcp_fraction'],'FCC_at_25%_%':100*r25['fcc_fraction'],
                     'BCC_at_25%_%':100*r25['bcc_fraction'],'Other_at_25%_%':100*r25['other_fraction'],
                     'PTM_RMSD_cutoff':0.15})
    s=pd.read_csv(d/'post'/'soap_distance.csv').sort_values('strain')
    row={'case':case}
    for target in [0.10,0.15,0.16,0.25]:
        rr=s.iloc[(s['strain']-target).abs().argmin()]
        row[f'SOAP_distance_at_{int(target*100)}%']=float(rr['soap_distance_from_ref'])
    soap_rows.append(row)
    m=pd.read_csv(d/'output'/'mechanics.csv')
    band=m[(m['strain']>=0.10)&(m['strain']<=0.22)]
    imax=band['temp_K'].idxmax(); tr=band.loc[imax]
    diag_rows.append({'case':case,'max_temperature_K_10-22%':tr['temp_K'],'strain_at_Tmax_%':100*tr['strain']})

mech=pd.DataFrame(mech_rows); eq=pd.DataFrame(eq_rows); ptm=pd.DataFrame(ptm_rows); soap=pd.DataFrame(soap_rows); diag=pd.DataFrame(diag_rows)
quality=json.loads((ROOT/'postprocessing'/'aggregate'/'soap_mds_quality.json').read_text())
mds=pd.DataFrame([{'n_frames':quality['n_frames'],'Kruskal_Stress_1':quality['kruskal_stress_1'],'distance_Pearson_r':quality['distance_pearson_r']}])

for name,df in [('mechanical_summary.csv',mech),('equilibration_summary.csv',eq),('ptm_summary.csv',ptm),('soap_summary.csv',soap),('temperature_diagnostics.csv',diag),('mds_quality.csv',mds)]:
    df.to_csv(RES/name,index=False)

# Combined markdown table for README/reference
summary=mech[['case','atoms','strain_rate_s^-1','elastic_modulus_GPa_2-10%','yield_strain_%','yield_stress_GPa','flow_stress_mean_GPa_20-25%']].copy()
summary.to_csv(RES/'headline_results.csv',index=False)

# XLSX workbook
wb=Workbook(); wb.remove(wb.active)
sets=[('Mechanical',mech),('Equilibration',eq),('PTM',ptm),('SOAP',soap),('Temperature',diag),('MDS quality',mds)]
header_fill=PatternFill('solid', fgColor='1F4E78')
header_font=Font(color='FFFFFF',bold=True)
imported_font=Font(color='008000')
static_font=Font(color='666666')
section_fill=PatternFill('solid', fgColor='D9EAF7')
thin=Side(style='thin', color='D9E1F2')
for title,df in sets:
    ws=wb.create_sheet(title)
    for c,col in enumerate(df.columns,1):
        cell=ws.cell(1,c,col); cell.fill=header_fill; cell.font=header_font; cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
    for r,row in enumerate(df.itertuples(index=False,name=None),2):
        for c,val in enumerate(row,1):
            cell=ws.cell(r,c,val.item() if isinstance(val,np.generic) else val)
            cell.border=Border(bottom=thin)
            cell.font=imported_font
            if isinstance(cell.value,float): cell.number_format='0.0000'
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    ws.sheet_view.showGridLines=False
    for i,col in enumerate(df.columns,1):
        maxlen=max(len(str(col)),*(len(str(ws.cell(r,i).value or '')) for r in range(2,ws.max_row+1)))
        ws.column_dimensions[get_column_letter(i)].width=min(max(maxlen+2,12),34)
    ws.row_dimensions[1].height=32

# Readme sheet explains interpretation
ws=wb.create_sheet('Notes')
notes=[
('Purpose','Compact GitHub-ready summary of the four completed HCP Ti compression simulations and post-processing.'),
('Mechanical smoothing','Savitzky-Golay smoothing is selected from a target 0.5% engineering-strain width, not a fixed row count. SciPy is required; the script fails explicitly if unavailable.'),
('PTM interpretation','HCP/FCC/BCC/Other values are local PTM template classifications (RMSD cutoff 0.15), not equilibrium bulk phase fractions.'),
('SOAP interpretation','SOAP distance measures change from the equilibrated 0% reference descriptor; it is not a monotonic disorder parameter.'),
('MDS quality',f"Kruskal Stress-1 = {quality['kruskal_stress_1']:.6f}; pairwise-distance Pearson r = {quality['distance_pearson_r']:.6f}."),
('Raw trajectory policy','LAMMPS trajectories and restart binaries are intentionally not included because the 108k trajectories exceed GitHub regular-file limits. Input files, selected states, scalar outputs and processed PTM/SOAP products are included so Drive is not required.'),
]
ws.append(['Topic','Note'])
for c in ws[1]: c.fill=header_fill; c.font=header_font
for row in notes: ws.append(row)
ws.column_dimensions['A'].width=28; ws.column_dimensions['B'].width=115
for row in ws.iter_rows():
    for cell in row:
        cell.alignment=Alignment(vertical='top',wrap_text=True)
        if cell.row > 1: cell.font=static_font
ws.sheet_view.showGridLines=False; ws.freeze_panes='A2'

ref=wb.create_sheet('References')
ref.append(['Source','URL'])
for c in ref[1]: c.fill=header_fill; c.font=header_font
refs=[
    ('Safari & Konstantinou HCP Ti study','https://arxiv.org/abs/2606.28155'),
    ('Kim-Lee-Baskes Ti MEAM paper','https://doi.org/10.1103/PhysRevB.74.014101'),
    ('NIST/OpenKIM Ti potential entry','https://www.ctcms.nist.gov/potentials/entry/2006--Kim-Y-M-Lee-B-J-Baskes-M-I--Ti/'),
    ('OVITO PTM documentation','https://www.ovito.org/manual/reference/pipelines/modifiers/polyhedral_template_matching.html'),
    ('DScribe SOAP documentation','https://singroup.github.io/dscribe/latest/tutorials/descriptors/soap.html'),
]
for row in refs: ref.append(row)
for row in ref.iter_rows(min_row=2):
    for cell in row: cell.font=imported_font; cell.alignment=Alignment(vertical='top',wrap_text=True)
ref.column_dimensions['A'].width=38; ref.column_dimensions['B'].width=95
ref.sheet_view.showGridLines=False; ref.freeze_panes='A2'

xlsx=RES/'results_summary.xlsx'; wb.save(xlsx)
# verify load
check=load_workbook(xlsx, read_only=True, data_only=False)
assert set(['Mechanical','Equilibration','PTM','SOAP','Temperature','MDS quality','Notes','References']).issubset(check.sheetnames)
check.close()

print('Mechanical\n',mech.to_string(index=False))
print('\nPTM\n',ptm.to_string(index=False))
print('\nSOAP\n',soap.to_string(index=False))
print('\nTemp\n',diag.to_string(index=False))
print('\nMDS',quality)
print('Wrote',xlsx)
