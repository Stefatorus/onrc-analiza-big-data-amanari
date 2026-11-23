"""Verificarea analizei de impact economic și fiscal (analysis/policy_paper_ro/audit_costs.py, 21.11.2026).

1. Reimplementare independentă a celor patru canale, din descrierea lor, pe intrările publicate (cost_inputs.csv,
   cost_observed_exposure.csv) -> trebuie să reproducă cost_scenarios.csv.
2. Renumărarea intrărilor măsurate din arhiva BERC curentă (aceeași fereastră: decizii 1.08–18.11.2026) și efectul
   asupra totalurilor.
3. Ponderea fiecărui canal și parametrii care mișcă cel mai mult rezultatul (cost_sensitivity.csv).
4. Comparația cu bugetul OUG sub substituție macroeconomică (macro_substitution_stress_test.csv).
Ieșire: out/cost_check.json. Nu modifică fișierele analizei.
"""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
AD = HERE.parent / "analysis" / "policy_paper_ro" / "audit_data"
OUT = HERE / "out" / "cost_check.json"


def ledger(r, ex):
    pb = r.pending * r.pending_new_j_share
    pc = r.pending * (1 - r.pending_new_j_share - .12)          # 12% din stoc: înființări non-J și alte tipuri, în afara canalelor
    a_turn = (ex["observed_new_j_excess_days"] + pb * r.pending_new_excess_days) * r.net_turnover_per_day
    a_lost = a_turn * r.lost_turnover_fraction
    late = pc * (.75 if r.pending_changes_excess_days >= 30 else .25)
    b_n = (ex["observed_changes_over_30"] + late) * r.seat_share * r.inactivation_increment
    c_days = (ex["observed_changes_excess_days"] + pc * r.pending_changes_excess_days) * r.disjoint_blocked_changes_share
    ch = dict(A=a_lost * r.value_added_share, B=b_n * r.seat_private_cost, C=c_days * r.blocked_change_cost,
              D=ex["postpone_actions"] * r.preventable_post_share * r.private_cost_per_post)
    tax = a_lost * r.tax_share + b_n * r.seat_fiscal_cost + ch["C"] * r.blocked_change_tax_share
    daily_e = pb * r.net_turnover_per_day * r.lost_turnover_fraction * r.value_added_share + pc * r.disjoint_blocked_changes_share * r.blocked_change_cost
    daily_t = pb * r.net_turnover_per_day * r.lost_turnover_fraction * r.tax_share + pc * r.disjoint_blocked_changes_share * r.blocked_change_cost * r.blocked_change_tax_share
    return dict(total=sum(ch.values()), tax=tax, channels=ch, turnover_at_risk=a_turn, lost_sales=a_lost, daily_econ=daily_e, daily_tax=daily_t)


def main():
    inp = pd.read_csv(AD / "cost_inputs.csv").set_index("scenario")
    ex = pd.read_csv(AD / "cost_observed_exposure.csv", index_col=0)["value"].to_dict()
    pub = pd.read_csv(AD / "cost_scenarios.csv").set_index("scenario")
    rep = {}
    for s, r in inp.iterrows():
        m = ledger(r, ex)
        rep[s] = dict(total=m["total"], tax=m["tax"], daily_econ=m["daily_econ"], daily_tax=m["daily_tax"],
                      published_total=float(pub.loc[s, "total_economic"]), published_tax=float(pub.loc[s, "lost_tax"]),
                      published_daily_econ=float(pub.loc[s, "daily_economic_stock"]), published_daily_tax=float(pub.loc[s, "daily_tax_stock"]),
                      channels_share={k: v / m["total"] for k, v in m["channels"].items()},
                      channels=m["channels"], turnover_at_risk=m["turnover_at_risk"], lost_sales=m["lost_sales"])
        for a, b in (("total", "published_total"), ("tax", "published_tax"), ("daily_econ", "published_daily_econ"), ("daily_tax", "published_daily_tax")):
            assert abs(rep[s][a] - rep[s][b]) <= max(1.0, 1e-6 * rep[s][b]), (s, a, rep[s][a], rep[s][b])
    # recount the measured inputs from the current archive, same window and filters
    d = pd.read_pickle("W:/SOLOResearch/analysis_decisions.pkl")[["cat", "app", "res", "sol", "jtype"]]
    d = d[(d.res >= "2026-08-01") & (d.res < "2026-11-19")].copy()
    d["w"] = (d.res - d.app).dt.total_seconds() / 86400
    d = d[d.w.between(0, 365)]
    b = d[(d.cat == "INMATRIC265") & (d.jtype == "J") & (d.sol == "Admis")]; c = d[(d.cat == "CERERE265") & (d.sol == "Admis")]
    ex_now = dict(approved_new_j=len(b), approved_changes=len(c), postpone_actions=int((d.cat == "AUTO_AMANARI").sum()),
                  observed_new_j_excess_days=float((b.w - 3).clip(lower=0).sum()), observed_changes_excess_days=float((c.w - 3).clip(lower=0).sum()),
                  observed_changes_over_30=int((c.w > 30).sum()))
    recount = {s: ledger(r, ex_now) for s, r in inp.iterrows()}
    sens = pd.read_csv(AD / "cost_sensitivity.csv")
    sens["swing"] = sens.economic_high - sens.economic_low
    top = sens.sort_values("swing", ascending=False).head(5)[["parameter", "prudent", "central", "tense", "economic_low", "economic_high"]]
    mac = pd.read_csv(AD / "macro_substitution_stress_test.csv")
    oug_budget = float((mac.central_net_all_mron / mac.central_ratio_vs_oug_budget).median())
    out = dict(
        _meta="Verificarea analizei de impact economic și fiscal (audit_costs.py, 21.11.2026). Reimplementare independentă + renumărare pe arhiva curentă.",
        window="decizii 1.08.2026–18.11.2026; zile în exces = așteptare peste 3 zile calendaristice",
        reproduced=True, scenarios=rep,
        exposure_published=ex, exposure_recount=ex_now,
        exposure_change_pct={k: 100 * (ex_now[k] / ex[k] - 1) for k in ex},
        recount_totals={s: dict(total=recount[s]["total"], tax=recount[s]["tax"],
                                total_change_pct=100 * (recount[s]["total"] / rep[s]["total"] - 1),
                                tax_change_pct=100 * (recount[s]["tax"] / rep[s]["tax"] - 1)) for s in recount},
        sensitivity_top=top.to_dict(orient="records"),
        macro=mac.to_dict(orient="records"), oug_budget_mil_lei=oug_budget,
        formation=pd.read_csv(AD / "formation_turnover.csv").to_dict(orient="records"))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    c = rep["central"]
    print("reproduced all 3 scenarios; central", round(c["total"] / 1e6, 2), "mil lei; channel shares",
          {k: round(100 * v, 1) for k, v in c["channels_share"].items()})
    print("recount change %", {k: round(v, 1) for k, v in out["exposure_change_pct"].items()})
    print("recount totals %", {s: round(v["total_change_pct"], 1) for s, v in out["recount_totals"].items()}, "OUG budget", round(oug_budget, 2))


if __name__ == "__main__":
    main()
