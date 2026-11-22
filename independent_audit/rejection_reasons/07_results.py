"""Step 7: coverage, procedural mechanism, archive linkage to earlier postponements, category shares (95% CI clustered by bulletin) for
registrations vs amendments, reweighting, comparison with the postponement reasons (delay_reasons), pair comparison, avoidable-at-filing
shares, weekly series, durations, figures, taxonomy.csv and the evidence JSON.
Inputs: _tmp/entries.pkl, _tmp/entry_labels.pkl, _tmp/seg_labels.pkl, _tmp/post_pairs.pkl, _tmp/rejections_raw.pkl (index counts only),
        archive (needed columns only), 04/06 outputs, ../out/delay_reasons.json and ../delay_reasons/07_results.out.json (read-only).
Outputs: figures/*.png|svg, taxonomy.csv, 07_results.out.json, ../out/rejection_reasons.json (aggregates only)."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import os, sys, json, importlib.util, collections, pickle, math
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp'); FIG = os.path.join(HERE, 'figures')
OUTJ = os.path.join(HERE, '..', 'out', 'rejection_reasons.json')
DRJ = os.path.join(HERE, '..', 'out', 'delay_reasons.json'); DR7 = os.path.join(HERE, '..', 'delay_reasons', '07_results.out.json')
os.makedirs(FIG, exist_ok=True)
WIN = ('2026-10-19', '2026-11-18')     # first..last decision day of the parsed rejections (same window as delay_reasons)
CONV_WIN = ('2026-09-01', '2026-10-15')  # postponements whose follow-up is observable by the archive end (conversion context)


def load(name):
    spec = importlib.util.spec_from_file_location('m' + name[:2], os.path.join(HERE, name)); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


C4 = load('04_classify.py'); CATS = C4.CATS
AVOID = {k: v[1] for k, v in CATS.items()}
ALIGNED = ['CAEN', 'SEDIU', 'ACT', 'ASOC_ID', 'SOLICITANT', 'SEMN', 'CERERE', 'BEN_REAL', 'CAPITAL', 'INSTIT', 'DENUM', 'TARIF']
CODES = list(CATS) + ['NERESTATAT']
MECHS = ['M_NEREMEDIAT', 'M_PARTIAL', 'M_AMANARE_ALT', 'M_DIRECT']


def share(df, col, w=None):
    """ratio estimator sum(y)/sum(n), 95% CI clustered by bulletin (linearisation; as in delay_reasons/07 and cost_evidence/03)."""
    if len(df) == 0:
        return dict(value=None, ci95=[None, None], n=0, bulletins=0)
    wt = df[w].astype(float) if w else pd.Series(1.0, index=df.index)
    y = df[col].astype(float) * wt
    g = pd.DataFrame({'y': y, 'n': wt, 'b': df.bulletin}).groupby('b').sum()
    G = len(g); p = g.y.sum() / g.n.sum()
    se = np.sqrt(G / (G - 1) * ((g.y - p * g.n) ** 2).sum()) / g.n.sum() if G > 1 else np.nan
    return dict(value=round(float(p), 4), ci95=[round(float(max(0, p - 1.96 * se)), 4), round(float(min(1, p + 1.96 * se)), 4)],
                n=int(len(df)), bulletins=int(G))


def wshare(df, col):
    """Wilson 95% CI (used for the small registrations group, where bulletin clusters hold ~1 entry and p can be 0)."""
    n = len(df); k = int(df[col].sum())
    if n == 0:
        return dict(value=None, ci95=[None, None], n=0)
    z = 1.96; p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return dict(value=round(p, 4), ci95=[round(max(0, c - h), 4), round(min(1, c + h), 4)], n=int(n), ci_method='Wilson')


def rake(df, margins, iters=60):
    w = np.ones(len(df))
    for _ in range(iters):
        for col, target in margins.items():
            cur = pd.Series(w).groupby(df[col].values).sum()
            w = w * (target / cur).reindex(df[col].values).fillna(1.0).values
    return w / w.mean()


def flag(s, mode):
    s = set(s) - {'NERESTATAT'}
    if not s:
        return False
    f = [AVOID[c] for c in s]
    if mode == 'strict':
        return all(x == 'da' for x in f)
    if mode == 'any':
        return any(x == 'da' for x in f)
    return all(x in ('da', 'parțial') for x in f)


def main():
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    L = pd.read_pickle(os.path.join(TMP, 'entry_labels.pkl'))
    E = E.merge(L, on='eid')
    E = E[(E.din_data >= WIN[0]) & (E.din_data <= WIN[1])].reset_index(drop=True)
    E['week'] = E.din_data.dt.to_period('W-SUN').astype(str)
    E['tip'] = np.where(E.cat == 'INMATRIC265', 'INMATRICULARE', 'MENTIUNI')
    R = {}

    # ---------------- archive: rejections, postponements, waivers
    df = pd.read_pickle(str(config.BERC_PKL))[['cat', 'app_nr', 'app', 'res', 'county', 'jtype', 'sol']]
    df = df[df.res >= '2026-01-01']
    archive_end = df.res.max()
    df['dd'] = df.res.dt.normalize(); df['ad'] = df.app.dt.normalize()
    A = df[df.cat == 'AUTO_AMANARI'][['app_nr', 'ad', 'dd']].drop_duplicates()
    Rj = df[(df.sol == 'Respins') & (df.dd >= WIN[0]) & (df.dd <= WIN[1])].drop_duplicates(['app_nr', 'dd']).copy()
    Rj['week'] = Rj.dd.dt.to_period('W-SUN').astype(str); Rj['county'] = Rj.county.astype(str); Rj['cat'] = Rj.cat.astype(str)
    Rj['tip'] = np.where(Rj.cat == 'INMATRIC265', 'INMATRICULARE', 'MENTIUNI')
    ren = df[(df.sol.astype(str).str.startswith('Renun')) & (df.dd >= WIN[0]) & (df.dd <= WIN[1])].drop_duplicates(['app_nr', 'dd'])
    post_w = A[(A.dd >= WIN[0]) & (A.dd <= WIN[1])]
    adm_w = df[(df.sol == 'Admis') & (df.dd >= WIN[0]) & (df.dd <= WIN[1])]
    R['archive_window'] = dict(rejections=int(len(Rj)), rejections_by_type=Rj.tip.value_counts().to_dict(), waivers_renuntat=int(len(ren)),
                               postponements=int(len(post_w)), admitted=int(adm_w.drop_duplicates(['app_nr', 'dd']).shape[0]),
                               rejection_to_postponement_ratio=round(len(Rj) / len(post_w), 4))
    # (a) archive-wide linkage: earlier postponement of the same request (same request nr and filing day)
    m = Rj[['app_nr', 'ad', 'dd', 'tip']].reset_index().merge(A.rename(columns={'dd': 'pdd'}), on=['app_nr', 'ad'])
    m = m[m.pdd < m.dd]
    g = m.groupby('index')
    Rj['n_post'] = Rj.index.map(g.size()).fillna(0).astype(int)
    Rj['days_last_post'] = (Rj.dd - Rj.index.map(g.pdd.max())).dt.days
    lk = {}
    for t, S in [('ALL', Rj)] + list(Rj.groupby('tip')):
        p = float((S.n_post > 0).mean()); n = len(S); se = np.sqrt(p * (1 - p) / n)
        lk[t] = dict(share_with_prior_postponement=round(p, 4), ci95=[round(p - 1.96 * se, 4), round(p + 1.96 * se, 4)], n=int(n),
                     postponements_per_rejection=S.n_post.value_counts().sort_index().to_dict(),
                     median_days_last_postponement_to_rejection=float(S.days_last_post.median()),
                     iqr_days_last_postponement_to_rejection=[float(S.days_last_post.quantile(.25)), float(S.days_last_post.quantile(.75))],
                     median_days_filing_to_rejection=float((S.dd - S.ad).dt.days.median()))
    R['archive_linkage'] = lk
    # conversion context: what happens after a postponement (postponements decided in CONV_WIN, first later decision of the same request)
    Pc = A[(A.dd >= CONV_WIN[0]) & (A.dd <= CONV_WIN[1])].drop_duplicates(['app_nr', 'ad'], keep='last').reset_index(drop=True)
    later = df[df.cat != 'AUTO_AMANARI'][['app_nr', 'ad', 'dd', 'sol']]
    mc = Pc.reset_index().merge(later.rename(columns={'dd': 'fdd'}), on=['app_nr', 'ad'])
    mc = mc[mc.fdd >= mc.dd].sort_values('fdd').drop_duplicates('index')
    outc = mc.sol.astype(str).map(lambda s: 'Admis' if s.startswith(('Admis', 'Certific', 'ADMIS')) else 'Respins' if s == 'Respins'
                                  else 'Renuntat' if s.startswith('Renun') else 'Altul').value_counts()
    R['postponement_outcomes'] = dict(window=CONV_WIN, postponed_requests=int(len(Pc)), resolved_by_archive_end=int(len(mc)),
                                      outcome_counts=outc.to_dict(), rejected_share_of_resolved=round(float(outc.get('Respins', 0) / len(mc)), 4),
                                      rejected_share_of_all_postponed=round(float(outc.get('Respins', 0) / len(Pc)), 4))
    del df, later, mc

    # ---------------- coverage and representativeness
    raw = pickle.load(open(os.path.join(TMP, 'rejections_raw.pkl'), 'rb'))
    ix = pd.DataFrame(raw['index']); ix['d'] = pd.to_datetime(ix.idx_date, format='%d.%m.%Y')
    ixr = ix[(ix.idx_sol == 'Respins') & (ix.d >= WIN[0]) & (ix.d <= WIN[1])].drop_duplicates(['app_nr', 'd'])
    days = sorted(E.din_data.unique())
    Rcov = Rj[Rj.dd.isin(days)]
    wk = pd.DataFrame({'archive': Rj.groupby('week').size(), 'parsed': E.groupby('week').size(),
                       'decision_days_parsed': E.groupby('week').din_data.nunique()}).fillna(0)
    wk['coverage'] = (wk.parsed / wk.archive).round(4)
    ct = pd.DataFrame({'archive': Rj.groupby('county').size(), 'parsed': E.groupby('county').size()}).fillna(0)
    ct = ct[ct.archive >= 20]; ct['cov'] = ct.parsed / ct.archive
    R['coverage'] = dict(parsed=int(len(E)), bulletin_index_rejections=int(len(ixr)), archive_window=int(len(Rj)), share=round(len(E) / len(Rj), 4),
                         archive_on_parsed_days=int(len(Rcov)), share_on_parsed_days=round(len(E) / len(Rcov), 4),
                         decision_days_parsed=int(len(days)), decision_days_archive=int(Rj.dd.nunique()), bulletins=int(E.bulletin.nunique()),
                         by_type=dict(parsed=E.tip.value_counts().to_dict(), archive=Rj.tip.value_counts().to_dict(),
                                      coverage={t: round(float((E.tip == t).sum() / (Rj.tip == t).sum()), 4) for t in ('MENTIUNI', 'INMATRICULARE')}),
                         by_week=wk.reset_index().rename(columns={'index': 'week'}).to_dict('records'),
                         counties_with_20plus=int(len(ct)), county_coverage_min_max=[round(float(ct['cov'].min()), 3), round(float(ct['cov'].max()), 3)],
                         county_coverage_cv=round(float(ct['cov'].std() / ct['cov'].mean()), 3),
                         counties_zero_parsed=int((ct.parsed == 0).sum()),
                         jtype_parsed=E.jtype.value_counts(normalize=True).round(3).to_dict(), jtype_archive=Rj.jtype.astype(str).value_counts(normalize=True).round(3).to_dict(),
                         sample_with_prior_postponement=round(float((E.n_prior_post > 0).mean()), 4))
    E['w'] = rake(E, {'county': Rj.groupby('county').size().astype(float) / len(Rj) * len(E),
                      'week': Rj.groupby('week').size().astype(float) / len(Rj) * len(E),
                      'tip': Rj.groupby('tip').size().astype(float) / len(Rj) * len(E)})
    R['weights_summary'] = dict(margins='county x week x registration/amendment (raking)', min=round(float(E.w.min()), 3), max=round(float(E.w.max()), 3),
                                deff_kish=round(float((E.w ** 2).mean() / E.w.mean() ** 2), 3))

    # ---------------- (a) mechanism (text) + linkage in the sample
    for mm in MECHS:
        E['m_' + mm] = E.mech == mm
    E['after_post_text'] = E.mech != 'M_DIRECT'
    E['linked'] = E.n_prior_post > 0
    E['after_post_any'] = E.after_post_text | E.linked
    E['unfulfilled'] = E.mech.isin(['M_NEREMEDIAT', 'M_PARTIAL'])
    R['mechanism'] = {t: {k: (wshare if t == 'INMATRICULARE' else share)(S, k) for k in ['m_' + x for x in MECHS] + ['after_post_text', 'linked', 'after_post_any', 'unfulfilled',
                                                                                    'S_INTERES', 'F_NEREMEDIAT', 'F_NEPRECIZARI', 'F_NEINDEPLINIT']}
                      for t, S in [('ALL', E)] + list(E.groupby('tip'))}
    R['mechanism']['ALL_weighted'] = {k: share(E, k, w='w')['value'] for k in ['unfulfilled', 'after_post_text', 'linked']}
    R['mechanism_x_linkage'] = pd.crosstab(E.mech, E.linked).rename(columns={True: 'linked', False: 'not_linked'}).to_dict('index')
    R['durations_sample'] = dict(median_days_filing_to_rejection=float(E.file_to_rej_days.median()),
                                 iqr=[float(E.file_to_rej_days.quantile(.25)), float(E.file_to_rej_days.quantile(.75))],
                                 median_days_last_postponement_to_rejection=float(E.days_last_post_to_rej.median()),
                                 postponements_per_rejection=E.n_prior_post.value_counts().sort_index().to_dict())

    # ---------------- (b),(d) categories
    for c in CODES:
        E['c_' + c] = E.L_H.map(lambda s: c in s); E['cC_' + c] = E.L_C.map(lambda s: c in s); E['cR_' + c] = E.L_R.map(lambda s: c in s)
    E['n_cats'] = E.L_H.map(lambda s: len(s - {'NERESTATAT'}))
    V = json.load(open(os.path.join(HERE, '06_validate.out.json'), encoding='utf-8'))
    per = V['L_H']['per_category']
    restated = E[~E.c_NERESTATAT]
    cat_rows = []
    for c in CODES:
        s = share(E, 'c_' + c); pr = per.get(c, {})
        adj = round(s['value'] * pr['precision'] / pr['recall'], 4) if pr.get('precision') and pr.get('recall') else None
        cat_rows.append(dict(code=c, label=CATS[c][0] if c in CATS else 'Neclasificat: clasificatorul nu a găsit nicio cauză (manual doar 4% din eșantion nu reiau cauza)',
                             avoidable=AVOID.get(c, 'n/a'), all=s, weighted=share(E, 'c_' + c, w='w'),
                             amendments=share(E[E.tip == 'MENTIUNI'], 'c_' + c), registrations=wshare(E[E.tip == 'INMATRICULARE'], 'c_' + c),
                             among_restated=share(restated, 'c_' + c) if c != 'NERESTATAT' else None,
                             cluster_only=round(float(E['cC_' + c].mean()), 4), rules_only=round(float(E['cR_' + c].mean()), 4),
                             precision_recall_adjusted=adj, sample_pred_vs_manual=V['category_share_pred_vs_manual'].get(c), manual_share_ci95=V['manual_share_ci95'].get(c)))
    R['categories'] = cat_rows
    R['n_categories_per_entry'] = E.n_cats.value_counts().sort_index().to_dict()

    # ---------------- comparison with postponements (delay_reasons, same window, read-only)
    drf = {f['id']: f for f in json.load(open(DRJ, encoding='utf-8'))['findings']}
    dr7 = json.load(open(DR7, encoding='utf-8')); drw = dr7['waits']
    dr_adj = {r['code']: r['precision_recall_adjusted'] for r in dr7['categories']}
    dr_man = json.load(open(os.path.join(HERE, '..', 'delay_reasons', '06_validate.out.json'), encoding='utf-8'))['category_share_sample_pred_vs_manual']
    comp = []
    for c in ALIGNED:
        p = drf[f'DR.category.{c}']; r = next(x for x in cat_rows if x['code'] == c)
        comp.append(dict(code=c, rejection=r['all']['value'], rejection_ci95=r['all']['ci95'], rejection_among_restated=r['among_restated']['value'],
                         postponement=p['value'], postponement_ci95=p['ci95'],
                         ratio=round(r['all']['value'] / p['value'], 3) if p['value'] else None,
                         ratio_restated=round(r['among_restated']['value'] / p['value'], 3) if p['value'] else None,
                         postponement_not_admitted_share_of_resolved=round(1 - drw[c]['admitted_share_of_resolved'], 3) if c in drw else None,
                         rejection_adjusted=r['precision_recall_adjusted'], postponement_adjusted=dr_adj.get(c),
                         rejection_manual=round(r['sample_pred_vs_manual'][1], 4), rejection_manual_ci95=r['manual_share_ci95'], rejection_manual_n=V['n_sample'],
                         postponement_manual=round(dr_man.get(c, [0, 0.0])[1], 4), postponement_manual_n=100))
    for x in comp:
        ra = [x['ratio'], (x['rejection_adjusted'] / x['postponement_adjusted']) if x['rejection_adjusted'] and x['postponement_adjusted'] else None,
              (x['rejection_manual'] / x['postponement_manual']) if x['postponement_manual'] else None]
        x['ratio_adjusted'] = round(ra[1], 3) if ra[1] is not None else None
        x['ratio_manual'] = round(ra[2], 3) if ra[2] is not None else None
        ok = [v for v in ra if v is not None]
        x['direction_consistent'] = ('mai frecvent la respingeri' if len(ok) >= 2 and all(v > 1.1 for v in ok)
                                     else ('mai rar la respingeri' if len(ok) >= 2 and all(v < 0.9 for v in ok) else 'neconcludent'))
    R['comparison_with_postponements'] = dict(categories=comp, postponement_n=drf['DR.coverage']['n'],
                                              postponement_not_admitted_all=round(1 - drw['ALL']['admitted_share_of_resolved'], 3),
                                              postponement_avoidable_strict=drf['DR.avoidable.strict']['value'], postponement_avoidable_any=drf['DR.avoidable.any']['value'])
    # pair comparison: the same request's postponement notice in the collected bulletins (keyword classifier on both sides)
    P = pd.read_pickle(os.path.join(TMP, 'post_pairs.pkl'))
    P['post_R'] = P.text.map(lambda t: frozenset(C4.rules(t)) & frozenset(ALIGNED + ['FARA_OBIECT', 'IMPOSIBIL']))
    P = P.merge(E[['eid', 'L_H', 'L_R']], on='eid')
    def pairstats(col):
        rows = [(set(a) - {'NERESTATAT'}, set(b)) for a, b in zip(P[col], P.post_R)]
        rows = [(a, b) for a, b in rows if a and b]
        return dict(n=len(rows), any_overlap=round(float(np.mean([bool(a & b) for a, b in rows])), 3) if rows else None,
                    rejection_subset_of_postponement=round(float(np.mean([a <= b for a, b in rows])), 3) if rows else None,
                    mean_jaccard=round(float(np.mean([len(a & b) / len(a | b) for a, b in rows])), 3) if rows else None,
                    new_category_in_rejection=round(float(np.mean([bool(a - b) for a, b in rows])), 3) if rows else None)
    R['pairs'] = dict(n_pairs=int(len(P)), hybrid_vs_rules=pairstats('L_H'), rules_vs_rules=pairstats('L_R'))

    # ---------------- (c) avoidable at filing
    for mode in ('strict', 'any', 'da_or_partial_all'):
        E['av_' + mode] = E.L_H.map(lambda s: flag(s, mode))
    _ml = load('05_manual_labels.py'); ML, ML2 = _ml.MANUAL, _ml.MANUAL2
    R['avoidable'] = {mode: dict(**share(E, 'av_' + mode), weighted=share(E, 'av_' + mode, w='w')['value'],
                                 amendments=share(E[E.tip == 'MENTIUNI'], 'av_' + mode)['value'],
                                 registrations=share(E[E.tip == 'INMATRICULARE'], 'av_' + mode)['value'],
                                 excluding_nerestatat=share(E[~E.c_NERESTATAT], 'av_' + mode) if mode != 'da_or_partial_all' else None,
                                 manual_sample=round(float(np.mean([flag(v, mode) for v in list(ML.values()) + list(ML2.values())])), 3)) for mode in ('strict', 'any', 'da_or_partial_all')}
    R['avoidable']['sample_like_for_like'] = dict(strict=V['avoidable_strict'], any=V['avoidable_any'], n=V['n_sample'], batch2_out_of_sample=dict(strict=V['batch2']['avoidable_strict'], any=V['batch2']['avoidable_any']))

    # ---------------- (e) weekly
    weeks = sorted(E.week.unique())
    keyc = ['CAEN', 'SEDIU', 'ACT', 'SOLICITANT', 'INSTIT', 'NERESTATAT']
    R['weekly'] = {w: dict(n=int((E.week == w).sum()), archive=int((Rj.week == w).sum()),
                           days=sorted(E[E.week == w].din_data.dt.strftime('%d.%m').unique().tolist()),
                           **{c: share(E[E.week == w], 'c_' + c) for c in keyc},
                           unfulfilled=share(E[E.week == w], 'unfulfilled'), avoidable_strict=share(E[E.week == w], 'av_strict'),
                           archive_with_prior_postponement=round(float((Rj[Rj.week == w].n_post > 0).mean()), 4)) for w in weeks}
    R['archive_end'] = str(archive_end)
    json.dump(R, open(os.path.join(HERE, '07_results.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    figures(R, cat_rows, comp, weeks, keyc)
    taxonomy_csv()
    evidence_json(R, V)
    show = {k: R[k] for k in ('archive_window', 'archive_linkage', 'postponement_outcomes', 'coverage', 'weights_summary', 'mechanism_x_linkage', 'durations_sample', 'pairs', 'n_categories_per_entry')}
    print(json.dumps(show, ensure_ascii=False, indent=1, default=str))
    for t in ('ALL', 'MENTIUNI', 'INMATRICULARE'):
        print('MECH', t, {k: (v['value'], v['ci95']) for k, v in R['mechanism'][t].items()})
    for r in cat_rows:
        print(r['code'], r['all']['value'], r['all']['ci95'], 'w', r['weighted']['value'], 'MEN', r['amendments']['value'], r['amendments']['ci95'],
              'INM', r['registrations']['value'], r['registrations']['ci95'], 'restated', (r['among_restated'] or {}).get('value'), 'adj', r['precision_recall_adjusted'])
    for c in comp:
        print('COMP', c)
    for k, v in R['avoidable'].items():
        print('AV', k, v)
    for w in weeks:
        d = R['weekly'][w]; print('WEEK', w, d['n'], d['archive'], d['days'], {c: d[c]['value'] for c in keyc}, 'unf', d['unfulfilled']['value'], 'av', d['avoidable_strict']['value'], 'arch_link', d['archive_with_prior_postponement'])


SHORT = {'CAEN': 'Obiect de activitate / CAEN\nși declarația de autorizare', 'SEDIU': 'Sediu (dovadă, valabilitate,\nacordul vecinilor)',
         'ACT': 'Act constitutiv, hotărâri,\nact modificator, mandat', 'ASOC_ID': 'Date de identificare\nasociați/administratori',
         'SOLICITANT': 'Solicitant/deponent:\nidentitate, împuternicire', 'SEMN': 'Semnătură și forma\nînscrisurilor',
         'CERERE': 'Cererea, anexa fiscală,\nformulare', 'BEN_REAL': 'Beneficiari reali', 'CAPITAL': 'Capital social, vărsăminte',
         'INSTIT': 'Avize/atestări ale altor instituții\n(cazier fiscal, ANAF, profesii)', 'DENUM': 'Denumire', 'TARIF': 'Tarife / contor de caractere',
         'FARA_OBIECT': 'Cerere rămasă fără obiect\n(mențiune deja înregistrată)', 'IMPOSIBIL': 'Impediment legal\n(o singură formă PFA, opoziție)',
         'NERESTATAT': 'Neclasificat (nicio cauză\ndetectată automat)'}
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
S1, S2 = '#2a78d6', '#eb6834'   # validated categorical pair (dataviz validate_palette: all checks pass, light surface)


def style(ax):
    ax.set_facecolor(SURF)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8.5)


def hbar_pair(ax, labels, a, alo, ahi, b, blo, bhi, la, lb, ma=None, mb=None):
    """two bar series with CI whiskers; value labels placed right of the whisker (and of the manual-sample marker ma/mb, if given)."""
    y = np.arange(len(labels)); h = 0.38
    for off, v, lo, hi, col, lab, mk in ((h / 2, a, alo, ahi, S1, la, ma), (-h / 2, b, blo, bhi, S2, lb, mb)):
        v = np.array(v) * 100
        ax.barh(y + off, v, height=h, color=col, edgecolor=SURF, linewidth=1.5, label=lab)
        ax.errorbar(v, y + off, xerr=[v - np.array(lo) * 100, np.array(hi) * 100 - v], fmt='none', ecolor=INK2, elinewidth=0.9, capsize=2)
        right = np.array(hi) * 100 if mk is None else np.maximum(np.array(hi) * 100, np.array(mk) * 100 + 0.4)
        for yi, vi, hh in zip(y + off, v, right):
            ax.text(hh + 0.6, yi, f'{vi:.1f}%'.replace('.', ','), va='center', fontsize=7, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8, color=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)


def figures(R, cat_rows, comp, weeks, keyc):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
    nm = R['coverage']['by_type']['parsed'].get('MENTIUNI', 0); ni = R['coverage']['by_type']['parsed'].get('INMATRICULARE', 0)
    rows = sorted(cat_rows, key=lambda r: (r['code'] != 'NERESTATAT', r['all']['value']))   # unclassified at the bottom
    fig, ax = plt.subplots(figsize=(9, 8.4), facecolor=SURF); style(ax)
    hbar_pair(ax, [SHORT[r['code']] for r in rows],
              [r['amendments']['value'] for r in rows], [r['amendments']['ci95'][0] for r in rows], [r['amendments']['ci95'][1] for r in rows],
              [r['registrations']['value'] for r in rows], [r['registrations']['ci95'][0] for r in rows], [r['registrations']['ci95'][1] for r in rows],
              f'cereri de mențiuni (n={nm})', f'cereri de înmatriculare (n={ni})')
    ax.set_xlabel('% din respingerile cu motiv publicat care invocă categoria (o respingere poate avea mai multe cauze)', fontsize=8.5, color=INK2)
    ax.set_title(f'De ce sunt respinse cererile la ONRC: cauzele reluate în încheierile de respingere\n'
                 f'{R["coverage"]["parsed"]} respingeri, decizii 19 oct.–18 nov. 2026 (BERC), IC 95% grupat pe buletin', fontsize=10.5, color=INK, loc='left')
    ax.legend(loc='lower right', fontsize=8, frameon=False, labelcolor=INK)
    fig.text(0.01, 0.005, 'Sursa: BERC 2026 (buletine colectate), clasificare locală (embeddings + reguli), validare manuală n=150 (recall ~0,65). '
                          'Înmatriculări: n mic, IC Wilson. Asistat de AI.', fontsize=6.8, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(FIG, f'fig_a_categorii_respingere.{ext}'), dpi=180, facecolor=SURF)
    plt.close(fig)

    cs = sorted(comp, key=lambda r: r['postponement'])
    fig, ax = plt.subplots(figsize=(9, 7.4), facecolor=SURF); style(ax)
    hbar_pair(ax, [SHORT[r['code']] for r in cs],
              [r['rejection'] for r in cs], [r['rejection_ci95'][0] for r in cs], [r['rejection_ci95'][1] for r in cs],
              [r['postponement'] for r in cs], [r['postponement_ci95'][0] for r in cs], [r['postponement_ci95'][1] for r in cs],
              f'respingeri (n={R["coverage"]["parsed"]})', f'amânări (n={R["comparison_with_postponements"]["postponement_n"]})',
              ma=[r['rejection_manual'] for r in cs], mb=[r['postponement_manual'] for r in cs])
    yy = np.arange(len(cs))
    ax.plot([r['rejection_manual'] * 100 for r in cs], yy + 0.19, 'D', ms=5, color=INK, markerfacecolor=SURF, markeredgewidth=1.3, label='eșantion manual (pe bara respectivă)')
    ax.plot([r['postponement_manual'] * 100 for r in cs], yy - 0.19, 'D', ms=5, color=INK, markerfacecolor=SURF, markeredgewidth=1.3)
    ax.set_xlabel('% din decizii care invocă categoria (multi-etichetă; aceeași taxonomie; bare = clasificator, romb = eșantion manual)', fontsize=8.5, color=INK2)
    ax.set_title('Respingeri vs. amânări: aceleași cauze, ponderi comparate\nDecizii 19 oct.–18 nov. 2026 (BERC), IC 95% grupat pe buletin', fontsize=10.5, color=INK, loc='left')
    ax.legend(loc='lower right', fontsize=8, frameon=False, labelcolor=INK)
    fig.text(0.01, 0.005, 'Doar categoriile comune. Barele = clasificator (recall ~0,65 la respingeri); rombul = eșantion manual (150 respingeri / 100 amânări). '
                          'Comparați romburile între ele. Analiză asistată de AI.', fontsize=6.6, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(FIG, f'fig_b_respingeri_vs_amanari.{ext}'), dpi=180, facecolor=SURF)
    plt.close(fig)

    panels = keyc[:5] + ['AV']
    fig, axs = plt.subplots(2, 3, figsize=(11, 6.4), sharex=True, facecolor=SURF)
    LUNA = {'10': 'oct', '11': 'nov'}
    def wlab(w):
        a, b = w.split('/'); return f"{a[8:10]} {LUNA[a[5:7]]}–\n{b[8:10]} {LUNA[b[5:7]]}\n(n={R['weekly'][w]['n']})"
    x = np.arange(len(weeks))
    for ax, c in zip(axs.flat, panels):
        style(ax)
        key = 'avoidable_strict' if c == 'AV' else c
        v = np.array([R['weekly'][w][key]['value'] for w in weeks]) * 100
        lo = np.array([R['weekly'][w][key]['ci95'][0] for w in weeks]) * 100; hi = np.array([R['weekly'][w][key]['ci95'][1] for w in weeks]) * 100
        ax.fill_between(x, lo, hi, color=S1, alpha=0.15, linewidth=0); ax.plot(x, v, color=S1, linewidth=2); ax.plot(x, v, 'o', ms=5, color=S1)
        ax.set_title('Evitabil la depunere (strict)' if c == 'AV' else SHORT[c], fontsize=8.5, color=INK, loc='left')
        ax.set_ylim(0, max(hi.max() * 1.15, 10)); ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
        ax.set_xticks(x); ax.set_xticklabels([wlab(w) for w in weeks], fontsize=6.8)
    for ax in axs[:, 0]:
        ax.set_ylabel('% respingeri', fontsize=8, color=INK2)
    fig.suptitle('Cauzele respingerilor pe săptămâni (data încheierii), % din respingeri, IC 95% grupat pe buletin', fontsize=10.5, color=INK, x=0.01, ha='left')
    fig.text(0.01, 0.005, 'Fiecare săptămână e acoperită doar în zilele cu buletine colectate; nu se afirmă nicio tendință. Analiză asistată de AI.', fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.025, 1, 0.95))
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(FIG, f'fig_c_saptamanal.{ext}'), dpi=180, facecolor=SURF)
    plt.close(fig)


# generic, self-written example phrases (not copied from any decision)
EXAMPLES = {
    'CAEN': ['declarația de autorizare nu cuprinde toate activitățile rezultate din recodificarea CAEN', 'codul CAEN cerut la autorizare lipsește din obiectul de activitate',
             'după actualizare au rămas coduri care cer condiții speciale'],
    'SEDIU': ['actul de folosință a spațiului a expirat și nu s-a depus prelungirea', 'nu s-a depus acordul asociației de proprietari pentru activitate în locuință',
              'adresa sediului nu coincide între cerere și contract'],
    'ACT': ['nu s-a depus actul constitutiv actualizat după modificare', 'hotărârea nu cuprinde toate modificările solicitate', 'durata mandatului administratorului lipsește din act'],
    'ASOC_ID': ['asociatul are alt act de identitate decât cel din registru', 'actualizarea datelor de identificare nu apare în decizie', 'nu s-a depus copia actului de identitate al administratorului'],
    'SOLICITANT': ['persoana care a depus cererea nu are împuternicire valabilă', 'cererea e semnată de cineva fără calitate în firmă', 'lipsește copia actului de identitate al solicitantului'],
    'SEMN': ['documentele nu poartă semnătură electronică calificată', 'semnătura olografă apare ca imagine copiată', 'cererea de mențiuni nu este semnată'],
    'CERERE': ['s-a ales alt tip de cerere decât cel potrivit', 'nu s-a clarificat ce mențiune se cere', 'lipsește o pagină din formularul cererii'],
    'BEN_REAL': ['nu s-a depus declarația privind beneficiarul real', 'beneficiarul real e trecut doar în actul constitutiv', 'declarația e semnată de altă persoană decât reprezentantul legal'],
    'CAPITAL': ['lipsește dovada vărsării capitalului subscris', 'nu s-a depus dovada majorării capitalului', 'structura părților sociale după cesiune nu e clară'],
    'INSTIT': ['asociatul are fapte înscrise în cazierul fiscal', 'la cesiune lipsește certificatul de atestare fiscală', 'activitatea cere aviz sau atestat profesional'],
    'DENUM': ['denumirea firmei e scrisă greșit în cerere', 'lipsește dovada rezervării denumirii', 'forma juridică din denumire nu mai corespunde'],
    'TARIF': ['nu s-a depus contorul de caractere pentru publicare', 'nota de calcul pentru publicare lipsește', 'tariful de publicare nu poate fi calculat'],
    'FARA_OBIECT': ['actualizarea CAEN fusese deja înregistrată pe altă cerere', 'mențiunea cerută figurează deja în registru', 'cererea a rămas fără obiect'],
    'IMPOSIBIL': ['titularul mai deține o altă formă de PFA/II', 'există opoziție la hotărârea de dizolvare', 'nu a trecut termenul legal de la publicarea hotărârii'],
}
GEN_EX = ['formulă procedurală: nu s-au remediat observațiile', 'temei legal al respingerii, fără cauză', 'reluarea termenului acordat']
MIX_EX = ['observații diverse reluate din amânare', 'fragment care amestecă mai multe documente', 'clasificat pe segment după reguli']
REASONING = {
    'CAEN': 'validarea codurilor față de CAEN Rev.3, a limitelor PFA/II și a concordanței declarație–obiect se poate automatiza; activitățile condiționate cer analiză juridică',
    'SEDIU': 'data de expirare a dovezii de sediu și prezența acordului pentru locuințe se pot verifica automat; conținutul contractului nu',
    'ACT': 'prezența actului constitutiv actualizat se poate verifica; conformitatea conținutului cu Legea 31/1990 rămâne control de legalitate',
    'ASOC_ID': 'datele de identificare pot fi comparate automat cu registrul / evidența persoanelor la depunere',
    'SOLICITANT': 'împuternicirea și calitatea semnatarului pot fi cerute și verificate la încărcare',
    'SEMN': 'validitatea semnăturii electronice calificate se verifică automat (validator eIDAS)',
    'CERERE': 'tipul cererii, câmpurile obligatorii și versiunea formularului se pot valida în formular',
    'BEN_REAL': 'obligația declarației se poate deduce automat din tipul modificării',
    'CAPITAL': 'prezența dovezii de vărsământ se poate cere; corelarea sumelor e parțial automatizabilă',
    'INSTIT': 'cazierul fiscal / atestarea ANAF pot fi interogate prin interoperabilitate; autorizațiile profesionale depind de alte instituții',
    'DENUM': 'regulile de formare a denumirii și potrivirea cu rezervarea se pot verifica automat',
    'TARIF': 'tariful de publicare se poate calcula automat la depunere',
    'FARA_OBIECT': 'o căutare automată în registru la depunere arată că mențiunea (ex. actualizarea CAEN Rev.3) este deja înregistrată sau în curs pe altă cerere',
    'IMPOSIBIL': 'regula unei singure forme PFA/II/IF e o verificare în baza de date; opoziția, litigiile și termenele legale nu se pot rezolva la depunere',
}


def taxonomy_csv():
    rows = []
    for cid, (lab, cat) in sorted(C4.CLUSTER_MAP.items()):
        ex = EXAMPLES.get(cat) or (GEN_EX if cat == 'GENERIC' else MIX_EX)
        rows.append(dict(cluster=cid, eticheta_cluster=lab, categorie=cat,
                         categorie_eticheta=CATS[cat][0] if cat in CATS else ('Formulă procedurală (exclusă din cauze)' if cat == 'GENERIC'
                                                                              else 'Cluster eterogen: categoria vine din reguli / vecini'),
                         evitabil_la_depunere=AVOID.get(cat, 'n/a'), motivare=REASONING.get(cat, ''), exemplu_1=ex[0], exemplu_2=ex[1], exemplu_3=ex[2]))
    pd.DataFrame(rows).to_csv(os.path.join(HERE, 'taxonomy.csv'), index=False, encoding='utf-8-sig')


def evidence_json(R, V):
    window = 'rejection decisions 19 Oct-18 Nov 2026 (21 decision days with collected BERC bulletins)'
    cav = ('PDFs cover only the collected bulletins (~11% of archive rejections in the window); CIs reflect sampling among collected bulletins only; '
           'one rejection can cite several categories (shares sum to >100%); registrations have small n (wide CIs).')
    F = []
    c = R['coverage']
    F.append(dict(id='RR.coverage', value=dict(parsed=c['parsed'], bulletin_index_rejections=c['bulletin_index_rejections'], archive_rejections_window=c['archive_window'],
                                               share=c['share'], share_on_parsed_days=c['share_on_parsed_days'], by_type=c['by_type'], bulletins=c['bulletins'],
                                               decision_days=c['decision_days_parsed'], county_coverage_min_max=c['county_coverage_min_max'],
                                               county_coverage_cv=c['county_coverage_cv'], jtype_parsed=c['jtype_parsed'], jtype_archive=c['jtype_archive']),
                  ci95=None, n=c['parsed'], window=window,
                  method='Full rejection decisions ("ÎNCHEIERE ... urmează a respinge prezenta cerere, pe motiv ... DISPUNE Respinge") parsed with PyMuPDF from all 545 '
                         'bulletins; deduplicated on request nr + decision day; 100% linked to the archive Respins decision; type from the bulletin index section.',
                  caveat='Denominators are archive counts (sol == Respins, deduplicated on request nr + day).'))
    aw = R['archive_window']
    F.append(dict(id='RR.archive_context', value=aw, ci95=None, n=aw['rejections'], window='archive decisions 19 Oct-18 Nov 2026',
                  method='Archive counts: Respins, Renunțat (applicant waived, a separate outcome, not a rejection), AUTO_AMANARI, Admis.', caveat='Archive misses some postponements on a few days.'))
    for t, d in R['archive_linkage'].items():
        F.append(dict(id=f'RR.archive_prior_postponement.{t}', value=d['share_with_prior_postponement'], ci95=d['ci95'], n=d['n'], window='all archive rejections 19 Oct-18 Nov 2026 (census)',
                      method='Share of archive rejections with an earlier AUTO_AMANARI decision of the same request (same request nr and filing day). '
                             f'Median days last postponement -> rejection {d["median_days_last_postponement_to_rejection"]}; filing -> rejection {d["median_days_filing_to_rejection"]}.',
                      caveat='Binomial CI; lower bound because the archive misses some postponements.'))
    po = R['postponement_outcomes']
    F.append(dict(id='RR.postponement_outcomes', value=dict(rejected_share_of_resolved=po['rejected_share_of_resolved'], rejected_share_of_all_postponed=po['rejected_share_of_all_postponed'],
                                                            outcome_counts=po['outcome_counts']), ci95=None, n=po['postponed_requests'],
                  window=f'postponements decided {po["window"][0]}..{po["window"][1]}, follow-up to {R["archive_end"]}',
                  method='First later non-postponement decision of the same request (request nr + filing day) after its last postponement in the window.',
                  caveat='Unresolved requests at archive end are excluded from "of resolved".'))
    for t in ('ALL', 'MENTIUNI', 'INMATRICULARE'):
        for k, lab in (('unfulfilled', 'text states the postponement was not (or only partly) complied with (M_NEREMEDIAT + M_PARTIAL)'),
                       ('after_post_text', 'text references an earlier postponement'), ('m_M_PARTIAL', 'partly remedied / completion documents defective'),
                       ('m_M_DIRECT', 'no postponement referenced in the text'), ('after_post_any', 'text reference OR archive linkage')):
            s = R['mechanism'][t][k]
            F.append(dict(id=f'RR.mechanism.{k}.{t}', value=s['value'], ci95=s['ci95'], n=s['n'], window=window,
                          method=f'Share of parsed rejections where the {lab}; regex on the procedural layer (step 2). Mechanism accuracy on the manual sample '
                                 f'{V["mechanism"]["accuracy"]} (binary after-postponement {V["mechanism"]["after_postponement_binary_accuracy"]}).',
                          caveat=cav + ' Text-based "direct" rejections mostly do have an archived prior postponement (see RR.archive_prior_postponement).'))
    for r in R['categories']:
        for part in ('all', 'amendments', 'registrations'):
            s = r[part]
            F.append(dict(id=f"RR.category.{r['code']}.{part}", value=s['value'], ci95=s['ci95'], n=s['n'], window=window,
                          method=('Share of rejections citing the category (any-of). Hybrid label (HDBSCAN clusters on local multilingual-e5-small embeddings + keyword rules '
                                  'reused from delay_reasons). ' + r['label'] + f"; avoidable at filing: {r['avoidable']}. "
                                  + (f"Raked {r['weighted']['value']}; among restated {(r['among_restated'] or {}).get('value')}; cluster-only {r['cluster_only']}; rules-only {r['rules_only']}; "
                                     f"precision/recall-adjusted {r['precision_recall_adjusted']}; sample predicted vs manual {r['sample_pred_vs_manual']}." if part == 'all' else '')),
                          caveat=cav))
    cp = R['comparison_with_postponements']
    for r in cp['categories']:
        F.append(dict(id=f"RR.vs_postponement.{r['code']}", value=dict(rejection=r['rejection'], postponement=r['postponement'], ratio=r['ratio'], ratio_restated=r['ratio_restated'],
                                                                       postponement_not_admitted_share_of_resolved=r['postponement_not_admitted_share_of_resolved'],
                                                                       ratio_adjusted=r['ratio_adjusted'], ratio_manual=r['ratio_manual'], direction_consistent=r['direction_consistent'],
                                                                       rejection_manual=r['rejection_manual'], postponement_manual=r['postponement_manual']),
                      ci95=dict(rejection=r['rejection_ci95'], postponement=r['postponement_ci95']), n=R['coverage']['parsed'], window=window,
                      method='Same taxonomy; keyword rules shared with delay_reasons plus a procedural pre-clean and two rejection-specific rules; postponement shares '
                             'from out/delay_reasons.json; ratio = rejection share / postponement share (>1: over-represented among rejections). value also in '
                             '07_results.out.json with ratio_adjusted, ratio_manual and direction_consistent.', caveat=cav + ' Classifier recall ~0.65 on rejections biases raw rejection shares down; compare ratio_adjusted and ratio_manual (manual samples: 150 rejections, 100 postponements) and use direction_consistent.'))
    F.append(dict(id='RR.pairs', value=R['pairs'], ci95=None, n=R['pairs']['n_pairs'], window=window,
                  method='Rejections whose own earlier postponement notice is also in the collected bulletins; keyword classifier on the postponement text vs the rejection label.',
                  caveat='Small n; keyword classifier only on the postponement side.'))
    for mode in ('strict', 'any'):
        sm = R['avoidable']['sample_like_for_like'][mode]
        F.append(dict(id=f'RR.avoidable.{mode}.manual', value=sm['manual'], ci95=sm['manual_ci95'], n=R['avoidable']['sample_like_for_like']['n'], window=window,
                      method=('HEADLINE. Pooled manual sample (150 rejections), Wilson CI: share where ' + ('all causes are avoidable at filing (strict).' if mode == 'strict'
                              else 'at least one cause is avoidable at filing (upper bound).') + f' Classifier on the same 150: {sm["predicted"]} (agreement {sm["agreement"]}).'),
                      caveat='"Avoidable" is an assessment of the auditor (AI-assisted), not an ONRC classification; single AI reviewer.'))
    for mode, lab in (('strict', 'all cited categories avoidable (classifier; lower estimate)'),('any', 'at least one avoidable category (upper bound)'), ('da_or_partial_all', 'all cited categories avoidable or partly avoidable')):
        a = R['avoidable'][mode]
        F.append(dict(id=f'RR.avoidable.{mode}', value=a['value'], ci95=a['ci95'], n=a['n'], window=window,
                      method=f'Share of rejections where {lab}; flags per category in taxonomy.csv (NERESTATAT counts as not avoidable). Raked {a["weighted"]}; '
                             f'amendments {a["amendments"]}; registrations {a["registrations"]}; excluding NERESTATAT {(a["excluding_nerestatat"] or {}).get("value")} {(a["excluding_nerestatat"] or {}).get("ci95")}; manual sample (n=150) {a["manual_sample"]} '
                             f'Wilson {R["avoidable"]["sample_like_for_like"][mode]["manual_ci95"] if mode in ("strict", "any") else None}. Classifier figures are LOWER estimates (recall ~0.65).',
                      caveat=cav + ' "Avoidable" is an assessment of the auditor (AI-assisted), not an ONRC classification.'))
    for w, d in R['weekly'].items():
        F.append(dict(id=f'RR.weekly.{w}', value={k: (v['value'] if isinstance(v, dict) else v) for k, v in d.items() if k not in ('days',)},
                      ci95={k: v['ci95'] for k, v in d.items() if isinstance(v, dict)}, n=d['n'], window=f'week {w}, decision days {",".join(d["days"])}',
                      method='Shares per decision week; archive = archive rejections in the week.', caveat=cav + ' No trend is claimed.'))
    vv = V['L_H']
    F.append(dict(id='RR.validation', value=dict(exact_set_accuracy=vv['exact_set_accuracy'], any_overlap=vv['any_overlap'], mean_jaccard=vv['mean_jaccard'], micro_precision=vv['micro_precision'],
                                                 micro_recall=vv['micro_recall'], cluster_only_exact=V['L_C']['exact_set_accuracy'], rules_only_exact=V['L_R']['exact_set_accuracy'],
                                                 mechanism_accuracy=V['mechanism']['accuracy'], nerestatat_pred_vs_manual=[V['nerestatat_predicted'], V['nerestatat_manual']], batch2_out_of_sample_exact=V['batch2']['L_H']['exact_set_accuracy'], batch2_precision_recall=[V['batch2']['L_H']['micro_precision'], V['batch2']['L_H']['micro_recall']]),
                  ci95=vv['exact_ci95'], n=V['n_sample'], window=window,
                  method='Two seeded random samples labelled from de-identified text: batch 1 (100, seed 20261122) before any classifier existed; batch 2 '
                         '(50, seed 20261123, disjoint) after the classifier was fixed but before joining predictions (out-of-sample). Values pooled over 150; '
                         'Wilson CI on exact-set accuracy.',
                  caveat=f'Single reviewer (AI model), no second coder. NERESTATAT is over-predicted ({V["nerestatat_predicted"]} vs {V["nerestatat_manual"]} of {V["n_sample"]}): '
                         'the classifier misses causes embedded in procedural sentences. FARA_OBIECT/IMPOSIBIL rules were written after reading batch 1 '
                         '(FARA_OBIECT recall on batch 2: 1 of 4).'))
    for c2 in ('FARA_OBIECT', 'IMPOSIBIL', 'NERESTATAT', 'CAEN', 'SEDIU', 'ACT', 'SOLICITANT', 'INSTIT', 'ASOC_ID', 'CERERE', 'CAPITAL'):
        F.append(dict(id=f'RR.category.{c2}.manual', value=V['category_share_pred_vs_manual'][c2][1], ci95=V['manual_share_ci95'][c2], n=V['n_sample'], window=window,
                      method='Share in the pooled manual sample (150 rejections, two seeded batches), Wilson CI. Least biased estimate; reference value for '
                             'FARA_OBIECT, IMPOSIBIL and NERESTATAT (manual NERESTATAT = rejections that restate no cause at all).',
                      caveat='Single AI reviewer; n=150.'))
    k = json.load(open(os.path.join(HERE, '04_classify.out.json'), encoding='utf-8'))
    F.append(dict(id='RR.agreement_cluster_vs_rules', value={c2: v['kappa_CR'] for c2, v in k['entry_level'].items()}, ci95=None, n=c['parsed'], window=window,
                  method='Cohen kappa per category, entry level, cluster-only vs keyword-only classifier.', caveat='Both classifiers read the same de-identified text.'))
    json.dump(dict(_meta='Why ONRC applications are rejected: reasons from BERC rejection decisions, compared with postponement reasons. Aggregates only; no identifiers. '
                         'Built by independent_audit/rejection_reasons/07_results.py. AI-assisted analysis (see README).', findings=F),
              open(OUTJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str, allow_nan=False)


if __name__ == '__main__':
    main()
