"""Step 4: name clusters, map them to the taxonomy, run the separate keyword classifier and build the final (hybrid) labels.

Three segment classifiers are kept side by side:
  C  cluster-only : HDBSCAN cluster (step 3) -> taxonomy category via CLUSTER_MAP (named after reading c-TF-IDF terms and the most
                    central masked phrases of every cluster); noise segments (-1) get the majority category of their 15 nearest
                    labelled neighbours (cosine, full embedding space).
  R  rules-only   : keyword/regex classifier on the de-identified text; a separate mechanism, but written after reading the clusters (multi-label).
  H  final/hybrid : generic-cluster members stay generic; else the cluster category if a rule confirms it; else the highest-priority
                    rule category; else the cluster category (single label per segment).
Entry level (one postponement decision): the set of non-generic categories over its segments (multi-label); an entry whose
segments are all generic legal formulae gets NESPEC.
Output: _tmp/entry_labels.pkl (eid -> label sets for C, R, H), stdout aggregates (kappa C vs R per category).
"""
import os, re, json, collections
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')

CATS = {  # code: (Romanian label, avoidable at filing by an automatic check)
    'CAEN':       ('Obiect de activitate / coduri CAEN și declarația de autorizare a activităților', 'parțial'),
    'SEDIU':      ('Sediu: dovada folosinței, valabilitate, acordul vecinilor/asociației, adresă', 'parțial'),
    'ACT':        ('Act constitutiv, hotărâri/decizii, act modificator, mandat administrator', 'parțial'),
    'ASOC_ID':    ('Date de identificare asociați/administratori (neconcordanțe cu registrul)', 'da'),
    'SOLICITANT': ('Solicitant/deponent: identitate, împuternicire, calitatea semnatarului', 'da'),
    'SEMN':       ('Semnătură (electronică/olografă) și forma înscrisurilor', 'da'),
    'CERERE':     ('Cererea de înregistrare, anexa fiscală, formulare completate greșit', 'da'),
    'BEN_REAL':   ('Declarația privind beneficiarii reali', 'da'),
    'CAPITAL':    ('Capital social: vărsăminte, părți sociale, aport', 'parțial'),
    'INSTIT':     ('Avize/atestări ale altor instituții (cazier fiscal, ANAF, autorizații profesionale)', 'parțial'),
    'DENUM':      ('Denumire: rezervare, formă legală a denumirii', 'da'),
    'TARIF':      ('Tarife: contor de caractere / tarif de publicare', 'da'),
}
GENERIC = 'GENERIC'

# cluster id -> (Romanian cluster label, category). Cluster ids are reproducible with the seeds and package versions in README.
CLUSTER_MAP = {
    0: ('Reluarea motivului-standard „nu sunt îndeplinite condițiile legale”', GENERIC),
    1: ('Cerere de completare înscrisuri / preschimbare termen', GENERIC),
    2: ('Cesiune părți sociale: notificare/atestare de la organul fiscal', 'INSTIT'),
    3: ('Precizări privind obiectul cererii / cereri paralele', 'CERERE'),
    4: ('Citare temei legal (Legea 265/2022, 31/1990)', GENERIC),
    5: ('Fapte înscrise în cazierul fiscal al asociatului/administratorului', 'INSTIT'),
    6: ('Cazier fiscal (variantă cu temei legal)', 'INSTIT'),
    7: ('Contor de caractere pentru tariful de publicare în Monitorul Oficial', 'TARIF'),
    8: ('Declarația privind beneficiarii reali nedepusă / greșită', 'BEN_REAL'),
    9: ('Formular de pe site-ul ONRC', 'CERERE'),
    10: ('Avizul asociației de proprietari / acordul vecinilor', 'SEDIU'),
    11: ('Beneficiar real menționat în actul constitutiv – declarație distinctă', 'BEN_REAL'),
    12: ('Copie certificată a cardului de avocat', 'SOLICITANT'),
    13: ('Formulă: control de legalitate prealabil, se acordă termen', GENERIC),
    14: ('Rezervarea denumirii PFA/II (nume și prenume)', 'DENUM'),
    15: ('Formulă: temei legal coroborat', GENERIC),
    16: ('Formulă: lipsa unui element obligatoriu atrage respingerea', GENERIC),
    17: ('Dovada vărsării/majorării capitalului social', 'CAPITAL'),
    18: ('Text suplimentar CAEN (ex. „fără dispecerat taxi”)', 'CAEN'),
    19: ('Capital subscris nevărsat la înmatriculare', 'CAPITAL'),
    20: ('Societate în dizolvare / lichidare', 'ACT'),
    21: ('Declarația-tip pentru sediul secundar / activități la terți', 'CAEN'),
    22: ('Declarația pe proprie răspundere privind condițiile de funcționare', 'CAEN'),
    23: ('Modificare date de identificare asociat/administrator prin act modificator', 'ASOC_ID'),
    24: ('Sediu: valabilitate expirată / neconcordanță / dovadă (mixt)', 'SEDIU'),
    25: ('Act constitutiv actualizat / decizie a asociatului (conținut, dată)', 'ACT'),
    26: ('Actualizare obiect de activitate conform CAEN Rev.3', 'CAEN'),
    27: ('Note explicative CAEN / clasificarea activităților', 'CAEN'),
    28: ('Durata mandatului administratorului – act constitutiv', 'ACT'),
    29: ('Durata mandatului administratorului – Cod civil', 'ACT'),
    30: ('Formulă: în temeiul art. ... amână cauza', GENERIC),
    31: ('Sediu profesional în locuință – declarație că nu se desfășoară activitate', 'SEDIU'),
    32: ('Neconcordanță adresă sediu între documente', 'SEDIU'),
    33: ('Copia actului de identitate al solicitantului', 'SOLICITANT'),
    34: ('Documentul care atestă dreptul de folosință asupra spațiului', 'SEDIU'),
    35: ('Dovadă valabilă de folosință pentru sediul secundar', 'SEDIU'),
    36: ('Prelungirea valabilității sediului expirat', 'SEDIU'),
    37: ('Contract de închiriere / act adițional – valabilitate', 'SEDIU'),
    38: ('Recodificare CAEN Rev.3 – cererea / obiectul principal', 'CAEN'),
    39: ('Declarația-tip cu conținut revizuit', 'CAEN'),
    40: ('Actul de identitate al asociatului/administratorului', 'ASOC_ID'),
    41: ('Cine poate fi împuternicit (consilier juridic, avocat, procură)', 'SOLICITANT'),
    42: ('Formulă: se constată neconcordanța (temei legal)', GENERIC),
    43: ('Semnătură olografă reprodusă / clarificarea semnăturilor', 'SEMN'),
    44: ('Cine semnează cererea (reprezentant legal / procură)', 'SOLICITANT'),
    45: ('Anexa fiscală / cererea completate incomplet sau eronat', 'CERERE'),
    46: ('Lipsa împuternicirii / calității deponentului', 'SOLICITANT'),
    47: ('Lipsa semnăturii electronice calificate', 'SEMN'),
    48: ('Modificare obiect/sedii – obligația declarației de autorizare', 'CAEN'),
    49: ('Act modificator de precizare a obiectului de activitate', 'CAEN'),
    50: ('Refacerea cererii / declarației (mixt)', 'CERERE'),
    51: ('Clarificarea obiectului de activitate', 'CAEN'),
    52: ('Cerere de înregistrare semnată/completată corespunzător (mixt)', 'CERERE'),
    53: ('Nu sunt autorizate toate activitățile din obiect', 'CAEN'),
    54: ('Declarația de autorizare cu toate activitățile', 'CAEN'),
    55: ('Declarația pe proprie răspundere – condiții de funcționare', 'CAEN'),
    56: ('Declarația-tip privind autorizarea funcționării nedepusă', 'CAEN'),
    57: ('Act constitutiv/decizie incomplete privind obiectul de activitate', 'CAEN'),
    58: ('Act constitutiv: date, conținut, refacere', 'ACT'),
    59: ('Împuternicire pentru deponent/expeditor', 'SOLICITANT'),
    60: ('Cerere semnată de persoană fără calitate', 'SOLICITANT'),
    61: ('Activitatea prevăzută de un cod CAEN anume', 'CAEN'),
    62: ('Act constitutiv actualizat lizibil / semnat / integral', 'ACT'),
    63: ('Act modificator neatașat', 'ACT'),
    64: ('Noile date de identificare ale asociatului – decizie + act constitutiv', 'ASOC_ID'),
    65: ('PFA/II: limita de clase CAEN (OUG 44/2008)', 'CAEN'),
    66: ('Coduri CAEN condiționate / interzise după recodificare', 'CAEN'),
    67: ('Activități medicale – autorizație de liberă practică / condiții speciale', 'INSTIT'),
}

# keyword rules (separate mechanism; written after the cluster inspection had been read) (on de-identified, diacritic-free, lower-case text); order = priority for the hybrid label
RULES = [
    ('BEN_REAL', r'beneficiar\w* real|legea_129_2019'),
    ('TARIF', r'tarif|contor\w* de caractere|nota de calcul|taxa de|achitar\w* (a )?(taxei|tarif)'),
    ('DENUM', r'denumir\w*|rezervar\w*|disponibilitat\w* (si rezervar\w* )?(a )?(denumirii|firmei)|firma unui profesionist'),
    ('INSTIT', r'cazier\w*|atestare fiscala|organului fiscal|og_39_2015|legea_239_2025|libera practica|certificat\w* de membru|colegiul|ceccar|'
               r'expertilor contabili|directi\w* de sanatate|sanitar\w* veterinar|incendi|aviz\w* (prealabil|de principiu|conform)'),
    ('CAPITAL', r'capital\w* social|capitalul|varsam|varsar|aport\w*|parti(le|lor)? sociale|nota contabila'),
    ('SOLICITANT', r'imputernic\w*|procur\w*|deponent\w*|expeditor\w*|avocat\w*|consilier\w* juridic|fara (nicio )?calitate|'
                   r'calitate\w* (de |a )?(reprezentant|imputernicit|deponent|semnatar|solicitant)|persoan\w* care (poate|nu are)|mandat\w* de reprezentare|'
                   r'(identitate|identitatii) (a |al )?(solicitant|deponent|titular)\w*|solicitant\w* cererii'),
    ('ASOC_ID', r'date(le|lor)? de identificare|act\w* de identitate|carti\w* de identitate|\bci\b|cnp|domicili\w*|pasaport|'
                r'evidenta persoanelor'),
    ('SEMN', r'semnatur\w*|olograf\w*|electronic\w* calificat|nesemnat|nu (este|sunt) semnat\w*|fara a fi semnat\w*|lizibil\w*|in original|'
             r'conformitate cu originalul|copie certificata'),
    ('SEDIU', r'sediu\w*|punct\w* de lucru|folosint\w*|comodat|inchiriere|subinchiriere|proprietari|vecin\w*|spatiu\w*|imobil\w*'),
    ('CAEN', r'caen|obiect\w* (principal |secundar )?de activitate|obiectului de activitate|activitat\w* (din|prevazut|autorizat|economic)|'
             r'recodific\w*|notele explicative|dispecerat|clase de activitati|declarati\w*[ -]tip|declaratia unica|declarati\w* (de|privind) autorizar\w*|'
             r'conditiilor de functionare|autorizar\w* (functionarii|activitatilor|tuturor)|toate activitatile'),
    ('ACT', r'act\w* constitutiv|act\w* modificator|hotarar\w*|\baga\b|\bagea\b|decizi\w* (asociat|consiliului)|statut\w*|mandatul(ui)? administrator|'
            r'durata mandatului|dizolv\w*|lichid\w*|asociat\w* unic'),
    ('CERERE', r'cerer\w* de inregistrare|anexa (privind )?inregistrar\w* fiscal|inregistrar\w* fiscala|formular\w*|\bpct\b|punctul #|caseta|'
               r'investitia straina|tipul cererii|obiectul cererii|cerere\w* tip'),
]
WB = chr(92) + 'b'   # regex word boundary
RULES = [(c, re.compile(WB + '(?:' + p + ')')) for c, p in RULES]
PRIO = [c for c, _ in RULES]


def rules(t):
    return [c for c, rx in RULES if rx.search(t)]


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = (a == b).mean(); pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float((po - pe) / (1 - pe)) if pe < 1 else float('nan')


def main():
    S = pd.read_pickle(os.path.join(TMP, 'seg_clusters.pkl')); X = np.load(os.path.join(TMP, 'embeddings.npy'))
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    missing = sorted(set(S.cluster.unique()) - set(CLUSTER_MAP) - {-1})
    assert not missing, f'clusters without a name: {missing} (re-run inspection; cluster ids changed?)'
    S['cat_C'] = S.cluster.map(lambda c: CLUSTER_MAP[c][1] if c in CLUSTER_MAP else None)
    lab = S.cat_C.notna().values
    noise = np.where(~lab)[0]
    if len(noise):
        sim = X[noise] @ X[lab].T
        nn = np.argsort(-sim, axis=1)[:, :15]
        labs = S.cat_C.values[lab]
        S.loc[S.index[noise], 'cat_C'] = [collections.Counter(labs[r]).most_common(1)[0][0] for r in nn]
    S['cats_R'] = S.text.map(rules)
    # hybrid (fixed before the manual review): members of clusters named generic stay generic; else the cluster category when a rule
    # confirms it; else the highest-priority rule category; else the cluster category
    gen_member = (S.cluster != -1) & (S.cat_C == GENERIC)
    S['cat_H'] = [GENERIC if g else (c if c in r else (r[0] if r else c)) for g, r, c in zip(gen_member, S.cats_R, S.cat_C)]

    def entry_sets(col, multi=False):
        d = collections.defaultdict(set)
        for e, v in zip(S.eid, S[col]):
            for c in (v if multi else [v]):
                if c != GENERIC:
                    d[e].add(c)
        return [frozenset(d.get(e, set())) or frozenset({'NESPEC'}) for e in E.eid]
    E['L_C'] = entry_sets('cat_C'); E['L_R'] = entry_sets('cats_R', multi=True); E['L_H'] = entry_sets('cat_H')
    E[['eid', 'L_C', 'L_R', 'L_H']].to_pickle(os.path.join(TMP, 'entry_labels.pkl'))
    S[['eid', 'k', 'cluster', 'cat_C', 'cats_R', 'cat_H']].to_pickle(os.path.join(TMP, 'seg_labels.pkl'))

    out = {'segments': len(S), 'noise_segments_knn_assigned': int(len(noise)),
           'segments_generic_C': int((S.cat_C == GENERIC).sum()), 'segments_no_rule': int((S.cats_R.str.len() == 0).sum()),
           'segments_H_from_rule': int((S.cats_R.str.len() > 0).sum())}
    agree = {}
    for c in list(CATS) + ['NESPEC']:
        a = E.L_C.map(lambda s: c in s); b = E.L_R.map(lambda s: c in s); h = E.L_H.map(lambda s: c in s)
        agree[c] = dict(share_C=round(float(a.mean()), 3), share_R=round(float(b.mean()), 3), share_H=round(float(h.mean()), 3),
                        agree_CR=round(float((a == b).mean()), 3), kappa_CR=round(kappa(a, b), 3))
    out['entry_level'] = agree
    out['exact_set_agreement_C_vs_R'] = round(float((E.L_C == E.L_R).mean()), 3)
    # segment-level agreement: cluster category among rule categories (segments where a rule fires and the cluster is not generic)
    m = (S.cats_R.str.len() > 0) & (S.cat_C != GENERIC)
    out['segment_C_in_R'] = round(float(np.mean([c in r for c, r in zip(S.cat_C[m], S.cats_R[m])])), 3)
    out['segment_C_eq_firstR'] = round(float(np.mean([c == r[0] for c, r in zip(S.cat_C[m], S.cats_R[m])])), 3)
    json.dump(out, open(os.path.join(HERE, '04_classify.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
