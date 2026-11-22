"""PART A — efectul cauzal al duratei de înmatriculare asupra firmelor noi (micro-econometrie).

Intrări: _work/sample.pkl, _work/inmatric_all.pkl (din 01_build_sample.py, record-level, șterse la final).
Ieșiri (DOAR agregate): tables/*.csv, partA_results.json (coeficienți, CI, n, F), folosite de 04_/05_.

Design-uri:
  (i)   OLS: FE săptămâna depunerii + FE oficiu (județ) + formă juridică; SE cluster pe oficiu (42).
  (ii)  2SLS: durata proprie instrumentată cu mediana leave-one-out a duratei celorlalte cereri de
        înmatriculare (orice formă) depuse la același oficiu în aceeași săptămână; F cluster-robust,
        interval Anderson-Rubin. Variantă: media LOO; SE two-way (oficiu x săptămână).
        Variantă „șoc național”: cohortele 2023+2024, instrument = mediana națională LOO pe săptămâna
        depunerii, FE săptămâna-din-an + cohortă + oficiu x cohortă (sezonalitate eliminată prin 2023).
  (iii) Trepte (bins) de durată: OLS pe durata proprie + formă redusă pe treptele instrumentului.
  (iv)  Placebo: atribute predeterminate pe instrument (aceleași FE).
  (v)   DiD: depuneri aug.–nov. vs iun.–25 iul., 2024 vs 2023 (anul complet următor) și 2024 vs 2025
        (primul an parțial); Wald-DiD = efect pe zi.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import econ_lib as E

HERE = Path(__file__).resolve().parent
WORK = HERE / "_work"
TAB = HERE / "tables"
BINS = [(0, 2), (3, 7), (8, 14), (15, 30), (31, 60), (61, 10_000)]
BIN_LABELS = ["0-2", "3-7", "8-14", "15-30", "31-60", ">60"]
MIN_CELL = 5  # minimum other filings in office-week cell


# ---------------------------------------------------------------- instrument
def loo_stats(cells_all: pd.Series, waits_all: pd.Series, cells_s: pd.Series, waits_s: pd.Series):
    """Leave-one-out median/mean/count of wait in each cell, removing one instance of the unit's own wait."""
    grp = {k: np.sort(v.to_numpy()) for k, v in waits_all.groupby(cells_all.to_numpy())}
    pairs = pd.DataFrame({"c": cells_s.to_numpy(), "w": waits_s.to_numpy()})
    uniq = pairs.drop_duplicates()
    med, mean, cnt = [], [], []
    for c, w in uniq.itertuples(index=False):
        s = grp.get(c)
        if s is None:
            med.append(np.nan); mean.append(np.nan); cnt.append(0); continue
        r = np.searchsorted(s, w, "left")
        if r < len(s) and s[r] == w:
            rest = np.delete(s, r)
        else:                                   # own record not in the pool (should not happen)
            rest = s
        cnt.append(len(rest))
        med.append(np.median(rest) if len(rest) else np.nan)
        mean.append(rest.mean() if len(rest) else np.nan)
    uniq = uniq.assign(med=med, mean=mean, cnt=cnt)
    m = pairs.merge(uniq, on=["c", "w"], how="left")
    return m.med.to_numpy(), m["mean"].to_numpy(), m.cnt.to_numpy()


def add_instruments(s: pd.DataFrame, allr: pd.DataFrame) -> pd.DataFrame:
    allr = allr[allr.sol.isin(["Admis", "Respins"])].copy()
    for d in (s, allr):
        d["week"] = (d.app - pd.to_timedelta(d.app.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
        d["cell"] = d.office + "|" + d.week
    s["z_med"], s["z_mean"], s["z_n"] = loo_stats(allr.cell, allr.wait, s.cell, s.wait)
    s["zn_med"], _, s["zn_n"] = loo_stats(allr.week, allr.wait, s.week, s.wait)
    s.loc[s.z_n < MIN_CELL, ["z_med", "z_mean"]] = np.nan
    return s


# ---------------------------------------------------------------- outcomes
def winsor_pos(x: pd.Series, q=.99):
    cap = x[x > 0].quantile(q)
    return x.clip(upper=cap)


def winsor_both(x: pd.Series, q=.01):
    nz = x[x != 0]
    return x.clip(lower=nz.quantile(q), upper=nz.quantile(1 - q))


def outcomes(s: pd.DataFrame, fy: int, prefix: str) -> pd.DataFrame:
    bs = s[f"bs{fy}"].astype(float)
    g = lambda c: s[f"{c}_{fy}"].astype(float).where(s[f"bs{fy}"], np.nan)
    turn = g("I13").fillna(0).clip(lower=0).where(s[f"bs{fy}"], 0.0)
    emp = g("I20").fillna(0).clip(lower=0).where(s[f"bs{fy}"], 0.0)
    i16, i17, i18, i19 = (g(c).fillna(0).where(s[f"bs{fy}"], 0.0) for c in ("I16", "I17", "I18", "I19"))
    taxA = i16 - i18
    taxB = (i16 - i17) - (i18 - i19)
    o = pd.DataFrame(index=s.index)
    o[prefix + "bs"] = bs
    o[prefix + "tpos"] = (turn > 0).astype(float)
    o[prefix + "lturn"] = np.log1p(turn)
    o[prefix + "turn_w"] = winsor_pos(turn)
    o[prefix + "turnvat_w"] = o[prefix + "turn_w"].where(turn > 395_000, 0.0)   # cifră peste plafonul TVA (395.000 lei), același plafon winsor ca turn_w
    o[prefix + "epos"] = (emp > 0).astype(float)
    o[prefix + "emp_w"] = winsor_pos(emp)
    o[prefix + "taxA_w"] = winsor_both(taxA)
    o[prefix + "taxApos"] = (taxA > 0).astype(float)
    o[prefix + "taxB_w"] = winsor_both(taxB)
    o[prefix + "taxBpos"] = (taxB > 0).astype(float)
    o[prefix + "turn_raw"] = turn
    caen = s[f"CAEN_{fy}"].astype("string").str.zfill(4).str[:2]
    o[prefix + "caen2"] = caen.where(s[f"bs{fy}"], pd.NA)
    return o


OUTCOME_LABELS = {
    "bs": "a depus bilanț (activitate/supraviețuire)", "tpos": "cifră de afaceri > 0", "lturn": "log(1+cifră de afaceri)",
    "turn_w": "cifră de afaceri, lei (winsor p99)", "turnvat_w": "cifră de afaceri peste plafonul TVA, lei",
    "epos": "salariați > 0", "emp_w": "salariați medii (winsor p99)",
    "taxA_w": "impozit direct proxy I16-I18, lei", "taxApos": "I16-I18 > 0",
    "taxB_w": "impozit direct proxy (I16-I17)-(I18-I19), lei", "taxBpos": "(I16-I17)-(I18-I19) > 0",
}
MAIN_Y = ["bs", "tpos", "lturn", "turn_w", "turnvat_w", "epos", "emp_w", "taxA_w", "taxApos", "taxB_w", "taxBpos"]


def form_dummies(s):
    return {"form_SA": (s.form == "SA").astype(float).to_numpy(),
            "form_other": (~s.form.isin(["SRL", "SA"])).astype(float).to_numpy()}


def row(res, term, outcome, spec, sample, design, extra=None):
    lo, hi = res["ci95"][term]
    r = dict(outcome=outcome, label=OUTCOME_LABELS.get(outcome, outcome), spec=spec, design=design, sample=sample,
             term=term, coef=res["coef"][term], se=res["se"][term], ci_lo=lo, ci_hi=hi, p=res["p"][term],
             n=res["n"], clusters=res["clusters"], two_way=res["two_way"], mean_y=res["mean_y"],
             first_stage_F=res.get("first_stage", {}).get("F_cluster_robust", np.nan),
             first_stage_coef=(res.get("first_stage", {}).get("coef") or [np.nan])[0])
    if extra:
        r.update(extra)
    return r


def main():
    TAB.mkdir(exist_ok=True)
    s = pd.read_pickle(WORK / "sample.pkl")
    allr = pd.read_pickle(WORK / "inmatric_all.pkl")
    s = add_instruments(s, allr)
    s["cohort"] = s.app.dt.year
    s["same_year"] = s.res.dt.year == s.app.dt.year
    s["woy"] = s.app.dt.isocalendar().week.astype(int).clip(upper=52)
    s["moy"] = s.app.dt.month
    rows, results = [], {}

    # ======================= main sample: 2024 filers, decided in 2024, outcome FY2025
    A = s[(s.cohort == 2024) & s.same_year].copy()
    A = A.join(outcomes(A, 2025, ""))
    n_drop_next_year = int(((s.cohort == 2024) & ~s.same_year).sum())
    fe = A[["week", "office"]]
    X = form_dummies(A)
    okz = A.z_med.notna()
    print(f"main sample n={len(A)} (dropped decided-in-2025: {n_drop_next_year}); instrument available {okz.mean():.3f}")

    # instrument diagnostics: residual variance after FE
    zres = E.demean(A.loc[okz, ["z_med", "wait"]].to_numpy(), E._codes(A.loc[okz, ["week", "office"]], okz.sum()))
    diag = dict(sd_wait=float(A.wait.std()), sd_z=float(A.z_med.std()), sd_z_resid=float(zres[:, 0].std()),
                sd_wait_resid=float(zres[:, 1].std()), corr_resid=float(np.corrcoef(zres.T)[0, 1]),
                wait_mean=float(A.wait.mean()), wait_p99=float(A.wait.quantile(.99)), wait_max=float(A.wait.max()),
                n_main=int(len(A)), n_dropped_decided_next_year=n_drop_next_year)
    print("instrument diagnostics", diag)

    for y in MAIN_Y:
        ex = {"wait": A.wait.to_numpy(), **X}
        o = E.fit(A[y].to_numpy(), ex, fe, A.office.to_numpy())
        rows.append(row(o, "wait", y, "OLS", "J 2024, FY2025", "OLS FE săpt.+oficiu"))
        A2 = A[okz]
        ex2 = {"wait": A2.wait.to_numpy(), **form_dummies(A2)}
        iv = E.fit(A2[y].to_numpy(), ex2, A2[["week", "office"]], A2.office.to_numpy(), endog="wait",
                   instr={"z_med": A2.z_med.to_numpy()})
        sd = iv["se"]["wait"]
        grid = np.linspace(iv["coef"]["wait"] - 8 * sd, iv["coef"]["wait"] + 8 * sd, 161)
        (alo, ahi), shape = E.anderson_rubin_ci(iv, grid)
        rows.append(row(iv, "wait", y, "2SLS_LOO_median", "J 2024, FY2025", "IV oficiu x săpt. (LOO mediană)",
                        dict(ar_lo=alo, ar_hi=ahi, ar_shape=shape)))
        results[f"iv_{y}"] = iv
        iv2 = E.fit(A2[y].to_numpy(), ex2, A2[["week", "office"]], A2.office.to_numpy(), endog="wait",
                    instr={"z_med": A2.z_med.to_numpy()}, cluster2=A2.week.to_numpy())
        rows.append(row(iv2, "wait", y, "2SLS_LOO_median_2way", "J 2024, FY2025", "IV, SE two-way oficiu x săpt."))
        iv3 = E.fit(A2[y].to_numpy(), ex2, A2[["week", "office"]], A2.office.to_numpy(), endog="wait",
                    instr={"z_mean": A2.z_mean.to_numpy()})
        rows.append(row(iv3, "wait", y, "2SLS_LOO_mean", "J 2024, FY2025", "IV oficiu x săpt. (LOO medie)"))
        rf = E.fit(A2[y].to_numpy(), {"z_med": A2.z_med.to_numpy(), **form_dummies(A2)}, A2[["week", "office"]],
                   A2.office.to_numpy())
        rows.append(row(rf, "z_med", y, "reduced_form", "J 2024, FY2025", "formă redusă pe instrument"))
    fs = E.fit(A2.wait.to_numpy(), {"z_med": A2.z_med.to_numpy(), **form_dummies(A2)}, A2[["week", "office"]], A2.office.to_numpy())
    rows.append(row(fs, "z_med", "wait", "first_stage", "J 2024", "prima etapă"))
    fs2 = E.fit(A2.wait.to_numpy(), {"z_med": A2.z_med.to_numpy(), **form_dummies(A2)}, A2[["week", "office"]],
                A2.office.to_numpy(), cluster2=A2.week.to_numpy())
    diag["first_stage_coef"] = fs["coef"]["z_med"]
    diag["first_stage_F_office"] = float((fs["coef"]["z_med"] / fs["se"]["z_med"]) ** 2)
    diag["first_stage_F_twoway"] = float((fs2["coef"]["z_med"] / fs2["se"]["z_med"]) ** 2)

    # Joint 2SLS for the Part-B revenue bridge (same sample, same instrument)
    jy = {k: A2[k].to_numpy() for k in ["bs", "taxB_w", "taxA_w", "emp_w", "turn_w", "turnvat_w"]}
    joint = E.fit(jy, {"wait": A2.wait.to_numpy(), **form_dummies(A2)}, A2[["week", "office"]], A2.office.to_numpy(),
                  endog="wait", instr={"z_med": A2.z_med.to_numpy()})
    jo = joint["_joint"]
    jo_ols = E.fit({k: A[k].to_numpy() for k in jy}, {"wait": A.wait.to_numpy(), **X}, fe, A.office.to_numpy())["_joint"]
    firm_means = {k: float(A[k].mean()) for k in jy}
    means_se = {k: float(A[k].std() / np.sqrt(len(A))) for k in jy}

    # Conditional on filing, with CAEN 2-digit FE (selected sample; robustness only)
    C = A2[A2.bs == 1]
    C = C[C.caen2.notna()]
    for y in ["lturn", "turn_w", "emp_w", "taxB_w", "tpos"]:
        iv = E.fit(C[y].to_numpy(), {"wait": C.wait.to_numpy(), **form_dummies(C)}, C[["week", "office", "caen2"]],
                   C.office.to_numpy(), endog="wait", instr={"z_med": C.z_med.to_numpy()})
        rows.append(row(iv, "wait", y, "2SLS_conditional_CAEN", "J 2024 cu bilanț FY2025", "IV + FE CAEN 2 cifre, condiționat"))
        o = E.fit(C[y].to_numpy(), {"wait": C.wait.to_numpy(), **form_dummies(C)}, C[["week", "office", "caen2"]], C.office.to_numpy())
        rows.append(row(o, "wait", y, "OLS_conditional_CAEN", "J 2024 cu bilanț FY2025", "OLS + FE CAEN 2 cifre, condiționat"))

    # ======================= national-shock IV: cohorts 2023+2024, next full year
    P = []
    for c, fy in ((2023, 2024), (2024, 2025)):
        q = s[(s.cohort == c) & s.same_year & (s.app >= f"{c}-03-01")].copy()   # arhiva 2023 completă din martie
        P.append(q.join(outcomes(q, fy, "")))
    P = pd.concat(P)
    P["office_c"] = P.office + "_" + P.cohort.astype(str)
    for y in ["bs", "lturn", "turn_w", "emp_w", "taxB_w"]:
        iv = E.fit(P[y].to_numpy(), {"wait": P.wait.to_numpy(), **form_dummies(P)}, P[["woy", "cohort", "office_c"]],
                   P.week.to_numpy(), endog="wait", instr={"zn_med": P.zn_med.to_numpy()})
        rows.append(row(iv, "wait", y, "2SLS_national_week", "J 2023+2024 (din mar.), an complet următor",
                        "IV mediană națională săpt.; FE săpt.-din-an + cohortă + oficiu x cohortă; cluster săpt."))
        iv2 = E.fit(P[y].to_numpy(), {"wait": P.wait.to_numpy(), **form_dummies(P)}, P[["woy", "cohort", "office_c"]],
                    P.office.to_numpy(), endog="wait", instr={"zn_med": P.zn_med.to_numpy()}, cluster2=P.week.to_numpy())
        rows.append(row(iv2, "wait", y, "2SLS_national_week_2way", "J 2023+2024 (din mar.), an complet următor",
                        "idem, SE two-way oficiu x săpt."))

    # ======================= (iii) bins
    def binned(x):
        out = pd.Series(BIN_LABELS[0], index=x.index)
        for (lo, hi), lab in zip(BINS, BIN_LABELS):
            out[(x >= lo) & (x <= hi)] = lab
        return out
    A["wbin"] = binned(A.wait)
    A["zbin"] = binned(A.z_med.round())
    bin_rows = []
    for kind, col, D in (("OLS_own_wait", "wbin", A), ("RF_instrument", "zbin", A[okz])):
        counts = D[col].value_counts()
        labs = [b for b in BIN_LABELS[1:] if counts.get(b, 0) >= 30]
        for y in ["bs", "lturn", "turn_w", "emp_w", "taxB_w", "epos"]:
            ex = {f"b_{b}": (D[col] == b).astype(float).to_numpy() for b in labs}
            ex.update(form_dummies(D))
            o = E.fit(D[y].to_numpy(), ex, D[["week", "office"]], D.office.to_numpy())
            base = float(D.loc[D[col] == "0-2", y].mean())
            bin_rows.append(dict(kind=kind, outcome=y, bin="0-2", coef=0.0, se=0.0, ci_lo=0.0, ci_hi=0.0,
                                 n_bin=int(counts.get("0-2", 0)), mean_ref=base))
            for b in labs:
                lo, hi = o["ci95"][f"b_{b}"]
                bin_rows.append(dict(kind=kind, outcome=y, bin=b, coef=o["coef"][f"b_{b}"], se=o["se"][f"b_{b}"],
                                     ci_lo=lo, ci_hi=hi, n_bin=int(counts.get(b, 0)), mean_ref=base))
            for b in BIN_LABELS[1:]:
                if b not in labs:
                    bin_rows.append(dict(kind=kind, outcome=y, bin=b, coef=np.nan, se=np.nan, ci_lo=np.nan, ci_hi=np.nan,
                                         n_bin=int(counts.get(b, 0)), mean_ref=base, note="<30 obs, neestimat"))
    pd.DataFrame(bin_rows).to_csv(TAB / "event_bins.csv", index=False, float_format="%.6g")

    # ======================= (iv) placebo on predetermined attributes
    pl_rows = []
    A2 = A[okz].copy()
    A2["caen_any"] = A2.caen2.fillna(A2.CAEN_2024.astype("string").str.zfill(4).str[:2])
    A2["filed_any"] = A2.caen_any.notna().astype(float)
    cap = A2.I11_2025.fillna(A2.I11_2024)
    sec = {"G_comert": ("45", "47"), "F_constructii": ("41", "43"), "M_profesional": ("69", "75"),
           "J_IT_media": ("58", "63"), "H_transport": ("49", "53"), "I_HoReCa": ("55", "56"), "C_industrie": ("10", "33")}
    placebos = {"form_SA": ((A2.form == "SA").astype(float), None), "form_other": ((~A2.form.isin(["SRL", "SA"])).astype(float), None),
                "weekend_filing": ((A2.app.dt.dayofweek >= 5).astype(float), None)}
    cond = A2.filed_any == 1
    placebos["log1p_capital"] = (np.log1p(cap.clip(lower=0)), cond & cap.notna())
    placebos["capital_gt_200"] = ((cap > 200).astype(float), cond & cap.notna())
    placebos["capital_ge_5000"] = ((cap >= 5000).astype(float), cond & cap.notna())
    for k, (lo, hi) in sec.items():
        c2 = A2.caen_any.astype(float, errors="ignore") if False else pd.to_numeric(A2.caen_any, errors="coerce")
        placebos["caen_" + k] = (((c2 >= int(lo)) & (c2 <= int(hi))).astype(float), cond)
    for k, (v, mask) in placebos.items():
        D = A2 if mask is None else A2[mask]
        vv = v if mask is None else v[mask]
        o = E.fit(vv.to_numpy(), {"z_med": D.z_med.to_numpy()}, D[["week", "office"]], D.office.to_numpy())
        lo, hi = o["ci95"]["z_med"]
        pl_rows.append(dict(attribute=k, conditional_on_any_balance_sheet=mask is not None, coef_per_day_instrument=o["coef"]["z_med"],
                            se=o["se"]["z_med"], ci_lo=lo, ci_hi=hi, p=o["p"]["z_med"], n=o["n"], mean=float(vv.mean()),
                            implied_change_per_10d_pct_of_mean=float(10 * o["coef"]["z_med"] / vv.mean() * 100) if vv.mean() else np.nan))
    pl = pd.DataFrame(pl_rows)
    pl.to_csv(TAB / "placebo.csv", index=False, float_format="%.6g")

    # ======================= (v) DiD around the 2024 launch
    def window(q, c):
        pre = (q.app >= f"{c}-06-01") & (q.app <= f"{c}-07-25")
        post = (q.app >= f"{c}-08-01") & (q.app <= f"{c}-11-30")
        q = q[pre | post].copy()
        q["shock"] = post[pre | post].astype(float)
        return q
    did_rows = []
    # full-year outcome: 2024 (treated) vs 2023 (control)
    F = []
    for c, fy in ((2023, 2024), (2024, 2025)):
        q = window(s[(s.cohort == c) & s.same_year], c)
        F.append(q.join(outcomes(q, fy, "")))
    F = pd.concat(F)
    # partial first-year outcome: 2024 (treated) vs 2025 (control)
    Pp = []
    for c in (2024, 2025):
        q = window(s[(s.cohort == c) & s.same_year], c)
        o = outcomes(q, c, "")
        dec31 = pd.Timestamp(f"{c}-12-31")
        o["tpd_filing"] = winsor_pos(o.turn_raw / ((dec31 - q.app).dt.days + 1))
        o["tpd_decision"] = winsor_pos(o.turn_raw / ((dec31 - q.res).dt.days + 1))
        Pp.append(q.join(o))
    Pp = pd.concat(Pp)
    counts = {}
    for name, D, treat_year, ys in (("an_complet_urmator_2024_vs_2023", F, 2024, ["wait", "bs", "tpos", "lturn", "turn_w", "epos", "emp_w", "taxB_w", "taxA_w"]),
                                    ("primul_an_partial_2024_vs_2025", Pp, 2024, ["wait", "bs", "tpos", "lturn", "turn_w", "taxB_w", "tpd_filing", "tpd_decision"])):
        D = D.copy()
        D["D"] = ((D.cohort == treat_year) & (D.shock == 1)).astype(float)
        D["office_c"] = D.office + "_" + D.cohort.astype(str)
        D["cell_c"] = D.cohort.astype(str) + "_" + D.shock.astype(int).astype(str)
        counts[name] = D.groupby(["cohort", "shock"]).size().rename("n").reset_index().to_dict(orient="records")
        fe_d = D[["woy", "office_c"]]
        for y in ys:
            r = E.fit(D[y].to_numpy(), {"D": D.D.to_numpy(), **form_dummies(D)}, fe_d, D.office.to_numpy())
            means = D.groupby(["cohort", "shock"])[y].mean()
            did_rows.append(row(r, "D", y, "DiD_reduced_form", name, "DiD (cohortă x aug.–nov.)",
                                dict(cell_means=json.dumps({f"{k[0]}_{int(k[1])}": round(float(v), 4) for k, v in means.items()}))))
            r2 = E.fit(D[y].to_numpy(), {"D": D.D.to_numpy(), **form_dummies(D)}, fe_d, D.office.to_numpy(), cluster2=D.week.to_numpy())
            did_rows.append(row(r2, "D", y, "DiD_reduced_form_2way", name, "DiD, SE two-way oficiu x săpt."))
            if y != "wait":
                w = E.fit(D[y].to_numpy(), {"wait": D.wait.to_numpy(), **form_dummies(D)}, fe_d, D.office.to_numpy(),
                          endog="wait", instr={"D": D.D.to_numpy()})
                did_rows.append(row(w, "wait", y, "Wald_DiD_per_day", name, "Wald-DiD (2SLS, instrument = DiD)"))
                w2 = E.fit(D[y].to_numpy(), {"wait": D.wait.to_numpy(), **form_dummies(D)}, fe_d, D.office.to_numpy(),
                           endog="wait", instr={"D": D.D.to_numpy()}, cluster2=D.week.to_numpy())
                did_rows.append(row(w2, "wait", y, "Wald_DiD_per_day_2way", name, "Wald-DiD, SE two-way"))
    did = pd.DataFrame(did_rows)
    did.to_csv(TAB / "did.csv", index=False, float_format="%.6g")
    # volume of filings (selection into filing): Aug–Nov / Jun–Jul by cohort, all J admitted
    vol = {}
    for c in (2023, 2024, 2025):
        q = window(s[s.cohort == c], c)
        vol[str(c)] = dict(pre=int((q.shock == 0).sum()), shock=int((q.shock == 1).sum()),
                           ratio_shock_to_pre=float((q.shock == 1).sum() / (q.shock == 0).sum()),
                           sa_share=float((q.form == "SA").mean()))

    # ======================= event study by filing month (2024 vs 2023), next full year
    F2 = []
    for c, fy in ((2023, 2024), (2024, 2025)):
        q = s[(s.cohort == c) & s.same_year & (s.moy >= 3) & (s.moy <= 11)].copy()
        F2.append(q.join(outcomes(q, fy, "")))
    F2 = pd.concat(F2)
    F2["office_c"] = F2.office + "_" + F2.cohort.astype(str)
    months = [m for m in range(3, 12) if m != 6]
    ev_rows = []
    for y in ["wait", "bs", "lturn", "turn_w", "taxB_w"]:
        ex = {f"m{m}": ((F2.cohort == 2024) & (F2.moy == m)).astype(float).to_numpy() for m in months}
        ex.update(form_dummies(F2))
        r = E.fit(F2[y].to_numpy(), ex, F2[["woy", "office_c"]], F2.office.to_numpy())
        for m in range(3, 12):
            if m == 6:
                ev_rows.append(dict(outcome=y, month=m, coef=0.0, se=0.0, ci_lo=0.0, ci_hi=0.0))
            else:
                lo, hi = r["ci95"][f"m{m}"]
                ev_rows.append(dict(outcome=y, month=m, coef=r["coef"][f"m{m}"], se=r["se"][f"m{m}"], ci_lo=lo, ci_hi=hi))
    pd.DataFrame(ev_rows).to_csv(TAB / "event_month_2024_vs_2023.csv", index=False, float_format="%.6g")

    # ======================= partial first year: per-day turnover since filing vs since decision
    pt_rows = []
    for c in (2024, 2025):
        q = s[(s.cohort == c) & s.same_year & (s.app <= f"{c}-10-31") & s.z_med.notna()].copy()
        o = outcomes(q, c, "")
        dec31 = pd.Timestamp(f"{c}-12-31")
        q = q.join(o)
        q["tpd_filing"] = winsor_pos(q.turn_raw / ((dec31 - q.app).dt.days + 1))
        q["tpd_decision"] = winsor_pos(q.turn_raw / ((dec31 - q.res).dt.days + 1))
        if c == 2024:
            pj = E.fit({k: q[k].to_numpy() for k in ["turn_w", "taxB_w", "emp_w", "turnvat_w"]},
                       {"wait": q.wait.to_numpy(), **form_dummies(q)}, q[["week", "office"]], q.office.to_numpy(),
                       endog="wait", instr={"z_med": q.z_med.to_numpy()})["_joint"]
            partial_bridge = dict(outcomes=pj["outcomes"], iv_coef=pj["coef"].tolist(), iv_vcov=pj["vcov"].tolist(),
                                  n=int(len(q)), note="2SLS LOO, J depuse 1.01–31.10.2024 și decise în 2024, rezultate FY2024 (an parțial); per zi")
        for y in ["bs", "turn_w", "tpd_filing", "tpd_decision", "lturn", "taxB_w", "emp_w", "turnvat_w"]:
            iv = E.fit(q[y].to_numpy(), {"wait": q.wait.to_numpy(), **form_dummies(q)}, q[["week", "office"]], q.office.to_numpy(),
                       endog="wait", instr={"z_med": q.z_med.to_numpy()})
            rows.append(row(iv, "wait", y, "2SLS_LOO_median", f"J {c}, primul an parțial FY{c} (depuse până la 31.10)",
                            "IV oficiu x săpt., an parțial"))
            if y == "tpd_decision":
                a_rate = float(q.tpd_decision.mean())
        b_turn = [r for r in rows if r["sample"].startswith(f"J {c}, primul") and r["outcome"] == "turn_w"][-1]
        # no catch-up => d turnover / d wait = -a (daily rate after start); full catch-up => 0
        pt_rows.append(dict(cohort=c, beta_turnover_per_day=b_turn["coef"], ci_lo=b_turn["ci_lo"], ci_hi=b_turn["ci_hi"],
                            daily_rate_after_decision=a_rate,
                            share_of_waiting_day_turnover_lost=-b_turn["coef"] / a_rate,
                            share_ci=(-b_turn["ci_hi"] / a_rate, -b_turn["ci_lo"] / a_rate), n=b_turn["n"],
                            mature_daily_turnover_next_FY=(float(A.turn_w.mean() / 365) if c == 2024 else np.nan),
                            F=b_turn["first_stage_F"]))
    pd.DataFrame(pt_rows).to_csv(TAB / "partial_year_catchup.csv", index=False, float_format="%.6g")

    coef = pd.DataFrame(rows)
    coef.to_csv(TAB / "coefficients.csv", index=False, float_format="%.6g")
    pd.DataFrame([diag]).to_csv(TAB / "instrument_diagnostics.csv", index=False, float_format="%.6g")

    out = dict(
        diagnostics=diag, filing_volume_windows=vol, did_cell_counts=counts,
        bridge=dict(outcomes=jo["outcomes"], iv_coef=jo["coef"].tolist(), iv_vcov=jo["vcov"].tolist(),
                    ols_coef=jo_ols["coef"].tolist(), ols_vcov=jo_ols["vcov"].tolist(),
                    mean_per_firm_FY2025=firm_means, mean_se=means_se, n=int(len(A2)),
                    first_stage_F=float(joint["bs"]["first_stage"]["F_cluster_robust"]),
                    note="2SLS LOO oficiu x săpt., J depuse și decise în 2024, rezultate FY2025; per zi de așteptare; "
                         "variabile necondiționate (0 pentru firmele fără bilanț), winsor p99."),
        partial_year_catchup=pt_rows, partial_bridge=partial_bridge,
    )
    (HERE / "partA_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    show = coef[coef.spec.isin(["OLS", "2SLS_LOO_median", "2SLS_national_week"]) & coef["sample"].str.contains("FY2025|următor")]
    print(show[["outcome", "spec", "coef", "ci_lo", "ci_hi", "p", "n", "first_stage_F"]].to_string(index=False))
    print(did[did.spec.isin(["DiD_reduced_form", "Wald_DiD_per_day"])][["sample", "outcome", "spec", "coef", "ci_lo", "ci_hi", "p", "first_stage_F"]].to_string(index=False))
    print(pl[["attribute", "coef_per_day_instrument", "ci_lo", "ci_hi", "p", "n"]].to_string(index=False))
    print(pd.DataFrame(pt_rows).to_string(index=False))
    print(json.dumps(vol, indent=1))


if __name__ == "__main__":
    main()
