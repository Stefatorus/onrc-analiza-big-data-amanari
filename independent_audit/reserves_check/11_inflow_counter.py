"""Task 1b: counter increments per filing day (all items registered) vs BERC distinct requests
with a published decision (by filing date), monthly 2024-2026; compare MJ / press."""
import sys; sys.path.insert(0, r'S:\Projects\SOLOResearch\independent_audit\reserves_check')
from rocal import is_wd, n_wd, HOL
import pandas as pd, numpy as np
b = pd.read_pickle(r'W:\SOLOResearch\analysis_decisions.pkl')[['cat','app_nr','app','res','sol','county']]
b = b[b.app >= '2023-01-01']; b['d'] = b.app.dt.normalize(); b['y'] = b.d.dt.year
FIN = ['Admis','Respins','Renunțat','Certificare înscriere în registrul comerțului','Renunțat din oficiu','ADMIS','certificare inscriere mentiuni']
b['fin'] = b.sol.isin(FIN)
OUT = r'S:\Projects\SOLOResearch\independent_audit\reserves_check'
# ---------- counter level per day, national era (26.07.2024 ->)
nat = b[b.d >= '2024-07-26']
lev = nat.groupby('d').app_nr.max()
days = pd.date_range('2024-07-26', '2026-11-19')
lev = lev.reindex(days)
# year-aware cumulative max; base before first day of each year
out = []
for Y in [2024, 2025, 2026]:
    s = lev[lev.index.year == Y].cummax().ffill()
    base = 2000010 if Y == 2024 else 0
    inc = s.diff(); inc.iloc[0] = s.iloc[0] - base
    out.append(pd.DataFrame({'level': s, 'inc': inc}))
cnt = pd.concat(out); cnt['wd'] = is_wd(cnt.index)
# BERC distinct requests (key y,app_nr) by filing day; finals; categories
key = nat.drop_duplicates(['y', 'app_nr'])
dist = key.groupby('d').size().reindex(days, fill_value=0)
fkey = nat[nat.fin].drop_duplicates(['y', 'app_nr']).groupby('d').size().reindex(days, fill_value=0)
cnt['berc_distinct'] = dist; cnt['berc_final'] = fkey
cnt.to_csv(OUT + r'\11_daily_counter_vs_berc.csv', encoding='utf-8')
print('peak daily counter increments:'); print(cnt.inc.nlargest(8).to_string())
print('weekend/holiday share of counter increments 2025:', round(cnt.loc['2025', 'inc'][~cnt.loc['2025', 'wd']].sum() / cnt.loc['2025', 'inc'].sum(), 4),
      ' of BERC distinct:', round(cnt.loc['2025', 'berc_distinct'][~cnt.loc['2025', 'wd']].sum() / cnt.loc['2025', 'berc_distinct'].sum(), 4))
print('weekend/holiday share 2026 Jan-Oct counter:', round(cnt.loc['2026-01':'2026-10', 'inc'][~cnt.loc['2026-01':'2026-10', 'wd']].sum() / cnt.loc['2026-01':'2026-10', 'inc'].sum(), 4))
# ---------- monthly
cnt['m'] = cnt.index.to_period('M')
M = cnt.groupby('m').agg(counter=('inc', 'sum'), berc=('berc_distinct', 'sum'), berc_fin=('berc_final', 'sum'), cal=('inc', 'size'), wdays=('wd', 'sum'))
M['counter_per_cal'] = M.counter / M.cal; M['counter_per_wd'] = M.counter / M.wdays
M['berc_per_cal'] = M.berc / M.cal; M['berc_per_wd'] = M.berc / M.wdays
M['coverage'] = M.berc / M.counter
print(M.round(3).to_string())
M.to_csv(OUT + r'\11_monthly_counter_vs_berc.csv', encoding='utf-8')
# ---------- old platform (H1 2024 and 2023): per-county counters, sum of county maxima
def county_total(lo, hi):
    s = b[(b.d >= lo) & (b.d <= hi)]
    return s.groupby('county', observed=True).app_nr.max().sum()
pre = b[(b.d < '2024-07-17')]
yrs = {}
for Y in [2023, 2024]:
    s = pre[pre.y == Y]
    # monthly: sum over counties of month-end max minus previous month-end max
    mm = s.groupby([s.d.dt.to_period('M'), 'county'], observed=True).app_nr.max().unstack().cummax().ffill().fillna(0)
    tot = mm.sum(axis=1); inc = tot.diff(); inc.iloc[0] = tot.iloc[0]
    kk = s.drop_duplicates(['county', 'app_nr']).groupby(s.d.dt.to_period('M')).size()
    T = pd.DataFrame({'counter_sum_counties': inc, 'berc_distinct': kk}); T['coverage'] = T.berc_distinct / T.counter_sum_counties
    print('OLD PLATFORM', Y); print(T.round(3).to_string())
# ---------- period aggregates vs MJ / press
def per(lo, hi, label):
    c = cnt.loc[lo:hi]; cal = len(c); wd = int(c.wd.sum())
    r = dict(period=label, cal_days=cal, wdays=wd, counter=int(c.inc.sum()), counter_per_cal=round(c.inc.sum() / cal), counter_per_wd=round(c.inc.sum() / wd),
             berc_distinct=int(c.berc_distinct.sum()), berc_per_cal=round(c.berc_distinct.sum() / cal), berc_per_wd=round(c.berc_distinct.sum() / wd),
             coverage=round(c.berc_distinct.sum() / c.inc.sum(), 3))
    return r
P = pd.DataFrame([per('2024-08-01', '2024-12-31', '2024 Aug-Dec (national)'), per('2025-01-01', '2025-12-31', '2025'),
                  per('2026-01-01', '2026-06-30', 'H1 2026 (MJ 4.533)'), per('2026-01-01', '2026-07-31', 'Jan-Jul 2026 (press >26.000)'),
                  per('2026-08-01', '2026-10-31', 'Aug-Oct 2026 (MJ 6.931; BERC censored)'), per('2025-08-01', '2025-10-31', 'Aug-Oct 2025')])
print(P.to_string()); P.to_csv(OUT + r'\11_period_vs_MJ_press.csv', index=False, encoding='utf-8')
