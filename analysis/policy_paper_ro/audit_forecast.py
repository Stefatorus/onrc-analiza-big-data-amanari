"""Run conditional daily workload scenarios and publication-aware throughput backtests.

The modeled lead time is for one standard file placed at the end of the modeled
queue at the close of a date. It does not predict duration for a particular filing
or reproduce the median duration of decisions published on that date.
"""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import json
from pathlib import Path

from dateutil.easter import EASTER_ORTHODOX, easter
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


HERE = Path(__file__).resolve().parent
ARCHIVE = Path(str(config.BERC_PKL))
OUT = HERE / "audit_data"
START = pd.Timestamp("2026-11-19")
HORIZON = pd.Timestamp("2028-06-30")
KNOWN_THROUGH = pd.Timestamp("2026-11-17")
N_DRAWS = 2000
WEEK = pd.Timedelta(days=7)
DAY = pd.Timedelta(days=1)
SCENARIOS = {
    "continuitate": (0., 0., 0., False),
    "sprijin": (.12, 0., 0., False),
    "digital": (0., .04, .60, False),
    "combinat": (.12, .04, .60, True),
}
REPORT_DATES = ["2027-01-25", "2027-06-14", "2027-10-18", "2028-03-13",
                "2028-06-19", "2028-06-30"]
MINISTRY_NOTE = {
    "source": ("https://www.just.ro/wp-content/uploads/2026/11/"
               "NF-OUG-pentru-instituirea-unor-masuri-privind-activitatea-de-inregistrare-"
               "in-registrului-comertului-si-pentru-completarea-Legii-nr.-265-2022.docx"),
    "backlog_at": "2026-11-06",
    "backlog": 204414,
    "caen_remaining_expected": 902243,
    "capital_potential_candidates": 266381,
    "capital_increase_filings": 107904,
    "anaf_entities_without_dissolution_or_deregistration": 422093,
}


def workdays(days):
    """National standard work calendar, Art. 139 and Orthodox dates."""
    fixed = ("01-01", "01-02", "01-06", "01-07", "01-24", "05-01", "06-01",
             "08-15", "11-30", "12-01", "12-25", "12-26")
    holidays = []
    for year in sorted(set(days.year)):
        orthodox = pd.Timestamp(easter(int(year), EASTER_ORTHODOX))
        holidays.extend(pd.Timestamp(f"{year}-{code}") for code in fixed)
        holidays.extend(orthodox + pd.Timedelta(days=offset) for offset in (-2, 0, 1, 49, 50))
    return (days.dayofweek < 5) & ~days.isin(holidays)


def complete_dates(start, stop):
    days = pd.date_range(start, stop)
    return days[workdays(days)]


def final_records():
    raw = pd.read_pickle(ARCHIVE)
    valid = (
        raw.cat.isin(["CERERE265", "INMATRIC265"])
        & raw.sol.isin(["Admis", "Respins"])
        & raw.res.between("2026-01-01", KNOWN_THROUGH + DAY, inclusive="left")
    )
    return raw.loc[valid, ["res", "pub"]].assign(date=lambda d: d.res.dt.normalize())


def backtest_capacity(records):
    # Four full future weeks, unrelated to the data used in their respective fit.
    # Train using the publication timestamp at each historical cut, rather than
    # the retrospectively visible final decision count for recent training days.
    daily = records.groupby("date").size()
    rows = []
    details = []
    for origin in pd.date_range("2026-03-01", "2026-10-11", freq="4W-SUN"):
        target = complete_dates(origin + DAY, origin + 4 * WEEK)
        actual = daily.reindex(target, fill_value=0).mean()
        visible = records.loc[records.pub.lt(origin + DAY)].groupby("date").size()
        eligible = complete_dates("2026-01-01", origin)
        settings = {"ultimele_12_zile": eligible[-12:],
                    "ultimele_4_saptamani": eligible[eligible > origin - 4 * WEEK],
                    "ultimele_8_saptamani": eligible[eligible > origin - 8 * WEEK]}
        for model, dates in settings.items():
            pred = float(visible.reindex(dates, fill_value=0).mean())
            details.append(dict(origin=origin.date().isoformat(), test_start=target[0].date().isoformat(),
                                test_end=target[-1].date().isoformat(), test_workdays=len(target),
                                model=model, predicted_per_day=pred, observed_per_day=float(actual),
                                error_percent=100 * (actual / pred - 1)))
    table = pd.DataFrame(details)
    for name, g in table.groupby("model", sort=False):
        rows.append(dict(model=name, folds=int(len(g)),
                         mae_per_day=float((g.predicted_per_day - g.observed_per_day).abs().mean()),
                         mape_percent=float((100 * (g.predicted_per_day / g.observed_per_day - 1)).abs().mean()),
                         observed_vs_prediction_min=float(g.error_percent.min()),
                         observed_vs_prediction_max=float(g.error_percent.max())))
    table.to_csv(OUT / "forecast_capacity_backtest.csv", index=False, float_format="%.4f")
    latest = complete_dates("2026-11-02", KNOWN_THROUGH)
    actual_level = float(daily.reindex(latest, fill_value=0).mean())
    return actual_level, len(latest), rows


def demand_profile():
    # The archive counts earlier filings that eventually have a disposition.
    # Treat this as mature demand evidence. The profile does not isolate CAEN.
    d = pd.read_csv(HERE.parent / "master_stats" / "daily_solved_and_inflow.csv", parse_dates=["date"])
    d["month"] = d.date.dt.month
    d["year"] = d.date.dt.year
    totals = d.groupby(["year", "month"]).inflow_observed_decided.sum()
    open_days = (
        d.assign(open=workdays(pd.DatetimeIndex(d.date)))
        .groupby(["year", "month"]).open.sum()
    )
    rate = (totals / open_days).unstack(0)
    # Relative to November and shrunk toward flat demand. July–October 2024 is
    # omitted from the pattern where the platform transition distorted filings.
    comparison = rate[[2024, 2025]].div(rate.loc[11, [2024, 2025]])
    comparison.loc[7:10, 2024] = np.nan
    seasonal = 0.5 + 0.5 * comparison.mean(axis=1)
    seasonal.to_csv(OUT / "forecast_monthly_profile.csv", header=["relative_to_november"], float_format="%.5f")
    history = d[d.year.eq(2025)]
    baseline = history.loc[history.is_workday, "inflow_observed_decided"].mean()
    weekday = (history[history.is_workday]
               .groupby(history.date.dt.dayofweek).inflow_observed_decided.mean() / baseline)
    closed_ratio = history.loc[~history.is_workday, "inflow_observed_decided"].mean() / baseline

    # Check transfer of the seasonal pattern before the 2026 autumn shock.
    # Use the already-mature filing counts; this is a retrospective model check
    # of observed submissions, not recovery of the contemporaneous inflow.
    details = []
    for month in range(4, 8):
        training = rate.loc[month - 3:month - 1, 2026]
        for model, pattern in [("profil_restrans", seasonal),
                               ("constant", pd.Series(1., index=seasonal.index))]:
            pred = float((training / pattern.loc[training.index]).mean() * pattern.loc[month])
            details.append(dict(month=month, model=model, predicted_per_day=pred,
                                mature_observed_per_day=float(rate.loc[month, 2026])))
    pd.DataFrame(details).to_csv(OUT / "forecast_demand_check.csv", index=False, float_format="%.4f")
    return seasonal, weekday, closed_ratio, details


def initial_stock(records, additive_nov):
    first = pd.Timestamp(MINISTRY_NOTE["backlog_at"]) + DAY
    bridge_dates = complete_dates(first, KNOWN_THROUGH)
    resolved = int(records.date.isin(bridge_dates).sum())
    per_day = [additive_nov[k] for k in ("reg_per_wd_p05", "reg_per_wd_est", "reg_per_wd_p95")]
    bridge = [MINISTRY_NOTE["backlog"] + len(bridge_dates) * rate - resolved for rate in per_day]
    # The bridge mixes the administrative stock, modeled arrivals and strict
    # BERC exits. Leave a wider scenario range for definition/date gaps.
    mode = round(bridge[1] / 10000) * 10000
    return mode, dict(full_workdays=len(bridge_dates), exits=resolved, stock_proxy_low=bridge[0],
                      stock_proxy_mode=bridge[1], stock_proxy_high=bridge[2])


def daily_profile(days, propensity, start, end, peak=None, exponent=2.):
    active = (days >= start) & (days <= end)
    weights = propensity * active
    if peak is not None:
        offset = (days - pd.Timestamp(peak)).days.to_numpy()
        duration = (pd.Timestamp(peak) - pd.Timestamp(start)).days
        rise = np.maximum(0., 1 + offset / (duration + 1)) ** exponent
        decay = np.exp(np.minimum(0, -0.85 * offset / 7))
        weights *= np.where(offset <= 0, rise, decay)
    return weights / weights.sum()


def capital_grid(population):
    rows = []
    for total in population:
        for uptake, separate, weight in [(.10, .70, 1.10), (.17, .80, 1.35), (.27, .90, 1.60)]:
            early = round(total * uptake)
            later = round((total - early) * .80 * separate)
            rows.append(dict(candidate_stock=total, discount_takeup=uptake, later_compliance=.80,
                             later_standalone_share=separate, capital_weight=weight, discount_filings=early,
                             later_net_filings=later, combined_standard_units=round((early + later) * weight)))
    return pd.DataFrame(rows)


def simulate(initial, inflow, capacity, open_calendar):
    """Clear FIFO workload, then schedule the next standard case at each day end."""
    stock = np.empty_like(inflow)
    prev = initial.reshape(-1)
    for i in range(inflow.shape[1]):
        prev = np.maximum(0., prev + inflow[:, i] - capacity[:, i])
        stock[:, i] = prev
    cum = capacity.cumsum(axis=1)
    filing_dates = np.arange(inflow.shape[1])
    needed = cum[:, :inflow.shape[1]] + stock + 1.
    resolution = np.stack([np.searchsorted(c, target, side="left") for c, target in zip(cum, needed)])
    if (resolution >= capacity.shape[1]).any():
        raise ValueError("Extend the working calendar until every standard file is served.")
    calendar_wait = resolution - filing_dates
    wd_count = np.cumsum(open_calendar)
    working_wait = wd_count[resolution] - wd_count[filing_dates]
    return stock, calendar_wait, working_wait


def check_calendar():
    # Friday evening, no other filings, closed over the weekend.
    caps = np.array([[1., 0., 0., 1., 1., 1.]])
    work = np.array([True, False, False, True, True, True])
    stocks, days, working = simulate(np.array([0.]), np.array([[0., 0., 0., 0.]]), caps, work)
    np.testing.assert_allclose(stocks, 0.)
    np.testing.assert_array_equal(days, [[3, 2, 1, 1]])
    np.testing.assert_array_equal(working, [[1, 1, 1, 1]])
    # Two files ahead at Friday close, case is processed on Wednesday.
    _, days, working = simulate(np.array([3.]), np.array([[0.]]), caps, work)
    assert days[0, 0] == 5 and working[0, 0] == 3


def pct(values):
    return np.quantile(values, [.1, .5, .9], axis=0)


def prepare_workload():
    check_calendar()
    OUT.mkdir(exist_ok=True)
    nat = json.loads((OUT / "national.json").read_text(encoding="utf-8"))
    finance = json.loads((OUT / "finance_sources.json").read_text(encoding="utf-8"))
    capital_screen = next(row["above_turnover_capital_below_5000"] for row in finance if row["year"] == 2025)
    capital_n = MINISTRY_NOTE["capital_potential_candidates"] - MINISTRY_NOTE["capital_increase_filings"]
    records = final_records()
    resolution_rate, n_recent, capacity_check = backtest_capacity(records)
    stock_mode, stock_bridge = initial_stock(records, nat["month_additive_nov"])
    seasonal, weekday, closed_ratio, demand_check = demand_profile()
    # Keep future capacity beyond June solely so files submitted inside the
    # reporting horizon can be resolved in their projected service calendar.
    calendar = pd.date_range(START, HORIZON + pd.Timedelta(days=730))
    dates = calendar[calendar <= HORIZON]
    opening = workdays(calendar)
    service_days = len(dates)
    after_policy = calendar >= "2027-01-04"
    temporary = after_policy & (calendar <= "2028-01-08")
    scenario_dates = dates[dates.dayofweek == 0]
    forecast_offset = (dates - START).days.to_numpy() / 365.2425
    propensity = np.where(opening[:service_days], weekday.reindex(dates.dayofweek).fillna(0.), closed_ratio)
    # The recurring rate is total filings divided by working days. Redistribute
    # that same monthly total to actual dates, including weekend registrations.
    month = dates.to_period("M")
    weights = pd.Series(propensity, index=dates)
    monthly_weight = weights.groupby(month).transform("sum")
    monthly_open = pd.Series(opening[:service_days], index=dates).groupby(month).transform("sum")
    recurring_weight = (weights * monthly_open / monthly_weight).to_numpy()
    caen_shape = daily_profile(dates, propensity, "2027-01-04", "2027-04-29", "2027-04-01", 2.3)
    early_shape = daily_profile(dates, propensity, "2026-11-19", "2027-01-07", "2026-12-30", 1.8)
    capital_shape = daily_profile(dates, propensity, "2027-08-27", "2028-01-08", "2027-12-17", 2.3)
    stagger_shape = daily_profile(dates, propensity, "2027-04-05", "2027-12-20")
    defensive_shape = daily_profile(dates, propensity, "2026-12-07", "2027-12-31")
    anaf_shape = daily_profile(dates, propensity, "2027-02-01", HORIZON)

    # The November additive proxy mixes all filings. Discount its mode for the
    # unidentified residual conversion wave before adding explicit future waves.
    recurrent_reference = round(nat["month_additive_nov"]["reg_per_wd_est"] * .83 / 50) * 50
    bounds = {
        "stoc_initial": (145000, stock_mode, 300000),
        "flux_zilnic_recurent": (2900, recurrent_reference, 4000),
        "crestere_anuala_flux": (-.04, .01, .07),
        "pondere_caen_iesiri": (.15, .265, .40),
        "dosare_caen_suplimentare": (140000, 245000, 390000),
        "efort_caen": (.50, .80, 1.25),
        "populatie_capital": (100000, capital_n, 220000),
        "proportie_reducere": (.10, .17, .27),
        "conformare_ulterioara": (.65, .80, .95),
        "depuneri_separate_ulterioare": (.65, .80, .95),
        "efort_capital": (1.10, 1.35, 1.60),
        "dosare_defensive": (30000, 75000, 110000),
        "cazuri_anaf": (45000, 165000, 260000),
        "fractie_anaf_capacitate_comuna": (0, .25, .70),
        "efort_anaf": (.35, .50, .75),
        "rezolvari_observate_pe_zi": (resolution_rate * .90, resolution_rate, resolution_rate * 1.08),
    }
    rng = np.random.default_rng(20261121)
    params = pd.DataFrame({k: rng.triangular(*v, N_DRAWS) for k, v in bounds.items()})
    pd.DataFrame.from_dict(bounds, orient="index", columns=["low", "mode", "high"]).to_csv(OUT / "forecast_inputs.csv")
    capital_grid([100000, capital_n, 220000]).to_csv(OUT / "capital_grid.csv", index=False)
    p = {k: params[k].to_numpy()[:, None] for k in params}

    recurring = (p["flux_zilnic_recurent"] * seasonal.reindex(dates.month).to_numpy() * recurring_weight
                 * (1 + p["crestere_anuala_flux"]) ** forecast_offset)
    caen = p["dosare_caen_suplimentare"] * caen_shape * p["efort_caen"]
    early = p["populatie_capital"] * p["proportie_reducere"] * p["efort_capital"] * early_shape
    capital_work = ((p["populatie_capital"] * (1 - p["proportie_reducere"]))
                    * p["conformare_ulterioara"] * p["depuneri_separate_ulterioare"] * p["efort_capital"])
    late = capital_work * capital_shape
    defensive = p["dosare_defensive"] * defensive_shape * .95
    dissolve = (p["cazuri_anaf"] * p["fractie_anaf_capacitate_comuna"]
                * p["efort_anaf"] * anaf_shape)
    ordinary = recurring + early + defensive + dissolve
    avg_work = 1 - p["pondere_caen_iesiri"] * (1 - p["efort_caen"])
    capacity = p["rezolvari_observate_pe_zi"] * avg_work * opening
    initial = p["stoc_initial"] * avg_work
    validation = dict(
        simulated_from=str(START.date()), initial_stock_ends=str((START - DAY).date()),
        simulated_through=str(HORIZON.date()), draws=N_DRAWS, recent_resolution_days=n_recent,
        recent_resolutions_per_workday=resolution_rate, capacity_validation=capacity_check,
        demand_validation=demand_check, non_workday_filing_ratio=float(closed_ratio),
        near_term_additive_inflow=nat["month_additive_nov"]["reg_per_wd_est"],
        assumed_regular_caen_share=.17, recurring_anchor=recurrent_reference,
        ministry_note=MINISTRY_NOTE, initial_stock_bridge=stock_bridge,
        capital_balance_sheet_screen=capital_screen, capital_administrative_difference=capital_n,
        band_interpretation="Conditional percentiles of scenario draws",
    )
    return dict(calendar=calendar, dates=dates, opening=opening, temporary=temporary,
                after_policy=after_policy, scenario_dates=scenario_dates, initial=initial,
                capacity=capacity, ordinary=ordinary, caen=caen, early=early, late=late,
                capital_work=capital_work, stagger_shape=stagger_shape, defensive=defensive,
                dissolve=dissolve, params=params, validation=validation)


def main():
    model = prepare_workload()
    dates, opening = model["dates"], model["opening"]
    after_policy, temporary = model["after_policy"], model["temporary"]
    initial, capacity = model["initial"], model["capacity"]
    ordinary, caen, early, late = (model[key] for key in ("ordinary", "caen", "early", "late"))
    capital_work, stagger_shape = model["capital_work"], model["stagger_shape"]
    defensive, dissolve, params = model["defensive"], model["dissolve"], model["params"]
    scenario_dates = model["scenario_dates"]
    service_days = len(dates)
    sample_idx = dates.get_indexer(scenario_dates)
    ref_idx = dates.get_indexer(pd.to_datetime(REPORT_DATES))
    trajectories, summary, sensitivity, wave_results, comparisons = [], [], [], [], []
    base_days = None
    base_peak = None
    for name, (support, durable_gain, auto, stagger) in SCENARIOS.items():
        effective_capacity = capacity * (1 + support * temporary + durable_gain * after_policy)
        inflow = (ordinary + (capital_work * stagger_shape if stagger else late)
                  + caen * (1 - auto * after_policy[:service_days]))
        stock, cal_days, work_days = simulate(initial, inflow, effective_capacity, opening)
        stock_q = pct(stock[:, sample_idx])
        wait_q = pct(cal_days[:, sample_idx])
        work_q = pct(work_days[:, sample_idx])
        for i, published in enumerate(scenario_dates):
            j = sample_idx[i]
            trajectories.append(dict(scenario=name, week=str(published.date()),
                                     stock_p10=stock_q[0, i], stock_p50=stock_q[1, i], stock_p90=stock_q[2, i],
                                     wait_p10=wait_q[0, i], wait_p50=wait_q[1, i], wait_p90=wait_q[2, i],
                                     work_wait_p10=work_q[0, i], work_wait_p50=work_q[1, i], work_wait_p90=work_q[2, i],
                                     fraction_draws_at_most_3=float(np.mean(cal_days[:, j] <= 3))))
        peak = cal_days.max(axis=1)
        periods = [*zip(REPORT_DATES, ref_idx), ("peak", None)]
        for when, j in periods:
            v = peak if j is None else cal_days[:, j]
            w = work_days.max(axis=1) if j is None else work_days[:, j]
            lo, md, hi = pct(v)
            lo_w, md_w, hi_w = pct(w)
            summary.append(dict(scenario=name, period=when, p10=lo, p50=md, p90=hi,
                                fraction_draws_over_120=float(np.mean(v > 120)),
                                work_p10=lo_w, work_p50=md_w, work_p90=hi_w,
                                fraction_draws_at_most_3=float(np.mean(v <= 3))))
            if base_days is not None:
                diff = (base_peak if j is None else base_days[:, j]) - v
                comparison = pct(diff)
                comparisons.append(dict(scenario=name, period=when, days_saved_p10=comparison[0],
                                        days_saved_p50=comparison[1], days_saved_p90=comparison[2],
                                        fraction_draws_faster=float(np.mean(diff > 0))))
        if name == "continuitate":
            base_days = cal_days
            base_peak = peak
            for key in params:
                sensitivity.append(dict(parameter=key, spearman_peak=spearmanr(params[key], peak).statistic))
            waves = {
                "fara_caen_suplimentar": caen,
                "fara_capital_suplimentar": early + late,
                "fara_sarcina_fiscala_suplimentara": defensive + dissolve,
            }
            for case, removed in waves.items():
                _, alt, _ = simulate(initial, np.maximum(0., inflow - removed), effective_capacity, opening)
                peak_difference = peak - alt.max(axis=1)
                june_difference = cal_days[:, -1] - alt[:, -1]
                peak_lo, peak_md, peak_hi = pct(peak_difference)
                june_lo, june_md, june_hi = pct(june_difference)
                wave_results.append(dict(wave_removed=case, peak_days_saved_p10=peak_lo,
                                         peak_days_saved_p50=peak_md, peak_days_saved_p90=peak_hi,
                                         june_days_saved_p10=june_lo, june_days_saved_p50=june_md,
                                         june_days_saved_p90=june_hi))
    tables = {
        "forecast_trajectories.csv": trajectories, "forecast_summary.csv": summary,
        "forecast_sensitivity.csv": sorted(sensitivity, key=lambda r: abs(r["spearman_peak"]), reverse=True),
        "forecast_wave_sensitivity.csv": wave_results, "forecast_paired.csv": comparisons,
    }
    for file, rows in tables.items():
        pd.DataFrame(rows).to_csv(OUT / file, index=False, float_format="%.4f")
    validation = model["validation"]
    (OUT / "forecast_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")

    print(pd.DataFrame(summary).round(2).to_string(index=False))
    print(pd.DataFrame(validation["capacity_validation"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
