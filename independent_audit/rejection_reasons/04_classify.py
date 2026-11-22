"""Step 4: name the rejection clusters, map them to the taxonomy, run the keyword classifier and build the final (hybrid) labels.

Taxonomy = the 12 postponement categories of delay_reasons/04 (same codes, labels and avoidable flags, imported read-only) + 2
rejection-specific categories (FARA_OBIECT, IMPOSIBIL); an entry with no substantive category is NERESTATAT (the rejection only says
the postponement was not complied with). The procedural layer (mechanism M_*) is parsed separately in step 2.

Classifiers (segment level), as in delay_reasons/04:
  C  cluster-only : HDBSCAN cluster (step 3) -> category via CLUSTER_MAP (named after reading c-TF-IDF terms and central masked phrases);
                    noise (-1) and heterogeneous clusters (MIXT) get the majority category of their 15 nearest labelled neighbours.
  R  rules-only   : the delay_reasons keyword rules (imported unchanged) + 2 rejection-specific rules, applied to the segment text after
                    removing procedural phrases about the request being rejected (e.g. "cererea de înregistrare urmează a fi respinsă"),
                    which otherwise trigger the CERERE rule.
  H  final/hybrid : FARA_OBIECT / IMPOSIBIL rule hits win; else generic-cluster members stay generic; else the cluster category if a rule
                    confirms it; else the highest-priority rule category; else the cluster (kNN) category. Fixed before step 6.
Output: _tmp/entry_labels.pkl, _tmp/seg_labels.pkl, 04_classify.out.json (aggregates: kappa C vs R per category).
"""
import sys; sys.dont_write_bytecode = True  # never leave __pycache__ in delay_reasons (read-only reuse)
import os, re, json, collections, importlib.util
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
spec = importlib.util.spec_from_file_location('dr04', os.path.join(HERE, '..', 'delay_reasons', '04_classify.py'))
DR04 = importlib.util.module_from_spec(spec); spec.loader.exec_module(DR04)

CATS = dict(DR04.CATS)
CATS['FARA_OBIECT'] = ('Cerere rămasă fără obiect: mențiunea (ex. actualizarea CAEN Rev.3) era deja înregistrată', 'da')
CATS['IMPOSIBIL'] = ('Impediment legal: o singură formă PFA/II/IF, termene legale (dizolvare), opoziție/litigiu în curs', 'parțial')
GENERIC, MIXT = 'GENERIC', 'MIXT'

CLUSTER_MAP = {
    0: ('Formulă: s-a acordat termen pentru lămurirea solicitărilor', GENERIC),
    1: ('Formulă: prin încheiere s-a acordat un nou termen de soluționare', GENERIC),
    2: ('Formulă: registratorul a acordat termen pentru următoarele considerente', GENERIC),
    3: ('Formulă: devin incidente prevederile legii', GENERIC),
    4: ('Formulă: soluționarea a fost amânată pentru a da posibilitate petentului', GENERIC),
    5: ('Formulă: în temeiul legii se constată', GENERIC),
    6: ('Nu s-au depus înscrisurile rectificate (fără detaliu)', GENERIC),
    7: ('Respinsă ca lipsită de interes: observațiile nu au fost remediate', GENERIC),
    8: ('Formulă: cererea a fost amânată în ședința din ... pentru următoarele motive', GENERIC),
    9: ('Solicitantul nu a clarificat obiecțiunile din încheierea de amânare', GENERIC),
    10: ('Înregistrarea se solicită prin cerere completată corespunzător + act modificator (mixt)', MIXT),
    11: ('Formulă: în temeiul legii cererea se va respinge', GENERIC),
    12: ('Solicitantul nu a dat curs observațiilor', GENERIC),
    13: ('Nu au fost remediate aspectele din încheierea de amânare', GENERIC),
    14: ('Împuternicire / calitatea deponentului și a semnatarului cererii', 'SOLICITANT'),
    15: ('Acordul asociației de proprietari / al vecinilor (Legea 196/2018)', 'SEDIU'),
    16: ('Nu s-au depus completări în termenul acordat', GENERIC),
    17: ('Formulă: la data de ... s-a acordat termen pentru', GENERIC),
    18: ('Solicitantul a rămas în pasivitate (nicio precizare până la termen)', GENERIC),
    19: ('Copia actului de identitate al solicitantului', 'SOLICITANT'),
    20: ('Formulă: art. 77 / termenul preschimbat', GENERIC),
    21: ('Fapte înscrise în cazierul fiscal', 'INSTIT'),
    22: ('Nu au fost depuse documentele solicitate prin încheierea de amânare', GENERIC),
    23: ('Activități medicale / reglementate de legi speciale (aviz, liberă practică)', 'INSTIT'),
    24: ('Motivele amânării reluate (mixt)', MIXT),
    25: ('Citare Legea 265/2022 (temei)', GENERIC),
    26: ('Depunere anexă / rezervare denumire / documente (mixt)', MIXT),
    27: ('Nu s-au clarificat mențiunile din încheierea de amânare (mixt, procedural)', GENERIC),
    28: ('Declarația pe propria răspundere privind condițiile de funcționare', 'CAEN'),
    29: ('Dovada dreptului de folosință asupra spațiului cu destinație de sediu', 'SEDIU'),
    30: ('Nu s-au depus înscrisuri: cererea urmează a fi respinsă', GENERIC),
    31: ('Formulă: la termenul acordat registratorul constată', GENERIC),
    32: ('Cererea nu a fost completată conform observațiilor (reiterate)', GENERIC),
    33: ('Formulă: în temeiul art. ... respinge cauza/cererea pe motiv', GENERIC),
    34: ('Citare temei legal (Legea 265/2022)', GENERIC),
    35: ('Act constitutiv actualizat eronat / neclar', 'ACT'),
    36: ('Cererea de înregistrare completată eronat / tip de cerere greșit', 'CERERE'),
    37: ('Formulă: se respinge cererea conform prevederilor', GENERIC),
    38: ('Lipsă document (cerere, copie CI, denumire) – mixt', MIXT),
    39: ('Act modificator / act constitutiv actualizat nedepus', 'ACT'),
    40: ('Dovada vărsării / majorării capitalului social', 'CAPITAL'),
    41: ('Înscrisuri depuse / anexa de pe site (mixt)', MIXT),
    42: ('Sediu secundar / punct de lucru cu dovada expirată', 'SEDIU'),
    43: ('Contract de închiriere / valabilitatea sediului social', 'SEDIU'),
    44: ('Obiectul cererii neclarificat față de CAEN Rev.3 deja înregistrat', 'CAEN'),
    45: ('Act constitutiv actualizat / hotărâre (conținut, semnare, publicare)', 'ACT'),
    46: ('Modificarea datelor de identificare ale asociatului/administratorului', 'ASOC_ID'),
    47: ('Formulă: prin încheierea din data de ... s-a acordat termen', GENERIC),
    48: ('Cesiune părți sociale: certificat de atestare fiscală / organul fiscal (Legea 239/2025)', 'INSTIT'),
    49: ('Act constitutiv: durata mandatului, capital, obiect (conținut)', 'ACT'),
    50: ('Observații reluate (mixt: sediu, stare firmă)', MIXT),
    51: ('Cerere / CAEN Rev.3 / mandat deponent (mixt)', MIXT),
    52: ('Coduri CAEN autorizate / rămase pe Rev.2', 'CAEN'),
    53: ('Nu s-a depus / nu s-a clarificat (mixt: obiect, declarație, mandat)', MIXT),
    54: ('Activități sub condiție rezultate din recodificare (incendii, pază etc.)', 'CAEN'),
    55: ('Actualizare obiect de activitate CAEN Rev.3: renunțare la autorizare, activitate principală', 'CAEN'),
    56: ('Actualizarea CAEN Rev.3 deja efectuată / activitatea principală în cerere', 'CAEN'),
    57: ('Date de identificare diferite de registru / semnătură electronică (mixt)', MIXT),
    58: ('Neconcordanțe CAEN între hotărâre, act constitutiv și declarația de autorizare', 'CAEN'),
    59: ('Declarația-tip de autorizare nedepusă / incompletă', 'CAEN'),
    60: ('Declarația-tip: toate activitățile, sedii secundare, terți', 'CAEN'),
}

EXTRA_RULES = [
    ('FARA_OBIECT', r'fara obiect|ramas\w* fara obiect|deja (?:inregistrat\w*|actualizat\w*|efectuat\w*)|are deja|a fost deja|'
                    r's-a inregistrat in registrul comertului urmare|au fost inregistrate (?:in baza de date|prin mentiunea)|a fost efectuata'),
    ('IMPOSIBIL', r'mai detine o forma|poate avea (?:un singur|cel mult un)|opozitie\w*|litigi\w*|contestati\w*|hotarar\w* judecatoreasc\w*|'
                  r'insolventa|faliment|termenul de # de zile de la data publicarii'),
]
WB = chr(92) + 'b'
EXTRA_RULES = [(c, re.compile(WB + '(?:' + p + ')')) for c, p in EXTRA_RULES]
RULES = EXTRA_RULES + list(DR04.RULES)
OVERRIDE = {'FARA_OBIECT', 'IMPOSIBIL'}
PROC = re.compile(r'(?:respinge(?:rea)?|respingerea) (?:prezentei |prezenta )?cerer\w*(?: de inregistrare)?|cerer\w* de inregistrare (?:<x> )?(?:urmeaza|se va|se|este|va fi|nu indeplineste|a fi)\w*(?: (?:sa )?(?:fie|a fi))? respins\w*|'
                  r'(?:in sustinerea|in completarea|solutionarea|inregistrarea|dispunerea inregistrarii) cererii(?: de inregistrare)?|cererea de inregistrare urmeaza|'
                  r'nu sunt indeplinite (?:cerintele|conditiile) legale pentru inregistrarea cererii|cererea de inregistrare se va respinge')


def rules(t):
    t = PROC.sub(' ', t)
    return [c for c, rx in RULES if rx.search(t)]


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = (a == b).mean(); pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float((po - pe) / (1 - pe)) if pe < 1 else float('nan')


def main():
    S = pd.read_pickle(os.path.join(TMP, 'seg_clusters.pkl')); X = np.load(os.path.join(TMP, 'embeddings.npy'))
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    missing = sorted(set(S.cluster.unique()) - set(CLUSTER_MAP) - {-1})
    assert not missing, f'clusters without a name: {missing} (cluster ids changed? re-read the inspection file)'
    S['cat_C'] = S.cluster.map(lambda c: CLUSTER_MAP[c][1] if c in CLUSTER_MAP else None)
    lab = S.cat_C.notna().values & (S.cat_C != MIXT).values
    todo = np.where(~lab)[0]
    if len(todo):
        sim = X[todo] @ X[lab].T
        nn = np.argsort(-sim, axis=1)[:, :15]
        labs = S.cat_C.values[lab]
        S.loc[S.index[todo], 'cat_C'] = [collections.Counter(labs[r]).most_common(1)[0][0] for r in nn]
    S['cats_R'] = S.text.map(rules)
    gen_member = (S.cluster != -1) & S.cluster.map(lambda c: CLUSTER_MAP.get(c, ('', ''))[1] == GENERIC)

    def hyb(g, r, c):
        ov = [x for x in r if x in OVERRIDE]
        if ov:
            return ov[0]
        if g:
            return GENERIC
        return c if c in r else (r[0] if r else c)
    S['cat_H'] = [hyb(g, r, c) for g, r, c in zip(gen_member, S.cats_R, S.cat_C)]

    def entry_sets(col, multi=False):
        d = collections.defaultdict(set)
        for e, v in zip(S.eid, S[col]):
            for c in (v if multi else [v]):
                if c != GENERIC:
                    d[e].add(c)
        return [frozenset(d.get(e, set())) or frozenset({'NERESTATAT'}) for e in E.eid]
    E['L_C'] = entry_sets('cat_C'); E['L_R'] = entry_sets('cats_R', multi=True); E['L_H'] = entry_sets('cat_H')
    E[['eid', 'L_C', 'L_R', 'L_H']].to_pickle(os.path.join(TMP, 'entry_labels.pkl'))
    S[['eid', 'k', 'cluster', 'cat_C', 'cats_R', 'cat_H']].to_pickle(os.path.join(TMP, 'seg_labels.pkl'))
    out = {'segments': len(S), 'clusters': int(S.cluster.max() + 1),
           'clusters_generic': sum(v[1] == GENERIC for v in CLUSTER_MAP.values()), 'clusters_mixed': sum(v[1] == MIXT for v in CLUSTER_MAP.values()),
           'segments_noise_or_mixed_knn': int(len(todo)), 'segments_generic_H': int((S.cat_H == GENERIC).sum()),
           'segments_no_rule': int((S.cats_R.str.len() == 0).sum())}
    agree = {}
    for c in list(CATS) + ['NERESTATAT']:
        a = E.L_C.map(lambda s: c in s); b = E.L_R.map(lambda s: c in s); h = E.L_H.map(lambda s: c in s)
        agree[c] = dict(share_C=round(float(a.mean()), 3), share_R=round(float(b.mean()), 3), share_H=round(float(h.mean()), 3),
                        agree_CR=round(float((a == b).mean()), 3), kappa_CR=round(kappa(a, b), 3))
    out['entry_level'] = agree
    out['exact_set_agreement_C_vs_R'] = round(float((E.L_C == E.L_R).mean()), 3)
    m = (S.cats_R.str.len() > 0) & (S.cat_C != GENERIC)
    out['segment_C_in_R'] = round(float(np.mean([c in r for c, r in zip(S.cat_C[m], S.cats_R[m])])), 3)
    json.dump(out, open(os.path.join(HERE, '04_classify.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
