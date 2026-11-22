"""Step 6: validation against the manual labels.
  batch1: 100 seeded entries (SEED 20261122), labelled before any classifier existed (in-sample for the rules FARA_OBIECT/IMPOSIBIL
          and the CERERE pre-cleaning, which were written after reading these texts);
  batch2: 50 further seeded entries (SEED2 20261123), labelled after the classifier was fixed but before joining its predictions
          (out-of-sample);
  pooled: the 150 together (top-level keys, used by step 7 for precision/recall adjustment and the manual-sample estimates).
Substantive categories for the three classifiers (H, C, R), procedural mechanism (regex, step 2), avoidable-at-filing flags.
Writes 06_validate.out.json (aggregates only)."""
import os, sys, json, importlib.util, math
sys.dont_write_bytecode = True
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')


def load(name):
    spec = importlib.util.spec_from_file_location('m' + name[:2], os.path.join(HERE, name)); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def avoid_flag(s, AV, mode):
    s = set(s) - {'NERESTATAT'}
    if not s:
        return False
    f = [AV[c] for c in s]
    return all(x == 'da' for x in f) if mode == 'strict' else any(x == 'da' for x in f)


def evaluate(eids, true, tmech, L, E, CATS):
    cats = sorted(set(CATS)); n = len(eids); out = {'n': n}
    for col in ('L_H', 'L_C', 'L_R'):
        pred = [set(L.loc[e, col]) - {'NERESTATAT'} for e in eids]
        exact = sum(p == t for p, t in zip(pred, true))
        jac = np.mean([len(p & t) / len(p | t) if (p | t) else 1.0 for p, t in zip(pred, true)])
        tp = sum(len(p & t) for p, t in zip(pred, true)); fp = sum(len(p - t) for p, t in zip(pred, true)); fn = sum(len(t - p) for p, t in zip(pred, true))
        per = {}
        for c in cats + ['NERESTATAT']:
            a = np.array([(not t) if c == 'NERESTATAT' else (c in t) for t in true]); b = np.array([(not p) if c == 'NERESTATAT' else (c in p) for p in pred])
            per[c] = dict(n_true=int(a.sum()), n_pred=int(b.sum()), precision=round(float((a & b).sum() / b.sum()), 3) if b.sum() else None,
                          recall=round(float((a & b).sum() / a.sum()), 3) if a.sum() else None)
        anyhit = sum(bool(p & t) or (not p and not t) for p, t in zip(pred, true))
        out[col] = dict(exact_set_accuracy=round(exact / n, 3), exact_ci95=wilson(exact, n), any_overlap=round(anyhit / n, 3), any_overlap_ci95=wilson(anyhit, n),
                        mean_jaccard=round(float(jac), 3), micro_precision=round(tp / (tp + fp), 3), micro_recall=round(tp / (tp + fn), 3),
                        label_level_accuracy=round(float(np.mean([(c in p) == (c in t) for p, t in zip(pred, true) for c in cats])), 4), per_category=per)
    pm = [E.loc[e, 'mech'] for e in eids]
    k = sum(a == b for a, b in zip(pm, tmech)); ka = sum((a != 'M_DIRECT') == (b != 'M_DIRECT') for a, b in zip(pm, tmech))
    conf = pd.crosstab(pd.Series(tmech, name='manual'), pd.Series(pm, name='pred'))
    linked = [bool(E.loc[e, 'n_prior_post'] > 0) for e in eids]
    unf_m = sum(t in ('M_NEREMEDIAT', 'M_PARTIAL') for t in tmech)
    out['mechanism'] = dict(accuracy=round(k / n, 3), ci95=wilson(k, n), after_postponement_binary_accuracy=round(ka / n, 3), ci95_binary=wilson(ka, n),
                            manual_counts=pd.Series(tmech).value_counts().to_dict(), predicted_counts=pd.Series(pm).value_counts().to_dict(),
                            manual_unfulfilled=round(unf_m / n, 3), manual_unfulfilled_ci95=wilson(unf_m, n),
                            confusion={r: {c: int(conf.loc[r, c]) for c in conf.columns} for r in conf.index},
                            manual_direct=int(sum(t == 'M_DIRECT' for t in tmech)),
                            manual_direct_but_archive_prior_postponement=int(sum(t == 'M_DIRECT' and l for t, l in zip(tmech, linked))))
    AV = {k2: v[1] for k2, v in CATS.items()}
    predH = [set(L.loc[e, 'L_H']) for e in eids]
    out['nerestatat_predicted'] = int(sum('NERESTATAT' in p for p in predH)); out['nerestatat_manual'] = int(sum(not t for t in true))
    for mode in ('strict', 'any'):
        a = np.array([avoid_flag(t, AV, mode) for t in true]); b = np.array([avoid_flag(p, AV, mode) for p in predH])
        out[f'avoidable_{mode}'] = dict(manual=round(float(a.mean()), 3), manual_ci95=wilson(int(a.sum()), n), predicted=round(float(b.mean()), 3),
                                        agreement=round(float((a == b).mean()), 3),
                                        table=dict(both=int((a & b).sum()), manual_only=int((a & ~b).sum()), pred_only=int((~a & b).sum()), neither=int((~a & ~b).sum())))
    out['category_share_pred_vs_manual'] = {c: [round(v['n_pred'] / n, 4), round(v['n_true'] / n, 4)] for c, v in out['L_H']['per_category'].items()}
    out['manual_share_ci95'] = {c: wilson(v['n_true'], n) for c, v in out['L_H']['per_category'].items()}
    return out


def main():
    ML = load('05_manual_labels.py'); MS = load('05_manual_sample.py')
    L = pd.read_pickle(os.path.join(TMP, 'entry_labels.pkl')).set_index('eid')
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl')).set_index('eid')
    CATS = load('04_classify.py').CATS
    e1, e2 = MS.sample_eids(), MS.sample_eids2()
    t1 = [set(ML.MANUAL[i + 1]) for i in range(len(e1))]; t2 = [set(ML.MANUAL2[i + 1]) for i in range(len(e2))]
    m1 = [ML.MECH[i + 1] for i in range(len(e1))]; m2 = [ML.MECH2[i + 1] for i in range(len(e2))]
    b1 = evaluate(e1, t1, m1, L, E, CATS); b2 = evaluate(e2, t2, m2, L, E, CATS); po = evaluate(e1 + e2, t1 + t2, m1 + m2, L, E, CATS)
    out = dict(seeds=[MS.SEED, MS.SEED2], n_sample=po['n'], batch1=b1, batch2=b2, **po)
    json.dump(out, open(os.path.join(HERE, '06_validate.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, allow_nan=False)
    for name, b in (('batch1', b1), ('batch2', b2), ('pooled', po)):
        print('=====', name, 'n', b['n'])
        for col in ('L_H', 'L_C', 'L_R'):
            print(col, {k2: v for k2, v in b[col].items() if k2 != 'per_category'})
        print('mechanism', {k2: v for k2, v in b['mechanism'].items() if k2 != 'confusion'})
        print({k2: v for k2, v in b.items() if k2.startswith(('nerestatat', 'avoidable'))})
    for c, v in po['L_H']['per_category'].items():
        print('  pooled H', c, v, '| batch2', b2['L_H']['per_category'][c])


if __name__ == '__main__':
    main()
