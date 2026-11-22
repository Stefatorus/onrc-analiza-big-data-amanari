"""Task 1: amendment-type shares from 2026 BERC bulletin decisions, linked to the CERERE265 JSON (admitted amendments).
Aggregates only. Writes _tmp/linked_entries.pkl (record-level, deleted at the end) and cost_evidence/_t1_amendment_types.json."""
import json, os, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
OUTD = HERE

P = pickle.load(open(os.path.join(TMP, 'pdf_decisions.pkl'), 'rb'))
pdf = pd.DataFrame(P['rows'])
js = pd.read_pickle(os.path.join(TMP, 'cerere_2026.pkl'))
js = js[js.app_nr.notna() & js.cui.notna()].copy()
js['app_nr'] = js.app_nr.astype('int64'); js['cui'] = js.cui.astype('int64')
pdf = pdf[pdf.app_nr.notna()].copy(); pdf['app_nr'] = pdf.app_nr.astype('int64')
pdf['cui_i'] = pdf.cui.fillna(-1).astype('int64')
pdf['pub_nr'] = pdf.bulletin.astype(str)
js['pub_nr'] = js.pub_nr.astype(str)
# strict link: same application nr, same fiscal code, same bulletin; fallback app nr + cui
k = js.drop_duplicates(['app_nr', 'cui', 'pub_nr'])
m1 = pdf.merge(k.rename(columns={'cui': 'cui_j'}), left_on=['app_nr', 'cui_i', 'pub_nr'], right_on=['app_nr', 'cui_j', 'pub_nr'],
               how='left', indicator=True)
link = dict(pdf_decisions=len(pdf), linked_same_bulletin=int((m1._merge == 'both').sum()))
rest = m1.loc[m1._merge != 'both', pdf.columns]
k2 = js.sort_values('res').drop_duplicates(['app_nr', 'cui'], keep='last').drop(columns='pub_nr').rename(columns={'cui': 'cui_j'})
m2 = rest.merge(k2, left_on=['app_nr', 'cui_i'], right_on=['app_nr', 'cui_j'], how='inner')
link['linked_app_cui_other_bulletin'] = len(m2)
L = pd.concat([m1[m1._merge == 'both'].drop(columns='_merge'), m2], ignore_index=True)
link['linked_total'] = len(L)
link['linked_sol_counts'] = L.sol.value_counts().to_dict()
L = L[L.sol.eq('Admis') & L.verb.eq('admite') & ~L.registration]
link['linked_admitted_amendments'] = len(L)
link['pdf_registration_decisions_not_in_scope'] = int(pdf.registration.sum())
L['month'] = L.res.dt.to_period('M').astype(str)
L['wait'] = (L.res - L.app).dt.total_seconds() / 86400
L['excess'] = L.wait.sub(3).clip(lower=0)

core = ['office_change', 'secondary', 'capital_shares', 'admins']
L['caen_any'] = L.caen_rev3 | L.activity_codes
substantive = ['dissolution', 'office_change', 'secondary', 'capital_shares', 'admins', 'office_docs', 'resumption', 'name_change']


def primary(r):
    if r.dissolution: return 'dissolution_deregistration_suspension'
    if r.office_change: return 'registered_office_change'
    if r.secondary: return 'secondary_offices_work_points'
    if r.capital_shares: return 'capital_shareholders_transfers'
    if r.admins: return 'administrators_representatives'
    if r.office_docs: return 'office_document_prolongation_or_proof'
    if r.resumption or r.name_change: return 'other'
    if r.caen_rev3 and not r.activity_codes: return 'caen_rev3_update_only'
    if r.caen_any: return 'activity_codes_change_only'
    return 'other'


L['primary'] = L.apply(primary, axis=1)
# strict: objects that change where/how/with whom the firm may operate (address, work points, capital, share transfers,
# appointment/revocation of administrators, resumption). broad: + 'modificare date asociati/administrator' (ONRC uses these
# items both for real changes in the shareholding/management and for mere updates of personal data). upper: + activity codes, name.
L['blocking_strict'] = (L.office_change | L.secondary | L.capital | L.share_transfer | L.admin_change | L.resumption) & ~L.dissolution
L['blocking_core'] = (L[core].any(axis=1) | L.resumption) & ~L.dissolution
L['blocking_upper'] = L.blocking_core | ((L.activity_codes | L.name_change) & ~L.dissolution)
L['shdata_with_caen_only_else'] = (L.shareholder_data | L.admin_data) & L.caen_any & ~(L.office_change | L.secondary | L.capital | L.share_transfer | L.admin_change | L.dissolution)
L['caen_only'] = L.caen_any & ~L[substantive].any(axis=1)
L['seat_related'] = L.office_change | L.office_docs
L['unparsed'] = L.src.eq('none')
L.to_pickle(os.path.join(TMP, 'linked_entries.pkl'))


def share(df, col, w=None):
    """ratio estimator, 95% CI clustered by bulletin (linearisation); w = optional weight column (e.g. excess days)."""
    n = df[w].astype(float) if w else pd.Series(1.0, index=df.index)
    y = df[col].astype(float) * n
    g = pd.DataFrame({'y': y, 'n': n, 'b': df.bulletin}).groupby('b').sum()
    G = len(g); p = g.y.sum() / g.n.sum()
    se = np.sqrt(G / (G - 1) * ((g.y - p * g.n) ** 2).sum()) / g.n.sum() if G > 1 else np.nan
    return dict(share=round(float(p), 4), ci95=[round(float(max(0, p - 1.96 * se)), 4), round(float(min(1, p + 1.96 * se)), 4)],
                n=int(len(df)), bulletins=int(G))


anyof = ['caen_rev3', 'activity_codes', 'caen_only', 'office_change', 'office_docs', 'seat_related', 'secondary', 'capital_shares', 'capital',
         'share_transfer', 'shareholder_data', 'admins', 'admin_change', 'admin_data', 'dissolution', 'resumption', 'name_change',
         'blocking_strict', 'blocking_core', 'blocking_upper', 'shdata_with_caen_only_else', 'unparsed']
prim = sorted(L.primary.unique())
for p_ in prim:
    L['P_' + p_] = L.primary.eq(p_)
res = dict(linkage=link, months_available=L.month.value_counts().sort_index().to_dict())
win = L[(L.res >= '2026-08-01') & (L.res < '2026-11-19') & L.wait.between(0, 365)]
res['window_aug1_nov18'] = dict(
    n=len(win), any_of={c: share(win, c) for c in anyof},
    primary={p_: share(win, 'P_' + p_) for p_ in prim},
    excess_day_weighted={c: share(win, c, 'excess') for c in ['blocking_strict', 'blocking_core', 'blocking_upper', 'caen_only', 'seat_related',
                                                               'office_docs', 'office_change', 'secondary', 'capital_shares', 'admins']})
res['by_month'] = {mo: dict(n=len(g), any_of={c: share(g, c) for c in ['caen_only', 'caen_rev3', 'office_change', 'office_docs', 'secondary',
                                                                       'capital_shares', 'admins', 'dissolution', 'blocking_strict', 'blocking_core', 'blocking_upper']},
                            primary={p_: share(g, 'P_' + p_)['share'] for p_ in prim})
                   for mo, g in L.groupby('month') if len(g) >= 100}
# robustness: post-stratify window shares to the county mix of all admitted amendments in the window (JSON population)
pop = js[(js.res >= '2026-08-01') & (js.res < '2026-11-19') & js.sol.eq('Admis')]
wts = pop.county.value_counts(normalize=True)
cs = win.groupby('county')[['blocking_strict', 'blocking_core', 'blocking_upper', 'caen_only', 'seat_related', 'office_docs']].mean()
cov = wts[wts.index.isin(cs.index)]
res['window_county_poststratified'] = dict(counties_covered=int(len(cov)), population_share_covered=round(float(cov.sum()), 3),
                                           **{c: round(float((cs[c] * cov).sum() / cov.sum()), 4) for c in cs.columns})
res['window_jtype_mix_sample_vs_population'] = dict(sample=win.jtype.value_counts(normalize=True).round(3).to_dict(),
                                                    population=pop.jtype.value_counts(normalize=True).round(3).to_dict())
res['window_J_only'] = {c: share(win[win.jtype.eq('J')], c) for c in ['blocking_strict', 'blocking_core', 'blocking_upper', 'caen_only', 'seat_related', 'office_docs']}
res['window_median_wait_by_primary'] = win.groupby('primary').wait.median().round(1).to_dict()
res['window_n_by_primary'] = win.primary.value_counts().to_dict()
vc = L[L.primary.eq('other')].resid.value_counts(); res['other_residual_top_min5'] = vc[vc >= 5].to_dict()
L['seat_excl_blocking_strict'] = L.blocking_strict & ~L.seat_related
# bare "capital social" mentions that only accompany activity-code items (no other strict object) are dropped here
cap_with_caen_only = L.capital & L.caen_any & ~(L.office_change | L.secondary | L.share_transfer | L.admin_change | L.resumption)
L['blocking_strict_excl_capital_with_caen'] = L.blocking_strict & ~cap_with_caen_only
L['seat_excl_blocking_strict_excl_capital_with_caen'] = L.blocking_strict_excl_capital_with_caen & ~L.seat_related
L['seat_excl_blocking_core'] = L.blocking_core & ~L.seat_related
win = L[(L.res >= '2026-08-01') & (L.res < '2026-11-19') & L.wait.between(0, 365)]
res['window_excl_seat_related'] = {c: dict(count_share=share(win, c), excess_day_share=share(win, c, 'excess')) for c in ['seat_excl_blocking_strict', 'seat_excl_blocking_core', 'blocking_strict_excl_capital_with_caen', 'seat_excl_blocking_strict_excl_capital_with_caen']}
w30 = win[win.wait > 30]
res['window_wait_over_30'] = {c: share(w30, c) for c in ['office_docs', 'office_change', 'seat_related', 'blocking_strict', 'blocking_core']}
res['dissolution_crosstab'] = dict(dissolution=int(win.dissolution.sum()), with_secondary=int((win.dissolution & win.secondary).sum()),
                                   with_admins=int((win.dissolution & win.admins).sum()), with_office_change=int((win.dissolution & win.office_change).sum()))
# shares by application month (within the sample)
win['app_month'] = win.app.dt.to_period('M').astype(str)
res['window_by_application_month'] = {mo: dict(n=len(g), **{c: round(float(g[c].mean()), 4) for c in ['blocking_strict', 'blocking_core', 'caen_only', 'caen_rev3', 'seat_related']})
                                      for mo, g in win.groupby('app_month') if len(g) >= 100}
# sample vs population: wait distribution and bulletin coverage for decisions 1 Oct-18 Nov
popw = pop.assign(wait=(pop.res - pop.app).dt.total_seconds() / 86400); popw = popw[popw.wait.between(0, 365)]
po = popw[popw.res >= '2026-10-01']; so = win[win.res >= '2026-10-01']
q = [.1, .25, .5, .75, .9]
res['sample_vs_population_oct1_nov18'] = dict(
    sample_n=len(so), population_n=len(po), sample_fraction=round(len(so) / len(po), 4),
    wait_quantiles_sample=so.wait.quantile(q).round(1).tolist(), wait_quantiles_population=po.wait.quantile(q).round(1).tolist(),
    mean_excess_sample=round(float(so.excess.mean()), 2), mean_excess_population=round(float(po.wait.sub(3).clip(lower=0).mean()), 2),
    share_wait_over_30_sample=round(float((so.wait > 30).mean()), 4), share_wait_over_30_population=round(float((po.wait > 30).mean()), 4),
    bulletins_sampled=int(so.bulletin.nunique()), distinct_pub_nr_population=int(po.pub_nr.nunique()))
# post-stratify the Oct-Nov sample to the population's application-month mix (sample over-represents long waits)
po_m = po.app.dt.to_period('M').astype(str).value_counts(normalize=True)
so = so.assign(app_month=so.app.dt.to_period('M').astype(str))
cm = so.groupby('app_month')[['blocking_strict', 'blocking_core', 'blocking_upper', 'caen_only', 'seat_related', 'office_docs', 'office_change']].mean()
cv = po_m[po_m.index.isin(cm.index)]
res['oct_nov_poststratified_by_application_month'] = dict(population_share_covered=round(float(cv.sum()), 3),
    **{c: round(float((cm[c] * cv).sum() / cv.sum()), 4) for c in cm.columns})
res['window_note'] = ('All window entries come from decisions of 1 Oct-18 Nov 2026 (the bulletin archive holds 60 Jan, 1 Feb and 482 Oct-Nov bulletins); '
                      'Aug-Sep 2026 and Jan-Sep monthly shares cannot be established from it. CIs cover sampling among collected bulletins only.')
print(json.dumps({k: res[k] for k in ('linkage', 'months_available', 'window_county_poststratified', 'window_jtype_mix_sample_vs_population',
                                      'window_median_wait_by_primary', 'window_n_by_primary')}, ensure_ascii=False, indent=1, default=str))
w = res['window_aug1_nov18']; print('window n', w['n'])
for c, v in w['any_of'].items(): print('ANY', c, v['share'], v['ci95'])
for c, v in w['primary'].items(): print('PRIM', c, v['share'], v['ci95'])
for c, v in w['excess_day_weighted'].items(): print('XDW', c, v['share'], v['ci95'])
for mo, v in res['by_month'].items(): print(mo, v['n'], {k: x['share'] for k, x in v['any_of'].items()})
for k in ('window_excl_seat_related', 'window_wait_over_30', 'dissolution_crosstab', 'window_by_application_month', 'sample_vs_population_oct1_nov18', 'oct_nov_poststratified_by_application_month', 'other_residual_top_min5'):
    print(k, json.dumps(res[k], ensure_ascii=False, default=str))

json.dump(res, open(os.path.join(OUTD, '_t1_amendment_types.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
