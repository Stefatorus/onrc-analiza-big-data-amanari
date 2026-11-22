"""Task 2: firms behind admitted amendments decided 1 Aug-18 Nov 2026, joined by fiscal code to Ministry of Finance
balance sheets (2025; 2024 if missing). Aggregates only -> cost_evidence/_t2_amendment_firms.json."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import json, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
FIN = str(config.FIN_CACHE)
MODEL_PER_CHANGE_DAY = {'prudent': .15 * 35, 'central': .20 * 70, 'tensionat': .25 * 110}   # share x lei/blocked day


def balance(year):
    f = pd.read_csv(os.path.join(FIN, f'WEB_UU_AN{year}.txt'), usecols=['CUI', 'I13', 'I16', 'I17', 'I18', 'I19', 'I20'])
    f = f.drop_duplicates(); f = f.drop_duplicates('CUI', keep=False)
    f['days'] = 366 if year % 4 == 0 else 365; f['fy'] = year
    return f


b25, b24 = balance(2025), balance(2024)
bal = pd.concat([b25, b24[~b24.CUI.isin(b25.CUI)]], ignore_index=True)
bal['daily'] = bal.I13.clip(lower=0) / bal.days
bal = bal[['CUI', 'fy', 'I13', 'I20', 'daily']]


def wquantile(x, w, q):
    o = np.argsort(x); x, w = np.asarray(x)[o], np.asarray(w)[o]; c = np.cumsum(w) / w.sum()
    return float(x[np.searchsorted(c, q)])


def stats(df, weight=None):
    """df has daily, I20 (NaN if unmatched), matched flag, excess."""
    m = df[df.matched]
    if len(m) == 0:
        return dict(n=len(df))
    cap = m.daily.quantile(.99)
    w = m[weight] if weight else pd.Series(1.0, index=m.index)
    dc = m.daily.clip(upper=cap)
    out = dict(n=int(len(df)), matched=int(len(m)), match_rate=round(len(m) / len(df), 4),
               median_daily_turnover=round(wquantile(m.daily, w, .5), 1),
               p25_daily=round(wquantile(m.daily, w, .25), 1), p75_daily=round(wquantile(m.daily, w, .75), 1),
               mean_daily_capped_p99=round(float((dc * w).sum() / w.sum()), 1), p99_cap=round(float(cap), 1),
               share_zero_turnover=round(float(((m.daily <= 0) * w).sum() / w.sum()), 4),
               share_ge1_employee=round(float(((m.I20 >= 1) * w).sum() / w.sum()), 4),
               median_employees=wquantile(m.I20.fillna(0), w, .5),
               mean_employees_capped_p99=round(float((m.I20.fillna(0).clip(upper=m.I20.quantile(.99)) * w).sum() / w.sum()), 2))
    # unmatched J firms counted as zero turnover (lower bound on the per-firm average)
    j = df[df.jtype.eq('J')]
    if len(j):
        wj = j[weight] if weight else pd.Series(1.0, index=j.index)
        dj = j.daily.fillna(0).clip(upper=cap)
        out['J_match_rate'] = round(float(j.matched.mean()), 4)
        out['J_median_daily_unmatched_as_zero'] = round(wquantile(j.daily.fillna(0), wj, .5), 1)
        out['J_mean_daily_capped_unmatched_as_zero'] = round(float((dj * wj).sum() / wj.sum()), 1)
    return out


js = pd.read_pickle(os.path.join(TMP, 'cerere_2026.pkl'))
w = js[(js.res >= '2026-08-01') & (js.res < '2026-11-19') & js.sol.eq('Admis')].copy()
w['wait'] = (w.res - w.app).dt.total_seconds() / 86400
w = w[w.wait.between(0, 365) & w.cui.notna()]
w['excess'] = w.wait.sub(3).clip(lower=0)
w['cui'] = w.cui.astype('int64')
w = w.merge(bal, left_on='cui', right_on='CUI', how='left'); w['matched'] = w.CUI.notna() & w.daily.notna()
res = dict(window='admitted CERERE265 decisions 1 Aug-18 Nov 2026, wait 0-365 days (raw JSON)', decisions=int(len(w)),
           fy_used=w.fy.value_counts().to_dict())
# firm level: one row per fiscal code (excess days summed)
firm = w.groupby('cui').agg(daily=('daily', 'first'), I20=('I20', 'first'), matched=('matched', 'first'), jtype=('jtype', 'first'),
                            excess=('excess', 'sum'), n=('excess', 'size')).reset_index()
res['overall_firm_level'] = stats(firm)
res['overall_excess_day_weighted'] = stats(w, 'excess')
res['overall_decision_level'] = stats(w)
res['by_jtype_match_rate'] = w.groupby('jtype').matched.mean().round(4).to_dict()
# by amendment category, using the bulletin-linked sample (decisions 1 Oct-18 Nov)
L = pd.read_pickle(os.path.join(TMP, 'linked_entries.pkl'))
L = L[(L.res >= '2026-08-01') & (L.res < '2026-11-19') & L.wait.between(0, 365)].copy()
L['cui'] = L.cui_j.astype('int64')
L = L.merge(bal, left_on='cui', right_on='CUI', how='left'); L['matched'] = L.CUI.notna() & L.daily.notna()
res['by_primary_category_linked_sample'] = {k: stats(g) for k, g in L.groupby('primary')}
for t in ('blocking_strict', 'blocking_core', 'caen_only', 'seat_related'):
    res[f'linked_sample_{t}'] = stats(L[L[t]]); res[f'linked_sample_{t}_excess_weighted'] = stats(L[L[t]], 'excess')
res['linked_sample_all'] = stats(L)
# model assumption vs measured scale
comp = {}
for s, v in MODEL_PER_CHANGE_DAY.items():
    comp[s] = dict(lei_per_change_day=v,
                   pct_of_median_firm=round(100 * v / res['overall_firm_level']['median_daily_turnover'], 1),
                   pct_of_capped_mean_firm=round(100 * v / res['overall_firm_level']['mean_daily_capped_p99'], 2),
                   pct_of_median_excess_weighted=round(100 * v / res['overall_excess_day_weighted']['median_daily_turnover'], 1),
                   pct_of_capped_mean_excess_weighted=round(100 * v / res['overall_excess_day_weighted']['mean_daily_capped_p99'], 2))
    bc = res['linked_sample_blocking_strict_excess_weighted']
    comp[s]['blocked_day_cost_pct_of_median_strict_blocking_firm'] = round(100 * v / (.2 if s == 'central' else (.15 if s == 'prudent' else .25)) / bc['median_daily_turnover'], 1)
res['model_vs_turnover'] = comp
json.dump(res, open(os.path.join(HERE, '_t2_amendment_firms.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
