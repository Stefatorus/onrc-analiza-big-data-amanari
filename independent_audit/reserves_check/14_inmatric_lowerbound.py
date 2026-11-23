"""Task 1d add-ons: (i) BERC-only lower bound of the stock (filed <= D, first final decision > D);
(ii) pending inmatriculari invisible in the portal sample (no companyId): Little-type estimate."""
import sys; sys.path.insert(0, r'S:\Projects\SOLOResearch\independent_audit\reserves_check')
from rocal import n_wd
import pandas as pd, numpy as np
b = pd.read_pickle(r'W:\SOLOResearch\analysis_decisions.pkl')[['cat','app_nr','app','res','sol']]
b = b[b.app >= '2025-01-01']; b['y'] = b.app.dt.year; b['cat'] = b.cat.astype(str)
FIN = ['Admis','Respins','Renunțat','Certificare înscriere în registrul comerțului','Renunțat din oficiu','ADMIS','certificare inscriere mentiuni']
b['fin'] = b.sol.isin(FIN)
k = b.groupby(['y','app_nr']).agg(app=('app','min'))
k['fin_res'] = b[b.fin].groupby(['y','app_nr']).res.min()
k['inm'] = b.groupby(['y','app_nr']).cat.agg(lambda s: False) if False else b[b.cat.str.contains('INMATRIC')].groupby(['y','app_nr']).size().reindex(k.index).notna()
for D in ['2026-10-30','2026-11-06']:
    Dt = pd.Timestamp(D) + pd.Timedelta('23:59:59')
    lb = ((k.app <= Dt) & ((k.fin_res > Dt) | k.fin_res.isna()))
    print(D, 'BERC-only lower bound (filed<=D, not final by D, but has a BERC row by 20.11):', int(lb.sum()), ' of which inmatric:', int((lb & k.inm).sum()))
# inmatriculari: monthly filings with decision, and wait
i = k[k.inm]
i['m'] = i.app.dt.to_period('M')
mon = i.groupby('m').size()
print('INMATRIC distinct by filing month 2025-2026:'); print(mon.to_string())
fin_nov = i[(i.fin_res >= '2026-11-02') & (i.fin_res <= '2026-11-20 23:59')]
w = (fin_nov.fin_res - fin_nov.app).dt.total_seconds() / 86400
rate = len(fin_nov) / n_wd('2026-11-02', '2026-11-20')
print('inmatric finals 2-20 Nov per working day', round(rate), ' mean wait (cal days)', round(w.mean(), 1), ' median', round(w.median(), 1))
# Little with calendar days: L = lambda_cal * W
lam_cal = len(fin_nov) / 19
print('Little estimate of pending inmatric (calendar-rate x mean wait):', round(lam_cal * w.mean()))
# mature-month inflow of inmatric per wd (H1 2026), as alternative lambda
h1 = ((i.app >= '2026-01-01') & (i.app <= '2026-06-30 23:59')).sum() / n_wd('2026-01-01', '2026-06-30')
print('H1 2026 inmatric with decision per wd:', round(h1))
