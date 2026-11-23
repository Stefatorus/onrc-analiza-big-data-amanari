"""Step 2: de-duplicate, de-identify and split postponement reasons.

Input : _tmp/postponements_raw.pkl (step 1) + W:/SOLOResearch/analysis_decisions.pkl (only AUTO_AMANARI, needed columns).
Output: _tmp/entries.pkl   one row per postponement decision (bulletin, decision day, county, ground flags, de-identified text,
                           term granted, filing-to-postponement days; request nr kept ONLY for the wait join in step 5)
        _tmp/segments.pkl  one row per reason segment (entry id, ground, de-identified segment text)
All of _tmp/ is deleted at the end of the work. stdout: aggregates only.

De-identification (applied to every text that leaves this step):
  1. fold diacritics, lower-case;
  2. mask e-mail, CNP/CUI/long numbers, J/F registry numbers, dates, amounts;
  3. mask address spans (str./strada/sat/comuna/nr./bl./ap./et./sector ... + following tokens);
  4. mask person-name cues ("domnul/doamna/numitul/asociatul X Y", initials like "c.g.m");
  5. vocabulary whitelist: a token survives only if it occurs in >= 8 distinct entries from >= 4 distinct bulletins and
     >= 3 counties; every other token becomes "<x>". Names, street names, firm names are rare -> masked.
"""
import os, re, pickle, collections, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
WIN = ('2026-10-19', '2026-11-20')   # decision window covered by the bulletin archive (notices exist 19 Oct-18 Nov)

GROUNDS = {  # the four standard grounds printed by the registrar software before the free text
    'G_conditii_legale': r'nu sunt indeplinite conditiile legale pentru inregistrarea in registrul comertului',
    'G_incompleta': r'documentatia este incompleta',
    'G_neconcordante': r'exista neconcordante intre documente',
    'G_forma': r'actele depuse nu indeplinesc conditiile legale de forma',
}
GROUND_RX = re.compile(r'-?\s*(' + '|'.join(GROUNDS.values()) + r')\s*,?\s*(?:in sensul|sens in care(?: se va depune)?|respectiv,? sens in care|respectiv)?\s*:?', re.I)
BOILER = re.compile(r'in temeiul dispozitiilor art\.? ?106[^.]*se acorda termen[^.]*\.?|documentele solicitate in completarea cererii se vor depune[^.]*\.?'
                    r'|se acorda termen,? in vederea inlaturarii neconformitatilor constatate\.?', re.I)
LAW = re.compile(r'\b(legea|legii|lg|oug|og|hg|ordinul|ordinului|omj|omf|regulamentul)\.?\s*(?:nr\.?\s*)?(\d{1,4})\s*/\s*(?:c\s*/\s*)?(\d{4})', re.I)
# address keyword followed by "proper" tokens (Capitalised, upper-case or digits) in the case-preserving text
BOILER2 = re.compile(r'(?:in vederea remedierii observatiilor cuprinse in incheierea de amanare )?documentele (?:solicitate )?(?:<x> )?(?:in completarea cererii )?(?:<x> )?se vor depune(?: <x>)?(?: transmite)?(?: in completarea cererii)?(?: <x>)? cu cel(?: putin)?(?: # zi lucratoare inainte de termenul de solutionare)?(?: stabilit prin incheierea de amanare)?(?: conform art # si art # din legea_265_2022)?'
                     r'|in vederea remedierii observatiilor cuprinse in incheierea de amanare|se acorda termen(?: <x>)? in vederea inlaturarii neconformitatilor constatate'
                     r'|din data <data>(?: <x>)? solutie(?: <x>)? amanat(?: <x>)? motivul amanarii|in temeiul dispozitiilor art # din legea_265_2022(?: <x>)? se acorda termen')
ADDR = re.compile(r'\b(?i:str|strada|bd|b-dul|bulevardul|sos|soseaua|calea|aleea|sat(?:ul)?|comuna|oras(?:ul)?|municipiul|mun|sector(?:ul)?|nr|bl|bloc|sc|scara|et|etaj|ap|apartament|cam|camera|judet(?:ul)?|jud|parter|spatiul|cod postal)\b\.?\s*(?:(?:[A-Z0-9][\w\-]*|[a-z]?\d+[a-z]?)[.,]?\s*){1,5}')
PERSON = re.compile(r'\b(?i:domn(?:ul|ului)?|doamn(?:a|ei)|dl|dna|d-l|d-na|numit(?:ul|a|ului|ei)|sotul|sotia|asociat(?:ul|a|ului|ei)|administrator(?:ul|ului)|imputernicit(?:ul|ului))\b\.?\s+((?:[A-Z][\w\-]*\s*){1,4})')
INITIALS = re.compile(r'\b(?:[A-Za-z]\.\s?){2,}[A-Za-z]?\b')


def fold(s):
    s = unicodedata.normalize('NFKD', s.replace('ş', 's').replace('ţ', 't').replace('Ş', 'S').replace('Ţ', 'T'))
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


def pre_mask(s):
    s = fold(s)
    s = re.sub(r'\S+@\S+', ' <email> ', s)
    s = re.sub(r'\b[JFC]\s?\d{1,2}\s?/\s?\d+\s?/\s?\d{4}\b', ' <nrc> ', s)
    s = re.sub(r'\bRO\s?\d{4,10}\b', ' <cui> ', s)
    s = re.sub(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', ' <data> ', s)
    s = LAW.sub(lambda m: f' {m.group(1).lower()}_{m.group(2)}_{m.group(3)} ', s)        # law identity is kept (not personal)
    s = PERSON.sub(lambda m: m.group(0)[:m.start(1) - m.start(0)] + ' <persoana> ', s)
    s = INITIALS.sub(lambda m: ' <initiale> ' if not re.fullmatch(r'(?:art|alin|lit|nr|pct|cf|ex)\.?', m.group(0).strip(), re.I) else m.group(0), s)
    s = ADDR.sub(' <adresa> ', s)
    s = s.lower()
    s = re.sub(r'\b\d[\d.,]*\s*(?:lei|ron|euro|eur)\b', ' <suma> ', s)
    s = re.sub(r'\b\d{6,}\b', ' <nr> ', s)
    s = re.sub(r'(?<![_\w])\d+[a-z]?\b', ' # ', s)
    return re.sub(r'\s+', ' ', s).strip()


def split_segments(body):
    """split one ground's free text into reason segments; dashes only when preceded by space/punctuation (keeps 'declaratia-tip')."""
    body = BOILER.sub(' ', body)
    parts = re.split(r'\s*(?:;|\*|•|(?<=[\s.:,])[-–]\s|(?<=[\s.;:])#\)\s|(?<=[.;:]\s)#\.\s|(?<=[.:])\s+(?=(?:se va|se vor|nu s-a|nu s-au|lipsa|lipseste|lipsesc|va depune|vor depune|depunere|depuneti)\b))', body)
    segs, buf = [], ''
    for p in parts:
        p = p.strip(' .,:-')
        if not p:
            continue
        w = re.findall(r'[a-z]{2,}', p)
        if len(w) < 4:            # too short to stand alone: glue to the previous segment
            buf = (buf + ' ' + p).strip()
            continue
        if buf and segs:
            segs[-1] = segs[-1] + ' ' + buf; buf = ''
        segs.append((buf + ' ' + p).strip() if buf else p); buf = ''
    if buf:
        if segs:
            segs[-1] += ' ' + buf
        elif len(re.findall(r'[a-z]{2,}', buf)) >= 2:
            segs.append(buf)
    return segs


def main():
    d = pickle.load(open(os.path.join(TMP, 'postponements_raw.pkl'), 'rb'))
    r = pd.DataFrame([x for x in d['rows'] if x['reason']])
    n_raw = len(r)
    r['app_nr'] = r.app_nr.astype(float)
    for c in ('din_data', 'termen', 'data_cerere'):
        r[c] = pd.to_datetime(r[c], format='%d.%m.%Y')
    r = r.drop_duplicates(['app_nr', 'din_data']).reset_index(drop=True)
    n_dedup = len(r)
    out_window = int((r.din_data < WIN[0]).sum())
    r = r[(r.din_data >= WIN[0]) & (r.din_data <= WIN[1])].reset_index(drop=True)
    # county from the archive (request nr + decision day); the PDF section header is the filing office too
    df = pd.read_pickle(r'W:\SOLOResearch\analysis_decisions.pkl')[['cat', 'app_nr', 'res', 'county', 'jtype']]
    a = df[(df.cat == 'AUTO_AMANARI') & (df.res >= '2026-10-01')].copy(); del df
    a['din_data'] = a.res.dt.normalize(); a = a.drop_duplicates(['app_nr', 'din_data'])
    r = r.merge(a[['app_nr', 'din_data', 'county', 'jtype']], on=['app_nr', 'din_data'], how='left')
    r['county'] = r.county.astype(str); r['jtype'] = r.jtype.astype(str)
    r['term_days'] = (r.termen - r.din_data).dt.days
    r['file_to_post_days'] = (r.din_data - r.data_cerere).dt.days

    texts = [pre_mask(t) for t in r.reason]
    # ground split
    seg_rows, ground_flags = [], []
    for i, t in enumerate(texts):
        ms = list(GROUND_RX.finditer(t))
        flags = {g: False for g in GROUNDS}
        pieces = []
        if not ms:
            pieces.append(('G_altul', t))
        else:
            if ms[0].start() > 10:
                pieces.append(('G_altul', t[:ms[0].start()]))
            for j, m in enumerate(ms):
                g = next(k for k, v in GROUNDS.items() if re.fullmatch(v, m.group(1), re.I))
                flags[g] = True
                pieces.append((g, t[m.end(): ms[j + 1].start() if j + 1 < len(ms) else len(t)]))
        ground_flags.append(flags)
        k = 0
        for g, body in pieces:
            for s in split_segments(body):
                seg_rows.append(dict(eid=i, ground=g, k=k, text=s)); k += 1
    S = pd.DataFrame(seg_rows)
    G = pd.DataFrame(ground_flags)
    r = pd.concat([r, G], axis=1)
    r['eid'] = np.arange(len(r))
    r['text_premask'] = texts

    # vocabulary whitelist (document frequency over entries, bulletins, counties)
    tok_e, tok_b, tok_c = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
    for i, t in enumerate(texts):
        for w in set(re.findall(r'<\w+>|[a-z_0-9#\-]+', t)):
            tok_e[w].add(i); tok_b[w].add(r.bulletin[i]); tok_c[w].add(r.county[i])
    keep = {w for w in tok_e if (len(tok_e[w]) >= 8 and len(tok_b[w]) >= 4 and len(tok_c[w]) >= 3) or w.startswith('<') or w == '#'}

    def wl(s):
        out = ' '.join(w if w in keep else '<x>' for w in re.findall(r'<\w+>|[a-z_0-9#\-]+', s))
        out = re.sub(r'(?:<x> ?){2,}', '<x> ', out)
        out = BOILER2.sub(' ', out)
        return re.sub(r'\s+', ' ', out).strip()
    S['text'] = S.text.map(wl)
    r['text'] = r.text_premask.map(wl)
    r = r.drop(columns=['text_premask', 'reason', 'region', 'jcode', 'sol'])
    # remove residual ground headlines, then glue citation-only fragments to the previous segment of the same entry
    S['text'] = S.text.str.replace('(' + '|'.join(GROUNDS.values()) + r')( in sensul| sens in care( se va depune)?)?', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    LEGAL_STOP = set('art alin lit pct din si al cu conform conf cf potrivit privind registrul comertului coroborat coroborate prevederile dispozitiilor dispozitiile '
                     'disp temeiul in de la a ale modificarile completarile ulterioare republicata modificata completata baza aplicarea # <x> <adresa> <data> legea lege '
                     'nr pentru si modificarea completarea altor acte normative incidenta asupra inregistrarii avand vedere'.split())
    def content(t):
        return sum(1 for w in t.split() if w not in LEGAL_STOP and not re.match(r'(legea|legii|lg|oug|og|hg|ordinul|ordinului|omj|omf|regulamentul)_', w) and len(w) > 2)
    merged = []
    for eid, grp in S.groupby('eid', sort=False):
        cur = []
        for _, row in grp.iterrows():
            if content(row.text) < 3 and cur:
                cur[-1]['text'] += ' ' + row.text
            elif content(row.text) >= 3:
                cur.append(dict(row))
        merged.extend(cur)
    S = pd.DataFrame(merged)
    S['k'] = S.groupby('eid').cumcount()
    S = S.reset_index(drop=True)
    r['n_segments'] = S.groupby('eid').size().reindex(r.eid).fillna(0).astype(int).values

    r.to_pickle(os.path.join(TMP, 'entries.pkl')); S.to_pickle(os.path.join(TMP, 'segments.pkl'))
    print('notices with reason text', n_raw, 'after dedup (request nr, day)', n_dedup, 'outside window (Feb 2026)', out_window, 'in window', len(r))
    print('county linked', int((r.county != 'nan').sum()), 'bulletins', r.bulletin.nunique(), 'decision days', r.din_data.nunique())
    print('ground counts', {g: int(r[g].sum()) for g in GROUNDS}, 'none of the 4', int((~r[list(GROUNDS)].any(axis=1)).sum()))
    print('n grounds per entry', r[list(GROUNDS)].sum(axis=1).value_counts().sort_index().to_dict())
    print('segments', len(S), 'per entry', r.n_segments.value_counts().sort_index().to_dict())
    print('vocab kept', len(keep), 'of', len(tok_e), '; share of tokens masked', round(float(np.mean([w == '<x>' for t in r.text for w in t.split()])), 4))
    print('term granted days quantiles', r.term_days.quantile([.1, .5, .9]).to_dict(), 'filing->postponement', r.file_to_post_days.quantile([.1, .5, .9]).to_dict())


if __name__ == '__main__':
    main()
