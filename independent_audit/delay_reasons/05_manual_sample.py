"""Step 5a: draw the seeded random sample of 100 postponement entries for manual review and write their DE-IDENTIFIED text to
_tmp/manual_sample.txt (positions 1..100 only; no request numbers, no bulletin ids). The reviewer labels from this text alone,
before seeing any prediction; labels are stored in 05_manual_labels.py keyed only by sample position."""
import os, re, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
SEED = 20261122


def sample_eids():
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl'))
    return list(np.random.default_rng(SEED).choice(E.eid.values, 100, replace=False))


if __name__ == '__main__':
    E = pd.read_pickle(os.path.join(TMP, 'entries.pkl')).set_index('eid')
    with open(os.path.join(TMP, 'manual_sample.txt'), 'w', encoding='utf-8') as fh:
        for pos, e in enumerate(sample_eids(), 1):
            t = re.sub(r'(nu sunt indeplinite conditiile legale pentru inregistrarea in registrul comertului|documentatia este incompleta|'
                       r'exista neconcordante intre documente|actele depuse nu indeplinesc conditiile legale de forma)', ' || ', E.text[e])
            fh.write(f'[{pos}] {t}\n')
    print('written', os.path.join(TMP, 'manual_sample.txt'))
