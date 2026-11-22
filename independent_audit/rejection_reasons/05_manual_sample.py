"""Step 5a: draw the seeded random sample of 100 rejection entries for manual review and write their DE-IDENTIFIED full reason text
(layer A + layer B, whitelisted vocabulary) to _tmp/manual_sample.txt (positions 1..100 only; no request numbers, no bulletin ids).
The reviewer labels from this text alone, BEFORE clustering/classification was run (this script was run right after step 2);
labels are stored in 05_manual_labels.py keyed only by sample position."""
import sys; sys.dont_write_bytecode = True  # never leave __pycache__ in delay_reasons (read-only reuse)
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
SEED = 20261122


SEED2 = 20261123   # second, out-of-sample batch of 50 (drawn after the classifier was fixed; labelled before joining predictions)


def sample_eids():
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    return list(np.random.default_rng(SEED).choice(E.eid.values, 100, replace=False))


def sample_eids2():
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    rest = np.setdiff1d(E.eid.values, sample_eids())
    return list(np.random.default_rng(SEED2).choice(rest, 50, replace=False))


if __name__ == '__main__':
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl')).set_index('eid')
    with open(os.path.join(TMP, 'manual_sample.txt'), 'w', encoding='utf-8') as fh:
        for pos, e in enumerate(sample_eids(), 1):
            fh.write(f'[{pos}] {E.text_full[e][:2500]}\n\n')
    with open(os.path.join(TMP, 'manual_sample2.txt'), 'w', encoding='utf-8') as fh:
        for pos, e in enumerate(sample_eids2(), 1):
            fh.write(f'[{pos}] {E.text_full[e][:4500]}\n\n')
    print('written', os.path.join(TMP, 'manual_sample.txt'), os.path.join(TMP, 'manual_sample2.txt'))
