"""Step 2: de-duplicate, link to the archive, parse the procedural layer (A), de-identify and split the substantive layer (B).

Input : _tmp/rejections_raw.pkl (step 1) + W:/SOLOResearch/analysis_decisions.pkl (only the needed columns).
Output: _tmp/entries.pkl    one row per rejection decision (bulletin, decision day, county, registration/amendment, procedural flags,
                            archive linkage to an earlier postponement, de-identified text; request nr kept ONLY for joins in step 7)
        _tmp/segments.pkl   one row per substantive reason segment (entry id, de-identified segment text)
        _tmp/post_pairs.pkl de-identified text of the bulletin postponement notice of the same request (pair comparison)
All of _tmp/ is deleted at the end. stdout: aggregates only.

Layer A (procedural ground of the rejection) is read by regex on the folded text:
  F_NEREMEDIAT   software formula "la termenul de soluționare se constată că profesionistul nu a remediat observațiile dispuse prin
                 încheierea de amânare"
  F_NEPRECIZARI  software formula "la termenul de soluționare, profesionistul nu a depus precizări în susținerea cererii"
  F_NEINDEPLINIT software formula "cererea de înregistrare nu îndeplinește cerințele legale prevăzute de actele normative în vigoare"
  plus free-text signals: postponement referenced, not remedied, partly remedied / defects in the completion documents,
  "lipsită de interes", waiver ("renunțare").
Mechanism (mutually exclusive, in this order):
  M_PARTIAL     a postponement is referenced and the completion was partial / the completion documents are themselves defective
  M_NEREMEDIAT  a postponement is referenced and the observations were not remedied (incl. the two "termen" software formulas)
  M_AMANARE_ALT a postponement is referenced, no statement on remedy
  M_DIRECT      no postponement referenced in the text (rejection on the first examination, as far as the text shows)
Layer B = the remaining text after removing the formulas and the rejection boilerplate (art. 106(4)/(5) explanations, art. 77 quote,
"prin încheierea ... s-a acordat termen ..."), de-identified with the SAME functions as delay_reasons/02 (pre_mask, split_segments,
GROUND_RX; imported read-only) and the same vocabulary whitelist rule (token kept only if in >= 8 entries, >= 4 bulletins, >= 3 counties).
"""
import sys; sys.dont_write_bytecode = True  # never leave __pycache__ in delay_reasons (read-only reuse)
import os, re, pickle, collections, importlib.util
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
DR = os.path.join(HERE, '..', 'delay_reasons')


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


DR02 = _load(os.path.join(DR, '02_normalize_split.py'), 'dr02')
fold, pre_mask, split_segments, GROUND_RX, GROUNDS = DR02.fold, DR02.pre_mask, DR02.split_segments, DR02.GROUND_RX, DR02.GROUNDS
WIN = ('2026-10-01', '2026-11-30')   # Oct-Nov 2026 decisions (bulletins hold a handful of Dec 2025/Feb/Sep decisions: excluded)

F_NEREM = r'(?:ca,?\s*)?la termenul de solutionare,?\s*se constata ca profesionistul nu a remediat observatiile dispuse prin incheierea de amanare,?\s*astfel\s*:?'
F_NEPREC = r'(?:ca,?\s*)?la termenul de solutionare,?\s*profesionistul nu a depus precizari in sustinerea cererii de inregistrare,?\s*astfel\s*:?'
F_NEIND = (r'(?:ca,?\s*)?cererea de inregistrare nu indeplineste cerintele legale prevazute de actele normative in vigoare,?\s*'
           r'pentru dispunerea inregistrarii cererii in registrul comertului,?\s*in sensul\s*(?:ca)?\s*:?')
POSTP = re.compile(r'incheier\w* de amanare|\bamanat\w*|\bamanarii\b|\bamanare\b|termen\w* (?:de solutionare )?acordat|s-a acordat (?:un )?(?:nou )?termen|'
                   r'se acorda (?:un )?(?:nou )?termen|nou termen|art\.?\s*106\b|preschimbar\w* (?:a )?termen|la termenul de solutionare', re.I)
NEREM = re.compile(r'nu a(?:u)? remediat|nu a(?:u)? fost remediat|nu a(?:u)? fost regularizat|nu (?:si-a|isi) (?:a )?indeplini\w* obligatii|'
                   r'nu a(?:u)? indeplinit|nu s-a(?:u)? indeplinit|nu a procedat la|nu a depus (?:nici ?un|niciun|documentele|inscrisuri|actele|in completare|precizari)|'
                   r'nu s-a(?:u)? depus|nu s-a conformat|nu a dat curs|nu a(?:u)? fost (?:inlaturat|depus|complet)|nu a completat|'
                   r'106\s*alin\.?\s*\(?\s*5|nu a clarificat|nu au fost clarificat|nu a (?:mai )?depus', re.I)
PARTIAL = re.compile(r'\bpartial\w*|\bin parte\b|nu (?:in totalitate|integral)|doar o parte|a(?:u)? ramas (?:nere|necl|neindepl|aceleasi)|'
                     r'(?:documentele|actele|inscrisurile|cererea) (?:depus\w* )?(?:in completare|de completare)|s-a(?:u)? depus (?:in completare|cerere de completare)|'
                     r'desi a depus|cu toate ca a depus|in completare (?:s-a|s-au|a) depus|documentele depuse ulterior|noile (?:documente|acte)', re.I)
INTERES = re.compile(r'lipsit\w* de interes|lipsa de interes|lipsei de interes', re.I)
RENUNT = re.compile(r'renunt\w*', re.I)
# rejection boilerplate (folded, case-preserving text, re.I)
BOIL = [
    r'facem precizarea ca,? potrivit legii[^”"]{0,900}?(?:fara a se mai acorda un alt termen de amanare|cererea de inregistrare este respinsa)[”".]*',
    r'potrivit art\.?\s*77 din legea nr\.?\s*265/2022[^”"]{0,250}[”"]?\s*lipsa unui element obligatoriu[^”"]{0,250}atrage respingerea cererii de inregistrare\.?[”"]?',
    r'[”"„]?lipsa unui element obligatoriu al cererii de inregistrare sau a unuia dintre inscrisurile obligatorii in sustinerea acestora atrage respingerea cererii de inregistrare\.?[”"]?',
    r'se vor avea in vedere prevederile art\.?\s*77[^.]{0,120}care stipuleaza ca',
    r'prin incheierea (?:registratorului )?(?:de registrul comertului )?(?:din data de|pronuntata (?:la|in) data de)\s*\d{2}\.\d{2}\.\d{4},?\s*'
    r'(?:s-a acordat termen pana la care solicitantul va remedia si completa documentele depuse in sustinerea cererii cu urmatoarele\s*:?[”"]?|au fost constatate urmatoarele\s*:?)',
    r'pentru indreptarea aspectelor/observatiilor de mai sus se acorda un nou termen de solutionare\.?',
    r'deoarece (?:se constata ca )?(?:la data solutionarii dosarului )?(?:in termenul prevazut la art\.?\s*106[^,]{0,250},\s*)?solicitantul nu a [^.]{0,300}\.',
    r'drept urmare,? in temeiul art\.?\s*106 alin\.?\s*\(?5\)?[^.]{0,120}se va respinge cererea\.?',
    r'in cauza fiind incidente prevederile art\.?\s*106[^.]{0,120}\.',
    r'avand in vedere prerogativa instituita de dispozitiile art\.?\s*28[^:]{0,300}urmatoarelor aspecte\s*:?',
    r'la termenul de solutionare din data de \d{2}\.\d{2}\.\d{4},? acordat conform prevederilor art\.?\s*106 alin\.?\s*\(?1\)? din legea nr\.?\s*265/2022,?',
    r'se constata ca solicitantul nu a procedat la clarificarea obiectiunilor precizate in incheierea de amanare din data de \d{2}\.\d{2}\.\d{4}\s*'
    r'si nu a depus,? in termenul prevazut la art\.?\s*106[^,]{0,60},?[^,]{0,40},? documentele solicitate,?',
]
BOIL = [re.compile(p, re.I) for p in BOIL]
LEGAL_STOP = set('art alin lit pct din si al cu conform conf cf potrivit privind registrul comertului coroborat coroborate prevederile dispozitiilor dispozitiile '
                 'disp temeiul in de la a ale modificarile completarile ulterioare republicata modificata completata baza aplicarea # <x> <adresa> <data> legea lege '
                 'nr pentru si modificarea completarea altor acte normative incidenta asupra inregistrarii avand vedere'.split())


def strip_b(s):
    s = re.sub(r'\s+', ' ', fold(s))
    for p in (F_NEREM, F_NEPREC, F_NEIND):
        s = re.sub(p, ' ', s, flags=re.I)
    for rx in BOIL:
        s = rx.sub(' ', s)
    return s


def content(t):
    return sum(1 for w in t.split() if w not in LEGAL_STOP and not re.match(r'(legea|legii|lg|oug|og|hg|ordinul|ordinului|omj|omf|regulamentul)_', w) and len(w) > 2)


def main():
    d = pickle.load(open(os.path.join(TMP, 'rejections_raw.pkl'), 'rb'))
    r = pd.DataFrame(d['rejections'])
    n_docs = len(r)
    r = r[r.reason.notna()].copy()
    n_reason = len(r)
    for c in ('din_data', 'data_cerere'):
        r[c] = pd.to_datetime(r[c], format='%d.%m.%Y')
    r['app_nr'] = r.app_nr.astype(float)
    r = r.drop_duplicates(['app_nr', 'din_data']).reset_index(drop=True)
    n_dedup = len(r)
    out_win = int(((r.din_data < WIN[0]) | (r.din_data > WIN[1])).sum())
    r = r[(r.din_data >= WIN[0]) & (r.din_data <= WIN[1])].reset_index(drop=True)
    # section from the bulletin index (joined on încheiere nr; fallback request nr)
    ix = pd.DataFrame(d['index'])
    sec_by_inch = ix.drop_duplicates('inch_nr').set_index('inch_nr').section
    sec_by_app = ix.assign(app_nr=ix.app_nr.astype(float)).drop_duplicates('app_nr').set_index('app_nr').section
    r['section'] = r.inch_nr.map(sec_by_inch)
    r.loc[r.section.isna(), 'section'] = r.loc[r.section.isna(), 'app_nr'].map(sec_by_app)

    # archive linkage: the Respins decision itself (category, county, jtype) and earlier postponements of the same request
    df = pd.read_pickle(r'W:\SOLOResearch\analysis_decisions.pkl')[['cat', 'app_nr', 'app', 'res', 'county', 'jtype', 'sol']]
    df = df[df.app_nr.isin(r.app_nr.unique())]
    R = df[df.sol == 'Respins'].copy(); R['din_data'] = R.res.dt.normalize()
    R = R.sort_values('res').drop_duplicates(['app_nr', 'din_data'])
    r = r.merge(R[['app_nr', 'din_data', 'cat', 'county', 'jtype']], on=['app_nr', 'din_data'], how='left')
    A = df[df.cat == 'AUTO_AMANARI'][['app_nr', 'app', 'res']].rename(columns={'res': 'post_res', 'app': 'post_app'})
    del df
    r['eid'] = np.arange(len(r))
    mm = r[['eid', 'app_nr', 'din_data', 'data_cerere']].merge(A, on='app_nr')
    mm = mm[(mm.post_res.dt.normalize() < mm.din_data) & (mm.post_app.dt.normalize() == mm.data_cerere)]
    g = mm.groupby('eid')
    r['n_prior_post'] = r.eid.map(g.size()).fillna(0).astype(int)
    last = g.post_res.max().dt.normalize()
    r['days_last_post_to_rej'] = (r.din_data - r.eid.map(last)).dt.days
    r['file_to_rej_days'] = (r.din_data - r.data_cerere).dt.days
    r['county'] = r.county.astype(str); r['jtype'] = r.jtype.astype(str); r['cat'] = r.cat.astype(str)

    # ---- layer A
    F = r.reason.map(lambda s: re.sub(r'\s+', ' ', fold(s)))
    r['F_NEREMEDIAT'] = F.str.contains(F_NEREM, case=False, regex=True)
    r['F_NEPRECIZARI'] = F.str.contains(F_NEPREC, case=False, regex=True)
    r['F_NEINDEPLINIT'] = F.str.contains(F_NEIND, case=False, regex=True)
    r['S_POSTP'] = F.map(lambda s: bool(POSTP.search(s)))
    r['S_NEREM'] = F.map(lambda s: bool(NEREM.search(s)))
    r['S_PARTIAL'] = F.map(lambda s: bool(PARTIAL.search(s)))
    r['S_INTERES'] = F.map(lambda s: bool(INTERES.search(s)))
    r['S_RENUNT'] = F.map(lambda s: bool(RENUNT.search(s)))
    post_ref = r.F_NEREMEDIAT | r.F_NEPRECIZARI | r.S_POSTP
    r['mech'] = np.select([post_ref & r.S_PARTIAL, post_ref & (r.S_NEREM | r.F_NEREMEDIAT | r.F_NEPRECIZARI), post_ref],
                          ['M_PARTIAL', 'M_NEREMEDIAT', 'M_AMANARE_ALT'], 'M_DIRECT')

    # ---- layer B: strip formulas + boilerplate on folded case-preserving text, then the delay_reasons de-identification
    texts = [pre_mask(strip_b(t)) for t in r.reason]
    texts_full = [pre_mask(re.sub(r'\s+', ' ', t)) for t in r.reason]   # full reason incl. layer A, for the manual review only
    seg_rows, gflags = [], []
    for i, t in enumerate(texts):
        ms = list(GROUND_RX.finditer(t)); flags = {gg: False for gg in GROUNDS}; pieces = []
        if not ms:
            pieces.append(('G_altul', t))
        else:
            if ms[0].start() > 10:
                pieces.append(('G_altul', t[:ms[0].start()]))
            for j, mt in enumerate(ms):
                gname = next(k for k, v in GROUNDS.items() if re.fullmatch(v, mt.group(1), re.I))
                flags[gname] = True
                pieces.append((gname, t[mt.end(): ms[j + 1].start() if j + 1 < len(ms) else len(t)]))
        gflags.append(flags)
        k = 0
        for gname, body in pieces:
            for s in split_segments(body):
                seg_rows.append(dict(eid=i, ground=gname, k=k, text=s)); k += 1
    S = pd.DataFrame(seg_rows)
    r = pd.concat([r, pd.DataFrame(gflags)], axis=1)

    # postponement notices of the same request (pair comparison): de-identified with the same functions
    P = pd.DataFrame(d['postponements_of_rejected'])
    P['app_nr'] = P.app_nr.astype(float); P['din_data'] = pd.to_datetime(P.din_data, format='%d.%m.%Y')
    P = P.merge(r[['eid', 'app_nr', 'din_data', 'county']].rename(columns={'din_data': 'rej_date'}), on='app_nr')
    P = P[P.din_data < P.rej_date].sort_values('din_data').drop_duplicates('eid', keep='last').reset_index(drop=True)
    ptexts = [pre_mask(t) for t in P.reason]

    # vocabulary whitelist over rejection + paired postponement texts (document frequency over entries, bulletins, counties)
    all_t = texts + ptexts
    bl = list(r.bulletin) + list(P.bulletin); co = list(r.county) + list(P.county)
    tok_e, tok_b, tok_c = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
    for i, t in enumerate(all_t):
        for w in set(re.findall(r'<\w+>|[a-z_0-9#\-]+', t)):
            tok_e[w].add(i); tok_b[w].add(bl[i]); tok_c[w].add(co[i])
    keep = {w for w in tok_e if (len(tok_e[w]) >= 8 and len(tok_b[w]) >= 4 and len(tok_c[w]) >= 3) or w.startswith('<') or w == '#'}

    def wl(s):
        out = ' '.join(w if w in keep else '<x>' for w in re.findall(r'<\w+>|[a-z_0-9#\-]+', s))
        out = re.sub(r'(?:<x> ?){2,}', '<x> ', out)
        out = DR02.BOILER2.sub(' ', out)
        return re.sub(r'\s+', ' ', out).strip()
    S['text'] = S.text.map(wl)
    S['text'] = S.text.str.replace('(' + '|'.join(GROUNDS.values()) + r')( in sensul| sens in care( se va depune)?)?', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    r['text'] = [wl(t) for t in texts]
    r['text_full'] = [wl(t) for t in texts_full]
    P['text'] = [wl(t) for t in ptexts]
    # glue citation-only fragments to the previous segment (same rule as delay_reasons/02)
    merged = []
    for eid, grp in S.groupby('eid', sort=False):
        cur = []
        for _, row in grp.iterrows():
            if content(row.text) < 3 and cur:
                cur[-1]['text'] += ' ' + row.text
            elif content(row.text) >= 3:
                cur.append(dict(row))
        merged.extend(cur)
    S = pd.DataFrame(merged); S['k'] = S.groupby('eid').cumcount(); S = S.reset_index(drop=True)
    r['n_segments'] = S.groupby('eid').size().reindex(r.eid).fillna(0).astype(int).values
    r = r.drop(columns=['reason', 'dword', 'rejected', 'has_urm', 'has_disp_after', 'bdate'])
    P = P[['eid', 'din_data', 'rej_date', 'text']]
    r.to_pickle(os.path.join(TMP, 'entries.pkl')); S.to_pickle(os.path.join(TMP, 'segments.pkl')); P.to_pickle(os.path.join(TMP, 'post_pairs.pkl'))

    print('rejection docs', n_docs, 'with reason', n_reason, 'after dedup (request nr, day)', n_dedup, 'outside Oct-Nov 2026', out_win, 'in window', len(r))
    print('decision days', r.din_data.nunique(), r.din_data.min().date(), r.din_data.max().date(), 'bulletins', r.bulletin.nunique())
    print('section', r.section.value_counts(dropna=False).to_dict(), '| archive cat', r.cat.value_counts().to_dict())
    print('crosstab section x cat', pd.crosstab(r.section.fillna('NA'), r.cat).to_dict())
    print('linked to archive Respins', int((r.cat != 'nan').sum()), '| with prior AUTO_AMANARI (same request, same filing day)', int((r.n_prior_post > 0).sum()))
    print('formulas', {c: int(r[c].sum()) for c in ['F_NEREMEDIAT', 'F_NEPRECIZARI', 'F_NEINDEPLINIT', 'S_POSTP', 'S_NEREM', 'S_PARTIAL', 'S_INTERES', 'S_RENUNT']})
    print('mechanism', r.mech.value_counts().to_dict())
    print('mech x prior postponement', pd.crosstab(r.mech, r.n_prior_post > 0).to_dict())
    print('grounds quoted', {gg: int(r[gg].sum()) for gg in GROUNDS})
    print('segments', len(S), 'per entry', r.n_segments.value_counts().sort_index().to_dict())
    print('vocab kept', len(keep), 'of', len(tok_e), '; share of tokens masked', round(float(np.mean([w == '<x>' for t in r.text for w in t.split()])), 4))
    print('paired bulletin postponement notices', len(P))


if __name__ == '__main__':
    main()
