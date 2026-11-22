"""Refiling after rejection vs baseline 'another request within N days' after an admitted request
(exact firm id, pseudonymised). Windows 30/90/365 days. Aggregates only."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import pandas as pd, numpy as np
r = pd.read_pickle(str(config.WORK_DIR / 'raw_compact.pkl'))[['cat', 'app', 'sol', 'firm', 'app_id', 'art']]
r = r.drop_duplicates('art'); r['cat'] = r.cat.astype(str); r['sol'] = r.sol.astype(str)
r = r[(r.cat == 'CERERE265') & (r.firm != 0) & r.sol.isin(['Admis', 'Respins', 'Renunțat'])]
r = r.drop_duplicates('app_id').sort_values(['firm', 'app'])
r['next_app'] = r.groupby('firm').app.shift(-1)
r['gap'] = (r.next_app - r.app).dt.total_seconds() / 86400
base = r[(r.app >= '2025-01-01') & (r.app < '2025-10-01')]
rows = []
for s in ['Respins', 'Admis', 'Renunțat']:
    x = base[base.sol == s]
    rows.append(dict(sol=s, n=len(x), **{f'next_within_{d}d': round((x.gap <= d).mean(), 4) for d in [30, 90, 365]}))
print(pd.DataFrame(rows).to_string())
x = base[base.sol == 'Respins']
print('median days to next request after a rejection:', round(x.gap.median(), 1), ' after an admission:', round(base[base.sol == 'Admis'].gap.median(), 1))
