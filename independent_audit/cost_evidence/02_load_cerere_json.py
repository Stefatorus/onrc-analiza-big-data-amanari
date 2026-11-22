"""Load 2026 CERERE265 decisions from the raw daily JSON (only the fields needed). Record-level output -> _tmp/."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import glob, json, os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
rows = []
for fp in sorted(glob.glob(str(config.ARTICLES_DIR / '2026' / '*_CERERE265.json'))) + sorted(glob.glob(str(config.ARTICLES_DIR / '2025' / '2025-12-3*_CERERE265.json'))):
    for r in json.load(open(fp, encoding='utf-8-sig')):
        if (r.get('publicitySituation') or {}).get('identifier') != 'CERERE265':
            continue
        pub = r.get('publication') or {}
        rows.append((r.get('id'), r.get('applicationNr'), r.get('cui'), r.get('resolution'), r.get('applicationDate'),
                     r.get('resolutionDate'), pub.get('nr'), r.get('juridicType'), r.get('applicationCounty')))
d = pd.DataFrame(rows, columns=['id', 'app_nr', 'cui', 'sol', 'app', 'res', 'pub_nr', 'jtype', 'county']).drop_duplicates('id')
for c in ('app', 'res'):
    d[c] = pd.to_datetime(d[c], format='mixed', utc=True, errors='coerce').dt.tz_convert('Europe/Bucharest').dt.tz_localize(None)
d['app_nr'] = pd.to_numeric(d.app_nr, errors='coerce'); d['cui'] = pd.to_numeric(d.cui, errors='coerce')
d = d.drop(columns='id')
d.to_pickle(os.path.join(TMP, 'cerere_2026.pkl'))
print('records', len(d), 'res range', d.res.min(), d.res.max()); print(d.sol.value_counts().head()); print(d.jtype.value_counts().head())
w = d[(d.res >= '2026-08-01') & (d.res < '2026-11-19')].copy(); w['wait'] = (w.res - w.app).dt.total_seconds() / 86400
w = w[w.wait.between(0, 365) & w.sol.eq('Admis')]
print('window admitted (0-365d wait)', len(w), 'excess days', round(w.wait.sub(3).clip(lower=0).sum()), 'cui present', w.cui.notna().mean())
