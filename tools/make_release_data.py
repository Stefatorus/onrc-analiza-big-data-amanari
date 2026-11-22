"""Build the GitHub Release assets for cross-verification (NOT committed to git).

  python -X utf8 tools/make_release_data.py [--pkl data/analysis_decisions.pkl] [--deliv analysis/raport_executiv_2026-11] [--out data/release]

Produces in --out:
  berc_decisions_min.csv.gz      one row per BERC decision: category, filing / decision / publication timestamps, outcome,
                                 county of filing, filing office code, juridical type. NO firm names, CUI, companyCode, J numbers,
                                 application numbers or document codes (column `code4` of the pickle is dropped too).
  counter_daily_national.csv.gz  per filing day (all categories): number of decisions, distinct application numbers, distinct
                                 numbers with a final decision, min / max application number  -> the national request counter
  counter_daily_by_category.csv.gz  the same per filing day x decision category
  counter_daily_by_county.csv.gz    the same per filing day x county (the pre-26.07.2024 counters were per county)
  the final PDFs, Date_ONRC_Coada_2026-11.xlsx, claims_registry.csv (copied from --deliv)
  SHA256SUMS
Anyone with a full BERC crawl can regenerate the data files: analysis/build_decisions.py, then this script.
A self-check rebuilds the daily counter level and the distinct-request series of reserves_check/11_inflow_counter.py from the
aggregated tables and compares them with the committed reserves_check/11_daily_counter_vs_berc.csv.
"""
from __future__ import annotations
import argparse, hashlib, shutil, sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import config  # noqa: E402

FIN = ['Admis', 'Respins', 'Renunțat', 'Certificare înscriere în registrul comerțului', 'Renunțat din oficiu', 'ADMIS',
       'certificare inscriere mentiuni']          # same list as reserves_check/11_inflow_counter.py
PDFS = ["Raport_ONRC_Coada_2026-11_COMPLET.pdf", "Raport_ONRC_Coada_2026-11.pdf", "Raport_ONRC_Coada_2026-11_EXECUTIV.pdf",
        "Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil.pdf", "Raport_ONRC_Coada_2026-11_VOL2_Anexe_statistice.pdf",
        "Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat.pdf", "Raport_ONRC_Coada_2026-11_VOL4_Munca_din_spatele_cozii.pdf",
        "Raport_ONRC_Coada_2026-11_VOL5_Fise_pe_judete.pdf", "Raport_ONRC_Coada_2026-11_VOL6_Verificare.pdf",
        "Raport_ONRC_Coada_2026-11_VOL7_Impact_economic_si_bugetar.pdf"]


def counter(df, keys):
    g = df.groupby(keys, observed=True)
    out = pd.DataFrame({"n_decisions": g.size(), "n_distinct_app_nr": g.app_nr.nunique(),
                        "app_nr_min": g.app_nr.min(), "app_nr_max": g.app_nr.max()})
    out["n_distinct_app_nr_final"] = df[df.fin].groupby(keys, observed=True).app_nr.nunique().reindex(out.index).fillna(0).astype(int)
    for c in ("app_nr_min", "app_nr_max"):
        out[c] = out[c].astype("Int64")
    return out.reset_index()


def self_check(nat_tab):
    ref = REPO / "independent_audit" / "reserves_check" / "11_daily_counter_vs_berc.csv"
    if not ref.exists():
        print("self-check skipped (no 11_daily_counter_vs_berc.csv)"); return
    r = pd.read_csv(ref, index_col=0, parse_dates=True)
    t = nat_tab.set_index("filing_date")
    t.index = pd.to_datetime(t.index)
    days = r.index
    lev = t.app_nr_max.reindex(days).astype("float")
    parts = []
    for Y in sorted(set(days.year)):
        s = lev[lev.index.year == Y].cummax().ffill(); parts.append(s)
    level = pd.concat(parts)
    dist = t.n_distinct_app_nr.reindex(days).fillna(0)
    fin = t.n_distinct_app_nr_final.reindex(days).fillna(0)
    ok_lev = (level.fillna(-1) == r.level.fillna(-1)).mean()
    ok_d = (dist.values == r.berc_distinct.values).mean(); ok_f = (fin.values == r.berc_final.values).mean()
    print(f"self-check vs 11_daily_counter_vs_berc.csv: level equal on {ok_lev:.1%} of days, distinct {ok_d:.1%}, finals {ok_f:.1%}")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkl", default=str(config.BERC_PKL))
    ap.add_argument("--deliv", default=str(REPO / "analysis" / "raport_executiv_2026-11"))
    ap.add_argument("--out", default=str(config.DATA_DIR / "release"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    d = pd.read_pickle(a.pkl)
    print(f"{len(d):,} decisions")
    m = pd.DataFrame({"category": d["cat"].astype(str), "filed_at": d["app"], "decided_at": d["res"], "published_at": d["pub"],
                      "outcome": d["sol"].astype(str), "county": d["county"].astype(str), "office": d["office"].astype(str),
                      "juridical_type": d["jtype"].astype(str)}).replace({"nan": "", "None": ""})
    m = m.sort_values(["decided_at", "filed_at", "category"], kind="mergesort").reset_index(drop=True)   # row order carries no id
    m.to_csv(out / "berc_decisions_min.csv.gz", index=False, date_format="%Y-%m-%d %H:%M:%S", compression={"method": "gzip", "mtime": 0})
    b = d[["cat", "app_nr", "app", "sol", "county"]].copy()
    b["filing_date"] = b.app.dt.strftime("%Y-%m-%d"); b["fin"] = b.sol.isin(FIN)
    b = b[b.app_nr.notna()]
    nat = counter(b, ["filing_date"]); nat.to_csv(out / "counter_daily_national.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    counter(b.rename(columns={"cat": "category"}), ["filing_date", "category"]).to_csv(
        out / "counter_daily_by_category.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    counter(b, ["filing_date", "county"]).to_csv(out / "counter_daily_by_county.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    self_check(nat)
    deliv = Path(a.deliv)
    for f in PDFS + ["Date_ONRC_Coada_2026-11.xlsx", "claims_registry.csv"]:
        if (deliv / f).exists():
            shutil.copy2(deliv / f, out / f)
        else:
            print("MISSING deliverable:", f)
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    (out / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.name}\n" for p in files), encoding="utf-8")
    for p in files:
        print(f"{p.stat().st_size:>12,}  {p.name}")


if __name__ == "__main__":
    main()
