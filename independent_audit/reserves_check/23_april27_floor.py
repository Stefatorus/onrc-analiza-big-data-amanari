"""27.04.2026 step: is it a minimum-wait floor? Wait distribution in working days, before vs after, by category."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import sys; sys.path.insert(0, str(config.REPO / 'independent_audit' / 'reserves_check'))
from rocal import HOL
import pandas as pd, numpy as np
r = pd.read_pickle(str(config.WORK_DIR / 'raw_compact.pkl'))[['cat', 'app', 'res', 'sol', 'art']]
r = r.drop_duplicates('art'); r['cat'] = r.cat.astype(str); r['sol'] = r.sol.astype(str)
r = r[(r.res >= '2026-03-02') & (r.res < '2026-06-29') & r.cat.isin(['CERERE265', 'INMATRIC265', 'AUTO_AMANARI'])].dropna(subset=['app', 'res'])
hol = np.array(HOL.values.astype('datetime64[D]'))
r['bd'] = np.busday_count(r.app.values.astype('datetime64[D]'), r.res.values.astype('datetime64[D]'), holidays=hol)
r['per'] = np.where(r.res < '2026-04-27', 'before (2.03-26.04)', 'after (27.04-28.06)')
for c in ['CERERE265', 'INMATRIC265', 'AUTO_AMANARI']:
    s = r[r.cat == c]
    t = pd.crosstab(s.per, s.bd.clip(upper=6), normalize='index').round(3)
    print(c, '- share by working days between filing and decision (6 = 6+)'); print(t.to_string())
# daily share decided in <=1 working day, to date the switch exactly
s = r[r.cat == 'CERERE265']
d = s.groupby(s.res.dt.normalize()).bd.apply(lambda x: (x <= 1).mean())
print('\nCERERE265 share decided within <=1 working day, by decision day 20.04-08.05:')
print(d['2026-04-20':'2026-05-08'].round(3).to_string())
