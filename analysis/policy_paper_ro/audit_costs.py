"""Build a conditional four-channel cost ledger in lei with stocks and flows kept distinct."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "audit_data"
REFERENCE_STOCK = 204_414  # Ministry of Justice substantiation note, 6 November 2026.


def main():
    data = pd.read_pickle(str(config.BERC_PKL))
    d = data[data.res.between("2026-08-01", "2026-11-19", inclusive="left")].copy()
    d["wait"] = (d.res - d.app).dt.total_seconds() / 86400
    d = d[d.wait.between(0, 365)]
    births = d[d.cat.eq("INMATRIC265") & d.jtype.eq("J") & d.sol.eq("Admis")]
    changes = d[d.cat.eq("CERERE265") & d.sol.eq("Admis")]
    n_post = int(d.cat.eq("AUTO_AMANARI").sum())
    observed_birth_days = births.wait.sub(3).clip(lower=0).sum()
    observed_change_days = changes.wait.sub(3).clip(lower=0).sum()
    observed_late_changes = changes.wait.gt(30).sum()

    inputs = pd.DataFrame([
        ["prudent", 145000, .07, 26, 40, 250, .15, .08, .38, .025, .02, 4000, 500, .15, 35, .08, .08, 350, 75],
        ["central", REFERENCE_STOCK, .105, 38, 54, 425, .35, .13, .45, .05, .06, 7000, 1400, .20, 70, .13, .15, 650, 120],
        ["tensionat", 260000, .14, 55, 70, 650, .55, .18, .50, .085, .12, 11000, 2600, .25, 110, .18, .25, 950, 180],
    ], columns=["scenario", "pending", "pending_new_j_share", "pending_new_excess_days",
                "pending_changes_excess_days", "net_turnover_per_day", "lost_turnover_fraction",
                "tax_share", "value_added_share", "seat_share", "inactivation_increment",
                "seat_private_cost", "seat_fiscal_cost", "disjoint_blocked_changes_share", "blocked_change_cost",
                "blocked_change_tax_share", "preventable_post_share", "private_cost_per_post", "admin_cost_per_post"])
    inputs.to_csv(OUT / "cost_inputs.csv", index=False)
    exposure = dict(approved_new_j=len(births), approved_changes=len(changes), postpone_actions=n_post,
                    observed_new_j_excess_days=observed_birth_days, observed_changes_excess_days=observed_change_days,
                    observed_changes_over_30=int(observed_late_changes))
    pd.Series(exposure, name="value").to_csv(OUT / "cost_observed_exposure.csv")
    def estimate(row):
        pending_births = row.pending * row.pending_new_j_share
        # Keep J creations, other creations and modifications apart. 12% here
        # reserves stock for non-J formations and out-of-scope case types.
        pending_changes = row.pending - pending_births - row.pending * .12
        a_days = observed_birth_days + pending_births * row.pending_new_excess_days
        a_turnover_affected = a_days * row.net_turnover_per_day
        a_lost_sales = a_turnover_affected * row.lost_turnover_fraction
        a_econ = a_lost_sales * row.value_added_share
        a_tax = a_lost_sales * row.tax_share
        pending_late = pending_changes * (.75 if row.pending_changes_excess_days >= 30 else .25)
        b_count = (observed_late_changes + pending_late) * row.seat_share * row.inactivation_increment
        b_econ, b_tax = b_count * row.seat_private_cost, b_count * row.seat_fiscal_cost
        c_days = (observed_change_days + pending_changes * row.pending_changes_excess_days) * row.disjoint_blocked_changes_share
        c_econ, c_tax = c_days * row.blocked_change_cost, c_days * row.blocked_change_cost * row.blocked_change_tax_share
        d_count = n_post * row.preventable_post_share
        d_econ = d_count * row.private_cost_per_post
        d_admin = d_count * row.admin_cost_per_post
        daily_a = pending_births * row.net_turnover_per_day * row.lost_turnover_fraction
        daily_c = pending_changes * row.disjoint_blocked_changes_share * row.blocked_change_cost
        return dict(
            scenario=row.scenario, at_risk_turnover=a_turnover_affected, permanently_lost_turnover=a_lost_sales,
            a_value_added=a_econ, a_tax=a_tax, b_cases=b_count, b_private=b_econ, b_tax=b_tax,
            c_private=c_econ, c_tax=c_tax, d_actions=d_count, d_private=d_econ, d_admin=d_admin,
            total_economic=a_econ + b_econ + c_econ + d_econ, lost_tax=a_tax + b_tax + c_tax,
            daily_economic_stock=daily_a * row.value_added_share + daily_c,
            daily_tax_stock=daily_a * row.tax_share + daily_c * row.blocked_change_tax_share,
        )
    output = pd.DataFrame(estimate(row) for row in inputs.itertuples(index=False))
    assert (output.daily_economic_stock > 0).all() and np.isfinite(output.to_numpy()[:, 1:].astype(float)).all()
    output.to_csv(OUT / "cost_scenarios.csv", index=False, float_format="%.2f")
    prudent, central, tense = list(inputs.itertuples(index=False))
    central_result = estimate(central)
    rows = []
    for key in inputs.columns[1:]:
        low = estimate(central._replace(**{key: getattr(prudent, key)}))
        high = estimate(central._replace(**{key: getattr(tense, key)}))
        rows.append(dict(parameter=key, prudent=getattr(prudent, key),
                         central=getattr(central, key), tense=getattr(tense, key),
                         economic_low=low["total_economic"] - central_result["total_economic"],
                         economic_high=high["total_economic"] - central_result["total_economic"],
                         fiscal_low=low["lost_tax"] - central_result["lost_tax"],
                         fiscal_high=high["lost_tax"] - central_result["lost_tax"],
                         admin_low=low["d_admin"] - central_result["d_admin"],
                         admin_high=high["d_admin"] - central_result["d_admin"]))
    pd.DataFrame(rows).to_csv(OUT / "cost_sensitivity.csv", index=False, float_format="%.5f")
    print(exposure)
    print(output.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
