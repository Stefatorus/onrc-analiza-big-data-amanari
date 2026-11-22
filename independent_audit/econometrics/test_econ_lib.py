"""Test econ_lib on simulated data: (1) OLS with FE equals statsmodels with dummies + cluster SE;
(2) 2SLS recovers beta under endogeneity and its 95% CI covers ~95% over Monte Carlo reps;
(3) AR CI contains the truth at roughly nominal rate. Seeded."""
import numpy as np
import pandas as pd
import econ_lib as E


def simulate(rng, G=42, T=40, per=12, beta=-0.004, pi=0.8):
    n = G * T * per
    g = np.repeat(np.arange(G), T * per)
    t = np.tile(np.repeat(np.arange(T), per), G)
    a_g, a_t = rng.normal(0, 1, G)[g], rng.normal(0, 1, T)[t]
    shock_gt = rng.gamma(2, 3, (G, T))[g, t]                   # office-week congestion
    ability = rng.normal(0, 1, n)
    wait = 2 + pi * shock_gt + 1.5 * a_g + a_t + 3 * np.maximum(0, -ability) + rng.normal(0, 2, n)
    # LOO-style instrument: noisy measure of the cell congestion
    z = shock_gt + rng.normal(0, 0.5, n)
    y = 0.6 + beta * wait + 0.05 * ability + 0.02 * a_g + 0.01 * a_t + rng.normal(0, .3, n)
    return pd.DataFrame(dict(y=y, wait=wait, z=z, g=g, t=t, x=rng.normal(0, 1, n)))


def main():
    rng = np.random.default_rng(20261122)
    d = simulate(rng, G=20, T=10, per=10)
    r = E.fit(d.y, {"wait": d.wait, "x": d.x}, d[["g", "t"]], d.g)
    try:
        import statsmodels.formula.api as smf
        m = smf.ols("y ~ wait + x + C(g) + C(t)", d).fit(cov_type="cluster", cov_kwds={"groups": d.g})
        print("OLS coef mine vs statsmodels:", r["coef"]["wait"], m.params["wait"])
        print("OLS SE   mine vs statsmodels:", r["se"]["wait"], m.bse["wait"])
        assert abs(r["coef"]["wait"] - m.params["wait"]) < 1e-8
        # statsmodels counts all dummies in K; mine follows reghdfe (FE nested in cluster not counted)
        assert abs(r["se"]["wait"] / m.bse["wait"] - 1) < 0.05
    except ImportError:
        print("statsmodels not available; skipping cross-check")
    cover_iv = cover_ar = 0
    bias_ols, bias_iv = [], []
    R = 200
    for _ in range(R):
        d = simulate(rng)
        o = E.fit(d.y, {"wait": d.wait}, d[["g", "t"]], d.g)
        iv = E.fit(d.y, {"wait": d.wait}, d[["g", "t"]], d.g, endog="wait", instr={"z": d.z})
        bias_ols.append(o["coef"]["wait"] + 0.004)
        bias_iv.append(iv["coef"]["wait"] + 0.004)
        lo, hi = iv["ci95"]["wait"]
        cover_iv += lo <= -0.004 <= hi
        cover_ar += E.ar_pvalue(iv, -0.004) > .05
    print(f"mean bias OLS {np.mean(bias_ols):+.5f}  2SLS {np.mean(bias_iv):+.5f} (truth -0.004)")
    print(f"2SLS 95% CI coverage {cover_iv / R:.3f}; AR coverage {cover_ar / R:.3f}; last F {iv['first_stage']['F_cluster_robust']:.0f}")
    assert abs(np.mean(bias_iv)) < 0.001 and abs(np.mean(bias_ols)) > 2 * abs(np.mean(bias_iv))
    assert 0.90 <= cover_iv / R <= 0.99 and 0.90 <= cover_ar / R <= 0.99
    # joint estimation equals separate estimation; two-way runs
    d = simulate(rng)
    d["y2"] = 2 * d.y + rng.normal(0, .1, len(d))
    jm = E.fit({"a": d.y, "b": d.y2}, {"wait": d.wait}, d[["g", "t"]], d.g, endog="wait", instr={"z": d.z})
    sa = E.fit(d.y, {"wait": d.wait}, d[["g", "t"]], d.g, endog="wait", instr={"z": d.z})
    assert abs(jm["a"]["coef"]["wait"] - sa["coef"]["wait"]) < 1e-12 and abs(jm["a"]["se"]["wait"] - sa["se"]["wait"]) < 1e-12
    assert abs(np.sqrt(jm["_joint"]["vcov"][0, 0]) - sa["se"]["wait"]) < 1e-12
    tw = E.fit(d.y, {"wait": d.wait}, d[["g", "t"]], d.g, endog="wait", instr={"z": d.z}, cluster2=d.t)
    print("two-way SE", tw["se"]["wait"], "one-way", sa["se"]["wait"])
    print("econ_lib tests passed")


if __name__ == "__main__":
    main()
