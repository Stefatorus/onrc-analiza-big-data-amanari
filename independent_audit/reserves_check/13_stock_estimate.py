"""Task 1d: stock of pending registration requests at 30.10.2026 and 06.11.2026 (and at harvest, 21.11),
from (a) portal sample of reqNumbers (design-based, stratified by 100k bins) backdated with BERC final
decision dates, (b) BERC-only lower bound. Also Aug-Oct 2026 inflow of judged requests. Aggregates only."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import sys; sys.path.insert(0, str(config.REPO / 'independent_audit' / 'reserves_check'))
from rocal import n_wd
import pandas as pd, numpy as np
rng = np.random.default_rng(42)
m = pd.read_pickle(str(config.WORK_DIR / 'portal_berc_join.pkl'))
m['rd'] = pd.to_datetime(m.request_date, errors='coerce')
LO, HI = 1900000, 4824375
m = m[(m.req_nr >= LO) & (m.req_nr <= HI)].copy()
m['bin'] = (m.req_nr - LO) // 100000
binsize = pd.Series({k: min(LO + (k + 1) * 100000, HI + 1) - (LO + k * 100000) for k in m.bin.unique()})
m['w'] = m.bin.map(binsize) / m.bin.map(m.bin.value_counts())
JUD = m.details_found & (m.is_judged == 1)
JUD_BERC = JUD & m.type_code.isin(['001', '002', '003', '008', '036', '063'])   # types that reach BERC
RESOLVED_PH = m.phase_code.isin(['12', '13', '14', '15', '24', '25', '27'])
def est(ind):
    """HT total with stratified bootstrap 95% CI"""
    tot = (ind * m.w).sum()
    bs = []
    g = [(grp.index.values, binsize[k]) for k, grp in m.groupby('bin')]
    for _ in range(400):
        t = 0
        for idx, N in g:
            s = rng.choice(idx, len(idx)); t += ind.loc[s].mean() * N
        bs.append(t)
    return round(tot), round(np.percentile(bs, 2.5)), round(np.percentile(bs, 97.5))
res = []
for D in ['2026-10-30', '2026-11-06', '2026-11-20']:
    Dt = pd.Timestamp(D) + pd.Timedelta('23:59:59')
    filed = m.rd <= Dt
    final_by = m.fin_res <= Dt
    # resolved per portal but no BERC final: unknown date -> variant lo (resolved before D) / hi (after D)
    nob = RESOLVED_PH & m.fin_res.isna()
    for lab, J in [('judged (all is_judged)', JUD), ('judged, BERC types only', JUD_BERC)]:
        pend_lo = J & filed & ~final_by & ~nob
        pend_hi = J & filed & ~final_by
        res.append(dict(date=D, defn=lab, stock_lo=est(pend_lo), stock_hi=est(pend_hi)))
R = pd.DataFrame(res); print(R.to_string())
# stage split at harvest (phases are as of 21-22.11)
live = JUD & m.phase_code.isin(['03', '04', '05', '08'])
s1 = JUD & m.phase_code.isin(['03', '04', '05']); s2 = JUD & (m.phase_code == '08')
print('harvest-date live (judged) total', est(live), ' stage1', est(s1), ' stage2', est(s2),
      ' share stage1', round((s1 * m.w).sum() / (live * m.w).sum(), 3))
# consistency: live at harvest vs 'pending at 20.11 by BERC backdating'
print('live by type at harvest:', {t: round(((live & (m.type_code == t)) * m.w).sum()) for t in ['001', '002', '003', '008', '033']})
# oldest live
print('oldest live filing in sample:', m[live].rd.min(), ' live filed before 2026-06-01 (weighted):', round(((live & (m.rd < '2026-06-01')) * m.w).sum()))
# numbers without companyId and not in BERC: weight -> how many such numbers (hidden pending inmatriculari are among them)
nocomp = ~m.details_found
print('no-company numbers (weighted):', est(nocomp)[0], ' of which in BERC:', round(((nocomp & m.cats.notna()) * m.w).sum()))
# ---- inflow of judged requests by period, from sample (weights) vs BERC distinct
def inflow(lo, hi, J=JUD):
    ind = J & (m.rd >= lo) & (m.rd <= pd.Timestamp(hi) + pd.Timedelta('23:59:59'))
    t = est(ind); wd = n_wd(lo, hi)
    return dict(period=f'{lo}..{hi}', wdays=wd, judged_total=t, per_wd=round(t[0] / wd), per_wd_lo=round(t[1] / wd), per_wd_hi=round(t[2] / wd),
                share_of_numbers=round((ind * m.w).sum() / ((m.rd.between(lo, pd.Timestamp(hi) + pd.Timedelta('23:59:59')) | (~m.details_found & m.req_nr.between(*rng_nr(lo, hi)))) * m.w).sum(), 3))
lev = pd.read_csv(str(config.REPO / 'independent_audit' / 'reserves_check' / '11_daily_counter_vs_berc.csv'), index_col=0, parse_dates=True).level
def rng_nr(lo, hi):
    a = lev[:pd.Timestamp(lo) - pd.Timedelta('1D')].iloc[-1] if pd.Timestamp(lo) > lev.index[0] else 0
    return a + 1, lev[:hi].iloc[-1]
I = pd.DataFrame([inflow('2026-05-12', '2026-07-31'), inflow('2026-08-01', '2026-10-31'), inflow('2026-09-01', '2026-09-30'), inflow('2026-10-01', '2026-10-31'), inflow('2026-11-01', '2026-11-19')])
print(I.to_string())
R.to_csv(str(config.REPO / 'independent_audit' / 'reserves_check' / '13_stock_estimates.csv'), index=False)
I.to_csv(str(config.REPO / 'independent_audit' / 'reserves_check' / '13_inflow_from_sample.csv'), index=False)
