"""Step 6: validation of the three classifiers against the manual labels (100 seeded entries) + agreement cluster vs rules.
Writes 06_validate.out.json (aggregates only)."""
import os, json, importlib.util, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('.py', ''), os.path.join(HERE, name)); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def main():
    M = load('05_manual_labels.py').MANUAL
    eids = load('05_manual_sample.py').sample_eids()
    L = pd.read_pickle(os.path.join(TMP, 'entry_labels.pkl')).set_index('eid')
    cats = sorted(set().union(*M.values()) | {'NESPEC'})
    out = {'n_sample': len(eids), 'seed': 20261122}
    for col in ('L_H', 'L_C', 'L_R'):
        pred = [set(L.loc[e, col]) - {'NESPEC'} for e in eids]
        true = [set(M[i + 1]) for i in range(len(eids))]
        exact = sum(p == t for p, t in zip(pred, true))
        jac = np.mean([len(p & t) / len(p | t) if (p | t) else 1.0 for p, t in zip(pred, true)])
        tp = sum(len(p & t) for p, t in zip(pred, true)); fp = sum(len(p - t) for p, t in zip(pred, true)); fn = sum(len(t - p) for p, t in zip(pred, true))
        per = {}
        for c in cats:
            a = np.array([c in t for t in true]); b = np.array([c in p for p in pred])
            per[c] = dict(n_true=int(a.sum()), n_pred=int(b.sum()), precision=round(float((a & b).sum() / b.sum()), 3) if b.sum() else None,
                          recall=round(float((a & b).sum() / a.sum()), 3) if a.sum() else None)
        # entry-level "label correct" = every true category found and no false one, already = exact; also "primary hit": any overlap
        anyhit = sum(bool(p & t) for p, t in zip(pred, true))
        out[col] = dict(exact_set_accuracy=round(exact / len(eids), 3), exact_ci95=wilson(exact, len(eids)),
                        any_overlap=round(anyhit / len(eids), 3), any_overlap_ci95=wilson(anyhit, len(eids)),
                        mean_jaccard=round(float(jac), 3), micro_precision=round(tp / (tp + fp), 3), micro_recall=round(tp / (tp + fn), 3),
                        label_level_accuracy=round(float(np.mean([(c in p) == (c in t) for p, t in zip(pred, true) for c in cats])), 4),
                        per_category=per)
    # like-for-like checks on the same 100 entries: predicted "unclassified" (NESPEC), avoidable-at-filing flags, category shares
    AV = {k: v[1] for k, v in load('04_classify.py').CATS.items()}

    def flag(s, mode):
        s = set(s) - {'NESPEC'}
        if not s:
            return False
        f = [AV[c] for c in s]
        return all(x == 'da' for x in f) if mode == 'strict' else any(x == 'da' for x in f)
    predH = [set(L.loc[e, 'L_H']) for e in eids]; true = [set(M[i + 1]) for i in range(len(eids))]
    out['nespec_predicted_in_sample'] = int(sum('NESPEC' in p for p in predH))
    out['nespec_manual_in_sample'] = int(sum(not t for t in true))
    for mode in ('strict', 'any'):
        a = np.array([flag(t, mode) for t in true]); b = np.array([flag(p, mode) for p in predH])
        out[f'avoidable_{mode}_sample'] = dict(manual=round(float(a.mean()), 3), predicted=round(float(b.mean()), 3),
                                               agreement=round(float((a == b).mean()), 3),
                                               table=dict(both=int((a & b).sum()), manual_only=int((a & ~b).sum()), pred_only=int((~a & b).sum()),
                                                          neither=int((~a & ~b).sum())))
    out['category_share_sample_pred_vs_manual'] = {c: [v['n_pred'] / len(eids), v['n_true'] / len(eids)] for c, v in out['L_H']['per_category'].items()}
    json.dump(out, open(os.path.join(HERE, '06_validate.out.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print({k: v for k, v in out.items() if k.startswith(('nespec', 'avoidable', 'category_share'))})
    for col in ('L_H', 'L_C', 'L_R'):
        o = out[col]; print(col, {k: v for k, v in o.items() if k != 'per_category'})
    for c, v in out['L_H']['per_category'].items():
        print('  H', c, v, '| C', out['L_C']['per_category'][c], '| R', out['L_R']['per_category'][c])


if __name__ == '__main__':
    main()
