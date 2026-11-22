"""Task 2 quick measurements on the raw-JSON compact table (pseudonymised ids). Aggregates only."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import sys; sys.path.insert(0, str(config.REPO / 'independent_audit' / 'reserves_check'))
from rocal import n_wd, is_wd
import pandas as pd, numpy as np
from scipy.stats import spearmanr, kendalltau
r = pd.read_pickle(str(config.WORK_DIR / 'raw_compact.pkl'))
r = r[['cat', 'app_nr_s', 'app', 'res', 'sol', 'firm', 'app_id', 'art', 'created', 'published', 'jt']]
r['cat'] = r.cat.astype(str); r['sol'] = r.sol.astype(str)
r = r.drop_duplicates('art')
FIN = {'Admis', 'Respins', 'Renunțat', 'Certificare înscriere în registrul comerțului', 'Renunțat din oficiu', 'ADMIS',
       'certificare inscriere mentiuni', 'Certificare înscriere în registrul comerţului'}
r['fin'] = r.sol.isin(FIN) & r.cat.isin(['CERERE265', 'INMATRIC265', 'CERERE_HJ265'])
r['adj'] = r.cat == 'AUTO_AMANARI'
print('rows', len(r))

# ---------- (A) adjournment linkage via applicationIdSource vs (app_nr, filing date)
fin = r[r.fin & (r.res >= '2026-11-01') & (r.res <= '2026-11-20 23:59:59')].copy()
adj = r[r.adj].copy()
a_by_id = adj[adj.app_id != 0].groupby('app_id').agg(n_adj=('art', 'size'), first_adj=('res', 'min'), last_adj=('res', 'max'))
f = fin.merge(a_by_id, left_on='app_id', right_index=True, how='left')
f['n_adj'] = f.n_adj.fillna(0)
adj['k'] = adj.app_nr_s + '|' + adj.app.dt.strftime('%Y-%m-%d'); f['k'] = f.app_nr_s + '|' + f.app.dt.strftime('%Y-%m-%d')
kb = adj.groupby('k').size()
f['n_adj_key'] = f.k.map(kb).fillna(0)
print('\n(A) finals 1-20 Nov 2026:', len(f), ' with >=1 adjournment (by applicationIdSource):', round((f.n_adj > 0).mean(), 4),
      ' (by nr+date):', round((f.n_adj_key > 0).mean(), 4), ' agreement:', round(((f.n_adj > 0) == (f.n_adj_key > 0)).mean(), 4))
print('   distribution of #adjournments (id link):', f.n_adj.clip(upper=4).value_counts(normalize=True).sort_index().round(4).to_dict())
w = (f.res - f.app).dt.total_seconds() / 86400
print('   median wait with / without adjournment:', round(w[f.n_adj > 0].median(), 1), '/', round(w[f.n_adj == 0].median(), 1))
fa = f[f.n_adj > 0]
print('   filing->first adj (median d):', round(((fa.first_adj - fa.app).dt.total_seconds() / 86400).median(), 1),
      ' last adj->final (median d):', round(((fa.res - fa.last_adj).dt.total_seconds() / 86400).median(), 1))
f26 = r[r.fin & (r.app >= '2026-01-01')].merge(a_by_id, left_on='app_id', right_index=True, how='left')
print('   all 2026 filings with final: share adjourned', round(f26.n_adj.notna().mean(), 4), ' mean #adj among adjourned', round(f26.n_adj.mean(), 3),
      ' share with >=2 adj', round((f26.n_adj >= 2).mean(), 4))
ct = pd.crosstab(f26.n_adj.notna(), f26.sol, normalize='index')
print('   outcome of adjourned (True) vs not (False), 2026 filings:'); print(ct[[c for c in ['Admis', 'Respins', 'Renunțat'] if c in ct]].round(3).to_string())
# adjournments whose request never got a final (still pending or withdrawn unpublished)
fin_ids = set(r.loc[r.fin, 'app_id'])
a26 = a_by_id[a_by_id.first_adj >= '2026-01-01']
print('   adjourned requests (first adj in 2026) without any final yet:', round((~a26.index.isin(fin_ids)).mean(), 4), 'of', len(a26))

# ---------- (B) refiling after rejection, exact firm id (same category, within 365 d)
fr = r[r.fin & (r.firm != 0)][['firm', 'cat', 'app', 'sol', 'app_id']]
rej = fr[(fr.sol == 'Respins') & (fr.app >= '2025-01-01') & (fr.app < '2025-10-01')]
later = fr[['firm', 'cat', 'app', 'app_id']].rename(columns={'app': 'app2', 'app_id': 'id2'})
j = rej.merge(later, on=['firm', 'cat'])
j = j[(j.app2 > j.app) & (j.app2 <= j.app + pd.Timedelta('365D')) & (j.id2 != j.app_id)]
ref = rej.app_id.isin(j.app_id)
print('\n(B) rejections filed Jan-Sep 2025:', len(rej), ' refiled (later final-decided request, same firm & category, <=365d):', round(ref.mean(), 4))
for c in ['CERERE265', 'INMATRIC265']:
    s = rej.cat == c; print('   ', c, int(s.sum()), round(ref[s].mean(), 4))
del fr, later, j

# ---------- (C) chronological processing: finals decided 2-20 Nov 2026, CERERE265
c = r[r.fin & (r.cat == 'CERERE265') & (r.res >= '2026-11-02') & (r.res <= '2026-11-20 23:59:59') & (r.app >= '2026-01-01')].copy()
c['nr'] = pd.to_numeric(c.app_nr_s, errors='coerce')
rho = spearmanr(c.app, c.res).correlation
smp = c.sample(min(20000, len(c)), random_state=1)
tau = kendalltau(smp.app.astype('int64'), smp.res.astype('int64')).correlation
print('\n(C) Nov 2-20 finals (mentiuni):', len(c), ' Spearman(filing, decision)=', round(rho, 3), ' Kendall tau=', round(tau, 3),
      ' => discordant pairs ~', round((1 - tau) / 2, 3))
c['dd'] = c.res.dt.normalize()
q = c.groupby('dd').app.quantile([.1, .5, .9]).unstack()
print('   per decision day, filing date p10/p50/p90 (first 6 days):'); print(q.head(6).to_string())
print('   share decided within 14 days of filing:', round(((c.res - c.app).dt.days < 14).mean(), 4))
wdr = c.groupby('dd').apply(lambda g: spearmanr(g.nr.astype(float), g.res.astype('int64')).correlation if len(g) > 50 else np.nan)
print('   mean within-day Spearman(app_nr, decision time):', round(wdr.mean(), 3))
fast = c[(c.res - c.app).dt.days < 14]
print('   fast (<14d) finals: share Respins', round((fast.sol == 'Respins').mean(), 3), ' vs all', round((c.sol == 'Respins').mean(), 3),
      ' share jtype F', round((fast.jt.astype(str) == 'F').mean(), 3), ' vs all', round((c.jt.astype(str) == 'F').mean(), 3))

# ---------- (D) 27 April 2026 step: weekly diagnostics
z = r[r.fin & (r.res >= '2026-03-30') & (r.res < '2026-06-01')].copy()
z['wk'] = z.res.dt.to_period('W-SUN').astype(str)
z['w2'] = (z.res - z.app).dt.total_seconds() / 86400 <= 2
z['created_lag_h'] = (z.created - z.res).dt.total_seconds() / 3600
z['pub_lag_h'] = (z.published - z.res).dt.total_seconds() / 3600
z['res_hour'] = z.res.dt.hour + z.res.dt.minute / 60
z['wh'] = (z.res - z.app).dt.total_seconds() / 3600
zz = z.groupby('wk').agg(n=('art', 'size'), within2d=('w2', 'mean'), wait_p05_h=('wh', lambda s: s.quantile(.05)), wait_med_d=('wh', lambda s: s.median() / 24),
                         created_lag_med_h=('created_lag_h', 'median'), pub_lag_med_h=('pub_lag_h', 'median'), res_hour_med=('res_hour', 'median'),
                         share_resp=('sol', lambda s: (s == 'Respins').mean()))
zz['adjourn'] = r[r.adj & (r.res >= '2026-03-30') & (r.res < '2026-06-01')].pipe(lambda d: d.groupby(d.res.dt.to_period('W-SUN').astype(str)).size())
print('\n(D) weekly around 27.04.2026:'); print(zz.round(3).to_string())

# ---------- (E) non-working-day filings
g = r[r.fin & (r.app >= '2025-01-01') & (r.app < '2026-07-01')]
print('\n(E) finals filed 2025-H1 2026 on non-working days:', round((~is_wd(g.app.dt.normalize())).mean(), 4))
