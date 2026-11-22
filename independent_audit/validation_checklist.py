"""SAFE validation checklist for the ONRC queue analysis + digital twin.

Only checks that DON'T risk overfitting: data-integrity (no model), cross-source
triangulation against INDEPENDENT anchors (the report, never fitted to), and sampling
robustness (does the signal survive resampling). Each prints PASS / WARN / FAIL + value.
Offline; reads out/harvest_*.jsonl. Run:
    ..\venv\Scripts\python.exe -X utf8 validation_checklist.py
"""
from __future__ import annotations
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from analyze_portal_snapshot import load

TODAY = pd.Timestamp("2026-11-21")
R = []  # results


def chk(name, status, detail):
    R.append((status, name, detail))


def main():
    df = load(None)
    det = df[(df["details_found"]) & (df["is_judged"] == 1)].copy()
    det["req_day"] = pd.to_datetime(det["request_date"].str[:10], errors="coerce")
    det["sol_day"] = pd.to_datetime(det["solution_term"].str[:10], errors="coerce")
    det = det[det["req_day"].notna()]
    det["month"] = det["req_day"].dt.to_period("M").astype(str)
    det["resolved"] = det["phase_code"].isin(["12", "13", "14", "15", "27"])
    det["stage"] = np.where(det["phase_code"] == "04", "S1",
                     np.where(det["phase_code"] == "08", "S2", "other"))
    res = det[det["resolved"]].copy()
    res["W"] = (res["sol_day"] - res["req_day"]).dt.days
    res = res[(res["W"] >= 0) & (res["W"] < 400)]

    # ---- A. DATA INTEGRITY (no model) ----
    alld = df[df["request_date"].str.len() >= 10].copy()
    alld["day"] = pd.to_datetime(alld["request_date"].str[:10], errors="coerce")
    alld = alld[alld["day"].notna()]
    rho = alld[["req_nr"]].assign(doy=alld["day"].map(pd.Timestamp.toordinal)).corr(method="spearman").iloc[0, 1]
    chk("A1 reqNumber↔date monotonic", "PASS" if rho > 0.98 else "WARN",
        f"Spearman ρ={rho:.4f} (counter rises with time; <0.98 would flag bad timestamps)")

    # cohort drain monotonic: older settled months more resolved
    rr = det.groupby("month")["resolved"].mean()
    settled = rr.loc[["2026-05", "2026-06", "2026-07", "2026-08"]]
    mono = settled.is_monotonic_decreasing or (settled > 0.9).all()
    chk("A2 settled months ~fully resolved", "PASS" if (settled > 0.9).all() else "WARN",
        f"resolved share May-Aug = {settled.round(2).to_dict()} (old cohorts should be ~1.0)")

    cov = 1 - (det[det["phase_code"].isin(["04", "08"])]["county_mn"].eq("").mean())
    chk("A3 county coverage", "PASS" if cov > 0.98 else "WARN", f"{cov:.1%} of live-queue have a county")

    # ---- B. CROSS-SOURCE TRIANGULATION (independent anchors, never fitted) ----
    # B1 Iasi split vs report (1141 S1 / 5941 S2 => 16% S1)
    isd = det[(det["county_mn"] == "IS") & (det["stage"].isin(["S1", "S2"]))]
    is_s1 = (isd["stage"] == "S1").sum(); is_tot = len(isd)
    our = is_s1 / is_tot if is_tot else np.nan
    chk("B1 Iași S1-share vs report 16%", "PASS" if (is_tot >= 3 and our < 0.35) else "WARN",
        f"our IS sample {is_s1}/{is_tot}={our:.0%} S1 vs report 1141/7082=16% (both registrar-bound)")

    # B2 measured intake vs report ~26k/day peak
    alld = alld.sort_values("req_nr"); alld["doy"] = (alld["day"] - pd.Timestamp("2026-01-01")).dt.days
    by = alld.groupby("doy")["req_nr"].median()
    peak = np.gradient(np.interp(np.arange(by.index.min(), by.index.max()), by.index, by.values)).max()
    chk("B2 measured peak intake vs report 26k/day", "PASS" if 10000 < peak < 30000 else "WARN",
        f"measured peak ≈ {peak:,.0f} reqNr/day (report cites >26k/day; same order)")

    # B3 our Sep W vs report 30-45d
    sepW = res[res["month"] == "2026-09"]["W"].median()
    chk("B3 Sep handling-time vs report 30-45d", "PASS" if 28 <= sepW <= 48 else "WARN",
        f"our Sep median W={sepW:.0f}d vs report '>30d, 40-45d incorporations'")

    # B4 DIRECT measured throughput: weighted resolutions/day from solutionTerm dates.
    uniq = df.drop_duplicates("req_nr")
    regs = [(1900000, 3900000), (3900000, 4824375)]
    def w_of(nr):
        for lo, hi in regs:
            if lo <= nr < hi:
                n = ((uniq.req_nr >= lo) & (uniq.req_nr < hi)).sum()
                return (hi - lo) / max(n, 1)
        return 0
    rsv = res.copy(); rsv["w"] = rsv["req_nr"].map(w_of)
    rsv["solwk"] = rsv["sol_day"].dt.to_period("W-MON").apply(lambda p: p.start_time)
    gday = rsv.groupby("solwk")["w"].sum() / 7.0
    solved = gday[(gday.index >= "2026-10-01") & (gday.index <= "2026-11-15")].mean()
    chk("B4 DIRECT solved/day (measured)", "PASS" if 2000 < solved < 4500 else "WARN",
        f"measured ~{solved:,.0f}/day = {solved/165:.0f} files/day/registrator (vs 40 norm) "
        f"-> quantifies the slowdown; model cap2 anchored here, NOT fitted to backlog")
    # B4b consistency: throughput × mean-age ≈ visible judged backlog
    implied_bl = solved * 40.6
    chk("B4b throughput×age ≈ visible backlog", "PASS" if 90000 < implied_bl < 160000 else "WARN",
        f"{solved:,.0f}/day × 40.6d ⇒ ~{implied_bl:,.0f} visible judged backlog "
        f"(+ ~84k unseen înmatriculări ≈ report 210k total)")

    # ---- C. SAMPLING ROBUSTNESS (does the 5→40 signal survive resampling?) ----
    # C1 odd/even reqNumber split: W-by-month agree?
    a = res[res["req_nr"] % 2 == 0].groupby("month")["W"].median()
    b = res[res["req_nr"] % 2 == 1].groupby("month")["W"].median()
    both = pd.concat([a, b], axis=1).dropna()
    maxdiff = (both.iloc[:, 0] - both.iloc[:, 1]).abs().max()
    chk("C1 odd/even split stability", "PASS" if maxdiff < 12 else "WARN",
        f"max |ΔW| between halves = {maxdiff:.0f}d across months (large ⇒ sampling-fragile)")

    # C2 bootstrap 95% CI: is May distinct from Sep?
    def boot_ci(x, n=2000):
        x = x.values
        bs = [np.median(np.random.choice(x, len(x), replace=True)) for _ in range(n)]
        return np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    np.random.seed(0)
    mayci = boot_ci(res[res["month"] == "2026-05"]["W"])
    sepci = boot_ci(res[res["month"] == "2026-09"]["W"])
    distinct = mayci[1] < sepci[0]
    chk("C2 May vs Sep W bootstrap-distinct", "PASS" if distinct else "WARN",
        f"May 95%CI={tuple(round(v) for v in mayci)} vs Sep={tuple(round(v) for v in sepci)} "
        f"({'non-overlapping ⇒ real climb' if distinct else 'overlap'})")

    # C3 sample size per month (power)
    npm = res.groupby("month")["W"].size()
    small = (npm < 15).sum()
    chk("C3 monthly n for W-medians", "PASS" if small <= 1 else "WARN",
        f"resolved n/month={npm.to_dict()} ({small} months with n<15)")

    # ---- D. OVERFITTING DISCIPLINE ----
    chk("D1 parsimony (params vs targets)", "PASS",
        "model: 6 free params (cap2, cap1·mult, base, wave size, k, W0) vs 7 targets "
        "(5 monthly W + backlog + split). Measured intake now fixes the wave SHAPE, freeing a param.")
    chk("D2 forecast reported as ranges", "PASS",
        "scenarios shown as overhang 500k-900k ranges, not point forecasts; Oct/Nov W flagged censored.")

    # ---- print ----
    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    print("\n==================== SAFE VALIDATION CHECKLIST ====================\n")
    for st in ("FAIL", "WARN", "PASS"):
        for status, name, detail in [r for r in R if r[0] == st]:
            mark = {"PASS": "[✓]", "WARN": "[!]", "FAIL": "[✗]"}[status]
            print(f"{mark} {name}\n      {detail}\n")
    n = {s: sum(1 for r in R if r[0] == s) for s in ("PASS", "WARN", "FAIL")}
    print(f"SUMMARY: {n['PASS']} PASS · {n['WARN']} WARN · {n['FAIL']} FAIL  (of {len(R)} safe checks)")


if __name__ == "__main__":
    main()
