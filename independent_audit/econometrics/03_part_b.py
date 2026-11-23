"""PART B — venituri bugetare la risc în 2027 (distribuție), din:
  (a) motorul de prognoză auditat (audit_forecast.py, importat NEMODIFICAT; 2.000 de variante, sămânța 20261121),
      scenariile 'continuitate', 'combinat' și un scenariu „coadă eliminată până la 30.06.2027” (multiplicator de
      capacitate din 4.01.2027, găsit prin bisecție pe motor);
  (b) volume lunare de înmatriculări J și mențiuni (BERC, sezonalitate 2024–2026);
  (c) efectele din PARTEA A, cu incertitudinea lor de eșantionare (extrageri normale multivariate din vcov cluster);
  (d) parametri fiscali statutari verificați (URL-uri în statutory_parameters.json).
Garduri: motorul scrie CSV-uri în audit_data la prepare_workload(); aici AF.OUT este redirecționat către un director
temporar cu copii ale celor două fișiere de intrare, iar CSV-urile regenerate sunt comparate byte-cu-byte cu cele
publicate; scenariul 'continuitate' trebuie să reproducă 74/136/214,1 la 30.06.2028.
Ieșiri: tables/revenue_at_risk_2027.csv, tables/revenue_at_risk_sensitivity.csv, tables/volumes_2027.csv,
        partB_results.json (doar agregate).
"""
from __future__ import annotations
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PP = HERE.parent.parent / "analysis" / "policy_paper_ro"
sys.path.insert(0, str(PP))
import audit_forecast as AF  # noqa: E402

TAB = HERE / "tables"
SEED = 20261122
FLOOR = 3            # zile: durata „normală” (podeaua metricii motorului; mediana 2025 = 2–3 zile)
SUPPORT_CAP = 35     # p99 al duratei în eșantionul PARTEA A (zile) – pentru sensibilitatea „în suport”
Q_EDGES = [0, 90, 181, 273, 365]   # zile de la 1.01.2027
Q_NAMES = ["T1_2027", "T2_2027", "T3_2027", "T4_2027"]

# ---- (d) statutory parameters (verified by reading official texts; see statutory_parameters.json)
STAT = json.loads((HERE / "statutory_parameters.json").read_text(encoding="utf-8"))
P = {k: v["value"] for k, v in STAT["parameters"].items()}


def labor_tax_per_employee_year():
    w = P["minimum_wage_2027_assumed"]
    cas, cass, cam = P["cas_rate"] * w, P["cass_rate"] * w, P["cam_rate"] * w
    deduction = P["personal_deduction_share_min_wage_0_dependants"] * w
    pit = P["income_tax_rate"] * max(0.0, w - cas - cass - deduction)
    return 12 * (cas + cass + pit + cam), dict(gross=w, cas=cas, cass=cass, pit=pit, cam=cam, deduction=deduction)


def tree_hash(d: Path) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("*")) if p.is_file()}


# ---------------------------------------------------------------- (a) engine draws
def engine():
    published = AF.OUT
    tmp = Path(tempfile.mkdtemp(prefix="econ_engine_"))
    for f in ("national.json", "finance_sources.json"):
        shutil.copy2(published / f, tmp / f)
    before = tree_hash(published)
    AF.OUT = tmp
    try:
        m = AF.prepare_workload()
    finally:
        AF.OUT = published
    assert tree_hash(published) == before, "audit_data changed"
    # the regenerated engine inputs must be identical to the published ones (same run)
    same = {f: (tmp / f).read_bytes() == (published / f).read_bytes()
            for f in ("forecast_inputs.csv", "capital_grid.csv", "forecast_monthly_profile.csv")}
    assert all(same.values()), same
    shutil.rmtree(tmp, ignore_errors=True)
    dates, opening = m["dates"], m["opening"]
    sd = len(dates)
    after, temporary = m["after_policy"], m["temporary"]
    base_in = m["ordinary"] + m["late"] + m["caen"]
    runs = {}
    _, cal, _ = AF.simulate(m["initial"], base_in, m["capacity"], opening)
    q = np.quantile(cal[:, sd - 1], [.1, .5, .9])
    assert [round(q[0]), round(q[1]), round(q[2], 1)] == [74, 136, 214.1], q
    runs["continuitate"] = cal
    eff = m["capacity"] * (1 + .12 * temporary + .04 * after)
    inflow = m["ordinary"] + m["capital_work"] * m["stagger_shape"] + m["caen"] * (1 - .60 * after[:sd])
    runs["combinat"] = AF.simulate(m["initial"], inflow, eff, opening)[1]
    # cleared by 30.06.2027: smallest uniform capacity uplift from 4.01.2027 s.t. median wait at 30.06.2027 <= floor
    j = int(np.searchsorted(dates.values, np.datetime64("2027-06-30")))
    lo, hi = 0.0, 3.0
    for _ in range(30):
        u = (lo + hi) / 2
        c = AF.simulate(m["initial"], base_in, m["capacity"] * (1 + u * after), opening)[1]
        if np.median(c[:, j]) <= FLOOR:
            hi = u
        else:
            lo = u
    runs["coada_eliminata_iun2027"] = AF.simulate(m["initial"], base_in, m["capacity"] * (1 + hi * after), opening)[1]
    cap_per_day = float(np.median(m["capacity"][:, :sd][:, opening[:sd]].mean(1)))
    info = dict(cleared_uplift=hi, capacity_per_open_day_p50=cap_per_day, engine_start=str(AF.START.date()),
                continuity_june2028_p10_p50_p90=[float(x) for x in q], draws=AF.N_DRAWS, audit_data_unchanged=True)
    return dates, opening[:sd], runs, info


# ---------------------------------------------------------------- (b) volumes
def volumes(days, workday, rng, n):
    d = pd.read_pickle("W:/SOLOResearch/analysis_decisions.pkl")[["cat", "app", "res", "sol", "jtype"]]
    d = d[d.sol.eq("Admis") & d.cat.isin(["INMATRIC265", "CERERE265"])]
    d["m"] = d.app.dt.to_period("M")
    J = d[(d.cat == "INMATRIC265") & (d.jtype == "J")].groupby("m").size()
    C = d[d.cat == "CERERE265"].groupby("m").size()
    # registrations: 2025 and 2026 levels by calendar month; Aug–Dec 2026 censored -> 2025 x (2026/2025, Jan–Jul)
    ratio = J["2026-01":"2026-07"].sum() / J["2025-01":"2025-07"].sum()
    rows = []
    for mth in range(1, 13):
        j25 = float(J[pd.Period(f"2025-{mth:02d}")])
        j26 = float(J[pd.Period(f"2026-{mth:02d}")]) if mth <= 7 else j25 * ratio
        c24, c25 = float(C[pd.Period(f"2024-{mth:02d}")]), float(C[pd.Period(f"2025-{mth:02d}")])
        rows.append(dict(month=mth, reg_low=min(j25, j26), reg_mode=(j25 + j26) / 2, reg_high=max(j25, j26),
                         amend_low=min(c24, c25), amend_mode=(c24 + c25) / 2, amend_high=max(c24, c25)))
    vol = pd.DataFrame(rows)
    for k in ("reg", "amend"):
        same = vol[f"{k}_low"] == vol[f"{k}_high"]
        vol.loc[same, f"{k}_high"] += 1
    # per draw monthly volumes (triangular), spread evenly over the month's working days
    month = days.month.to_numpy()
    year = days.year.to_numpy()
    reg = np.zeros((n, len(days)))
    amd = np.zeros((n, len(days)))
    for (y, mth) in sorted(set(zip(year, month))):
        sel = (year == y) & (month == mth) & workday
        v = vol.iloc[mth - 1]
        rv = rng.triangular(v.reg_low, v.reg_mode, v.reg_high, n)
        av = rng.triangular(v.amend_low, v.amend_mode, v.amend_high, n)
        reg[:, sel] = (rv / sel.sum())[:, None]
        amd[:, sel] = (av / sel.sum())[:, None]
    # observed 2026 exposure of registrations already decided (locked-in for 2027 = their first full year)
    d26 = d[(d.cat == "INMATRIC265") & (d.jtype == "J") & (d.res >= "2026-01-01")].copy()
    w = (d26.res.dt.normalize() - d26.app.dt.normalize()).dt.days
    locked = dict(n=int(len(d26)), excess_days_sum=float((w - FLOOR).clip(lower=0).sum()),
                  last_decision=str(d26.res.max().date()), ratio_2026_vs_2025_jan_jul=float(ratio))
    # registration/amendment wait ratio by decision week, last 4 complete weeks (queue priority for registrations)
    dd = pd.read_pickle("W:/SOLOResearch/analysis_decisions.pkl")[["cat", "app", "res", "sol", "jtype"]]
    dd = dd[dd.sol.isin(["Admis", "Respins"]) & (dd.res >= "2026-06-01") & dd.cat.isin(["INMATRIC265", "CERERE265"])]
    dd["w"] = (dd.res.dt.normalize() - dd.app.dt.normalize()).dt.days
    dd["wk"] = dd.res.dt.to_period("W")
    reg_w = dd[(dd.cat == "INMATRIC265") & (dd.jtype == "J")].groupby("wk").w.median()
    am_w = dd[dd.cat == "CERERE265"].groupby("wk").w.median()
    r = (reg_w / am_w).dropna()
    r = r[r.index < pd.Period("2026-11-16", "W")].iloc[-4:]
    kappa = dict(weeks=[str(x) for x in r.index], ratios=[float(x) for x in r], low=float(r.min()),
                 mode=float(r.mean()), high=1.0)
    return vol, reg, amd, locked, kappa


def overlap(start, end, a, b):
    return np.clip(np.minimum(end, b) - np.maximum(start, a), 0, None)


def compute(cal, days, reg, amd, kappa, b_partial, b_next, r_amend, y, cap=None, mechanical_rate=None,
            substitution=0.0):
    """Return dict of arrays (draws x 5) for quarters + full year, by component."""
    n = cal.shape[0]
    t0 = (days - pd.Timestamp("2027-01-01")).days.to_numpy()[None, :].astype(float)
    W_reg = kappa[:, None] * cal
    e_reg = np.maximum(0., W_reg - FLOOR)
    e_am = np.maximum(0., cal - FLOOR)
    e_eff = np.minimum(e_reg, cap) if cap is not None else e_reg
    loss_per_day = -b_partial if mechanical_rate is None else mechanical_rate      # lei per firm per waiting day (>0 = loss)
    out = {}
    keep = 1 - substitution
    # (1) deferred revenue: window [t0+FLOOR, t0+FLOOR+e); amount = rate x days in window
    s, e = t0 + FLOOR, t0 + FLOOR + e_reg
    s_a, e_a = t0 + FLOOR, t0 + FLOOR + e_am
    for qi, name in enumerate(Q_NAMES + ["an_2027"]):
        a, b = (Q_EDGES[qi], Q_EDGES[qi + 1]) if qi < 4 else (0, 365)
        dr = (reg * loss_per_day[:, None] * overlap(s, e, a, b)).sum(1) * keep
        da = (amd * r_amend[:, None] * overlap(s_a, e_a, a, b)).sum(1) * keep
        # time value: amount deferred by e days, discounted at the bond yield
        tv_r = (reg * loss_per_day[:, None] * overlap(s, e, a, b) * (1 - (1 + y) ** (-e_reg / 365))).sum(1) * keep
        tv_a = (amd * r_amend[:, None] * overlap(s_a, e_a, a, b) * (1 - (1 + y) ** (-e_am / 365))).sum(1) * keep
        # part of the 2027 deferred amount whose recovery (shift by e days) falls after 31.12.2027
        # recovered into this period: deferred day t is recovered at t+e (reading "doar amânat")
        rec = ((reg * loss_per_day[:, None] * overlap(s + e_reg, e + e_reg, a, b)).sum(1)
               + (amd * r_amend[:, None] * overlap(s_a + e_am, e_a + e_am, a, b)).sum(1)) * keep
        # (2) persistent loss: annual flow -b_next x e from the decision date (t0+W) onward
        lost = (reg * (-b_next)[:, None] * e_eff * overlap(t0 + W_reg, np.full_like(t0, 1e9), a, b) / 365).sum(1) * keep
        out[name] = dict(deferred_reg=dr, deferred_amend=da, timevalue_reg=tv_r, timevalue_amend=tv_a,
                         recovered_in_period=rec, lost_persistent=lost)
    return out


def summarize(x):
    x = np.asarray(x) / 1e6
    return dict(mean=float(x.mean()), p10=float(np.quantile(x, .1)), p50=float(np.quantile(x, .5)),
                p90=float(np.quantile(x, .9)), p95=float(np.quantile(x, .95)), p05=float(np.quantile(x, .05)),
                p025=float(np.quantile(x, .025)), p975=float(np.quantile(x, .975)))


def main():
    TAB.mkdir(exist_ok=True)
    A = json.loads((HERE / "partA_results.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    dates, workday, runs, info = engine()
    n = runs["continuitate"].shape[0]
    win = (dates >= "2026-12-01") & (dates <= "2027-12-31")
    days = dates[win]
    wd = workday[win]
    vol, reg, amd, locked, kq = volumes(days, wd, rng, n)
    kappa = rng.triangular(kq["low"], kq["mode"], kq["high"], n)

    L, ldet = labor_tax_per_employee_year()
    vat = P["vat_standard_rate"]
    va = rng.triangular(.20, .30, .40, n)          # value-added share of turnover (assumption, not estimated)

    def revenue_coef(bridge, draws_rng, ols=False, with_vat=True):
        names = bridge["outcomes"]
        mu = np.array(bridge["ols_coef" if ols else "iv_coef"])
        V = np.array(bridge["ols_vcov" if ols else "iv_vcov"])
        B = draws_rng.multivariate_normal(mu, V, n, method="eigh")
        g = {k: B[:, i] for i, k in enumerate(names)}
        point = {k: mu[i] for i, k in enumerate(names)}
        w = 1.0 if with_vat else 0.0
        R = g["taxB_w"] + L * g["emp_w"] + w * vat * va * g["turnvat_w"]
        Rp = point["taxB_w"] + L * point["emp_w"] + w * vat * .30 * point["turnvat_w"]
        decomposition = dict(direct_tax=point["taxB_w"], labour=L * point["emp_w"], vat=w * vat * .30 * point["turnvat_w"])
        return R, Rp, decomposition
    b_next, b_next_point, dec_next = revenue_coef(A["bridge"], rng)
    b_part, b_part_point, dec_part = revenue_coef(A["partial_bridge"], rng)
    b_next_ols, b_next_ols_point, _ = revenue_coef(A["bridge"], rng, ols=True)
    b_next_nv, _, _ = revenue_coef(A["bridge"], np.random.default_rng(SEED + 1), with_vat=False)
    mf = A["bridge"]["mean_per_firm_FY2025"]
    # CENTRAL calibration of the "delayed" channel: mean public revenue of a new firm per day (first full year, all firms,
    # 0 for non-filers). The partial-year IV estimate (larger than one mature day per waiting day) is an upper sensitivity.
    mech_rate = (mf["taxB_w"] + L * mf["emp_w"] + vat * va * mf["turnvat_w"]) / 365
    mech_rate_nv = np.full(n, (mf["taxB_w"] + L * mf["emp_w"]) / 365)
    mech_point = dict(direct_tax=mf["taxB_w"] / 365, labour=L * mf["emp_w"] / 365, vat=vat * .30 * mf["turnvat_w"] / 365)
    # amendments: parametric (audit_costs.py central/prudent/tense), NOT estimated here
    r_amend = (rng.triangular(35, 70, 110, n) * rng.triangular(.15, .20, .25, n) * rng.triangular(.08, .13, .18, n))
    y10 = P["bond_yield_10y_ron_oct2026"]

    res = {}
    for sc, cal in runs.items():
        res[sc] = compute(cal[:, win], days, reg, amd, kappa, b_part, b_next, r_amend, y10, mechanical_rate=mech_rate)
    base = res["continuitate"]

    rows = []
    def add(scn, period, comp, arr):
        rows.append(dict(scenario=scn, period=period, component=comp, **summarize(arr)))
    for sc, r in res.items():
        for per, c in r.items():
            tot_def = c["deferred_reg"] + c["deferred_amend"]
            net = tot_def - c["recovered_in_period"]
            tv = c["timevalue_reg"] + c["timevalue_amend"]
            add(sc, per, "1a_amanat_brut_inmatriculari", c["deferred_reg"])
            add(sc, per, "1a_amanat_brut_mentiuni_(parametric)", c["deferred_amend"])
            add(sc, per, "1a_amanat_brut_total", tot_def)
            add(sc, per, "1b_recuperat_in_perioada", c["recovered_in_period"])
            add(sc, per, "1c_efect_net_numerar_amanare", net)
            add(sc, per, "1d_cost_valoare_in_timp", tv)
            add(sc, per, "2_pierdut_persistent_(PARTEA_A)", c["lost_persistent"])
            add(sc, per, "A_doar_amanat_impact_numerar_(1c+2)", net + c["lost_persistent"])
            add(sc, per, "A_doar_amanat_cost_economic_(1d+2)", tv + c["lost_persistent"])
            add(sc, per, "B_nerecuperat_impact_(1a+2)", tot_def + c["lost_persistent"])
            if sc != "continuitate":
                bb = base[per]
                bdef = bb["deferred_reg"] + bb["deferred_amend"]
                add(sc, per, "evitat_vs_continuitate_B_(1a+2)",
                    (bdef + bb["lost_persistent"]) - (tot_def + c["lost_persistent"]))
                add(sc, per, "evitat_vs_continuitate_A_numerar_(1c+2)",
                    (bdef - bb["recovered_in_period"] + bb["lost_persistent"]) - (net + c["lost_persistent"]))
    locked_lost = -b_next * locked["excess_days_sum"]
    add("continuitate", "an_2027", "memo_pierdut_persistent_cohorta_2026_deja_decisa", locked_lost)
    table = pd.DataFrame(rows)
    table.to_csv(TAB / "revenue_at_risk_2027.csv", index=False, float_format="%.3f")

    # sensitivities (full year, continuity): total risk and lost component
    cal = runs["continuitate"][:, win]
    sens = []
    def srow(name, r, note=""):
        c = r["an_2027"]
        dfr = c["deferred_reg"] + c["deferred_amend"]
        A_ = dfr - c["recovered_in_period"] + c["lost_persistent"]
        B_ = dfr + c["lost_persistent"]
        sa, sb, sl = summarize(A_), summarize(B_), summarize(c["lost_persistent"])
        sens.append(dict(sensitivity=name, note=note,
                         A_numerar_p50=sa["p50"], A_numerar_p90=sa["p90"], A_numerar_p95=sa["p95"],
                         B_nerecuperat_p50=sb["p50"], B_nerecuperat_p90=sb["p90"], B_nerecuperat_p95=sb["p95"],
                         valoare_timp_p50=summarize(c["timevalue_reg"] + c["timevalue_amend"])["p50"],
                         pierdut_p50=sl["p50"], pierdut_p90=sl["p90"], pierdut_p95=sl["p95"]))
    srow("central", base)
    srow("randament 12 luni 6,02%", compute(cal, days, reg, amd, kappa, b_part, b_next, r_amend, P["money_market_12m_oct2026"], mechanical_rate=mech_rate))
    srow("kappa=1 (înmatriculări = coada generală)", compute(cal, days, reg, amd, np.ones(n), b_part, b_next, r_amend, y10, mechanical_rate=mech_rate))
    srow("kappa=0,65 (prioritate maximă observată)", compute(cal, days, reg, amd, np.full(n, kq["low"]), b_part, b_next, r_amend, y10, mechanical_rate=mech_rate))
    srow("rată estimată IV an parțial (limită superioară, > o zi matură per zi de așteptare)", compute(cal, days, reg, amd, kappa, b_part, b_next, r_amend, y10))
    srow("efect persistent plafonat la suportul observat (35 zile)", compute(cal, days, reg, amd, kappa, b_part, b_next, r_amend, y10, cap=SUPPORT_CAP, mechanical_rate=mech_rate))
    srow("efect persistent = OLS (limită superioară a daunei, endogen)", compute(cal, days, reg, amd, kappa, b_part, b_next_ols, r_amend, y10, mechanical_rate=mech_rate))
    srow("efect persistent trunchiat la >=0 pierdere", compute(cal, days, reg, amd, kappa, b_part, np.minimum(b_next, 0), r_amend, y10, mechanical_rate=mech_rate),
         "trunchiere: extragerile cu semn de câștig puse la 0")
    srow("substituție 50% (firmele existente preiau jumătate)", compute(cal, days, reg, amd, kappa, b_part, b_next, r_amend, y10, substitution=.5, mechanical_rate=mech_rate))
    srow("fără TVA (doar impozit direct + contribuții salariale)", compute(cal, days, reg, amd, kappa, b_part, b_next_nv, r_amend, y10, mechanical_rate=mech_rate_nv))
    srow("fără mențiuni (doar înmatriculări, estimat)", compute(cal, days, reg, amd * 0, kappa, b_part, b_next, r_amend, y10, mechanical_rate=mech_rate))
    pd.DataFrame(sens).to_csv(TAB / "revenue_at_risk_sensitivity.csv", index=False, float_format="%.3f")
    vol.to_csv(TAB / "volumes_2027.csv", index=False, float_format="%.0f")

    # wait distribution (registration) by quarter for the record
    t0 = (days - pd.Timestamp("2027-01-01")).days.to_numpy()
    wq = {}
    for sc, cal_s in runs.items():
        W = kappa[:, None] * cal_s[:, win]
        wq[sc] = {}
        for qi, name in enumerate(Q_NAMES):
            sel = (t0 >= Q_EDGES[qi]) & (t0 < Q_EDGES[qi + 1])
            m = W[:, sel].mean(1)
            wq[sc][name] = dict(p10=float(np.quantile(m, .1)), p50=float(np.quantile(m, .5)), p90=float(np.quantile(m, .9)))
    out = dict(
        engine=info, kappa=kq, locked_2026=locked, labor_tax_per_employee_year=L, labor_tax_detail=ldet,
        revenue_coef_per_waiting_day=dict(
            next_full_year_point=float(b_next_point), next_full_year_draws=summarize(b_next * 1e6),
            next_full_year_ols_point=float(b_next_ols_point),
            partial_year_point=float(b_part_point), partial_year_draws=summarize(b_part * 1e6),
            mechanical_mean_revenue_per_firm_day=summarize(mech_rate * 1e6),
            decomposition_mechanical_per_day=mech_point, decomposition_partial_year_per_day=dec_part,
            decomposition_next_full_year_per_day=dec_next,
            central_delayed_calibration="mecanică: venitul public mediu al unei firme noi pe zi (FY2025)",
            note="lei de venit al administrației publice (impozit direct proxy + contribuții/impozit salarial la salariul minim x "
                 "salariați + TVA 21% x pondere VA x cifra peste plafon) per firmă, per zi de așteptare"),
        registration_wait_by_quarter=wq, yield_used=y10, seed=SEED,
    )
    (HERE / "partB_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    pd.set_option("display.width", 250)
    print(table[(table.period == "an_2027")].to_string(index=False))
    print(table[(table.scenario == "continuitate") & table.component.isin(["B_nerecuperat_impact_(1a+2)", "A_doar_amanat_impact_numerar_(1c+2)", "2_pierdut_persistent_(PARTEA_A)", "1a_amanat_brut_total"])].to_string(index=False))
    print(pd.DataFrame(sens).to_string(index=False))
    print(json.dumps({k: out[k] for k in ("engine", "kappa", "locked_2026", "revenue_coef_per_waiting_day")}, indent=1, default=float))


if __name__ == "__main__":
    main()
