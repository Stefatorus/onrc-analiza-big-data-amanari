"""Verify the browser engine (js/engine.js, run in Node) against the audited Python engine.

Three layers, all on the same 2,000 draws (seed 20261121):
  A. PUBLISHED: the original scripts' own expressions (audit_oug.py, steelman_and_solutions_engine.py,
     forecast_grid.py, forecast_caen_compliance.py), run on audit_forecast.prepare_workload() + simulate(),
     must reproduce the published files (scenarios.csv, solutions CSV, forecast_grid.json,
     forecast_caen_compliance.json).
  B. REFERENCE: one general lever function in Python (numpy, engine matrices, engine simulate) for every
     lever setting; at the named settings it must equal layer A.
  C. JS: js/engine.js on the same settings; compared to B on p10/p50/p90 at 30.06.2027, peak and
     30.06.2028, the full weekly (Monday) paths of wait and stock, and the paired gains. Required: |diff| <= 0.5 day.
Then the claims (registry values) are checked against the JS values.

Run:  S:\\Projects\\SOLOResearch\\venv\\Scripts\\python.exe -X utf8 -B site/verify_js_vs_py.py
Writes site/verification.json and site/data/verification.js. Never writes outside site/.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))
from site_export import AF, PP, REPO, load_model, sha256  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

TOL = 0.5
MJ = AF.MINISTRY_NOTE["caen_remaining_expected"]
VARIANTS = {"none": (0, 0, 0.), "redus": (5, 20, 0.), "central": (15, 25, .25), "ridicat": (30, 30, .5)}
DEFAULTS = dict(in_pct=0, cap_pct=0, caen="motor", caen_auto=False, caen_auto_share=0.75, stagger=False,
                oug="none", oug_extended=False, art3=None, staff_fte=0, triage=False, start="2027-01-04")
NO_MEASURES = dict(caen_auto=False, stagger=False, oug="none", oug_extended=False, art3=None, staff_fte=0, triage=False)


# ----------------------------------------------------------------------------- statistics (engine definitions)
def stats(m, stock, cal, base=None):
    dates = m["dates"]
    mondays = np.flatnonzero(dates.dayofweek == 0)
    j27 = dates.get_loc(pd.Timestamp("2027-06-30"))
    j28 = len(dates) - 1
    fin = lambda a: np.where(np.isfinite(a), a, np.nan)   # censored (inf / inf-inf) -> nan, as JS null
    q = lambda v: [float(x) for x in fin(np.quantile(v, [.1, .5, .9]))]
    out = dict(weekly_dates=[str(d.date()) for d in dates[mondays]],
               wait_weekly=fin(np.quantile(cal[:, mondays], [.1, .5, .9], axis=0)).T.tolist(),
               stock_weekly=np.quantile(stock[:, mondays], [.1, .5, .9], axis=0).T.tolist(),
               mid2027=q(cal[:, j27]), peak=q(cal.max(axis=1)), june2028=q(cal[:, j28]),
               le3_june2028=float(np.mean(cal[:, j28] <= 3)),
               stock_june2028=q(stock[:, j28]), stock_mid2027=q(stock[:, j27]))
    if base is not None:
        bcal = base
        g = lambda a, b: float(np.median(a - b)) if np.isfinite(a).all() and np.isfinite(b).all() else float("nan")
        out["gain_june2028"] = g(bcal[:, j28], cal[:, j28])
        out["gain_mid2027"] = g(bcal[:, j27], cal[:, j27])
        out["gain_peak"] = g(bcal.max(axis=1), cal.max(axis=1))
    return out


def lindley_stock(initial, inflow, capacity):
    """Copy of the first loop of AF.simulate, used only when the engine raises (file not served in calendar)."""
    stock = np.empty_like(inflow)
    prev = initial.reshape(-1)
    for i in range(inflow.shape[1]):
        prev = np.maximum(0., prev + inflow[:, i] - capacity[:, i])
        stock[:, i] = prev
    return stock


def sim(m, inflow, cap):
    try:
        stock, cal, _ = AF.simulate(m["initial"], inflow, cap, m["opening"])
        return stock, cal, False
    except ValueError:
        return lindley_stock(m["initial"], inflow, cap), None, True


def simulate_censored(initial, inflow, capacity, opening):
    """Non-raising copy of AF.simulate: files not served inside the calendar get an infinite wait.
    Used only for settings where the engine raises, to compare the finite quantiles with JS."""
    stock = lindley_stock(initial, inflow, capacity)
    cum = capacity.cumsum(axis=1)
    n = inflow.shape[1]
    needed = cum[:, :n] + stock + 1.
    resolution = np.stack([np.searchsorted(c, t, side="left") for c, t in zip(cum, needed)])
    wait = (resolution - np.arange(n)).astype(float)
    wait[resolution >= capacity.shape[1]] = np.inf
    return stock, wait


# ----------------------------------------------------------------------------- B. general reference (numpy)
def reference_arrays(m, s):
    s = {**DEFAULTS, **s}
    cal, dates, open_ = m["calendar"], m["dates"], m["opening"]
    n = len(dates)
    start = pd.Timestamp(s["start"])
    after = cal >= start
    perm = cal >= start + pd.Timedelta(days=15)
    staff = cal >= start + pd.Timedelta(days=56)
    temp = after if s["oug_extended"] else after & (cal <= "2028-01-08")
    ramp = np.where(temp, np.where(np.cumsum(temp & open_) <= 20, .5, 1.), 0.)
    fte, units, art3_default = VARIANTS[s["oug"]]
    art3 = art3_default if s["art3"] is None else s["art3"]
    triage = 0.02 * m["capacity"].mean() if s["triage"] else 0.
    capacity = (m["capacity"] * (1 + s["cap_pct"] / 100)
                + (fte * units * ramp + s["staff_fte"] * 25 * staff + triage * after) * open_)
    if s["caen"] == "motor":
        caen = m["caen"]
    else:
        caen = m["caen"] * (float(s["caen"]) * MJ / m["params"]["dosare_caen_suplimentare"].to_numpy()[:, None])
    auto = s["caen_auto_share"] if s["caen_auto"] else 0.
    caen = caen * (1 - auto * after[:n])
    capital = m["capital_work"] * m["stagger_shape"] if s["stagger"] else m["late"]
    inflow = (m["ordinary"] + caen + capital - art3 * m["dissolve"] * perm[:n]) * (1 + s["in_pct"] / 100)
    return inflow, capacity


def reference(m, s):
    inflow, cap = reference_arrays(m, s)
    stock, cal, beyond = sim(m, inflow, cap)
    b_in, b_cap = reference_arrays(m, {**s, **NO_MEASURES})
    _, bcal, bbeyond = sim(m, b_in, b_cap)
    if beyond:
        stock, cal = simulate_censored(m["initial"], inflow, cap, m["opening"])
    if bbeyond:
        _, bcal = simulate_censored(m["initial"], b_in, b_cap, m["opening"])
    return dict(beyond=beyond, censored_cells=int(np.isinf(cal).sum()), **stats(m, stock, cal, bcal)), (stock, cal)


# ----------------------------------------------------------------------------- A. published expressions (verbatim)
def published_cases(m):
    """Inflow/capacity exactly as written in the original scripts, for their named scenarios."""
    dates, calendar, open_ = m["dates"], m["calendar"], m["opening"]
    n = len(dates)
    temp, after = m["temporary"], m["after_policy"]
    base, init = m["capacity"], m["initial"]
    cases = {}
    # audit_oug.py test_draft()
    ramp = np.where(temp, np.where(np.cumsum(temp & open_) <= 20, .5, 1.), 0.)
    permanent = calendar >= "2027-01-19"
    reform = calendar >= "2027-01-04"
    base_in = m["ordinary"] + m["caen"] + m["late"]
    for label, fte, output, transfer, digital, stagger in [
            ("referinta", 0, 0, 0, False, False), ("oug_redus", 5, 20, 0, False, False),
            ("oug_central", 15, 25, .25, False, False), ("oug_ridicat", 30, 30, .50, False, False),
            ("doar_art_iii", 0, 0, .25, False, False), ("oug_esalonare", 15, 25, .25, False, True)]:
        capacity = base * (1 + int(digital) * .04 * reform) + fte * output * ramp * open_
        activity = base_in - (transfer * m["dissolve"] * permanent[:n])
        if stagger:
            activity = activity - m["late"] + m["capital_work"] * m["stagger_shape"]
        cases["oug:" + label] = (activity, capacity)
    # steelman_and_solutions_engine.py build_solutions_feasibility() P0, P2–P5
    ramp_after = np.where(after, np.where(np.cumsum(after & open_) <= 20, 0.5, 1.0), 0.0)
    perm19 = calendar >= "2027-01-19"
    cases["sol:P0"] = (base_in, base)
    cases["sol:P2"] = (base_in - 0.25 * m["dissolve"] * perm19[:n], base + 375.0 * ramp * open_)
    cases["sol:P3"] = (base_in - 0.30 * m["dissolve"] * perm19[:n],
                       base + (375.0 * ramp_after + 375.0 * (calendar >= "2027-03-01")) * open_)
    cases["sol:P4"] = (m["ordinary"] + m["caen"] * (1.0 - 0.75 * after[:n]) + m["capital_work"] * m["stagger_shape"], base)
    cases["sol:P5"] = (m["ordinary"] + m["caen"] * (1.0 - 0.75 * after[:n]) + m["capital_work"] * m["stagger_shape"]
                       - 0.30 * m["dissolve"] * perm19[:n],
                       base + (375.0 * ramp_after + 0.02 * base.mean() * after) * open_)
    # forecast_grid.py
    g_in = m["ordinary"] + m["late"] + m["caen"]
    for di in [-20, -10, 0, 10, 20, 30]:
        for do in [-10, 0, 10, 20, 30, 40]:
            cases[f"grid:{di}:{do}"] = (g_in * (1 + di / 100), base * (1 + do / 100))
    # forecast_caen_compliance.py
    wave = m["params"]["dosare_caen_suplimentare"].to_numpy()[:, None]
    aft = (dates >= "2027-01-04")[None, :]
    for sh, auto in [(0.5, 0.), (0.8, 0.), (1.0, 0.), (0.5, .75), (0.8, .75), (1.0, .75)]:
        caen = m["caen"] * (sh * MJ / wave)
        caen = caen * (1 - auto * aft)
        cases[f"caen:{sh}:{auto}"] = (m["ordinary"] + m["late"] + caen, base)
    return cases


PUBLISHED_TO_SETTINGS = {
    "oug:referinta": {}, "oug:oug_redus": {"oug": "redus"}, "oug:oug_central": {"oug": "central"},
    "oug:oug_ridicat": {"oug": "ridicat"}, "oug:doar_art_iii": {"art3": 0.25},
    "oug:oug_esalonare": {"oug": "central", "stagger": True},
    "sol:P0": {}, "sol:P2": {"oug": "central"},
    "sol:P3": {"oug": "central", "oug_extended": True, "art3": 0.30, "staff_fte": 15},
    "sol:P4": {"caen_auto": True, "stagger": True},
    "sol:P5": {"oug": "central", "oug_extended": True, "art3": 0.30, "caen_auto": True, "stagger": True, "triage": True},
}
for _di in [-20, -10, 0, 10, 20, 30]:
    for _do in [-10, 0, 10, 20, 30, 40]:
        PUBLISHED_TO_SETTINGS[f"grid:{_di}:{_do}"] = {"in_pct": _di, "cap_pct": _do}
for _sh, _a in [(0.5, 0.), (0.8, 0.), (1.0, 0.), (0.5, .75), (0.8, .75), (1.0, .75)]:
    PUBLISHED_TO_SETTINGS[f"caen:{_sh}:{_a}"] = {"caen": _sh, "caen_auto": _a > 0}


def published_files_check(m, cases):
    """Layer A: the verbatim expressions reproduce the published output files."""
    rows = []
    ia = REPO / "independent_audit" / "out"
    j27 = m["dates"].get_loc(pd.Timestamp("2027-06-30"))
    sc = pd.read_csv(PP / "audit_data" / "oug_2026" / "scenarios.csv").set_index(["scenario", "period"])
    sol = pd.read_csv(PP / "audit_data" / "solutions_feasibility_and_simulations.csv").set_index("id")
    grid = {(c["d_in"], c["d_out"]): c for c in json.loads((ia / "forecast_grid.json").read_text(encoding="utf-8"))["cells"]}
    comp = json.loads((ia / "forecast_caen_compliance.json").read_text(encoding="utf-8"))["scenarios"]
    sims = {}
    for key, (inflow, cap) in cases.items():
        sims[key] = sim(m, inflow, cap)

    def add(source, case, metric, published, computed):
        ok = (published is None and computed is None) or (
            published is not None and computed is not None and abs(published - computed) <= 1e-3 + 5e-5 * abs(published))
        rows.append(dict(source=source, case=case, metric=metric, published=published, computed=computed, ok=bool(ok)))

    ref_cal = sims["oug:referinta"][1]
    for key in [k for k in cases if k.startswith("oug:")]:
        label = key[4:]
        _, cal, _ = sims[key]
        for period, v, b in [("2027-06-30", cal[:, j27], ref_cal[:, j27]), ("2028-06-30", cal[:, -1], ref_cal[:, -1]),
                             ("peak", cal.max(axis=1), ref_cal.max(axis=1))]:
            r = sc.loc[(label, period)]
            for name, val in zip(["p10", "median", "p90"], np.quantile(v, [.1, .5, .9])):
                add("audit_data/oug_2026/scenarios.csv", label, f"{period} {name}", float(r[name]), float(val))
            add("audit_data/oug_2026/scenarios.csv", label, f"{period} median_saved", float(r["median_saved"]), float(np.median(b - v)))
    sq = sims["sol:P0"][1]
    for key in [k for k in cases if k.startswith("sol:")]:
        pid = key[4:]
        st, cal, _ = sims[key]
        r = sol.loc[pid]
        for name, val in [("wait_jun28_p10", np.quantile(cal[:, -1], .1)), ("wait_jun28_p50", np.median(cal[:, -1])),
                          ("wait_jun28_p90", np.quantile(cal[:, -1], .9)), ("peak_p50", np.median(cal.max(axis=1))),
                          ("days_saved_jun28_med", np.median(sq[:, -1] - cal[:, -1]))]:
            add("audit_data/solutions_feasibility_and_simulations.csv", pid, name, float(r[name]), round(float(val), 1))
    for key in [k for k in cases if k.startswith("grid:")]:
        _, di, do = key.split(":")
        c = grid[(int(di), int(do))]
        st, cal, beyond = sims[key]
        if c["beyond_horizon"] or beyond:
            add("independent_audit/out/forecast_grid.json", f"in {di}% / cap {do}%", "beyond_horizon",
                1.0 if c["beyond_horizon"] else 0.0, 1.0 if beyond else 0.0)
            continue
        jq = np.percentile(cal[:, -1], [10, 50, 90]); pq = np.percentile(cal.max(axis=1), [10, 50, 90])
        for name, val in zip(["june2028_p10", "june2028_p50", "june2028_p90", "peak_p10", "peak_p50", "peak_p90"], [*jq, *pq]):
            add("independent_audit/out/forecast_grid.json", f"in {di}% / cap {do}%", name, float(c[name]), float(val))
    for r in comp:
        if r["pondere"] == "motor (140–390 mii)":
            continue
        key = f"caen:{r['pondere']}:{r['automatizare_caen']}"
        _, cal, _ = sims[key]
        for per, v in [("iun2027", cal[:, j27]), ("varf", cal.max(axis=1)), ("iun2028", cal[:, -1])]:
            for name, val, pub in zip(["p10", "p50", "p90"], np.percentile(v, [10, 50, 90]), r[per]):
                add("independent_audit/out/forecast_caen_compliance.json", f"CAEN {r['pondere']} auto {r['automatizare_caen']}",
                    f"{per} {name}", float(pub), float(val))
    return rows, sims


# ----------------------------------------------------------------------------- settings grid
def settings_grid():
    g = []
    named = [
        ("Status quo / referință (C42, C59, C60, C62)", {}),
        ("OUG, livrare redusă (C61)", {"oug": "redus"}),
        ("OUG, varianta centrală (C43)", {"oug": "central"}),
        ("OUG, livrare ridicată (C61)", {"oug": "ridicat"}),
        ("Doar Art. III (C44)", {"art3": 0.25}),
        ("OUG + eșalonare capital", {"oug": "central", "stagger": True}),
        ("Pachet P3 (C52)", PUBLISHED_TO_SETTINGS["sol:P3"]),
        ("Pachet P4 (C53)", PUBLISHED_TO_SETTINGS["sol:P4"]),
        ("Pachet P5 (C54)", PUBLISHED_TO_SETTINGS["sol:P5"]),
    ]
    for name, s in named:
        g.append(dict(name=name, settings=s, group="scenarii numite"))
    for di in [-20, -10, 0, 10, 20, 30]:
        for do in [-10, 0, 10, 20, 30, 40]:
            if di == 0 and do == 0:
                continue
            g.append(dict(name=f"Grilă: cereri {di:+d}%, capacitate {do:+d}%" + (" (C63)" if di == 0 and do in (-10, 10) else ""),
                          settings={"in_pct": di, "cap_pct": do}, group="grila C63"))
    for sh in [0.5, 0.8, 1.0]:
        g.append(dict(name=f"Val CAEN {int(sh*100)}% din cifra MJ (C94)", settings={"caen": sh}, group="CAEN C94/C95"))
        g.append(dict(name=f"Val CAEN {int(sh*100)}% + conversie automată (C95)", settings={"caen": sh, "caen_auto": True}, group="CAEN C94/C95"))
    combos = [
        ("Fără val CAEN", {"caen": 0}),
        ("Conversie CAEN singură", {"caen_auto": True}),
        ("Conversie CAEN de la 01.03.2027", {"caen_auto": True, "start": "2027-03-01"}),
        ("OUG central, start 07.12.2026", {"oug": "central", "start": "2026-12-07"}),
        ("OUG central, start 07.06.2027", {"oug": "central", "start": "2027-06-07"}),
        ("OUG central prelungit, start 04.10.2027", {"oug": "central", "oug_extended": True, "start": "2027-10-04"}),
        ("+40 FTE (fără OUG)", {"staff_fte": 40}),
        ("+40 FTE, cereri +10%, capacitate −5%", {"staff_fte": 40, "in_pct": 10, "cap_pct": -5}),
        ("Triaj singur", {"triage": True}),
        ("OUG ridicat prelungit + 60 FTE + CAEN 100% cu conversie", {"oug": "ridicat", "oug_extended": True, "staff_fte": 60, "caen": 1.0, "caen_auto": True}),
        ("P5 cu cereri −15%", {**PUBLISHED_TO_SETTINGS["sol:P5"], "in_pct": -15}),
        ("P5 cu capacitate −20%, CAEN 80%", {**PUBLISHED_TO_SETTINGS["sol:P5"], "cap_pct": -20, "caen": 0.8}),
        ("Toate măsurile, start 01.02.2027, cereri +5%", {"oug": "central", "oug_extended": True, "caen_auto": True, "stagger": True,
                                                         "staff_fte": 30, "triage": True, "start": "2027-02-01", "in_pct": 5}),
        ("Colț extrem: cereri −30%, capacitate +40%", {"in_pct": -30, "cap_pct": 40}),
        ("Peste orizont: cereri +30%, capacitate −30%", {"in_pct": 30, "cap_pct": -30}),
        ("Capacitate −25%", {"cap_pct": -25}),
        ("Parțial peste orizont: cereri +20%, capacitate −20%", {"in_pct": 20, "cap_pct": -20}),
        ("Cereri +10%, capacitate −25%, cu OUG central", {"in_pct": 10, "cap_pct": -25, "oug": "central"}),
        ("Parțial peste orizont: cereri +30%, capacitate −20%", {"in_pct": 30, "cap_pct": -20}),
        ("Cereri +25%, capacitate −25%, cu P5", {**PUBLISHED_TO_SETTINGS["sol:P5"], "in_pct": 25, "cap_pct": -25}),
        ("Capacitate −30%, cu OUG central", {"cap_pct": -30, "oug": "central"}),
    ]
    for name, s in combos:
        g.append(dict(name=name, settings=s, group="combinații"))
    return g


def run_js(cases):
    tmp = Path(tempfile.mkdtemp(prefix="onrc_verify_"))
    (tmp / "settings.json").write_text(json.dumps(cases), encoding="utf-8")
    t0 = time.time()
    subprocess.run(["node", str(SITE / "js" / "verify_node.js"), str(SITE / "data" / "engine_inputs.json"),
                    str(tmp / "settings.json"), str(tmp / "out.json")], check=True)
    out = json.loads((tmp / "out.json").read_text(encoding="utf-8"))
    node_v = subprocess.run(["node", "-v"], capture_output=True, text=True).stdout.strip()
    return out, node_v, time.time() - t0


def maxdiff(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if a.shape != b.shape:
        return float("inf")
    both_nan = np.isnan(a) & np.isnan(b)
    d = np.abs(a - b)
    d[both_nan] = 0
    return float(np.nanmax(d)) if d.size else 0.0


CLAIM_CHECKS = [  # claim id, case name, metric, expected (registry value, as numbers), label
    ("C42", "Status quo / referință (C42, C59, C60, C62)", "june2028", [74, 136, 214], "iunie 2028, p10 / mediană / p90"),
    ("C59", "Status quo / referință (C42, C59, C60, C62)", "mid2027", [105, 138, 175], "30.06.2027, p10 / mediană / p90"),
    ("C60", "Status quo / referință (C42, C59, C60, C62)", "peak", [124, 165, 220], "vârf, p10 / mediană / p90"),
    ("C62", "Status quo / referință (C42, C59, C60, C62)", "stock_june2028_p50", [395000], "stoc 30.06.2028, mediană (rotunjit la mii)"),
    ("C43", "OUG, varianta centrală (C43)", "june2028", [41, 102, 172], "iunie 2028, p10 / mediană / p90"),
    ("C43", "OUG, varianta centrală (C43)", "gain_june2028", [34], "câștig median pe aceleași simulări"),
    ("C44", "Doar Art. III (C44)", "gain_june2028", [2], "câștig median pe aceleași simulări"),
    ("C61", "OUG, livrare redusă (C61)", "june2028", [66, 126, 203], "slab: iunie 2028"),
    ("C61", "OUG, livrare redusă (C61)", "gain_june2028", [8], "slab: câștig"),
    ("C61", "OUG, livrare ridicată (C61)", "june2028", [3, 56, 122], "ridicat: iunie 2028 (p10 «≤3»)"),
    ("C61", "OUG, livrare ridicată (C61)", "gain_june2028", [79], "ridicat: câștig"),
    ("C63", "Grilă: cereri +0%, capacitate +10% (C63)", "june2028_p50", [73], "capacitate +10%: mediana iunie 2028"),
    ("C63", "Grilă: cereri +0%, capacitate -10% (C63)", "june2028_p50", [222], "capacitate −10%: mediana iunie 2028"),
    ("C94", "Val CAEN 50% din cifra MJ (C94)", "mid2027_p50", [196], "50%: mediana 30.06.2027"),
    ("C94", "Val CAEN 80% din cifra MJ (C94)", "mid2027_p50", [274], "80%: mediana 30.06.2027"),
    ("C94", "Val CAEN 100% din cifra MJ (C94)", "mid2027_p50", [328], "100%: mediana 30.06.2027"),
    ("C95", "Val CAEN 80% + conversie automată (C95)", "mid2027_p50", [114], "80% + conversie: mediana 30.06.2027"),
    ("C95", "Val CAEN 100% + conversie automată (C95)", "mid2027_p50", [127], "100% + conversie: mediana 30.06.2027"),
    ("C52", "Pachet P3 (C52)", "june2028", [3, 38, 94], "P3: iunie 2028 (p10 «≤3»)"),
    ("C53", "Pachet P4 (C53)", "june2028", [20, 81, 147], "P4: iunie 2028"),
    ("C54", "Pachet P5 (C54)", "june2028", [3, 21, 81], "P5: iunie 2028 (p10 «≤3»)"),
]


def claim_value(res, metric):
    if metric in ("june2028", "mid2027", "peak"):
        return res[metric]
    if metric.endswith("_p50"):
        base = metric[:-4]
        return [res[base][1]] if base in res else None
    return [res[metric]]


def main():
    t_start = time.time()
    m, identical = load_model()
    cases_pub = published_cases(m)
    pub_rows, pub_sims = published_files_check(m, cases_pub)
    pub_ok = all(r["ok"] for r in pub_rows)

    # B == A at named settings (array level)
    ba_rows = []
    for key, s in PUBLISHED_TO_SETTINGS.items():
        inflow, cap = reference_arrays(m, s)
        a_in, a_cap = cases_pub[key]
        st_a, cal_a, by_a = pub_sims[key]
        st_b, cal_b, by_b = sim(m, inflow, cap)
        row = dict(case=key, settings=s, inflow_max_abs_diff=float(np.max(np.abs(inflow - a_in))),
                   capacity_max_abs_diff=float(np.max(np.abs(cap - a_cap))),
                   stock_max_abs_diff=float(np.max(np.abs(st_a - st_b))), beyond_same=bool(by_a == by_b))
        row["wait_cells_different"] = None if (by_a or by_b) else int(np.sum(cal_a != cal_b))
        ba_rows.append(row)
    ba_ok = all((r["wait_cells_different"] in (0, None)) and r["beyond_same"] for r in ba_rows)

    grid = settings_grid()
    js, node_v, js_secs = run_js([dict(name=c["name"], settings=c["settings"]) for c in grid])
    js_by = {c["name"]: c for c in js["cases"]}
    results, global_max = [], 0.0
    for c in grid:
        py, _ = reference(m, c["settings"])
        j = js_by[c["name"]]
        row = dict(name=c["name"], group=c["group"], settings=c["settings"], beyond_py=py["beyond"], beyond_js=j["beyond"] > 0,
                   js_ms=j["ms"])
        if True:  # censored settings too: compared on their finite quantiles and censored-cell counts
            diffs = {k: maxdiff(py[k], j[k]) for k in ["mid2027", "peak", "june2028", "wait_weekly"]}
            gains = {k: maxdiff([py.get(k, np.nan)], [j[k] if j[k] is not None else np.nan]) for k in ["gain_june2028", "gain_mid2027", "gain_peak"]}
            row.update(max_diff_days=max([*diffs.values(), *gains.values()]), diffs={**diffs, **gains},
                       max_diff_stock_weekly=maxdiff(py["stock_weekly"], j["stock_weekly"]),
                       max_rel_diff_stock=maxdiff(np.asarray(py["stock_weekly"]) / np.maximum(1, np.asarray(py["stock_weekly"])),
                                                  np.asarray(j["stock_weekly"], float) / np.maximum(1, np.asarray(py["stock_weekly"]))))
            row["ok"] = bool(row["max_diff_days"] <= TOL and (j["beyond"] > 0) == py["beyond"] and j["beyond"] == py["censored_cells"])
            row["censored_cells_py"] = py["censored_cells"]; row["censored_cells_js"] = j["beyond"]
            global_max = max(global_max, row["max_diff_days"])
            keep = ["mid2027", "peak", "june2028", "gain_june2028", "le3_june2028", "stock_june2028"]
            row["py"] = {k: py.get(k) for k in keep}
            row["js"] = {k: j.get(k) for k in keep}
            if c["group"] == "scenarii numite":
                row["weekly"] = dict(dates=py["weekly_dates"], py_p50=[w[1] for w in py["wait_weekly"]],
                                     js_p50=[w[1] for w in j["wait_weekly"]])
        results.append(row)

    claims = []
    reg = pd.read_csv(REPO / "analysis" / "raport_executiv_2026-11" / "claims_registry.csv").set_index("id")
    res_by = {r["name"]: r for r in results}
    for cid, case, metric, expected, label in CLAIM_CHECKS:
        jsres = js_by[case]
        jsres = {**jsres, "stock_june2028_p50": None}
        if metric == "stock_june2028_p50":
            val = [round(js_by[case]["stock_june2028"][1] / 1000) * 1000]
        else:
            val = claim_value(js_by[case], metric)
        ok = all(abs(v - e) <= TOL + (500 if metric.startswith("stock") else 0) or (e == 3 and v <= 3)
                 for v, e in zip(val, expected))
        claims.append(dict(claim=cid, scenario=case, what=label, registry_value=str(reg.loc[cid, "value"]),
                           registry_status=str(reg.loc[cid, "status"]), expected=expected, js_value=val, ok=bool(ok)))

    out = dict(
        _meta=("Verificare JS (js/engine.js în Node) vs. motorul Python verificat (audit_forecast.py), "
               "aceleași 2.000 de variante, seed 20261121. Toleranță cerută: 0,5 zile."),
        generated=time.strftime("%Y-%m-%d %H:%M"), node=node_v, numpy=np.__version__, pandas=pd.__version__,
        python=sys.version.split()[0], tolerance_days=TOL, n_settings=len(grid), n_draws=int(len(m["params"])),
        max_abs_diff_days=global_max, all_ok=bool(all(r["ok"] for r in results)),
        js_total_seconds=round(js_secs, 2), js_init_ms=js["init_ms"],
        engine_sha256=sha256(PP / "audit_forecast.py"),
        engine_inputs_sha256=sha256(SITE / "data" / "engine_inputs.json"),
        engine_js_sha256=sha256(SITE / "js" / "engine.js"),
        side_effect_csvs_identical=identical,
        published_check=dict(ok=pub_ok, n=len(pub_rows), rows=pub_rows),
        reference_equals_published=dict(ok=ba_ok, rows=ba_rows),
        results=results, claims=dict(ok=all(c["ok"] for c in claims), rows=claims),
        runtime_seconds=round(time.time() - t_start, 1),
    )
    def clean(o):  # strict JSON: NaN/inf (censored, undefined gains) -> null
        if isinstance(o, float):
            return o if np.isfinite(o) else None
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return o
    out = clean(out)
    txt = json.dumps(out, ensure_ascii=False, indent=1, default=float, allow_nan=False)
    (SITE / "verification.json").write_text(txt, encoding="utf-8")
    (SITE / "data" / "verification.js").write_text("window.ONRC_VERIFY=" + json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=float) + ";\n", encoding="utf-8")
    summ = dict(n_settings=len(grid), max_abs_diff_days=global_max, all_ok=out["all_ok"], claims_ok=out["claims"]["ok"],
                generated=out["generated"], engine_js_sha256=out["engine_js_sha256"])
    (SITE / "data" / "verify_summary.js").write_text("window.ONRC_VERIFY_SUMMARY=" + json.dumps(summ) + ";\n", encoding="utf-8")
    print(f"published files reproduced: {pub_ok} ({sum(r['ok'] for r in pub_rows)}/{len(pub_rows)})")
    for r in pub_rows:
        if not r["ok"]:
            print("  PUB MISMATCH", r)
    print(f"reference == published expressions: {ba_ok}")
    for r in ba_rows:
        if r["wait_cells_different"] or r["inflow_max_abs_diff"] or r["capacity_max_abs_diff"]:
            print("  B vs A", r["case"], r["inflow_max_abs_diff"], r["capacity_max_abs_diff"], r["stock_max_abs_diff"], r["wait_cells_different"])
    print(f"JS vs Python: {len(grid)} settings, max |diff| = {global_max} days, all ok = {out['all_ok']}")
    for r in results:
        flag = ("" if r["ok"] else "  <-- FAIL") + (f"  censored py/js {r.get('censored_cells_py')}/{r.get('censored_cells_js')}" if r["beyond_py"] else "")
        print(f"  {r['name'][:60]:60} diff={r['max_diff_days']}  stockdiff={r['max_diff_stock_weekly']:.3g} beyond py/js={r['beyond_py']}/{r['beyond_js']}{flag}")
    print(f"claims ok: {out['claims']['ok']}")
    for c in claims:
        print(f"  {c['claim']} {c['what']:45} registry {c['registry_value'][:40]:40} js {c['js_value']} {'OK' if c['ok'] else 'FAIL'}")


if __name__ == "__main__":
    main()
