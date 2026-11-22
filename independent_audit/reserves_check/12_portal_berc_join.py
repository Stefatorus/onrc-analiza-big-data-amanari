"""Task 1c: is portal reqNumber the same counter as BERC app_nr? Which portal types reach BERC?
What are the numbers without companyId? Aggregates only."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import sys; sys.path.insert(0, str(config.REPO / 'independent_audit'))
from analyze_portal_snapshot import load
import pandas as pd, numpy as np
from scipy.stats import spearmanr
p = load(None)[['req_nr','s1_found','has_company_id','details_found','request_date','type_code','is_judged','phase_code','stage','solution','solution_term','last_update_date','initial_req_number','req_day']]
b = pd.read_pickle(str(config.BERC_PKL))[['cat','app_nr','app','res','sol']]
b = b[(b.app>='2026-01-01')]
FIN = ['Admis','Respins','Renunțat','Certificare înscriere în registrul comerțului','Renunțat din oficiu','ADMIS','certificare inscriere mentiuni']
b['fin'] = b.sol.isin(FIN)
b['cat']=b.cat.astype(str)
g = b.groupby('app_nr').agg(app=('app','min'), first_res=('res','min'), n=('cat','size'))
cs = b[['app_nr','cat']].drop_duplicates().sort_values('cat').groupby('app_nr').cat.agg('+'.join)
g['cats'] = cs
g['fin_res'] = b[b.fin].groupby('app_nr').res.min()
m = p.merge(g, left_on='req_nr', right_index=True, how='left')
m['inB'] = m.cats.notna()
print('probed', len(m), ' in BERC (2026 filings)', m.inB.sum())
print(pd.crosstab([m.details_found, m.has_company_id], m.inB, margins=True))
d = m[m.details_found & m.inB].copy()
d['rd'] = pd.to_datetime(d.request_date)
print('same-counter test: n', len(d), ' |request_date - app| <= 1 min:', ((d.rd - d.app).abs() <= pd.Timedelta('1min')).mean().round(4),
      ' same day:', (d.rd.dt.normalize() == d.app.dt.normalize()).mean().round(4))
print('spearman req_nr vs request_date (details):', round(spearmanr(m[m.details_found].req_nr, pd.to_datetime(m[m.details_found].request_date).astype('int64')).correlation, 6))
print('\nBY TYPE: share found in BERC; BERC category mix')
t = m[m.details_found].groupby('type_code').agg(n=('req_nr','size'), inB=('inB','mean'))
print(t.round(3).to_string())
print(pd.crosstab(m[m.details_found].type_code, m[m.details_found].cats.fillna('-')).to_string())
print('\nBY PHASE (details, judged): in BERC with a FINAL decision?')
dj = m[m.details_found & (m.is_judged == 1)].copy()
dj['has_fin'] = dj.fin_res.notna()
print(pd.crosstab(dj.phase_code, [dj.inB, dj.has_fin]).to_string())
print('\nNO companyId numbers (no details): in BERC by category')
nd = m[~m.details_found]
print(nd.cats.fillna('-').value_counts().to_string())
print('no-company numbers found in BERC as INMATRIC:', nd.cats.fillna('').str.contains('INMATRIC').sum(), 'of', len(nd))
# for details & judged & resolved-phase, share in BERC (BERC publication coverage of judged decisions)
res_ph = dj[dj.phase_code.isin(['12','13','14','15','27'])]
print('\nresolved-phase judged dossiers found in BERC with final:', res_ph.has_fin.mean().round(4), 'n', len(res_ph))
print(res_ph.groupby('type_code').has_fin.agg(['size','mean']).round(3).to_string())
live = dj[dj.phase_code.isin(['04','05','08'])]
print('live (04/05/08) judged with a final BERC decision (should be ~0):', live.has_fin.mean().round(4), 'n', len(live),
      ' with any BERC row (adjournment):', live.inB.mean().round(4))
print(live.groupby('phase_code').agg(n=('inB','size'), any_berc=('inB','mean'), fin=('has_fin','mean')).round(3).to_string())
# solution_term presence by phase (stage timing proxy?)
print('\nsolution_term non-empty by phase:'); print(dj.groupby('phase_code').solution_term.apply(lambda s: (s.astype(str).str.len() >= 8).mean()).round(3).to_string())
lu = pd.to_datetime(dj.last_update_date.astype(str).str[:19], errors='coerce')
print('last_update_date range', lu.min(), lu.max(), ' share before request_date:', (lu < pd.to_datetime(dj.request_date)).mean().round(3))
m.drop(columns=['cats']).assign(cats=m.cats).to_pickle(str(config.WORK_DIR / 'portal_berc_join.pkl'))
