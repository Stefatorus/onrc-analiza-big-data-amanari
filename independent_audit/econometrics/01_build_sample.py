"""PART A, pas 1 — construiește eșantionul la nivel de dosar (intermediar, șters la final).

Citește (read-only):
  * W:/SOLOResearch/articles/YYYY/*_INMATRIC265.json  (încheieri de înmatriculare, BERC)
  * WEB_UU_AN2024.txt / WEB_UU_AN2025.txt (bilanțuri MF, date deschise, cache local)
Scrie (record-level, DOAR în _work/, șters de 99_cleanup.py):
  * _work/inmatric_all.pkl   toate deciziile de înmatriculare (orice formă juridică) - pentru instrument
  * _work/sample.pkl          înmatriculări J admise 2023-2025, legate prin CUI de bilanțuri
Nicio ieșire agregată aici; agregatele se produc în 02_/03_.
Reguli: data depunerii și a deciziei = data calendaristică locală (precizie de zi pentru ambele
platforme: platforma veche, înainte de 26.07.2024, are doar ora 00:00 la depunere).
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WORK = HERE / "_work"
ARTICLES = Path("W:/SOLOResearch/articles")
FIN = Path(r"C:\Users\stefa\AppData\Local\Temp\onrc-review-finance")
YEARS = (2023, 2024, 2025, 2026)


def legal_form(name: str) -> str:
    s = re.sub(r"[^A-Z]", "", (name or "").upper().replace("Ă", "A").replace("Ș", "S").replace("Ş", "S"))
    if s.endswith("SRL") or s.endswith("SRLD"):
        return "SRL"
    if s.endswith("SA"):
        return "SA"
    if s.endswith("SNC") or s.endswith("SCS") or s.endswith("SCA"):
        return "PERS"   # societăți de persoane
    if "COOPERATIV" in s:
        return "COOP"
    return "ALT"


def load_articles() -> pd.DataFrame:
    rows = []
    for y in YEARS:
        for fp in sorted((ARTICLES / str(y)).glob("*_INMATRIC265.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8-sig"))
            except Exception as e:  # noqa: BLE001
                print("skip", fp.name, e)
                continue
            for r in data:
                if (r.get("publicitySituation") or {}).get("identifier") != "INMATRIC265":
                    continue
                app, res = r.get("applicationDate") or "", r.get("resolutionDate") or ""
                if len(app) < 10 or len(res) < 10:
                    continue
                cui = str(r.get("cui") or "")
                rows.append((cui if cui.isdigit() else "", app[:10], res[:10], r.get("juridicType") or "",
                             r.get("resolution") or "", r.get("applicationCounty") or "", r.get("siruta"),
                             str(r.get("registrationYear") or ""), legal_form(r.get("name")) if r.get("juridicType") == "J" else "",
                             str(r.get("applicationNr") or ""), len(app) > 10 and app[11:19] != "00:00:00"))
    df = pd.DataFrame(rows, columns=["cui", "app", "res", "jtype", "sol", "office", "siruta", "regyear", "form", "appnr", "has_time"])
    df["app"] = pd.to_datetime(df.app)
    df["res"] = pd.to_datetime(df.res)
    df["wait"] = (df.res - df.app).dt.days
    return df


def balance(year: int) -> pd.DataFrame:
    cols = ["CUI", "CAEN", "I11", "I13", "I14", "I15", "I16", "I17", "I18", "I19", "I20"]
    f = pd.read_csv(FIN / f"WEB_UU_AN{year}.txt", usecols=cols, dtype={"CUI": "Int64", "CAEN": "string"})
    f = f.dropna(subset=["CUI"]).drop_duplicates()
    conflict = set(f.loc[f.CUI.duplicated(keep=False), "CUI"].astype("int64"))
    f = f.drop_duplicates("CUI", keep=False)       # CUI cu rânduri conflictuale: eliminate (ca audit_finance.py)
    f.attrs["conflict"] = conflict
    for c in cols[2:]:
        f[c] = pd.to_numeric(f[c], errors="coerce").astype("float32")
    f["CUI"] = f.CUI.astype("int64")
    return f.set_index("CUI")


def main():
    WORK.mkdir(exist_ok=True)
    art = load_articles()
    # one decision per (applicationNr, office, res) – articles can be republished/corrected
    art = art.drop_duplicates(["appnr", "office", "res", "sol", "cui"])
    art = art[art.wait.between(0, 400)]
    art[["app", "res", "wait", "jtype", "sol", "office", "has_time"]].to_pickle(WORK / "inmatric_all.pkl")
    print("decisions", len(art), art.sol.value_counts().head(4).to_dict())

    j = art[(art.jtype == "J") & (art.sol == "Admis") & (art.cui != "")].copy()
    j["cui"] = j.cui.astype("int64")
    j = j.sort_values("res").drop_duplicates("cui", keep="first")
    j = j[(j.app >= "2023-01-01") & (j.app <= "2025-12-31")]
    b24, b25 = balance(2024), balance(2025)
    for y, b in ((2024, b24), (2025, b25)):
        m = b.reindex(j.cui.to_numpy())
        j[f"bs{y}"] = j.cui.isin(b.index).to_numpy()          # bilanț depus = rândul există
        j[f"conflict{y}"] = j.cui.isin(b.attrs["conflict"]).to_numpy()
        print(y, "conflicting-duplicate CUIs in sample", int(j[f"conflict{y}"].sum()))
        for c in ["CAEN", "I11", "I13", "I16", "I17", "I18", "I19", "I20"]:
            j[f"{c}_{y}"] = m[c].to_numpy()
    print("J admitted sample", len(j), "by filing year", j.app.dt.year.value_counts().sort_index().to_dict())
    print("office missing", (j.office == "").mean(), "has_time share by year",
          j.groupby(j.app.dt.year).has_time.mean().round(3).to_dict())
    j.drop(columns=["appnr", "jtype", "sol"]).to_pickle(WORK / "sample.pkl")


if __name__ == "__main__":
    main()
