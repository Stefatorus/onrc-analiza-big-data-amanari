"""Aggregate the harvested myportal snapshot into the two-queue (Stage 1 / Stage 2)
composition tables. Offline only -- reads out/harvest_*.jsonl, writes anonymized
CSV + JSON summary. Partial-friendly: runs on whatever rows exist so far.

    .\venv\Scripts\python.exe -X utf8 independent_audit\analyze_portal_snapshot.py --run snap_national
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); import config  # repo config.py
import argparse, glob, json, collections
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PORTAL = config.PORTAL_DIR   # the row-level myportal sample is NOT published; empty -> load() returns an empty frame

# public reference data (ONRC county code -> ORCT 2-letter mnemonic), not PII
CODE2MN = {"3":"AG","4":"BC","5":"BH","6":"BN","7":"BT","8":"BV","9":"BR","10":"BZ",
 "11":"CS","12":"CJ","13":"CT","14":"CV","15":"DB","16":"DJ","17":"GL","18":"GJ",
 "19":"HR","20":"HD","21":"IL","22":"IS","24":"MM","25":"MH","26":"MS","27":"NT",
 "28":"OT","29":"PH","30":"SM","31":"SJ","32":"SB","33":"SV","34":"TR","35":"TM",
 "36":"TL","37":"VS","38":"VL","39":"VN","40":"B","51":"CL","52":"GR","23":"IF",
 "1":"AB","2":"AR"}

PHASE_STAGE = {"04":"Stage1_operare","05":"Stage1_operare","08":"Stage2_solutionare",
 "12":"Resolved","13":"Resolved","14":"Resolved","15":"Resolved","27":"Resolved",
 "23":"Attached_017","24":"Archived","25":"Archived"}
TYPE_NAME = {"001":"Inmatriculare","002":"Mentiune","003":"Radiere",
 "017":"Completare_acte"}


def _clean(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v)


def unify_county(r: dict) -> str:
    cand = (_clean(r.get("county")) or _clean(r.get("old_county_code"))
            or _clean(r.get("county_resolved")))
    if cand.isdigit():  # numeric code (possibly zero-padded) -> mnemonic
        return CODE2MN.get(str(int(cand)), cand)
    return cand


def load(run: str | None) -> pd.DataFrame:
    files = ([PORTAL / f"harvest_{run}.jsonl"] if run else
             [Path(p) for p in glob.glob(str(PORTAL / "harvest_*.jsonl"))])
    rows = {}
    for f in files:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            rows[int(r["req_nr"])] = r  # dedup, last wins
    df = pd.DataFrame(list(rows.values()))
    if df.empty:
        return df
    df["county_mn"] = df.apply(unify_county, axis=1)
    df["stage"] = df["phase_code"].map(PHASE_STAGE).fillna(
        df["phase_code"].apply(lambda c: "Other" if c else ""))
    df["type_name"] = df["type_code"].map(TYPE_NAME).fillna(df["type_code"])
    df["req_day"] = pd.to_datetime(df["request_date"].str[:10], errors="coerce")
    df["req_week"] = df["req_day"].dt.to_period("W-SUN").apply(
        lambda p: p.start_time.strftime("%Y-%m-%d") if pd.notna(p) else "")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="run id; default = all harvest files")
    args = ap.parse_args()
    df = load(args.run)
    if df.empty:
        print("No rows yet.")
        return

    n = len(df)
    det = df[df["details_found"]]
    noc = df[(df["s1_found"]) & (~df["has_company_id"])]
    print(f"=== PORTAL SNAPSHOT  (probed={n}, details={len(det)}, "
          f"no-companyId inmatric-in-progress={len(noc)} [{len(noc)/n:.0%}]) ===\n")

    print("-- Phase code dictionary observed --")
    for (pc, pd_), c in collections.Counter(
            zip(det["phase_code"], det["phase_desc"])).most_common():
        print(f"  {pc:>3} {PHASE_STAGE.get(pc,'?'):18} {pd_[:34]:34} n={c}")

    print("\n-- Stage composition (is_judged==1 registry dossiers) --")
    jud = det[det["is_judged"] == 1]
    sc = jud["stage"].value_counts()
    tot_q = sc.get("Stage1_operare", 0) + sc.get("Stage2_solutionare", 0)
    for s, c in sc.items():
        print(f"  {s:20} {c:4}  ({c/len(jud):.1%})")
    if tot_q:
        s1 = sc.get("Stage1_operare", 0); s2 = sc.get("Stage2_solutionare", 0)
        print(f"  --> among the two LIVE queues only: Stage1={s1} ({s1/tot_q:.0%}) "
              f"vs Stage2={s2} ({s2/tot_q:.0%})")

    print("\n-- Judged dossiers by request type --")
    print(jud["type_name"].value_counts().to_string())

    print("\n-- LIVE-QUEUE dossiers (phase 04/08) by filing week --")
    live = jud[jud["stage"].isin(["Stage1_operare", "Stage2_solutionare"])].copy()
    if not live.empty:
        piv = live.pivot_table(index="req_week", columns="stage",
                               values="req_nr", aggfunc="count", fill_value=0)
        print(piv.to_string())
        print(f"  oldest still-pending filing in sample: {live['req_day'].min().date()}")

    print("\n-- LIVE-QUEUE dossiers by county (phase 04/08) --")
    lc = live[live["county_mn"] != ""]
    if not lc.empty:
        cpiv = lc.pivot_table(index="county_mn", columns="stage",
                              values="req_nr", aggfunc="count", fill_value=0)
        cpiv["total"] = cpiv.sum(axis=1)
        print(cpiv.sort_values("total", ascending=False).to_string())
    print(f"\n  county known for {(live['county_mn']!='').sum()}/{len(live)} live-queue dossiers")

    # ---- age-of-pile: localize the bottleneck (today - requestDate, in days) ----
    TODAY = pd.Timestamp("2026-11-21")
    live["age_days"] = (TODAY - live["req_day"]).dt.days
    print("\n-- AGE OF EACH PILE (days since filing; bottleneck = oldest/deepest) --")
    ag = live.groupby("stage")["age_days"].agg(
        n="count", median="median", p90=lambda s: s.quantile(.9), max="max")
    print(ag.to_string())
    print("  (Stage1 age = W1-so-far, still un-operated; Stage2 age = W1_done + W2-so-far)")

    # ---- cohort stock-share: drain curve -> W1/W2 inference ----
    print("\n-- COHORT STOCK-SHARE by filing week (of judged dossiers w/ known stage) --")
    coh = det[(det["is_judged"] == 1) &
              (det["stage"].isin(["Stage1_operare", "Stage2_solutionare", "Resolved"]))].copy()
    coh["elapsed_days"] = (TODAY - coh["req_day"]).dt.days
    g = coh.groupby("req_week")
    tab = g["stage"].value_counts().unstack(fill_value=0)
    for c in ["Stage1_operare", "Stage2_solutionare", "Resolved"]:
        if c not in tab:
            tab[c] = 0
    tab["n"] = tab[["Stage1_operare", "Stage2_solutionare", "Resolved"]].sum(axis=1)
    tab["elapsed_d"] = g["elapsed_days"].median().round().astype("Int64")
    tab["pct_S1"] = (100 * tab["Stage1_operare"] / tab["n"]).round(0)
    tab["pct_S2"] = (100 * tab["Stage2_solutionare"] / tab["n"]).round(0)
    tab["pct_resolved"] = (100 * tab["Resolved"] / tab["n"]).round(0)
    print(tab[["elapsed_d", "n", "Stage1_operare", "Stage2_solutionare", "Resolved",
               "pct_S1", "pct_S2", "pct_resolved"]].to_string())
    print("  W1 ~ elapsed where pct_S1 falls through 50%; total ~ where pct_resolved reaches 50%.")

    # anonymized CSV (drop any transient id-ish columns; none stored anyway)
    keep = ["req_nr","req_day","req_week","county_mn","stage","phase_code","phase_desc",
            "type_code","type_name","subtype_desc","is_judged","is_quick_finish",
            "solution","has_company_id","s1_found","details_found"]
    csv = OUT / f"snapshot_clean_{args.run or 'all'}.csv"
    df[keep].sort_values("req_nr").to_csv(csv, index=False, encoding="utf-8")
    print(f"\nWrote {csv}")


if __name__ == "__main__":
    main()
