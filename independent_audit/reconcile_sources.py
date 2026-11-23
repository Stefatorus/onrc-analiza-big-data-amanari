"""Single source of truth for the ONRC queue numbers.

Computes the authoritative figures ONCE from BERC (the 4M-decision bulletin — the
flow/throughput side) and the portal sample (the stock/queue side), cross-checks the
two independent sources against each other, and LOCKS the result to out/LOCKED_CONSTANTS.json.
Every downstream tool (model, twin, report) reads that file, so the numbers never drift.

Run:  ..\venv\Scripts\python.exe -X utf8 reconcile_sources.py
"""
from __future__ import annotations
import sys, json; sys.path.insert(0, ".")
import pandas as pd, numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
BERC = r"W:\SOLOResearch\analysis_decisions.pkl"
REG = 165                       # active registrators (report 150-185; mid-point)
RECENT = ("2026-10-01", "2026-11-22")
FINAL = ["Admis", "Respins", "Renunțat",
         "Certificare înscriere în registrul comerțului",
         "certificare inscriere mentiuni", "Renunțat din oficiu"]


def rate(df, col, lo, hi):
    s = df[(df[col] >= lo) & (df[col] < hi)]
    return len(s) / max(s[col].dt.normalize().nunique(), 1)


def main():
    # ---------- BERC: flow side (authoritative) ----------
    b = pd.read_pickle(BERC)
    b = b[b["res"].notna() & b["app"].notna()].copy()
    b["is_final"] = b["sol"].isin(FINAL)
    fin = b[b["is_final"]]
    lo, hi = RECENT
    thr_final = rate(fin, "res", lo, hi)
    thr_ment = rate(fin[fin.cat == "CERERE265"], "res", lo, hi)
    thr_inm = rate(fin[fin.cat == "INMATRIC265"], "res", lo, hi)
    thr_aman = rate(b[b.sol == "Amânat"], "res", lo, hi)
    # August dip (finals) vs Jun-Jul baseline
    aug = rate(fin, "res", "2026-08-01", "2026-09-01")
    junjul = rate(fin, "res", "2026-06-01", "2026-08-01")
    aug_ratio = round(aug / junjul, 3)
    # authoritative W by filing month (finals, res-app) -- no censoring for settled months
    b["W"] = (b["res"] - b["app"]).dt.days
    f = b[b.is_final & (b.W >= 0) & (b.W < 400) & (b.app >= "2026-01-01")]
    wm = f.groupby(f.app.dt.to_period("M"))["W"].median()
    berc_W = {str(k): float(v) for k, v in wm.items() if str(k) <= "2026-09"}
    # settled-month completeness (n per filing month) to flag censoring
    nmonth = f.groupby(f.app.dt.to_period("M")).size()

    # ---------- BERC: history (regimes) and the CURRENT wait by decision week ----------
    b["d"] = b["res"].dt.normalize()
    b["Wf"] = (b["res"] - b["app"]).dt.total_seconds() / 86400
    FIN3 = ["Admis", "Respins", "Renunțat"]
    def regime(lo2, hi2):
        s = b[(b.d >= lo2) & (b.d <= hi2)]
        f2 = s[s.sol.isin(FIN3) & (s.Wf >= 0) & (s.Wf < 400)]
        nd = s.d.nunique()
        return {"days": int(nd), "finals_per_day": round(len(f2) / max(nd, 1)),
                "adjourn_share": round(float((s.sol == "Amânat").mean()), 3),
                "median_wait": round(float(f2.Wf.median()), 1),
                "p90_wait": round(float(f2.Wf.quantile(.9)), 1)}
    regimes = {
        "platforma_veche_2023_iul2024": regime("2023-04-03", "2024-07-17"),
        "colaps_portal_nou_2024": regime("2024-07-29", "2024-11-30"),
        "stabil_2025": regime("2025-01-01", "2025-12-31"),
        "2026_inainte_de_val": regime("2026-01-01", "2026-07-31"),
        "aug_2026": regime("2026-08-01", "2026-08-31"),
        "sep_2026": regime("2026-09-01", "2026-09-30"),
        "oct_2026": regime("2026-10-01", "2026-10-31"),
        "nov_1_21_2026": regime("2026-11-01", "2026-11-21"),
    }
    r2 = b[b.sol.isin(FIN3) & (b.Wf >= 0) & (b.Wf < 400) & (b.d >= "2026-09-28")].copy()
    r2["wk"] = r2.d.dt.to_period("W-SUN").apply(lambda p: str(p.start_time.date()))
    dw = {cat: {k: round(float(v), 1) for k, v in
                r2[r2.cat == cat].groupby("wk")["Wf"].median().items()}
          for cat in ("CERERE265", "INMATRIC265")}
    berc_max = str(b.res.max())[:16]
    # two-speed queue: share of finals decided within 14 calendar days, 2-19 Nov 2026
    tw = b[b.sol.isin(FIN3) & (b.Wf >= 0) & (b.d >= "2026-11-02") & (b.d <= "2026-11-19")]
    # Gate v2 (CICERO-REELS) definitions, per LEGAL working day (Romanian 2026 holidays):
    HOL26 = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-06", "2026-01-07", "2026-01-24",
                            "2026-04-10", "2026-04-13", "2026-05-01", "2026-06-01", "2026-08-15",
                            "2026-11-30", "2026-12-01", "2026-12-25"])
    def legal_wd(lo2, hi2):
        return sum(1 for x in pd.bdate_range(lo2, hi2) if x not in HOL26)
    fs = b[b.sol.isin(FIN3)]
    def per_legal_wd(lo2, hi2):
        return len(fs[(fs.d >= lo2) & (fs.d <= hi2)]) / legal_wd(lo2, hi2)
    aug_ratio_legal = round(per_legal_wd("2026-08-01", "2026-08-31") / per_legal_wd("2026-06-01", "2026-07-31"), 3)
    # 27 Apr 2026 step: share of final decisions with wait <=2 calendar days, by DECISION date
    fw = fs[fs.Wf >= 0]
    pre27 = fw[(fw.d >= "2026-03-01") & (fw.d <= "2026-04-26")]
    post27 = fw[(fw.d >= "2026-04-27") & (fw.d <= "2026-07-31")]
    le2d_27apr = {"pre_1mar_26apr_pct": round(100 * float((pre27.Wf <= 2).mean()), 1),
                  "post_27apr_31jul_pct": round(100 * float((post27.Wf <= 2).mean()), 2),
                  "n_pre": int(len(pre27)), "n_post": int(len(post27))}
    # Rejection share among strict finals (CERERE265 + INMATRIC265), and median wait — gate v3
    rj = fw[fw.cat.isin(["CERERE265", "INMATRIC265"])]
    def rej(lo2, hi2):
        g = rj[(rj.d >= lo2) & (rj.d <= hi2)]
        return {"respins_pct": round(100 * float((g.sol == "Respins").mean()), 2),
                "median_wait": round(float(g.Wf.median()), 2), "n": int(len(g))}
    rejection_share = {"H2_2025": rej("2025-07-01", "2025-12-31"), "year_2025": rej("2025-01-01", "2025-12-31"),
                       "oct_1_nov_20_2026": rej("2026-10-01", "2026-11-20")}
    two_speed = {cat: {"share_le14d_pct": round(100 * float((g.Wf <= 14).mean()), 1),
                       "median_wait": round(float(g.Wf.median()), 1), "n": int(len(g))}
                 for cat, g in tw.groupby("cat", observed=True) if cat in ("CERERE265", "INMATRIC265")}

    # ---------- Portal: stock side ----------
    from analyze_portal_snapshot import load
    p = load(None)
    det = p[(p.details_found) & (p.is_judged == 1)].copy()
    det["rq"] = pd.to_datetime(det["request_date"].str[:10], errors="coerce")
    det["so"] = pd.to_datetime(det["solution_term"].str[:10], errors="coerce")
    live = det[det.phase_code.isin(["04", "08"])]
    split_s1 = float((live.phase_code == "04").mean())
    # portal mentiuni throughput (weighted) for cross-check
    uniq = p.drop_duplicates("req_nr"); regs = [(1900000, 3900000), (3900000, 4824375)]
    def w_of(nr):
        for a, z in regs:
            if a <= nr < z:
                return (z - a) / max(((uniq.req_nr >= a) & (uniq.req_nr < z)).sum(), 1)
        return 0
    res = det[det.phase_code.isin(["12", "13", "14", "15", "27"]) & det.so.notna()].copy()
    res["w"] = res.req_nr.map(w_of)
    res["wk"] = res.so.dt.to_period("W-MON").apply(lambda x: x.start_time)
    gday = res.groupby("wk")["w"].sum() / 7.0
    portal_ment_thr = float(gday[(gday.index >= lo) & (gday.index <= "2026-11-15")].mean())
    # portal W by filing month (resolved)
    res["W"] = (res.so - res.rq).dt.days
    rw = res[(res.W >= 0) & (res.W < 400)].groupby(res.rq.dt.to_period("M"))["W"].median()
    portal_W = {str(k): float(v) for k, v in rw.items() if str(k) <= "2026-09"}

    # ---------- cross-check ----------
    print("=" * 64)
    print("CROSS-SOURCE RECONCILIATION  (BERC flow  vs  portal stock)")
    print("=" * 64)
    print(f"\nThroughput — mentiuni finals/day (the overlapping quantity):")
    print(f"   BERC (4M decisions)     : {thr_ment:,.0f}/day")
    print(f"   Portal (7k sample, wtd) : {portal_ment_thr:,.0f}/day")
    agree = abs(thr_ment - portal_ment_thr) / thr_ment
    print(f"   -> agree within {agree:.0%}  [{'PASS' if agree < 0.25 else 'CHECK'}]")
    print(f"\nHandling-time W by filing month (independent):")
    print(f"   {'month':8} {'BERC':>6} {'portal':>7}")
    for m in sorted(set(berc_W) | set(portal_W)):
        print(f"   {m:8} {berc_W.get(m,float('nan')):>6.0f} {portal_W.get(m,float('nan')):>7.0f}")
    print(f"\nAugust capacity dip (BERC finals): {aug:,.0f}/day vs Jun-Jul {junjul:,.0f} = {aug_ratio:.0%}")

    # ---------- LOCK ----------
    locked = {
        "_meta": "AUTHORITATIVE — computed once from BERC (flow) + portal (stock). Do not hand-edit.",
        "as_of": "2026-11-22", "registrators": REG, "recent_window": RECENT,
        "throughput_finals_per_day": round(thr_final),
        "throughput_mentiuni_per_day": round(thr_ment),
        "throughput_inmatric_per_day": round(thr_inm),
        "adjournments_per_day": round(thr_aman),
        "files_per_day_per_registrator_finals": round(thr_final / REG, 1),
        "august_capacity_ratio": aug_ratio,
        "W_by_filing_month_days": {k: round(v) for k, v in berc_W.items()},
        "backlog_total_report": 210000,
        "backlog_split_stage1": round(split_s1, 3),
        "crosscheck_mentiuni_portal_vs_berc_pct": round(agree, 3),
        "regimes_by_decision_date": regimes,
        "wait_of_dossiers_decided_by_week": dw,
        "berc_last_decision": berc_max,
        "two_speed_2_19_nov": two_speed,
        "august_ratio_strict_finals_per_legal_wd": aug_ratio_legal,
        "le2d_share_27apr_by_decision_date": le2d_27apr,
        "rejection_share_strict_finals": rejection_share,
        "sources": {"BERC": "analysis_decisions.pkl (4,077,510 decisions)",
                    "portal": "myportal harvest (~7,469 dossiers)"},
    }
    (OUT / "LOCKED_CONSTANTS.json").write_text(json.dumps(locked, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"\nLOCKED -> {OUT/'LOCKED_CONSTANTS.json'}")
    print(json.dumps({k: v for k, v in locked.items() if not k.startswith("_")
                      and k not in ("W_by_filing_month_days", "sources")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
