"""One row per BERC decision (2024 baseline + W:/SOLOResearch/articles), saved as a compact pickle for the regressions.
Usage: python build_decisions.py <out.pkl>"""
import glob
import json
import os
import sys

import pandas as pd

SOURCES = [r"S:\Projects\SOLOResearch\results\counties_backup", r"S:\Projects\SOLOResearch\results\counties"] + \
          [rf"W:\SOLOResearch\articles\{y}" for y in ("2023", "2024", "2025", "2026")]
CATS = {"CERERE265", "INMATRIC265", "AUTO_AMANARI", "CERERE_HJ265"}

rows, seen = [], set()
for folder in SOURCES:
    for f in glob.glob(os.path.join(folder, "*.json")):
        for a in json.load(open(f, encoding="utf-8")):
            cat = (a.get("publicitySituation") or {}).get("identifier")
            if cat not in CATS or a.get("id") in seen:
                continue
            seen.add(a.get("id"))
            parts = (a.get("fileName") or "").split("_")
            rows.append((cat, a.get("applicationNr"), a.get("applicationDate"), a.get("resolutionDate"), a.get("publishedAt"),
                         a.get("applicationCounty"), a.get("resolution"), parts[0] if len(parts) > 4 else None,
                         parts[3] if len(parts) > 4 else None, a.get("juridicType")))

d = pd.DataFrame(rows, columns=["cat", "app_nr", "app", "res", "pub", "county", "sol", "office", "code4", "jtype"])
for c in ("app", "res", "pub"):
    d[c] = pd.to_datetime(d[c], utc=True, errors="coerce").dt.tz_convert("Europe/Bucharest").dt.tz_localize(None)
d["app_nr"] = pd.to_numeric(d.app_nr, errors="coerce")
for c in ("cat", "county", "sol", "office", "code4", "jtype"):
    d[c] = d[c].astype("category")
d = d.dropna(subset=["app", "res"])
d.to_pickle(sys.argv[1])
print(f"{len(d):,} decisions, {d.res.min():%Y-%m-%d} .. {d.res.max():%Y-%m-%d}")
print(d.cat.value_counts().to_string())
print(d.sol.value_counts().head(8).to_string())
