"""Export the audited forecast engine's prepared inputs for the browser estimator.

Imports analysis/policy_paper_ro/audit_forecast.py UNCHANGED and calls its own
prepare_workload() (same calendar, shapes, 2,000 triangular draws, seed 20261121).
Only the output folder of the engine's side-effect CSVs is redirected to a scratch
copy, so analysis/policy_paper_ro/audit_data/ is never written; the scratch CSVs are
then compared byte-for-byte with the published ones (proof that this is the same run).

The browser does not receive 2000 x 590 matrices. Every workload component of the
engine is a per-draw scalar times a date vector (or, for the recurring flow, a
per-draw scalar, two date vectors and (1+g)**t), so we ship the 16 parameter
columns plus the engine's own date vectors; engine.js rebuilds every component in
the engine's order of operations (float64).

Run (from anywhere):
  S:\\Projects\\SOLOResearch\\venv\\Scripts\\python.exe -X utf8 -B site/site_export.py
Writes site/data/engine_inputs.json, site/data/engine_inputs.js (same object, for
file:// use), site/data/report_refs.json/.js (claims, backtests, published outputs).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
PP = REPO / "analysis" / "policy_paper_ro"
if not (PP / "audit_forecast.py").exists():  # fallback: research working copy
    PP = Path(r"S:\Projects\SOLOResearch\analysis\policy_paper_ro")
sys.path.insert(0, str(PP))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import audit_forecast as AF  # noqa: E402

DATA = SITE / "data"
SIDE_EFFECT_CSVS = ["forecast_capacity_backtest.csv", "forecast_monthly_profile.csv",
                    "forecast_demand_check.csv", "forecast_inputs.csv", "capital_grid.csv"]
CLAIMS = ["C42", "C43", "C44", "C52", "C53", "C54", "C59", "C60", "C61", "C62", "C63",
          "C70", "C94", "C95", "C96", "C97"]
GITHUB = "https://github.com/Stefatorus/onrc-analiza-big-data-amanari"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(d: Path) -> dict:
    return {p.name: sha256(p) for p in sorted(d.glob("*")) if p.is_file()}


def load_model():
    """Call the engine's prepare_workload() with its CSV side effects sent to a scratch dir."""
    real_out = AF.OUT
    before = tree_hash(real_out)
    scratch = Path(tempfile.mkdtemp(prefix="onrc_site_export_"))
    for f in ("national.json", "finance_sources.json"):
        shutil.copy2(real_out / f, scratch / f)
    AF.OUT = scratch
    try:
        m = AF.prepare_workload()
    finally:
        AF.OUT = real_out
    identical = {f: sha256(scratch / f) == sha256(real_out / f) for f in SIDE_EFFECT_CSVS}
    after = tree_hash(real_out)
    assert before == after, "audit_data changed (must never happen)"
    shutil.rmtree(scratch, ignore_errors=True)
    return m, identical


def engine_vectors(m, dp):
    """Recreate, with the engine's own functions, the date vectors used inside prepare_workload."""
    dates, calendar = m["dates"], m["calendar"]
    opening = m["opening"]
    n = len(dates)
    seasonal, weekday, closed_ratio, _ = dp
    propensity = np.where(opening[:n], weekday.reindex(dates.dayofweek).fillna(0.), closed_ratio)
    month = dates.to_period("M")
    weights = pd.Series(propensity, index=dates)
    monthly_weight = weights.groupby(month).transform("sum")
    monthly_open = pd.Series(opening[:n], index=dates).groupby(month).transform("sum")
    recurring_weight = (weights * monthly_open / monthly_weight).to_numpy()
    vec = dict(
        seasonal=seasonal.reindex(dates.month).to_numpy(),
        recurring_weight=recurring_weight,
        forecast_offset=(dates - AF.START).days.to_numpy() / 365.2425,
        caen_shape=AF.daily_profile(dates, propensity, "2027-01-04", "2027-04-29", "2027-04-01", 2.3),
        early_shape=AF.daily_profile(dates, propensity, "2026-11-19", "2027-01-07", "2026-12-30", 1.8),
        capital_shape=AF.daily_profile(dates, propensity, "2027-08-27", "2028-01-08", "2027-12-17", 2.3),
        stagger_shape=m["stagger_shape"],
        defensive_shape=AF.daily_profile(dates, propensity, "2026-12-07", "2027-12-31"),
        anaf_shape=AF.daily_profile(dates, propensity, "2027-02-01", AF.HORIZON),
    )
    return vec


def rebuild_check(m, vec):
    """Rebuild every engine component from (params, vectors) exactly as engine.js does; must be bit-identical."""
    p = {k: m["params"][k].to_numpy()[:, None] for k in m["params"]}
    recurring = (p["flux_zilnic_recurent"] * vec["seasonal"] * vec["recurring_weight"]
                 * (1 + p["crestere_anuala_flux"]) ** vec["forecast_offset"])
    caen = p["dosare_caen_suplimentare"] * vec["caen_shape"] * p["efort_caen"]
    early = p["populatie_capital"] * p["proportie_reducere"] * p["efort_capital"] * vec["early_shape"]
    cw = ((p["populatie_capital"] * (1 - p["proportie_reducere"]))
          * p["conformare_ulterioara"] * p["depuneri_separate_ulterioare"] * p["efort_capital"])
    late = cw * vec["capital_shape"]
    defensive = p["dosare_defensive"] * vec["defensive_shape"] * .95
    dissolve = p["cazuri_anaf"] * p["fractie_anaf_capacitate_comuna"] * p["efort_anaf"] * vec["anaf_shape"]
    ordinary = recurring + early + defensive + dissolve
    avg = 1 - p["pondere_caen_iesiri"] * (1 - p["efort_caen"])
    capacity = p["rezolvari_observate_pe_zi"] * avg * m["opening"]
    initial = p["stoc_initial"] * avg
    pairs = dict(caen=(caen, m["caen"]), early=(early, m["early"]), late=(late, m["late"]),
                 capital_work=(cw, m["capital_work"]), defensive=(defensive, m["defensive"]),
                 dissolve=(dissolve, m["dissolve"]), ordinary=(ordinary, m["ordinary"]),
                 capacity=(capacity, m["capacity"]), initial=(initial, m["initial"]))
    return {k: bool(np.array_equal(a, b)) for k, (a, b) in pairs.items()}


def report_refs():
    """Claims and published outputs the site cites (read, never recomputed here)."""
    ia = REPO / "independent_audit" / "out"
    reg = pd.read_csv(REPO / "analysis" / "raport_executiv_2026-11" / "claims_registry.csv")
    claims = []
    for _, r in reg[reg.id.isin(CLAIMS)].iterrows():
        claims.append({k: (None if pd.isna(r[k]) else str(r[k])) for k in
                       ["id", "text", "value", "unit", "level", "status", "source", "script",
                        "data_sha256", "data_date", "rezerva_obligatorie", "public_ro"]})
    bt = json.loads((ia / "backtest_queue_mechanics.json").read_text(encoding="utf-8"))
    cap_bt = pd.read_csv(PP / "audit_data" / "forecast_capacity_backtest.csv")
    files = {
        "independent_audit/out/backtest_queue_mechanics.json": ia / "backtest_queue_mechanics.json",
        "analysis/policy_paper_ro/audit_data/forecast_capacity_backtest.csv": PP / "audit_data" / "forecast_capacity_backtest.csv",
        "independent_audit/out/forecast_grid.json": ia / "forecast_grid.json",
        "independent_audit/out/forecast_caen_compliance.json": ia / "forecast_caen_compliance.json",
        "analysis/policy_paper_ro/audit_data/oug_2026/scenarios.csv": PP / "audit_data" / "oug_2026" / "scenarios.csv",
        "analysis/policy_paper_ro/audit_data/solutions_feasibility_and_simulations.csv": PP / "audit_data" / "solutions_feasibility_and_simulations.csv",
        "analysis/raport_executiv_2026-11/claims_registry.csv": REPO / "analysis" / "raport_executiv_2026-11" / "claims_registry.csv",
    }
    return dict(claims=claims, backtest_queue=bt,
                backtest_capacity=json.loads(cap_bt.to_json(orient="records")),
                file_sha256={k: sha256(v) for k, v in files.items()})


def main():
    # demand_profile() is deterministic and only reads master_stats; call it once more for the
    # vectors that prepare_workload keeps local (its CSV side effect goes to the scratch dir too).
    m, identical = load_model()
    scratch = Path(tempfile.mkdtemp(prefix="onrc_site_export_dp_"))
    real_out = AF.OUT
    AF.OUT = scratch
    try:
        dp = AF.demand_profile()
    finally:
        AF.OUT = real_out
        shutil.rmtree(scratch, ignore_errors=True)
    vec = engine_vectors(m, dp)
    rebuilt = rebuild_check(m, vec)
    assert all(rebuilt.values()), rebuilt

    cal, dates = m["calendar"], m["dates"]
    cap_mean = float(m["capacity"].mean())       # cross-draw aggregate used by package P5 (triage +2%)
    params = m["params"]
    out = dict(
        _meta=("Intrările pregătite de motorul verificat audit_forecast.py (prepare_workload, nemodificat): "
               "calendar, vectori de formă, 2.000 de variante (triunghiulare, seed 20261121). "
               "engine.js reconstruiește fiecare componentă în ordinea de calcul a motorului."),
        engine_file=str((PP / "audit_forecast.py").relative_to(REPO)) if PP.is_relative_to(REPO) else str(PP / "audit_forecast.py"),
        engine_sha256=sha256(PP / "audit_forecast.py"),
        start=str(AF.START.date()), horizon=str(AF.HORIZON.date()),
        calendar_end=str(cal[-1].date()), n_calendar=len(cal), n_dates=len(dates),
        seed=20261121, n_draws=int(len(params)),
        opening=[int(x) for x in m["opening"]],
        vectors={k: [float(x) for x in v] for k, v in vec.items()},
        param_names=list(params.columns),
        params={k: [float(x) for x in params[k].to_numpy()] for k in params.columns},
        bounds=json.loads(pd.read_csv(PP / "audit_data" / "forecast_inputs.csv", index_col=0)
                          .rename(columns=str).to_json(orient="index")),
        constants=dict(mj_caen_remaining=AF.MINISTRY_NOTE["caen_remaining_expected"],
                       capacity_mean_all=cap_mean, triage_units=0.02 * cap_mean,
                       oug_end="2028-01-08", default_policy_start="2027-01-04",
                       art3_lag_days=15, staff_lag_days=56, ramp_workdays=20,
                       units_per_fte=25, caen_auto_share=0.75),
        checks=dict(side_effect_csvs_identical_to_published=identical, rebuilt_components_bit_identical=rebuilt,
                    validation_initial_bridge=m["validation"]["initial_stock_bridge"],
                    recent_resolutions_per_workday=m["validation"]["recent_resolutions_per_workday"]),
        input_sha256={
            "analysis_decisions.pkl (BERC archive)": sha256(AF.ARCHIVE),
            "analysis/master_stats/daily_solved_and_inflow.csv": sha256(PP.parent / "master_stats" / "daily_solved_and_inflow.csv"),
            "analysis/policy_paper_ro/audit_data/national.json": sha256(PP / "audit_data" / "national.json"),
            "analysis/policy_paper_ro/audit_data/finance_sources.json": sha256(PP / "audit_data" / "finance_sources.json"),
        },
    )
    DATA.mkdir(exist_ok=True)
    txt = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    (DATA / "engine_inputs.json").write_text(txt, encoding="utf-8")
    (DATA / "engine_inputs.js").write_text("window.ONRC_INPUTS=" + txt + ";\n", encoding="utf-8")
    refs = report_refs()
    refs["engine_inputs_sha256"] = sha256(DATA / "engine_inputs.json")
    rtxt = json.dumps(refs, ensure_ascii=False, separators=(",", ":"))
    (DATA / "report_refs.json").write_text(rtxt, encoding="utf-8")
    (DATA / "report_refs.js").write_text("window.ONRC_REFS=" + rtxt + ";\n", encoding="utf-8")
    print("side-effect CSVs identical to published:", identical)
    print("rebuilt components bit-identical:", rebuilt)
    print(f"engine_inputs.json {len(txt)/1e6:.2f} MB, sha256 {refs['engine_inputs_sha256']}")


if __name__ == "__main__":
    main()
