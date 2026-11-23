"""Step 7: coverage, category shares (95% CI clustered by bulletin), weights, weekly shares, avoidable-at-filing share,
waits by category (term granted, filing->postponement, Kaplan-Meier filing->final decision), figures and evidence JSON.
Inputs: _tmp/entries.pkl, _tmp/entry_labels.pkl, _tmp/seg_labels.pkl, archive (needed columns only), 04/06 outputs.
Outputs: figures/*.png|svg, taxonomy.csv, 07_results.out.json, ../out/delay_reasons.json (aggregates only)."""
import os, json, importlib.util, collections, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp'); FIG = os.path.join(HERE, 'figures')
OUTJ = os.path.join(HERE, '..', 'out', 'delay_reasons.json')
os.makedirs(FIG, exist_ok=True)
WIN = ('2026-10-19', '2026-11-18')
SRC = 'BERC bulletin PDFs 2026 (W:/SOLOResearch/bulletins/2026, 545 files, all parsed) + decisions archive W:/SOLOResearch/analysis_decisions.pkl'


def load(name):
    spec = importlib.util.spec_from_file_location('m' + name[:2], os.path.join(HERE, name)); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


C4 = load('04_classify.py'); CATS = C4.CATS
AVOID = {k: v[1] for k, v in CATS.items()}


def share(df, col, w=None, ncol=None):
    """ratio estimator sum(y)/sum(n), 95% CI clustered by bulletin (linearisation; as in cost_evidence/03)."""
    wt = df[w].astype(float) if w else pd.Series(1.0, index=df.index)
    n = (df[ncol].astype(float) if ncol else pd.Series(1.0, index=df.index)) * wt
    y = df[col].astype(float) * wt
    g = pd.DataFrame({'y': y, 'n': n, 'b': df.bulletin}).groupby('b').sum()
    G = len(g); p = g.y.sum() / g.n.sum()
    se = np.sqrt(G / (G - 1) * ((g.y - p * g.n) ** 2).sum()) / g.n.sum() if G > 1 else np.nan
    return dict(value=round(float(p), 4), ci95=[round(float(max(0, p - 1.96 * se)), 4), round(float(min(1, p + 1.96 * se)), 4)],
                n=int(len(df)), bulletins=int(G))


def rake(df, margins, iters=50):
    w = np.ones(len(df))
    for _ in range(iters):
        for col, target in margins.items():
            cur = pd.Series(w).groupby(df[col].values).sum()
            f = (target / cur).reindex(df[col].values).fillna(1.0).values
            w = w * f
    return w / w.mean()


def km_median(t, event):
    """Kaplan-Meier median (days); None if the survival curve never reaches 0.5 (censored)."""
    t = np.asarray(t, float); e = np.asarray(event, bool)
    order = np.argsort(t); t, e = t[order], e[order]
    s, n = 1.0, len(t)
    for ti in np.unique(t):
        at = (t >= ti).sum(); d = ((t == ti) & e).sum()
        if at and d:
            s *= 1 - d / at
            if s <= 0.5:
                return float(ti)
    return None


def main():
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    L = pd.read_pickle(os.path.join(TMP, 'entry_labels.pkl'))
    SL = pd.read_pickle(os.path.join(TMP, 'seg_labels.pkl'))
    E = E.merge(L[['eid', 'L_H', 'L_C', 'L_R']], on='eid')
    E = E[(E.din_data >= WIN[0]) & (E.din_data <= WIN[1])].reset_index(drop=True)
    E['week'] = E.din_data.dt.to_period('W-SUN').astype(str)
    R = {}

    # ---------------- coverage vs archive
    df = pd.read_pickle(r'W:\SOLOResearch\analysis_decisions.pkl')[['cat', 'app_nr', 'app', 'res', 'county', 'jtype', 'sol']]
    df = df[df.res >= '2026-01-01']
    archive_end = df.res.max()
    A = df[df.cat == 'AUTO_AMANARI'].copy(); A['dd'] = A.res.dt.normalize(); A = A.drop_duplicates(['app_nr', 'dd'])
    Aw = A[(A.dd >= WIN[0]) & (A.dd <= WIN[1])].copy(); Aw['week'] = Aw.dd.dt.to_period('W-SUN').astype(str)
    days = sorted(E.din_data.dt.normalize().unique())
    Acov = Aw[Aw.dd.isin(days)]
    wk = pd.DataFrame({'archive': Aw.groupby('week').size(), 'parsed': E.groupby('week').size(),
                       'decision_days_parsed': E.groupby('week').din_data.nunique()}).fillna(0)
    wk['coverage'] = (wk.parsed / wk.archive).round(4)
    ct = pd.DataFrame({'archive': Aw.groupby('county', observed=True).size(), 'parsed': E.groupby('county').size()}).fillna(0)
    ct['cov'] = ct.parsed / ct.archive
    jt_p = E.jtype.value_counts(normalize=True).round(3).to_dict(); jt_a = Aw.jtype.astype(str).value_counts(normalize=True).round(3).to_dict()
    R['coverage'] = dict(parsed=int(len(E)), archive_window=int(len(Aw)), share=round(len(E) / len(Aw), 4),
                         archive_on_parsed_days=int(len(Acov)), share_on_parsed_days=round(len(E) / len(Acov), 4),
                         decision_days_parsed=int(len(days)), decision_days_window=int(Aw.dd.nunique()),
                         bulletins=int(E.bulletin.nunique()), by_week=wk.reset_index().rename(columns={'index': 'week'}).to_dict('records'),
                         county_coverage_min_max=[round(float(ct['cov'].min()), 3), round(float(ct['cov'].max()), 3)],
                         county_coverage_cv=round(float(ct['cov'].std() / ct['cov'].mean()), 3),
                         jtype_parsed=jt_p, jtype_archive=jt_a)
    # raking weights to archive county x week margins of the window
    E['w'] = rake(E, {'county': Aw.groupby('county', observed=True).size().astype(float) / len(Aw) * len(E),
                      'week': Aw.groupby('week').size().astype(float) / len(Aw) * len(E)})
    R['weights_summary'] = dict(min=round(float(E.w.min()), 3), max=round(float(E.w.max()), 3), deff_kish=round(float((E.w ** 2).mean() / E.w.mean() ** 2), 3))

    # ---------------- official grounds
    R['grounds'] = {g: share(E, g) for g in ['G_conditii_legale', 'G_incompleta', 'G_neconcordante', 'G_forma']}

    # ---------------- category shares (any-of, multi-label)
    codes = list(CATS) + ['NESPEC']
    for c in codes:
        E['c_' + c] = E.L_H.map(lambda s: c in s)
        E['cC_' + c] = E.L_C.map(lambda s: c in s); E['cR_' + c] = E.L_R.map(lambda s: c in s)
    E['n_cats'] = E.L_H.map(lambda s: len(s - {'NESPEC'}))
    # mention share: non-generic segments per category / all non-generic segments
    SL = SL[SL.eid.isin(E.eid)]
    segc = SL[SL.cat_H != 'GENERIC'].groupby(['eid', 'cat_H']).size().unstack(fill_value=0).reindex(E.eid).fillna(0)
    E['nseg_spec'] = segc.sum(axis=1).values
    V = json.load(open(os.path.join(HERE, '06_validate.out.json'), encoding='utf-8'))
    per = V['L_H']['per_category']
    cat_rows = []
    for c in codes:
        s = share(E, 'c_' + c); sw = share(E, 'c_' + c, w='w')
        sm = None
        if c in segc.columns:
            E['m_' + c] = segc[c].values
            sm = share(E[E.nseg_spec > 0], 'm_' + c, ncol='nseg_spec')
        pr = per.get(c, {})
        adj = round(s['value'] * pr['precision'] / pr['recall'], 4) if pr.get('precision') and pr.get('recall') else None
        cat_rows.append(dict(code=c, label=CATS[c][0] if c in CATS else 'Neclasificat (nicio categorie găsită de clasificator; manual 0/100 fără motiv concret)',
                             avoidable=AVOID.get(c, 'n/a'), any_of=s, any_of_weighted=sw, mention_share=sm,
                             cluster_only=round(float(E['cC_' + c].mean()), 4), rules_only=round(float(E['cR_' + c].mean()), 4),
                             precision_recall_adjusted=adj, sample_pred_vs_manual=V['category_share_sample_pred_vs_manual'].get(c)))
    R['categories'] = cat_rows
    R['n_categories_per_entry'] = E.n_cats.value_counts().sort_index().to_dict()

    # ---------------- avoidable at filing
    def flag(s, mode):
        s = s - {'NESPEC'}
        if not s:
            return False
        f = [AVOID[c] for c in s]
        return all(x == 'da' for x in f) if mode == 'strict' else (any(x == 'da' for x in f) if mode == 'any' else all(x in ('da', 'parțial') for x in f))
    for mode in ('strict', 'any', 'da_or_partial_all'):
        E['av_' + mode] = E.L_H.map(lambda s: flag(s, mode))
    R['avoidable'] = {m: dict(**share(E, 'av_' + m), weighted=share(E, 'av_' + m, w='w')['value']) for m in ('strict', 'any', 'da_or_partial_all')}
    R['avoidable']['manual_sample_strict'] = round(float(np.mean([flag(set(v), 'strict') for v in load('05_manual_labels.py').MANUAL.values()])), 3)
    R['avoidable']['strict_excluding_unclassified'] = share(E[~E.c_NESPEC], 'av_strict')
    R['avoidable']['sample_like_for_like'] = dict(strict=V['avoidable_strict_sample'], any=V['avoidable_any_sample'])
    R['avoidable']['manual_sample_any'] = round(float(np.mean([flag(set(v), 'any') for v in load('05_manual_labels.py').MANUAL.values()])), 3)

    # ---------------- weekly
    weeks = sorted(E.week.unique())
    R['weekly'] = {w: {c: share(E[E.week == w], 'c_' + c) for c in codes} | {'avoidable_strict': share(E[E.week == w], 'av_strict'),
                                                                               'n': int((E.week == w).sum()),
                                                                               'days': sorted(E[E.week == w].din_data.dt.strftime('%d.%m').unique().tolist())}
                   for w in weeks}

    # ---------------- waits
    links = df[df.app_nr.isin(E.app_nr.unique())][['cat', 'app_nr', 'app', 'res', 'sol']]
    links = links[links.cat != 'AUTO_AMANARI']
    m = E[['eid', 'app_nr', 'din_data', 'data_cerere']].merge(links, on='app_nr', how='left')
    m = m[(m.res > m.din_data) & (m.app.dt.normalize() == m.data_cerere)]
    fin = m.sort_values('res').drop_duplicates('eid').set_index('eid')
    E['final_res'] = E.eid.map(fin.res); E['final_sol'] = E.eid.map(fin.sol.astype(str))
    E['resolved'] = E.final_res.notna()
    E['t_file_final'] = np.where(E.resolved, (E.final_res - E.data_cerere).dt.total_seconds() / 86400,
                                 (archive_end - E.data_cerere).dt.total_seconds() / 86400)
    E['t_post_final'] = np.where(E.resolved, (E.final_res - E.din_data).dt.total_seconds() / 86400,
                                 (archive_end - E.din_data).dt.total_seconds() / 86400)
    reposts = A[A.app_nr.isin(E.app_nr)][['app_nr', 'dd']]
    rp = E[['eid', 'app_nr', 'din_data']].merge(reposts, on='app_nr'); rp = rp[rp.dd > rp.din_data].groupby('eid').size()
    E['repost'] = E.eid.map(rp).fillna(0) > 0
    waits = {}
    for c in codes + ['ALL']:
        S = E if c == 'ALL' else E[E['c_' + c]]
        if len(S) < 20:
            continue
        waits[c] = dict(n=int(len(S)), term_granted_median=float(S.term_days.median()), filing_to_postponement_median=float(S.file_to_post_days.median()),
                        filing_to_postponement_p25_p75=[float(S.file_to_post_days.quantile(.25)), float(S.file_to_post_days.quantile(.75))],
                        resolved_by_archive_end=round(float(S.resolved.mean()), 3),
                        km_median_filing_to_final=km_median(S.t_file_final, S.resolved),
                        km_median_postponement_to_final=km_median(S.t_post_final, S.resolved),
                        admitted_share_of_resolved=round(float((S.final_sol[S.resolved] == 'Admis').mean()), 3) if S.resolved.any() else None,
                        repostponed_share=round(float(S.repost.mean()), 3))
    R['waits'] = waits
    R['archive_filing_to_postponement_median'] = float(((Aw.dd - Aw.app.dt.normalize()).dt.days).median())
    R['archive_filing_to_postponement_p25_p75'] = [float(x) for x in ((Aw.dd - Aw.app.dt.normalize()).dt.days).quantile([.25, .75])]
    R['archive_end'] = str(archive_end)

    json.dump(R, open(os.path.join(HERE, '07_results.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    figures(R, cat_rows, weeks)
    taxonomy_csv()
    evidence_json(R, V)
    print(json.dumps({k: R[k] for k in ('coverage', 'weights_summary', 'avoidable', 'n_categories_per_entry')}, ensure_ascii=False, indent=1, default=str))
    for r in cat_rows:
        print(r['code'], r['any_of']['value'], r['any_of']['ci95'], 'w', r['any_of_weighted']['value'], 'mention', (r['mention_share'] or {}).get('value'),
              'C', r['cluster_only'], 'R', r['rules_only'], 'adj', r['precision_recall_adjusted'], 'sample pred/manual', r['sample_pred_vs_manual'])
    for c, v in waits.items():
        print('WAIT', c, v)
    for w in weeks:
        print('WEEK', w, R['weekly'][w]['n'], R['weekly'][w]['days'], {c: R['weekly'][w][c]['value'] for c in ['CAEN', 'SEDIU', 'ACT', 'CERERE', 'SOLICITANT']},
              'av', R['weekly'][w]['avoidable_strict']['value'])


SHORT = {'CAEN': 'Obiect de activitate / CAEN\nși declarația de autorizare', 'SEDIU': 'Sediu (dovadă, valabilitate,\nacordul vecinilor, adresă)',
         'ACT': 'Act constitutiv, hotărâri,\nact modificator, mandat', 'ASOC_ID': 'Date de identificare\nasociați/administratori',
         'SOLICITANT': 'Solicitant/deponent:\nidentitate, împuternicire', 'SEMN': 'Semnătură și forma\nînscrisurilor',
         'CERERE': 'Cererea, anexa fiscală,\nformulare', 'BEN_REAL': 'Beneficiari reali', 'CAPITAL': 'Capital social, vărsăminte',
         'INSTIT': 'Avize/atestări ale altor instituții\n(cazier fiscal, ANAF, profesii)', 'DENUM': 'Denumire (rezervare, formă)',
         'TARIF': 'Tarife / contor de caractere', 'NESPEC': 'Neclasificat'}
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
COL = {'da': '#2a78d6', 'parțial': '#eb6834', 'n/a': '#8a8984'}


def style(ax):
    ax.set_facecolor(SURF)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8.5)


def figures(R, cat_rows, weeks):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
    rows = sorted([r for r in cat_rows], key=lambda r: r['any_of']['value'])
    fig, ax = plt.subplots(figsize=(8.6, 6.6), facecolor=SURF); style(ax)
    y = np.arange(len(rows))
    v = np.array([r['any_of']['value'] for r in rows]) * 100
    lo = v - np.array([r['any_of']['ci95'][0] for r in rows]) * 100; hi = np.array([r['any_of']['ci95'][1] for r in rows]) * 100 - v
    ax.barh(y, v, height=0.62, color=[COL[r['avoidable']] for r in rows], edgecolor=SURF, linewidth=2)
    ax.errorbar(v, y, xerr=[lo, hi], fmt='none', ecolor=INK2, elinewidth=1, capsize=2.5)
    for yi, vi, h in zip(y, v, hi):
        ax.text(vi + h + 0.6, yi, f'{vi:.1f}%', va='center', fontsize=8, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([SHORT[r['code']] for r in rows], fontsize=8, color=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_xlabel('% din amânările cu motiv publicat care invocă categoria (o amânare poate avea mai multe motive)', fontsize=8.5, color=INK2)
    ax.set_xlim(0, max(v + hi) * 1.15)
    n = R['coverage']['parsed']
    ax.set_title(f'De ce se amână dosarele la ONRC: motivele din încheierile de amânare\n'
                 f'{n:,}'.replace(',', '.') + ' amânări, decizii 19 oct.–18 nov. 2026 (BERC), IC 95% grupat pe buletin',
                 fontsize=10.5, color=INK, loc='left')
    ax.legend(handles=[Patch(color=COL['da'], label='evitabil printr-o verificare automată la depunere'),
                       Patch(color=COL['parțial'], label='parțial evitabil'), Patch(color=COL['n/a'], label='nu se aplică')],
              loc='lower right', fontsize=8, frameon=False, labelcolor=INK)
    fig.text(0.01, 0.005, 'Sursa: BERC 2026 (buletine colectate), clasificare locală (embeddings + reguli), validare manuală n=100. Analiză asistată de AI.',
             fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(FIG, f'fig_a_categorii_amanare.{ext}'), dpi=180, facecolor=SURF)
    plt.close(fig)

    top = [r['code'] for r in sorted(cat_rows, key=lambda r: -r['any_of']['value']) if r['code'] != 'NESPEC'][:8]
    panels = top + ['AV']
    fig, axs = plt.subplots(3, 3, figsize=(11, 8.2), sharex=True, facecolor=SURF)
    LUNA = {'10': 'oct', '11': 'nov'}
    def wlab(w):
        a, b = w.split('/'); nd = len(R['weekly'][w]['days'])
        return f"{a[8:10]} {LUNA[a[5:7]]}–\n{b[8:10]} {LUNA[b[5:7]]}\n({nd} zile)"
    wl = [wlab(w) for w in weeks]
    for ax, c in zip(axs.flat, panels):
        style(ax)
        key = 'avoidable_strict' if c == 'AV' else c
        vals = np.array([R['weekly'][w][key]['value'] for w in weeks]) * 100
        los = np.array([R['weekly'][w][key]['ci95'][0] for w in weeks]) * 100; his = np.array([R['weekly'][w][key]['ci95'][1] for w in weeks]) * 100
        x = np.arange(len(weeks))
        ax.fill_between(x, los, his, color='#2a78d6', alpha=0.15, linewidth=0)
        ax.plot(x, vals, color='#2a78d6', linewidth=2)
        ax.plot(x, vals, 'o', ms=5, color='#2a78d6')
        ax.set_title('Evitabil la depunere\n(strict: toate motivele evitabile)' if c == 'AV' else SHORT[c], fontsize=8.5, color=INK, loc='left')
        ax.set_ylim(0, max(his.max() * 1.15, 10)); ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
        ax.set_xticks(x); ax.set_xticklabels(wl, fontsize=6.8, rotation=0)
    for ax in axs[:, 0]:
        ax.set_ylabel('% amânări', fontsize=8, color=INK2)
    ns = ', '.join(wl[i].split(chr(10))[0] + wl[i].split(chr(10))[1] + f": n={R['weekly'][w]['n']}" for i, w in enumerate(weeks))
    fig.suptitle('Motivele amânărilor pe săptămâni (data încheierii), % din amânări, cu IC 95% grupat pe buletin', fontsize=10.5, color=INK, x=0.01, ha='left')
    fig.text(0.01, 0.005, f'{ns}. Fiecare săptămână e acoperită doar în zilele cu buletine colectate. Analiză asistată de AI.', fontsize=7, color=INK2)
    fig.tight_layout(rect=(0, 0.025, 1, 0.96))
    for ext in ('png', 'svg'):
        fig.savefig(os.path.join(FIG, f'fig_b_saptamanal.{ext}'), dpi=180, facecolor=SURF)
    plt.close(fig)


# generic, self-written example phrases (not copied from any notice)
EXAMPLES = {
    'CAEN': ['codul CAEN nu se mai regăsește în CAEN Rev.3 – se reface cererea', 'nu sunt autorizate toate activitățile din obiectul de activitate',
             'declarația-tip privind condițiile de funcționare nu a fost depusă'],
    'SEDIU': ['dovada folosinței spațiului cu destinație de sediu a expirat', 'lipsește acordul asociației de proprietari / vecinilor',
              'adresa sediului diferă între contract și cerere'],
    'ACT': ['actul constitutiv actualizat nu corespunde actului modificator', 'durata mandatului administratorului nu este precizată',
            'hotărârea de dizolvare nu arată stingerea pasivului'],
    'ASOC_ID': ['asociatul se identifică cu alt act de identitate decât cel din registru', 'datele de identificare se actualizează prin act modificator',
                'se depune copia actului de identitate al administratorului'],
    'SOLICITANT': ['lipsește împuternicirea pentru deponentul cererii', 'cererea este semnată de o persoană fără calitate în societate',
                   'se depune copia actului de identitate al solicitantului'],
    'SEMN': ['documentele nu poartă semnătură electronică calificată validă', 'semnătura olografă a fost reprodusă ca imagine',
             'declarația se semnează personal, nu prin reprezentant'],
    'CERERE': ['anexa privind înregistrarea fiscală este completată eronat', 'cererea de înregistrare nu este completată la punctul relevant',
               'lipsește anexa privind investiția străină'],
    'BEN_REAL': ['nu s-a depus declarația privind beneficiarii reali', 'beneficiarul real indicat nu este o persoană fizică',
                 'declarația se depune distinct de actul constitutiv'],
    'CAPITAL': ['lipsește dovada vărsării capitalului social', 'nu se arată structura capitalului după majorare', 'aportul fiecărui asociat nu este precizat'],
    'INSTIT': ['asociatul/administratorul are fapte înscrise în cazierul fiscal', 'pentru cesiune se depune certificatul de atestare fiscală',
               'activitatea medicală cere autorizație de liberă practică / aviz'],
    'DENUM': ['denumirea PFA nu conține numele și prenumele titularului', 'denumirea din acte nu corespunde dovezii de rezervare',
              'denumirea societății este scrisă eronat în acte'],
    'TARIF': ['se depune contorul de caractere pentru publicarea în Monitorul Oficial', 'tariful de publicare nu a fost achitat',
              'se completează numărul de caractere în cerere'],
}
REASONING = {
    'CAEN': 'validarea codurilor față de CAEN Rev.3, a limitelor PFA/II și a prezenței declarației-tip se poate automatiza; activitățile condiționate cer analiză juridică',
    'SEDIU': 'data de expirare a dovezii de sediu, prezența acordului vecinilor pentru locuințe și nomenclatorul stradal se pot verifica automat; conținutul contractului nu',
    'ACT': 'prezența actului constitutiv actualizat și ordinea datelor se pot verifica; corelarea conținutului cu legea 31/1990 rămâne control de legalitate',
    'ASOC_ID': 'datele de identificare pot fi comparate automat cu registrul/evidența persoanelor la depunere',
    'SOLICITANT': 'împuternicirea și calitatea semnatarului (rol în registru) pot fi cerute și verificate la încărcare',
    'SEMN': 'validitatea semnăturii electronice calificate se verifică automat (validator eIDAS)',
    'CERERE': 'câmpuri obligatorii, versiunea formularului și coerența anexei fiscale se pot valida în formular',
    'BEN_REAL': 'obligația declarației se poate deduce automat din tipul modificării (structura asociaților)',
    'CAPITAL': 'prezența dovezii de vărsământ se poate cere; corelarea sumelor și a părților sociale e parțial automatizabilă',
    'INSTIT': 'cazierul fiscal / atestarea ANAF pot fi interogate prin interoperabilitate, dar autorizațiile profesionale depind de alte instituții',
    'DENUM': 'regulile de formare a denumirii și potrivirea cu rezervarea se pot verifica automat',
    'TARIF': 'tariful de publicare se poate calcula automat din document la depunere',
}


# cluster-specific generic phrases (self-written) where the category examples would not fit the cluster
CLUSTER_EX = {
    0: ['se reia motivul-standard al amânării', 'nu sunt îndeplinite condițiile legale (fără detaliere)', 'formulă introductivă'],
    1: ['cerere de completare a înscrisurilor', 'solicitare de preschimbare a termenului', 'formulă procedurală'],
    2: ['pentru cesiune se depune certificatul de atestare fiscală', 'se face dovada notificării organului fiscal', 'acordul organului fiscal privind garanțiile'],
    3: ['se cer precizări privind obiectul cererii', 'există o altă cerere cu același obiect', 'se clarifică ce mențiune se solicită'],
    4: ['citarea legii registrului comerțului', 'citarea legii societăților', 'temei legal fără motiv'],
    5: ['asociatul are fapte înscrise în cazierul fiscal', 'administratorul are fapte înscrise în cazierul fiscal', 'interdicție potrivit legii cazierului fiscal'],
    6: ['cazier fiscal cu fapte înscrise (cu temei legal)', 'noul asociat are fapte în cazierul fiscal', 'se aplică interdicția din legea cazierului fiscal'],
    7: ['se depune contorul de caractere pentru publicare', 'tariful de publicare în Monitorul Oficial', 'se completează numărul de caractere'],
    10: ['se depune avizul asociației de proprietari', 'se depune acordul vecinilor direct afectați', 'acordul se depune în original'],
    13: ['control de legalitate prealabil – se acordă termen', 'formulă despre prerogativa registratorului', 'temei legal fără motiv'],
    14: ['denumirea PFA trebuie să conțină numele titularului', 'rezervarea denumirii nu respectă legea', 'se completează denumirea cu inițiala tatălui'],
    15: ['formulă: temei legal coroborat', 'citarea mai multor articole', 'fără motiv concret'],
    16: ['lipsa unui element obligatoriu atrage respingerea', 'avertisment de respingere', 'formulă standard'],
    18: ['se elimină textul suplimentar „fără dispecerat”', 'activitatea de dispecerat ține de alt cod', 'se refac cererea și declarația'],
    20: ['societatea este în dizolvare', 'hotărârea nu arată stingerea pasivului', 'acordul creditorilor privind pasivul'],
    21: ['declarația-tip pentru sediul secundar', 'activitățile desfășurate la terți', 'se declară dacă există activitate la punctul de lucru'],
    23: ['decizia trebuie să ia act de noile date de identificare', 'asociatul are alt act de identitate decât în registru', 'modificarea se face prin act modificator'],
    26: ['obiectul nu este actualizat conform CAEN Rev.3', 'clasa CAEN nu mai există în noua clasificare', 'se actualizează obiectul de activitate'],
    27: ['se respectă notele explicative CAEN', 'clasificarea activităților din economia națională', 'activitatea se încadrează în alt cod'],
    28: ['se reface durata mandatului administratorului', 'durata mandatului diferă între acte', 'durata se stabilește prin hotărâre'],
    29: ['durata mandatului nu poate fi nedeterminată', 'se precizează o perioadă de timp a mandatului', 'Codul civil privind mandatul'],
    30: ['formulă: în temeiul legii se amână cauza', 'amână cauza pentru motivele următoare', 'temei legal fără motiv'],
    31: ['declarație că nu se desfășoară activitate la sediul profesional', 'sediu profesional în locuință (PFA)', 'declarație pe proprie răspundere'],
    32: ['adresa sediului diferă între contract și cerere', 'se clarifică adresa sediului social', 'neconcordanță de adresă între documente'],
    36: ['se depune dovada prelungirii valabilității sediului', 'sediul secundar are dovada expirată', 'sediul profesional are dovada expirată'],
    37: ['contractul de închiriere a expirat', 'actul adițional nu prelungește durata', 'perioada de valabilitate a actului de sediu'],
    41: ['cine poate fi împuternicit potrivit legii', 'consilier juridic, avocat sau procură autentică', 'împuternicitul trebuie să facă dovada calității'],
    42: ['formulă: se constată neconcordanța', 'temei legal coroborat', 'fără motiv concret'],
    43: ['semnătura olografă a fost reprodusă ca imagine', 'se clarifică semnăturile de pe documente', 'semnătura trebuie aplicată de mână sau electronic calificat'],
    47: ['documentele nu au semnătură electronică calificată validă', 'se redepun documentele semnate electronic', 'semnătura electronică nu identifică semnatarul'],
    61: ['activitatea prevăzută de un cod CAEN anume', 'codul CAEN indicat nu corespunde activității', 'precizarea activității din cod'],
    65: ['PFA poate avea un număr limitat de clase CAEN', 'limitele OUG 44/2008 pentru PFA/II', 'se reduce numărul de activități'],
    66: ['cod CAEN condiționat de o lege specială', 'activitate interzisă formei de organizare', 'după recodificare rezultă activități nepermise'],
    67: ['activități medicale cer autorizație de liberă practică', 'cabinetul medical are obiect de activitate limitat', 'administratorul trebuie să fie medic'],
}


def taxonomy_csv():
    rows = []
    for cid, (lab, cat) in sorted(C4.CLUSTER_MAP.items()):
        ex = CLUSTER_EX.get(cid) or EXAMPLES.get(cat, ['formulă standard / temei legal fără motiv concret'] * 3)
        rows.append(dict(cluster=cid, eticheta_cluster=lab, categorie=cat, categorie_eticheta=CATS[cat][0] if cat in CATS else 'Formulă generică (exclusă din categorii)',
                         evitabil_la_depunere=AVOID.get(cat, 'n/a'), motivare=REASONING.get(cat, ''),
                         exemplu_1=ex[0], exemplu_2=ex[1 % len(ex)], exemplu_3=ex[2 % len(ex)]))
    pd.DataFrame(rows).to_csv(os.path.join(HERE, 'taxonomy.csv'), index=False, encoding='utf-8-sig')


def evidence_json(R, V):
    window = 'decisions 19 Oct-18 Nov 2026 (17 decision days with collected BERC bulletins)'
    cav = ('PDFs cover only the bulletins collected (about one in four postponements on covered days, none on other days); '
           'CIs reflect sampling among collected bulletins only; one postponement can cite several categories (shares sum to >100%).')
    F = []
    c = R['coverage']
    F.append(dict(id='DR.coverage', value=dict(parsed=c['parsed'], archive_postponements_window=c['archive_window'], share=c['share'],
                                               share_on_parsed_days=c['share_on_parsed_days'], decision_days=c['decision_days_parsed'],
                                               bulletins=c['bulletins'], county_coverage_min_max=c['county_coverage_min_max'],
                                               jtype_parsed=c['jtype_parsed'], jtype_archive=c['jtype_archive']),
                  ci95=None, n=c['parsed'], window=window,
                  method='Postponement notices ("Comunicare încheiere de amânare ... Motivul amânării") parsed with PyMuPDF from all 545 bulletins; '
                         'deduplicated on request nr + decision day; 100% linked to AUTO_AMANARI in the archive.',
                  caveat='The archive itself misses some postponements on a few days (see missing_postponements_sensitivity.json); denominators are archive counts.'))
    for g, s in R['grounds'].items():
        F.append(dict(id=f'DR.ground.{g}', value=s['value'], ci95=s['ci95'], n=s['n'], window=window,
                      method='Standard ground printed by the registrar software before the free text; ratio estimator, CI clustered by bulletin.', caveat=cav))
    for r in R['categories']:
        F.append(dict(id=f"DR.category.{r['code']}", value=r['any_of']['value'], ci95=r['any_of']['ci95'], n=r['any_of']['n'], window=window,
                      method=('Share of postponements citing the category (any-of). Final label = hybrid of HDBSCAN clusters on local multilingual-e5-small '
                              'embeddings and a separate keyword classifier (written after reading the clusters). Label: ' + r['label'] + f"; avoidable at filing: {r['avoidable']}. "
                              f"Raked (county x week) {r['any_of_weighted']['value']}; mention share {(r['mention_share'] or {}).get('value')}; "
                              f"cluster-only {r['cluster_only']}; rules-only {r['rules_only']}; precision/recall-adjusted {r['precision_recall_adjusted']}; "
                              f"same 100-entry sample predicted vs manual share {r['sample_pred_vs_manual']}."),
                      caveat=cav))
    for mkey, lab in (('strict', 'all cited categories avoidable (headline)'), ('any', 'at least one avoidable category (upper bound)'),
                      ('da_or_partial_all', 'all cited categories avoidable or partly avoidable')):
        a = R['avoidable'][mkey]
        F.append(dict(id=f'DR.avoidable.{mkey}', value=a['value'], ci95=a['ci95'], n=a['n'], window=window,
                      method=f'Share of postponements where {lab}; flags per category in taxonomy.csv. Raked: {a["weighted"]}. '
                             f'Manual sample: strict {R["avoidable"]["manual_sample_strict"]}, any {R["avoidable"]["manual_sample_any"]}.',
                      caveat=cav + ' "Avoidable" is an assessment of the auditor (AI-assisted), not an ONRC classification.'))
    for w, d in R['weekly'].items():
        F.append(dict(id=f'DR.weekly.{w}', value={k: v['value'] for k, v in d.items() if isinstance(v, dict)}, ci95={k: v['ci95'] for k, v in d.items() if isinstance(v, dict)},
                      n=d['n'], window=f'week {w}, decision days {",".join(d["days"])}', method='Any-of category shares per decision week.', caveat=cav + ' Week of 19-25 Oct is effectively one decision day (20 Oct); bulletin-clustered CIs understate day-to-day variance; no trend is claimed.'))
    for k, d in R['waits'].items():
        F.append(dict(id=f'DR.wait.{k}', value=d, ci95=None, n=d['n'], window=window,
                      method='Term granted = term date - postponement date; filing->postponement from the notice; final decision = first non-postponement '
                             'decision in the archive for the same request nr + filing date; Kaplan-Meier with censoring at archive end.',
                      caveat=f'Archive ends {R["archive_end"]}; most terms fall after it, so final-decision medians are censored (null = not reached). '
                             f'Filing->postponement median: sample {R["waits"]["ALL"]["filing_to_postponement_median"]} d vs archive window {R["archive_filing_to_postponement_median"]} d.'))
    vv = V['L_H']
    F.append(dict(id='DR.validation', value=dict(exact_set_accuracy=vv['exact_set_accuracy'], any_overlap=vv['any_overlap'], mean_jaccard=vv['mean_jaccard'],
                                                 micro_precision=vv['micro_precision'], micro_recall=vv['micro_recall'], label_level_accuracy=vv['label_level_accuracy'],
                                                 cluster_only_exact=V['L_C']['exact_set_accuracy'], rules_only_exact=V['L_R']['exact_set_accuracy']),
                  ci95=vv['exact_ci95'], n=V['n_sample'], window=window,
                  method='Seeded random sample of 100 postponements labelled from de-identified text before predictions were joined; Wilson CI.',
                  caveat='Headline metric is exact-set accuracy (value["exact_set_accuracy"], ci95 Wilson). Label-level accuracy is inflated by true negatives (predicting nothing scores ~0.89). '
                          'Single reviewer (AI model), no second coder; CERERE is over-assigned (precision ~0.37); 5/100 entries predicted unclassified vs 0/100 manual. '
                          f'Avoidable strict on the same 100: predicted {V["avoidable_strict_sample"]["predicted"]} vs manual {V["avoidable_strict_sample"]["manual"]}, agreement {V["avoidable_strict_sample"]["agreement"]}.'))
    k = json.load(open(os.path.join(HERE, '04_classify.out.json'), encoding='utf-8'))
    F.append(dict(id='DR.agreement_cluster_vs_rules', value={c: v['kappa_CR'] for c, v in k['entry_level'].items()}, ci95=None, n=c['parsed'], window=window,
                  method='Cohen kappa per category, entry level, cluster-only vs keyword-only classifier.', caveat='Both classifiers read the same de-identified text.'))
    json.dump(dict(_meta='Why ONRC files are postponed: reasons from BERC postponement notices. Aggregates only; no identifiers. '
                         'Built by independent_audit/delay_reasons/07_results.py. AI-assisted analysis (see README).', findings=F),
              open(OUTJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)


if __name__ == '__main__':
    main()
