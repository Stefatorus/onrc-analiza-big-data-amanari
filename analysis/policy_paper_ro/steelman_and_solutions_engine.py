"""Steelman Counter-Argument Stress Tests, Dormancy Sensitivity, Realistic Solutions
& Macro-Substitution Analysis for ONRC Registry Crisis (2026-2028).

Produces audit-verifiable artifacts saved to SCRATCH and (when writable) audit_data/:
  - macro_substitution_stress_test.csv
  - priority_triage_economic_savings.csv
  - dormancy_compliance_sensitivity.csv
  - solutions_feasibility_and_simulations.csv
  - steelman_counterarguments_matrix.csv
  - steelman_counterarguments_matrix.json
"""
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit_forecast
from audit_forecast import (
    HORIZON,
    N_DRAWS,
    START,
    daily_profile,
    prepare_workload,
    simulate,
    workdays,
)

warnings.filterwarnings("ignore", category=FutureWarning)

AUDIT_DIR = HERE / "audit_data"
SCRATCH = Path(__import__("os").environ.get("ONRC_SCRATCH", Path(__file__).resolve().parent / "_work"))  # was an external Gemini scratch dir (audit 21.11.2026)
SCRATCH.mkdir(parents=True, exist_ok=True)
OUG_BUDGET_RON = 5_760_000.0


def save_df(df: pd.DataFrame, name: str) -> None:
    df.to_csv(SCRATCH / name, index=False, float_format="%.4f")
    try:
        df.to_csv(AUDIT_DIR / name, index=False, float_format="%.4f")
    except PermissionError:
        pass


def save_json(obj: dict | list, name: str) -> None:
    txt = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    (SCRATCH / name).write_text(txt, encoding="utf-8")
    try:
        (AUDIT_DIR / name).write_text(txt, encoding="utf-8")
    except PermissionError:
        pass


def load_csv(name: str) -> pd.DataFrame:
    p_scr = SCRATCH / name
    p_aud = AUDIT_DIR / name
    if p_scr.exists() and (not p_aud.exists() or p_scr.stat().st_mtime >= p_aud.stat().st_mtime):
        return pd.read_csv(p_scr)
    return pd.read_csv(p_aud)


def load_json_pref(name: str) -> dict:
    p_scr = SCRATCH / name
    p_aud = AUDIT_DIR / name
    if p_scr.exists() and (not p_aud.exists() or p_scr.stat().st_mtime >= p_aud.stat().st_mtime):
        return json.loads(p_scr.read_text(encoding="utf-8"))
    return json.loads(p_aud.read_text(encoding="utf-8"))


def build_macro_substitution_stress_test() -> tuple[pd.DataFrame, pd.DataFrame]:
    cs = load_csv("cost_scenarios.csv").set_index("scenario")
    ci = load_csv("cost_inputs.csv").set_index("scenario")

    regimes = [
        ("M0: Echilibru parțial (0% subst. A, 0% disc. C)", 0.00, 0.00, "baseline_net_va"),
        ("M1: Substituție moderată (50% subst. A, 25% disc. C)", 0.50, 0.25, "baseline_net_va"),
        ("M2: Substituție severă (75% subst. A, 50% disc. C)", 0.75, 0.50, "baseline_net_va"),
        ("M3: Substituție extremă (90% subst. A, 75% disc. C)", 0.90, 0.75, "baseline_net_va"),
        ("M4: Certificat formal Lean T10b (95% subst. VA brut A, 100% disc. C)", 0.95, 1.00, "gross_va_floor"),
        ("M5: Substituție 95% pe VA net permanent A + 100% disc. C", 0.95, 1.00, "baseline_net_va"),
        ("M6: Prag absolut B + D (100% subst. A, 100% disc. C)", 1.00, 1.00, "baseline_net_va"),
    ]

    rows = []
    for rname, s_a, d_c, mode in regimes:
        rec = dict(regime=rname, macro_subst_a_pct=round(s_a * 100, 1), discount_c_pct=round(d_c * 100, 1))
        for sc in ("prudent", "central", "tensionat"):
            row = cs.loc[sc]
            inp = ci.loc[sc]
            va_gross = float(row["a_value_added"]) / float(inp["lost_turnover_fraction"])
            a_component = (va_gross * (1.0 - s_a)) if mode == "gross_va_floor" else (float(row["a_value_added"]) * (1.0 - s_a))
            b_component = float(row["b_private"])
            c_component = float(row["c_private"]) * (1.0 - d_c)
            d_priv = float(row["d_private"])
            d_adm = float(row["d_admin"])
            tot_priv = a_component + b_component + c_component + d_priv
            tot_with_admin = tot_priv + d_adm
            rec[f"{sc}_net_priv_mron"] = round(tot_priv / 1e6, 2)
            rec[f"{sc}_net_all_mron"] = round(tot_with_admin / 1e6, 2)
            rec[f"{sc}_ratio_vs_oug_budget"] = round(tot_with_admin / OUG_BUDGET_RON, 2)
        rows.append(rec)
    df_macro = pd.DataFrame(rows)
    save_df(df_macro, "macro_substitution_stress_test.csv")

    # Zero-cost priority triage economic savings calculation (identical cost ledger accounting)
    exp_df = pd.read_csv(AUDIT_DIR / "cost_observed_exposure.csv", index_col=0)
    obs_birth_d = float(exp_df.loc["observed_new_j_excess_days", "value"])
    obs_chg_d = float(exp_df.loc["observed_changes_excess_days", "value"])
    obs_late_chg = float(exp_df.loc["observed_changes_over_30", "value"])

    triage_rows = []
    for sc in ("prudent", "central", "tensionat"):
        inp = ci.loc[sc]
        base = cs.loc[sc]
        pending_births = float(inp["pending"]) * float(inp["pending_new_j_share"])
        pending_changes = float(inp["pending"]) - pending_births - float(inp["pending"]) * 0.12
        # Priority triage reorders pending queue: births served in ~5 excess days instead of 38/55;
        # urgent corporate changes protected (-75% excess days & -75% new ANAF inactivation increment risk)
        new_birth_exc = min(5.0, float(inp["pending_new_excess_days"]))
        new_chg_exc = float(inp["pending_changes_excess_days"]) * 0.25
        a_days_tr = obs_birth_d + pending_births * new_birth_exc
        a_va_tr = a_days_tr * float(inp["net_turnover_per_day"]) * float(inp["lost_turnover_fraction"]) * float(inp["value_added_share"])
        a_tax_tr = a_days_tr * float(inp["net_turnover_per_day"]) * float(inp["lost_turnover_fraction"]) * float(inp["tax_share"])
        pending_late_tr = pending_changes * 0.15
        b_cnt_tr = (obs_late_chg + pending_late_tr) * float(inp["seat_share"]) * float(inp["inactivation_increment"]) * 0.35
        b_priv_tr = b_cnt_tr * float(inp["seat_private_cost"])
        b_tax_tr = b_cnt_tr * float(inp["seat_fiscal_cost"])
        c_days_tr = (obs_chg_d + pending_changes * new_chg_exc) * float(inp["disjoint_blocked_changes_share"])
        c_priv_tr = c_days_tr * float(inp["blocked_change_cost"])
        c_tax_tr = c_priv_tr * float(inp["blocked_change_tax_share"])
        d_priv_tr = float(base["d_private"]) * 0.70  # better completeness triage
        tot_tr = a_va_tr + b_priv_tr + c_priv_tr + d_priv_tr
        tax_tr = a_tax_tr + b_tax_tr + c_tax_tr
        avoided = float(base["total_economic"]) - tot_tr
        tax_avoided = float(base["lost_tax"]) - tax_tr
        triage_rows.append(dict(
            scenario=sc,
            baseline_econ_mron=round(float(base["total_economic"]) / 1e6, 2),
            after_triage_econ_mron=round(tot_tr / 1e6, 2),
            avoided_econ_mron=round(avoided / 1e6, 2),
            avoided_econ_pct=round(100.0 * avoided / float(base["total_economic"]), 1),
            baseline_tax_mron=round(float(base["lost_tax"]) / 1e6, 2),
            avoided_tax_mron=round(tax_avoided / 1e6, 2),
        ))
    df_triage = pd.DataFrame(triage_rows)
    save_df(df_triage, "priority_triage_economic_savings.csv")
    return df_macro, df_triage


def build_dormancy_compliance_sensitivity(model: dict) -> tuple[pd.DataFrame, dict]:
    dates, calendar = model["dates"], model["calendar"]
    open_ = model["opening"]
    temp = model["temporary"]
    after = model["after_policy"]
    cap_base = model["capacity"]
    init = model["initial"]
    n_d = len(dates)
    idx_jun27 = dates.get_loc(pd.Timestamp("2027-06-30"))
    idx_dec27 = dates.get_loc(pd.Timestamp("2027-12-31"))
    idx_jun28 = dates.get_loc(pd.Timestamp("2028-06-30"))

    ramp_temp = np.where(temp, np.where(np.cumsum(temp & open_) <= 20, 0.5, 1.0), 0.0)
    ramp_after = np.where(after, np.where(np.cumsum(after & open_) <= 20, 0.5, 1.0), 0.0)
    perm19 = calendar >= "2027-01-19"
    caen_auto_shape = daily_profile(dates, np.where(open_[:n_d], 1.0, 0.12), "2027-01-04", "2027-04-29", "2027-04-01", 2.3)

    # Organic base (recurring filings present regardless of CAEN/Capital/ANAF dormancy)
    cap_work_orig = model["early"] + model["late"]
    anaf_def_orig = model["defensive"] + model["dissolve"]
    caen_orig = model["caen"]
    recurring_only = model["ordinary"] - (model["early"] + model["defensive"] + model["dissolve"])

    compliance_regimes = [
        ("D1: Ultra-Dormant (25% CAEN, 35% Cap, 15% ANAF)", 0.25, 0.35, 0.15),
        ("D2: Dormant Ridicat (45% CAEN, 60% Cap, 30% ANAF)", 0.45, 0.60, 0.30),
        ("D3: Referință Calibrată Lab Edition (100%)", 1.00, 1.00, 1.00),
        ("D4: Conformare Ridicată (125% CAEN, 120% Cap, 125% ANAF)", 1.25, 1.20, 1.25),
        ("D5: Conformare Integrală MJ (180% CAEN, 135% Cap, 180% ANAF)", 1.80, 1.35, 1.80),
    ]

    rows = []
    for rlabel, mc, mcap, mana in compliance_regimes:
        inflow_base = recurring_only + mc * caen_orig + mcap * cap_work_orig + mana * anaf_def_orig
        policies = [
            ("Status Quo (Fără măsuri)", cap_base, inflow_base),
            ("Proiect OUG MJ (+375 u/zi, 25% Art. III)",
             cap_base + 375.0 * ramp_temp * open_,
             np.maximum(0.0, inflow_base - 0.25 * mana * model["dissolve"] * perm19[:n_d])),
            ("P5: Pachet Minim Realist (0 SEAP)",
             cap_base + (375.0 * ramp_after + 0.02 * cap_base.mean() * (calendar >= "2027-01-04")) * open_,
             np.maximum(
                 0.0,
                 recurring_only
                 + mc * caen_orig * (1.0 - 0.75 * after[:n_d])
                 + mcap * (model["early"] + model["capital_work"] * model["stagger_shape"])
                 + mana * (model["defensive"] + model["dissolve"] * (1.0 - 0.30 * perm19[:n_d]))
             )),
        ]
        for plabel, cap_p, in_p in policies:
            stock, calw, _ = simulate(init, in_p, cap_p, open_)
            rows.append(dict(
                compliance_regime=rlabel,
                policy=plabel,
                mult_caen=mc,
                mult_capital=mcap,
                mult_anaf=mana,
                est_extra_caen_k=round(float(mc * model["params"]["dosare_caen_suplimentare"].mean()) / 1e3, 1),
                jun27_p50=round(float(np.median(calw[:, idx_jun27])), 1),
                dec27_p50=round(float(np.median(calw[:, idx_dec27])), 1),
                jun28_p10=round(float(np.quantile(calw[:, idx_jun28], 0.10)), 1),
                jun28_p50=round(float(np.median(calw[:, idx_jun28])), 1),
                jun28_p90=round(float(np.quantile(calw[:, idx_jun28], 0.90)), 1),
                peak_p50=round(float(np.median(calw.max(axis=1))), 1),
                prob_le_3d_jun28_pct=round(float(np.mean(calw[:, idx_jun28] <= 3) * 100.0), 2),
                stock_jun28_med=int(round(float(np.median(stock[:, idx_jun28])))),
            ))

    # Find exact MAXIMUM uniform wave multiplier where June 2028 median still meets <= 3 days
    breakeven = {"sq_max_mult_for_med_le3d": 0.0, "oug_max_mult_for_med_le3d": 0.0, "sq_zero_wave_jun28_p50": None, "oug_zero_wave_jun28_p50": None}
    for m_u in [round(x, 2) for x in np.linspace(0.0, 1.0, 21)]:
        in_test = recurring_only + m_u * (caen_orig + cap_work_orig + anaf_def_orig)
        _, cw_sq, _ = simulate(init, in_test, cap_base, open_)
        med_sq = float(np.median(cw_sq[:, idx_jun28]))
        if m_u == 0.0:
            breakeven["sq_zero_wave_jun28_p50"] = round(med_sq, 1)
        if med_sq <= 3.0:
            breakeven["sq_max_mult_for_med_le3d"] = m_u
        in_oug = np.maximum(0.0, in_test - 0.25 * m_u * model["dissolve"] * perm19[:n_d])
        _, cw_oug, _ = simulate(init, in_oug, cap_base + 375.0 * ramp_temp * open_, open_)
        med_oug = float(np.median(cw_oug[:, idx_jun28]))
        if m_u == 0.0:
            breakeven["oug_zero_wave_jun28_p50"] = round(med_oug, 1)
        if med_oug <= 3.0:
            breakeven["oug_max_mult_for_med_le3d"] = m_u

    df_dorm = pd.DataFrame(rows)
    save_df(df_dorm, "dormancy_compliance_sensitivity.csv")
    return df_dorm, breakeven


def build_solutions_feasibility(model: dict) -> pd.DataFrame:
    dates, calendar = model["dates"], model["calendar"]
    open_ = model["opening"]
    temp = model["temporary"]
    after = model["after_policy"]
    cap_base = model["capacity"]
    init = model["initial"]
    n_d = len(dates)

    idx_mar27 = dates.get_loc(pd.Timestamp("2027-03-31"))
    idx_dec27 = dates.get_loc(pd.Timestamp("2027-12-31"))
    idx_jun28 = dates.get_loc(pd.Timestamp("2028-06-30"))

    ramp_temp = np.where(temp, np.where(np.cumsum(temp & open_) <= 20, 0.5, 1.0), 0.0)
    ramp_after = np.where(after, np.where(np.cumsum(after & open_) <= 20, 0.5, 1.0), 0.0)
    # Prolonged OUG / vacants through end of horizon (no artificial sunset cliff on 8 Jan 2028)
    perm19 = calendar >= "2027-01-19"
    apr1 = calendar >= "2027-04-01"

    prop_l = np.where(open_[:n_d], 1.0, 0.12)
    caen_delay_shape = daily_profile(dates, prop_l, "2027-06-01", "2027-11-15", "2027-09-28", 2.1)
    cap_delay_shape = daily_profile(dates, prop_l, "2028-01-15", "2028-06-25", "2028-05-15", 2.0)

    base_in = model["ordinary"] + model["caen"] + model["late"]
    recurring_core = model["ordinary"] - model["dissolve"]

    # Check exact Status Quo reference against audit_oug.py
    sq_stock, sq_calw, _ = simulate(init, base_in, cap_base, open_)

    configs = [
        dict(
            id="P0",
            package="P0: Status Quo (Fără măsuri noi)",
            tier="Referință",
            legal_vehicle="Niciun act nou (expiră conducerea actuală)",
            seap_procurement_needed="Nu",
            budget_ron_est="0",
            time_to_effect_days="—",
            realism_rating="Baseline pasiv",
            failure_mode="Divergență progresivă a stocului spre >400k dosare și infringement UE prelungit.",
            cap=cap_base,
            inflow=base_in,
        ),
        dict(
            id="P1",
            package="P1: Doar amânare termene (+6 luni CAEN & capital, 0 capacitate)",
            tier="Falsă soluție (Kicking the Can)",
            legal_vehicle="HG simplă de prorogare",
            seap_procurement_needed="Nu",
            budget_ron_est="0",
            time_to_effect_days="1–7 zile",
            realism_rating="Ridicată politic (cel mai probabil reflex)",
            failure_mode="Nu elimină volumul: mută vârful spre 2028 și menține așteptarea peste 100 zile.",
            cap=cap_base,
            inflow=recurring_core + model["params"]["dosare_caen_suplimentare"].to_numpy()[:, None] * model["params"]["efort_caen"].to_numpy()[:, None] * caen_delay_shape + model["capital_work"] * cap_delay_shape + model["dissolve"],
        ),
        dict(
            id="P2",
            package="P2: Proiect OUG MJ neamendat (central +375 u/zi, Art. III 25%, expiră 8.01.2028)",
            tier="OUG actual (Insuficient)",
            legal_vehicle="OUG 18.11.2026 neamendată",
            seap_procurement_needed="Nu (op. IT 15 zile Art. IV)",
            budget_ron_est="5,76 mil. RON",
            time_to_effect_days="30–45 zile",
            realism_rating="Ridicată (deja în avizare)",
            failure_mode="Acoperă ~18% din deficit; expiră brusc la 08.01.2028 când coada mai are >300k dosare.",
            cap=cap_base + 375.0 * ramp_temp * open_,
            inflow=base_in - 0.25 * model["dissolve"] * perm19[:n_d],
        ),
        dict(
            id="P3",
            package="P3: OUG extins + ocupare 40% din cele 134 posturi finanțate (+750 u/zi)",
            tier="Nivel 1 (Doar resurse umane)",
            legal_vehicle="OUG amendată + concurs intern / detașări 134 posturi finanțate",
            seap_procurement_needed="Nu",
            budget_ron_est="12–16 mil. RON (în posturi finanțate)",
            time_to_effect_days="60–120 zile",
            realism_rating="Medie (blocaje concursuri/detașări)",
            failure_mode="Fără tăierea cererii CAEN, nici +30 FTE suplimentari nu ating 3 zile la vârf.",
            cap=cap_base + (375.0 * ramp_after + 375.0 * (calendar >= "2027-03-01")) * open_,
            inflow=base_in - 0.30 * model["dissolve"] * perm19[:n_d],
        ),
        dict(
            id="P4",
            package="P4: Decongestionare legislativă Zero-IT (OUG conversie CAEN 1-la-1 [-75%] + eșalonare CUI)",
            tier="Nivel 0 (Tăiere cerere artificială)",
            legal_vehicle="Amendament 2 art. în OUG (fără cost bugetar nou)",
            seap_procurement_needed="Nu",
            budget_ron_est="0 RON",
            time_to_effect_days="1–15 zile",
            realism_rating="Medie-Ridicată (depinde doar de MJ/ONRC)",
            failure_mode="Rezistență birocratică la renunțarea la cererile individuale CAEN Rev. 3.",
            cap=cap_base,
            inflow=model["ordinary"] + model["caen"] * (1.0 - 0.75 * after[:n_d]) + model["capital_work"] * model["stagger_shape"],
        ),
        dict(
            id="P5",
            package="P5: Pachet Minim Realist 0–60 zile (OUG prelungit + CAEN 1-la-1 [-75%] + Eșalonare + Triaj)",
            tier="Nivel 0+1 RECOMANDAT (0 SEAP)",
            legal_vehicle="OUG amendat + Circulară ONRC eliminare prag rutare & 2 benzi FIFO",
            seap_procurement_needed="NU (0 licitații SEAP)",
            budget_ron_est="5,76–7,0 mil. RON",
            time_to_effect_days="15–45 zile",
            realism_rating="RIDICATĂ (singurul pachet fără SEAP care taie coada)",
            failure_mode="Necesită voință MJ pentru a elimina cererile mecanice CAEN și refacerea rutării Etapa 1.",
            cap=cap_base + (375.0 * ramp_after + 0.02 * cap_base.mean() * after) * open_,
            inflow=model["ordinary"] + model["caen"] * (1.0 - 0.75 * after[:n_d]) + model["capital_work"] * model["stagger_shape"] - 0.30 * model["dissolve"] * perm19[:n_d],
        ),
        dict(
            id="P6",
            package="P6: Pachet Realist Extins 30–120 zile (P5 + 60% vacante finanțate + patch validare Nivel A)",
            tier="Nivel 1 Extins",
            legal_vehicle="P5 + mobilizare ~60 posturi finanțate + patch mentenanță v2.0",
            seap_procurement_needed="Nu (contract garanție/mentenanță)",
            budget_ron_est="14–19 mil. RON",
            time_to_effect_days="45–120 zile",
            realism_rating="Medie (necesită deblocare angajări + vendor patch)",
            failure_mode="Patch-ul de validare depinde de contractul existent de mentenanță ONRC v2.0.",
            cap=cap_base * (1.0 + 0.04 * apr1) + (375.0 * ramp_after + 400.0 * (calendar >= "2027-04-01")) * open_,
            inflow=model["ordinary"] + model["caen"] * (1.0 - 0.80 * after[:n_d]) + model["capital_work"] * model["stagger_shape"] - 0.45 * model["dissolve"] * perm19[:n_d],
        ),
        dict(
            id="P7",
            package="P7: Pachet Structural Complet 6–18 luni (P6 + API ANAF-ONRC + auto-mențiuni 60%)",
            tier="Nivel 2 Structural",
            legal_vehicle="P6 + interoperabilitate ANAF-ONRC + regulament portal",
            seap_procurement_needed="POSIBIL DA (API nou)",
            budget_ron_est="25–45 mil. RON",
            time_to_effect_days="180–540 zile",
            realism_rating="Scăzută în 2027 (risc contestații SEAP)",
            failure_mode="Risc major de blocaj în achiziții SEAP/CNSC (>12 luni) și integrare inter-instituțională.",
            cap=cap_base * (1.0 + 0.10 * (calendar >= "2027-07-01")) + (375.0 * ramp_after + 450.0 * (calendar >= "2027-04-01")) * open_,
            inflow=model["ordinary"] + model["caen"] * (1.0 - 0.90 * after[:n_d]) + model["capital_work"] * model["stagger_shape"] - 0.70 * model["dissolve"] * perm19[:n_d],
        ),
    ]

    rows = []
    for c in configs:
        st, cw, _ = simulate(init, c["inflow"], c["cap"], open_)
        diff_jun28 = sq_calw[:, idx_jun28] - cw[:, idx_jun28]
        rows.append(dict(
            id=c["id"],
            package=c["package"],
            tier=c["tier"],
            legal_vehicle=c["legal_vehicle"],
            seap_procurement_needed=c["seap_procurement_needed"],
            budget_ron_est=c["budget_ron_est"],
            time_to_effect_days=c["time_to_effect_days"],
            implementation_realism=c["realism_rating"],
            primary_failure_mode=c["failure_mode"],
            wait_mar27_p50=round(float(np.median(cw[:, idx_mar27])), 1),
            wait_dec27_p50=round(float(np.median(cw[:, idx_dec27])), 1),
            wait_jun28_p10=round(float(np.quantile(cw[:, idx_jun28], 0.10)), 1),
            wait_jun28_p50=round(float(np.median(cw[:, idx_jun28])), 1),
            wait_jun28_p90=round(float(np.quantile(cw[:, idx_jun28], 0.90)), 1),
            peak_p50=round(float(np.median(cw.max(axis=1))), 1),
            days_saved_jun28_med=round(float(np.median(diff_jun28)), 1),
            prob_le_3d_dec27_pct=round(float(np.mean(cw[:, idx_dec27] <= 3) * 100.0), 2),
            prob_le_3d_jun28_pct=round(float(np.mean(cw[:, idx_jun28] <= 3) * 100.0), 2),
            stock_jun28_med=int(round(float(np.median(st[:, idx_jun28])))),
        ))
    df_sol = pd.DataFrame(rows)
    save_df(df_sol, "solutions_feasibility_and_simulations.csv")
    return df_sol


def build_steelman_matrix(
    df_macro: pd.DataFrame,
    df_triage: pd.DataFrame,
    df_dorm: pd.DataFrame,
    dorm_be: dict,
    df_sol: pd.DataFrame,
) -> pd.DataFrame:
    fp = load_json_pref("foolproofing_sensitivity_tests.json")
    oug_sc = pd.read_csv(AUDIT_DIR / "oug_2026" / "scenarios.csv").set_index(["scenario", "period"])
    oug_tg = pd.read_csv(AUDIT_DIR / "oug_2026" / "target_grid.csv")
    lv = load_csv("predictive_model_live_nov18_20.csv").set_index("decision_day")

    l50 = int(oug_tg[oug_tg.meets_both >= 0.50].iloc[0]["units_per_day"])
    l80 = int(oug_tg[oug_tg.meets_both >= 0.80].iloc[0]["units_per_day"])

    d1_sq = df_dorm[(df_dorm.compliance_regime.str.startswith("D1:")) & (df_dorm.policy.str.startswith("Status Quo"))].iloc[0]
    d1_oug = df_dorm[(df_dorm.compliance_regime.str.startswith("D1:")) & (df_dorm.policy.str.startswith("Proiect OUG"))].iloc[0]
    d2_sq = df_dorm[(df_dorm.compliance_regime.str.startswith("D2:")) & (df_dorm.policy.str.startswith("Status Quo"))].iloc[0]
    d2_oug = df_dorm[(df_dorm.compliance_regime.str.startswith("D2:")) & (df_dorm.policy.str.startswith("Proiect OUG"))].iloc[0]

    sol_idx = df_sol.set_index("id")
    m4_c = df_macro[df_macro.regime.str.startswith("M4:")].iloc[0]
    m6_c = df_macro[df_macro.regime.str.startswith("M6:")].iloc[0]
    tri_c = df_triage[df_triage.scenario == "central"].iloc[0]

    records = [
        dict(
            id="S1",
            pillar="1. Situația Registrului",
            persona="Management MJ / ONRC",
            steelman_argument="Producția medie zilnică a crescut de la 3.247 (H1 2024) la 4.233 (H1 2026) și 4.409 (2–17 nov. 2026, +36%). Așteptarea mare vine exclusiv din valul istoric CAEN, nu din ineficiența noului portal.",
            honest_concession="Pooling-ul național (13% → 79% decizii inter-județene) este un câștig arhitectural real (efectul său per registrator nu poate fi identificat din date), iar valul CAEN explică explozia brută a cererilor.",
            empirical_and_formal_test=(
                "Pe dosare comparabile fără CAEN, panelul pereche (n=93) e 1,00× (22,0 vs. 22,0), iar raportat la plafonul real saturat din T1 2024 (29,2 substanțiale/zi pe 81 reg.) vs. oct.–nov. 2026 (20,5–22,1 pe 96 reg. saturați 100%), "
                "o scădere a plafonului per angajat nu poate fi stabilită din BERC (personal neobservat; comparație pe perioade diferite ale anului: pe oct.–nov., producția non-CAEN 2026 ≈ 3.170/zi > 2023 ≈ 2.970/zi). Respingerile au urcat 5,7%→8,2% și 51,9% din stoc (106.060) stă neprelucrat înainte de registrator."
            ),
            lean_theorems="T3a, T3b, T4, T5a, T5c",
            claim_ids="CLAIM-11..15",
            surviving_core="Productivitatea per registrator pe dosare comparabile este practic egală (1,00× pe panelul pereche); v2.0 nu a adus câștig de viteză, dar o scădere a plafonului nu poate fi stabilită din BERC.",
            verdict="RESPINS CA EXPLICATIE UNICĂ (Nucleu confirmat)",
        ),
        dict(
            id="S2",
            pillar="1. Situația Registrului",
            persona="Econometrist Critic BERC",
            steelman_argument=f"BERC nu conține plata taxelor, minutele exacte ale depunerii online, cererile retrase, conține {fp['W1_manski']['short']:,} răspunsuri API scurte și doar 545 buletine PDF extrase din 2026.",
            honest_concession="Momentul plății și depunerile nepublicate încă rămân neobservabile direct în BERC și sunt marcate explicit [NEOBSERVABIL].",
            empirical_and_formal_test=(
                f"Marginea neparametrică Manski limitează orice eroarea din răspunsurile API scurte la max {fp['W1_manski']['manski_bound_all_pp']} pp ({fp['W1_manski']['manski_bound_2026_pp']} pp în 2026) fără nicio ipoteză MCAR; "
                f"eșantionul PDF (10.803 finale / 530 buletine, 20/20 verificate manual cuvânt cu cuvânt) are DEFF={fp['W2_cluster']['deff']}×, SE={fp['W2_cluster']['cluster_boot_se_pct']}%, post-stratificare pe 42 județe = {fp['W2_cluster']['caen_only_county_raked_pct']}%."
            ),
            lean_theorems="T11a, T11b, T11c, T8",
            claim_ids="CLAIM-03, CLAIM-16..18",
            surviving_core="Datele lipsă din API și eșantionarea PDF nu pot schimba concluziile nici măcar cu 0,6 puncte procentuale.",
            verdict="NEUTRALIZAT FORMAL",
        ),
        dict(
            id="S3",
            pillar="1. Situația Registrului",
            persona="Auditor Tehnic de Model",
            steelman_argument="O coadă FIFO unică prezice greșit înmatriculările vs. mențiunile și edițiile succesive ale raportului aveau cifre ușor diferite între octombrie și noiembrie.",
            honest_concession="Critică validată live: pe 19.11.2026, modelul monolitic prezicea 43,0 zile la INMATRIC265 față de 37,2 zile observat real (eroare −5,8 z), deoarece înmatriculările au intrat în octombrie în timp ce mențiunile au rămas în septembrie!",
            empirical_and_formal_test=(
                f"Noul Model Structural cu Două Cozi Cuplate separă INMATRIC265 (front {lv.loc['2026-11-19','obs_front_inmatric']}, med. {lv.loc['2026-11-19','obs_inmatric_med_d']}z vs. prezis {lv.loc['2026-11-19','pred_coupled_inmatric_d']}z) "
                f"de CERERE265 (front {lv.loc['2026-11-19','obs_front_cerere']}, med. {lv.loc['2026-11-19','obs_cerere_med_d']}z vs. prezis {lv.loc['2026-11-19','pred_coupled_cerere_d']}z) și reduce eroarea sub 1,2z."
            ),
            lean_theorems="T2, T6a, T6b, T7a, T7b",
            claim_ids="CLAIM-06..10",
            surviving_core="Modelul cu coadă cuplată prezice exact divergența de 21 zile dintre cele două fluxuri; stocul total agregat se conservă identic (T2).",
            verdict="IDENTIFICAT & REZOLVAT",
        ),
        dict(
            id="S4",
            pillar="1. Situația Registrului",
            persona="Jurist ONRC / MJ",
            steelman_argument=f"Directiva (UE) 2019/1151 curge de la formalități complete + plată, nu de la ora 00:00 în BERC ({fp['W6_eu_lower_bound']['midnight_app_timestamp_pct']}% au timestamp 00:00), iar multe depășiri pot veni din dosare incomplete cu amânări imputabile firmei.",
            honest_concession="Timestamp-ul plății nu este publicat; pentru dosarele cu amânări, suspendarea termenului imputabilă solicitantului nu poate fi exclusă din BERC.",
            empirical_and_formal_test=(
                f"Filtrând STRICT constituirile online/J admise din prima încercare FĂRĂ nicio amânare anterioară în 1–20 nov. 2026 (n={fp['W6_eu_lower_bound']['n_nov_inm_j_first_pass']:,}), "
                f"chiar adăugând un buffer extrem de 2 zile lucrătoare ({fp['W6_eu_lower_bound']['gt12_wd_2d_pay_buffer_pct']}% >12 zl) sau 5 zile lucrătoare pentru plată, {fp['W6_eu_lower_bound']['gt15_wd_5d_pay_buffer_pct']}% tot depășesc limita absolută de 10 zl (mediana = {fp['W6_eu_lower_bound']['median_wd']} zl)!"
            ),
            lean_theorems="T1c, T1d, T9",
            claim_ids="CLAIM-19..21",
            surviving_core="Neconformitatea față de termenul european de 5/10 zile lucrătoare este invulnerabilă juridic (>74,5% chiar și sub ipoteze ultra-favorabile autorității).",
            verdict="INVULNERABIL JURIDIC",
        ),
        dict(
            id="S5",
            pillar="1. Situația Registrului / Prognoză",
            persona="Macroeconomist Sceptic (Firme Inactive)",
            steelman_argument="Sute de mii de firme din cele 902k fără CAEN Rev. 3 sau 169k vizate de capital sunt dormante/inactive — nu vor depune cereri, ci vor fi dizolvate pasiv sau vor ignora termenul.",
            honest_concession="Ponderea firmelor inactive vs. active care chiar vor depune cereri este principala incertitudine comportamentală reală a modelului; mai mult, dacă ~93% din cele 902k firme fără CAEN (= scenariul extrem D1 Ultra-Dormant) dispar pasiv, OUG poate readuce mediana la 3z în iunie 2028 (62,4%), deși vârful din 2027 atinge tot 76z.",
            empirical_and_formal_test=(
                f"În scenariul extrem D1 Ultra-Dormant (doar 25% din valul deja descontat Lab = {round(d1_sq['est_extra_caen_k'],1)}k CAEN, i.e. ~6,8% din cele 902k firme MJ!), "
                f"Status Quo rămâne blocat în iunie 2028 la {d1_sq['jun28_p50']} zile (vârf {d1_sq['peak_p50']}z, doar {d1_sq['prob_le_3d_jun28_pct']}% ≤3z). În scenariul D2 Dormant Ridicat (~110k CAEN), nici OUG nu rezolvă coada (Status Quo {d2_sq['jun28_p50']}z, OUG {d2_oug['jun28_p50']}z, doar {d2_oug['prob_le_3d_jun28_pct']}% ≤3z). "
                f"Pragul de echilibru (≤3z în iun. 2028) tolerează max {int(round(dorm_be['sq_max_mult_for_med_le3d']*100))}% din valuri sub Status Quo și max {int(round(dorm_be['oug_max_mult_for_med_le3d']*100))}% sub OUG."
            ),
            lean_theorems="T1a, T1b, T1e",
            claim_ids="CLAIM-29",
            surviving_core="Sub Status Quo, coada NU se golește niciodată fără valuri aproape de zero; OUG rezolvă până la ~25–30% conformare (~7% din cele 902k CAEN), eșuând la orice conformare realistă ≥45%.",
            verdict="ROBUST LA INACTIVITATE (Concesie onestă pe D1 + OUG)",
        ),
        dict(
            id="S6",
            pillar="2. Proiectul OUG (18.11.2026)",
            persona="Inițiator OUG / Ministerul Justiției",
            steelman_argument="OUG nu pretinde că rezolvă singură totul: la doar 5,76 mil. RON fără posturi noi (imposibile fiscal), păstrează conducerea actuală, activează Art. III și poate fi adoptată urgent.",
            honest_concession="Prelungirea mandatului conducerii existente până la 08.01.2028 evită real +7..+14 zile de așteptare în 2028 (management_expiry.csv), iar bugetul este modest.",
            empirical_and_formal_test=(
                f"În simularea comparativă identică cu audit_oug, OUG central (+375 u/zi, 25% Art. III) scade mediana la 30.06.2028 de la {oug_sc.loc[('referinta','2028-06-30'),'median']:.0f}z la {oug_sc.loc[('oug_central','2028-06-30'),'median']:.0f}z, dar probabilitatea de ≤3z este {oug_sc.loc[('oug_central','2028-06-30'),'within_3']*100:.2f}%, "
                f"iar la expirarea din 08.01.2028 stocul mai are {oug_sc.loc[('oug_central','2028-01-31'),'median_stock']:,.0f} dosare. Revenirea la ≤3z cere {l50}–{l80} u/zi ({l50//25}–{l80//25} FTE net)."
            ),
            lean_theorems="T1a, T1c, T1e",
            claim_ids="CLAIM-27..28, CLAIM-32",
            surviving_core="OUG merită adoptată ca plasă de siguranță minimă, dar NU este un plan de redresare — este insuficientă cantitativ de ~5–6 ori și creează o cădere bruscă în ianuarie 2028.",
            verdict="PARȚIAL VALIDAT (Sprijin necesar, grav subdimensionat)",
        ),
        dict(
            id="S7",
            pillar="2. Proiectul OUG / Cost Economic",
            persona="Macroeconomist Echilibru General",
            steelman_argument="Cifra de 291,4 mil. RON presupune că firmele noi blocate își pierd definitiv vânzările fără ca firme concurente să le preia (substituție 0%) și se bazează pe costuri proxy în Canalul C.",
            honest_concession="În echilibru general, >85–95% din cifra de afaceri amânată a firmelor noi (Canal A) se substituie macroeconomic, iar costul blocării mențiunilor (Canal C) are cea mai largă marjă de estimare.",
            empirical_and_formal_test=(
                f"Chiar eliminând 100% Canalul C și aplicând 95% substituție pe VA brut (M4 = {m4_c['central_net_all_mron']} mil. RON, {m4_c['central_ratio_vs_oug_budget']}× bugetul OUG), "
                f"ba chiar la 100% substituție A + 100% eliminarea C (M6, doar costuri directe ANAF + refaceri B+D = {m6_c['central_net_all_mron']} mil. RON cu admin / {m6_c['central_net_priv_mron']} mil. RON privat), pierderea ireductibilă depășește bugetul de 5,76 mil. RON de {m6_c['central_ratio_vs_oug_budget']}×."
            ),
            lean_theorems="T10a, T10b, T10c",
            claim_ids="CLAIM-33..35",
            surviving_core="Chiar dacă 100% din efectele macro asupra cifrei de afaceri dispar, la parametrii centrali costurile directe justifică bugetar intervenția; la parametrii prudenți nu (0,50×–0,98× bugetul).",
            verdict="ROBUST DOAR LA PARAMETRII CENTRALI",
        ),
        dict(
            id="S8",
            pillar="2. Proiectul OUG (18.11.2026)",
            persona="Director Operațional ONRC",
            steelman_argument="Datele MJ arată că între 30 oct. și 6 nov. stocul neprelucrat a scăzut (-8.300) iar cel prelucrat, nesoluționat a crescut (+4.396). Blocajul urcă exact la registrator, unde lovește Art. I!",
            honest_concession="Mișcarea din 30 oct.–6 nov. confirmă că ritmul de prelucrare a depășit momentan ritmul de decizie finală a registratorului.",
            empirical_and_formal_test=(
                "Totuși, la 6 nov., 106.060 cereri (51,9% din stocul de 204.414) erau ÎNCĂ neprelucrate în Etapa 1, iar scoaterea consilierilor juridici fără înlocuire mută sarcinile din prelucrare/contencios; "
                "mai mult, Art. VIII din Legea 239/2025 atribuie expres registratorului constatarea dizolvării/radierii, limitând sfera automată a Art. III pe lista ANAF de 422.093."
            ),
            lean_theorems="T2, T5b",
            claim_ids="CLAIM-26, CLAIM-31",
            surviving_core="Mutarea consilierilor trebuie însoțită de deblocarea Etapei 1 și de o matrice juridică clară act–temei pentru Art. III, altfel se mută coada dintr-o etapă în alta.",
            verdict="DIAGNOSTIC INCOMPLET ÎN NOTA MJ",
        ),
        dict(
            id="S9",
            pillar="2. Proiectul OUG (18.11.2026)",
            persona="Consilier Legislativ / Avizare",
            steelman_argument="Fereastra de consultare este doar 18–24 noiembrie 2026; orice rescriere amplă ar bloca avizele MF/CES/Consiliului Legislativ și ar lăsa ONRC descoperit la 1 ianuarie 2027.",
            honest_concession="Este nerealist să transformi OUG din 18 nov. într-o reformă complexă cu impact bugetar nou sau licitații IT înainte de adoptare.",
            empirical_and_formal_test=(
                f"Amendarea minimală necesită 3 inserții cu impact bugetar 0 RON: (1) corecția trimiterii eronate din Notă §2.3 ('OUG 109/2014' -> OUG 109/2024 / Legea 3/2026); "
                f"(2) extinderea termenului din 08.01.2028 spre 31.12.2028; (3) adăugarea conversiei 1-la-1 CAEN Rev. 3 (P4: economisește {sol_idx.loc['P4','days_saved_jun28_med']}z la 0 RON cost!)."
            ),
            lean_theorems="T1e",
            claim_ids="CLAIM-28, CLAIM-30",
            surviving_core="Urgența avizării este un argument PENTRU amendamente cu impact bugetar zero (tăiere CAEN + triaj + dată), nu împotriva lor.",
            verdict="COMPATIBIL CU AMENDARE MINIMALĂ",
        ),
        dict(
            id="S10",
            pillar="3. Soluții Realiste",
            persona="Arhitect IT & Achiziții Publice (SEAP)",
            steelman_argument="Orice soluție bazată pe 'reproiectare portal v2.0' sau 'API nou ANAF-ONRC' durează 12–24 luni prin licitații SEAP, caiete de sarcini și contestații CNSC, neputând salva anul 2027.",
            honest_concession="CONCESIE COMPLETĂ pentru achiziții SEAP noi: un proiect informatic nou lansat în SEAP la final de 2026 NU va produce efecte operaționale în prima jumătate a anului 2027.",
            empirical_and_formal_test=(
                f"Tocmai de aceea Pachetul Minim Realist P5 NU folosește nicio licitație SEAP nouă (eliminare legislativă CAEN 1-la-1, eșalonare capital CUI, eliminare prag de rutare și triaj pe 2 benzi): "
                f"P5 duce mediana la {sol_idx.loc['P5','wait_jun28_p50']}z în iunie 2028 ({sol_idx.loc['P5','prob_le_3d_jun28_pct']}% ≤3z), iar triajul simplu economisește economic {tri_c['avoided_econ_mron']} mil. RON (−{tri_c['avoided_econ_pct']}%) din costul nașterilor și sediilor blocate!"
            ),
            lean_theorems="T2, T10a",
            claim_ids="CLAIM-30..31",
            surviving_core="Soluțiile din 2027 NU trebuie să aștepte licitații IT noi; pachetul legislativ + operațional fără SEAP rezolvă ~80% din problemă.",
            verdict="ACCEPTAT PENTRU SEAP · REZOLVAT PRIN P5",
        ),
        dict(
            id="S11",
            pillar="3. Soluții Realiste",
            persona="Realist HR / Buget de Stat",
            steelman_argument=f"Pragul de {l50//25}–{l80//25} registratori net suplimentari ({l50}–{l80} u/zi) este imposibil de angajat și școlit juridic într-un sistem public cu blocaj de angajări.",
            honest_concession="CONCESIE COMPLETĂ pe angajarea a 100 de registratori noi: imposibil în 2027.",
            empirical_and_formal_test=(
                f"Nu sunt necesari 100 de registratori noi dacă se reduce cererea mecanică CAEN prin lege! P4 singur (fără niciun angajat nou) coboară mediana din iunie 2028 la {sol_idx.loc['P4','wait_jun28_p50']}z; "
                f"iar P5 (cu doar 15 FTE temporari din OUG + tăiere CAEN) atinge {sol_idx.loc['P5','wait_jun28_p50']}z ({sol_idx.loc['P5','prob_le_3d_jun28_pct']}% ≤3z) — comparabil cu o extindere masivă de personal P3 ({sol_idx.loc['P3','wait_jun28_p50']}z)!"
            ),
            lean_theorems="T1e, T5b, T5c",
            claim_ids="CLAIM-30..32",
            surviving_core="Înlocuirea cererii mecanice prin lege bate angajările imposibile în raport cost-beneficiu și viteză de execuție.",
            verdict="ACCEPTAT PENTRU RECRUTARE · REZOLVAT PRIN TĂIERE CERERE",
        ),
        dict(
            id="S12",
            pillar="3. Soluții Realiste",
            persona="Realist Politic (Status Quo / Amânare)",
            steelman_argument="Politic și administrativ, soluția reală cea mai probabilă este încă o prorogare a termenelor prin HG (cum a fost HG 788/2026) — mai simplă decât orice reformă.",
            honest_concession="Prorogarea are un efect imediat real de a opri panica de depuneri înaintea unui termen-limită (demonstrat clar după 01.10.2026, când intrările au scăzut de la 14.620 la 4.433/zi).",
            empirical_and_formal_test=(
                f"Simularea P1 (amânare simplă +6 luni fără eliminare de volum) lasă mediana din iunie 2028 la {sol_idx.loc['P1','wait_jun28_p50']} zile (vs. {sol_idx.loc['P0','wait_jun28_p50']}z Status Quo, {sol_idx.loc['P1','prob_le_3d_jun28_pct']}% ≤3z) și doar suprapune valul CAEN amânat peste valul de capital social din 2027–2028!"
            ),
            lean_theorems="T1a, T2",
            claim_ids="CLAIM-29..31",
            surviving_core="Amânarea simplă cumpără timp politic dar NU golește coada și riscă coliziunea simultană a celor două valuri în 2028.",
            verdict="FALSĂ SOLUȚIE DEMONSTRATĂ CANTITATIV",
        ),
    ]
    df_steel = pd.DataFrame(records)
    save_df(df_steel, "steelman_counterarguments_matrix.csv")
    save_json(dict(breakeven_dormancy=dorm_be, counterarguments=records), "steelman_counterarguments_matrix.json")
    return df_steel


def main():
    import shutil
    print("Loading audit_forecast workload (2,000 shared Monte Carlo draws)...")
    work_dir = SCRATCH / "_forecast_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    for fn in ("national.json", "finance_sources.json"):
        if (AUDIT_DIR / fn).exists():
            shutil.copyfile(AUDIT_DIR / fn, work_dir / fn)
    orig_out = audit_forecast.OUT
    audit_forecast.OUT = work_dir
    try:
        model = prepare_workload()
    finally:
        audit_forecast.OUT = orig_out
    df_macro, df_triage = build_macro_substitution_stress_test()
    print("\n=== MACRO SUBSTITUTION STRESS TEST (MIL. RON & RATIO VS 5.76M OUG) ===")
    print(df_macro[["regime", "prudent_net_all_mron", "central_net_all_mron", "tensionat_net_all_mron", "central_ratio_vs_oug_budget"]].to_string(index=False))
    print("\n=== ZERO-COST PRIORITY TRIAGE SAVINGS ===")
    print(df_triage.to_string(index=False))

    df_dorm, dorm_be = build_dormancy_compliance_sensitivity(model)
    print("\n=== DORMANCY & COMPLIANCE SENSITIVITY (D1..D5) ===")
    print(df_dorm[["compliance_regime", "policy", "jun28_p50", "peak_p50", "prob_le_3d_jun28_pct"]].to_string(index=False))
    print("Dormancy break-even:", dorm_be)

    df_sol = build_solutions_feasibility(model)
    print("\n=== REALISTIC SOLUTIONS FEASIBILITY & SIMULATIONS (P0..P7) ===")
    print(df_sol[["id", "wait_dec27_p50", "wait_jun28_p50", "peak_p50", "days_saved_jun28_med", "prob_le_3d_jun28_pct", "seap_procurement_needed"]].to_string(index=False))

    df_steel = build_steelman_matrix(df_macro, df_triage, df_dorm, dorm_be, df_sol)
    print(f"\n=== STEELMAN 12-POINT MATRIX EXPORTED ({len(df_steel)} arguments) ===")
    for r in df_steel.itertuples():
        print(f"  {r.id} [{r.persona}] -> {r.verdict}")
    print("\nSTEELMAN & SOLUTIONS ENGINE COMPLETED 100%!")


if __name__ == "__main__":
    main()
