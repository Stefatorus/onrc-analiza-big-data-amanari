"""Asamblează ../out/econometrics.json: o intrare per rezultat {id, estimate, ci95, n, method, sample, window, caveat}
(+ câmpuri suplimentare: unit, p, distribution). Doar agregate, din tables/ și part*_results.json."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = HERE / "tables"
OUT = HERE.parent / "out" / "econometrics.json"

UNITS = {"bs": "probabilitate (0–1) per zi", "tpos": "probabilitate per zi", "lturn": "log-puncte per zi",
         "turn_w": "lei cifră de afaceri per firmă per zi", "turnvat_w": "lei per firmă per zi", "epos": "probabilitate per zi",
         "emp_w": "salariați per firmă per zi", "taxA_w": "lei per firmă per zi", "taxApos": "probabilitate per zi",
         "taxB_w": "lei per firmă per zi", "taxBpos": "probabilitate per zi", "wait": "zile",
         "tpd_filing": "lei/zi (cifră/zile de la depunere) per zi de așteptare",
         "tpd_decision": "lei/zi (cifră/zile de la decizie) per zi de așteptare"}
GEN_CAVEAT = ("Identificat pe durate observate 0–93 zile (p99 = 35); rezultate în bilanțuri MF (proxy, nu încasări ANAF); "
              "firmele fără bilanț au 0; variabile monetare winsorizate p99.")


def f(x):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else float(x)


def main():
    entries = []
    coef = pd.read_csv(TAB / "coefficients.csv")
    did = pd.read_csv(TAB / "did.csv")
    pl = pd.read_csv(TAB / "placebo.csv")
    A = json.loads((HERE / "partA_results.json").read_text(encoding="utf-8"))
    B = json.loads((HERE / "partB_results.json").read_text(encoding="utf-8"))
    diag = A["diagnostics"]

    def add(id_, est, ci, n, method, sample, window, caveat, **extra):
        entries.append(dict(id=id_, estimate=f(est), ci95=[f(ci[0]), f(ci[1])] if ci is not None else None, n=n,
                            method=method, sample=sample, window=window, caveat=caveat, **extra))

    win_main = "depuneri 1.01–31.12.2024 decise în 2024; rezultat = bilanț FY2025 (primul an complet)"
    smp_main = "înmatriculări J admise (BERC), legate prin CUI de bilanțurile MF 2024–2025"
    fs = coef[(coef.spec == "first_stage")].iloc[0]
    add("A.prima_etapa.LOO_oficiu_saptamana", fs.coef, (fs.ci_lo, fs.ci_hi), int(fs.n),
        "OLS durată proprie pe mediana LOO a duratei celorlalte înmatriculări depuse la același oficiu în aceeași săptămână; FE săpt.+oficiu",
        smp_main, win_main,
        f"F cluster-robust (oficiu, 42) = {diag['first_stage_F_office']:.0f}; F two-way (oficiu×săpt.) = {diag['first_stage_F_twoway']:.0f}. "
        f"Variația instrumentului după FE: abatere standard {diag['sd_z_resid']:.2f} zile (din {diag['sd_z']:.2f}).",
        unit="zile de așteptare proprie per zi a instrumentului", first_stage_F=diag["first_stage_F_office"],
        first_stage_F_twoway=diag["first_stage_F_twoway"])
    for _, r in coef.iterrows():
        if r.spec in ("first_stage",):
            continue
        tag = {"OLS": "OLS", "2SLS_LOO_median": "IV", "2SLS_LOO_median_2way": "IV_2way", "2SLS_LOO_mean": "IV_media",
               "reduced_form": "forma_redusa", "2SLS_conditional_CAEN": "IV_conditionat_CAEN",
               "OLS_conditional_CAEN": "OLS_conditionat_CAEN", "2SLS_national_week": "IV_national",
               "2SLS_national_week_2way": "IV_national_2way"}[r.spec]
        partial = "parțial" in r["sample"]
        sec = "A.an_partial" if partial else "A.an_urmator"
        coh = "_" + r["sample"][2:6] if partial else ""
        cav = GEN_CAVEAT
        if not np.isnan(r.get("ar_lo", np.nan)):
            cav += f" IC Anderson-Rubin (robust la instrument slab): [{r.ar_lo:.4g}, {r.ar_hi:.4g}]."
        if "conditional" in r.spec:
            cav += " CONDIȚIONAT pe depunerea bilanțului (selecție pe rezultat) - doar robustețe."
        if "national" in r.spec:
            cav += " Variația provine din șocul național pe săptămâni (2024 vs. aceleași săptămâni din 2023); un singur episod - SE pe săptămână."
        if r.spec == "OLS" or r.spec == "OLS_conditional_CAEN":
            cav += " OLS: durata proprie e endogenă (amânări pentru dosare incomplete) - nu e efect cauzal."
        add(f"{sec}{coh}.{tag}.{r.outcome}", r.coef, (r.ci_lo, r.ci_hi), int(r.n), r.design, r["sample"],
            "an parțial al înregistrării" if partial else win_main, cav,
            unit=UNITS.get(r.outcome, "per zi") if r.spec != "reduced_form" else "per zi a instrumentului", p=f(r.p),
            first_stage_F=f(r.first_stage_F), mean_outcome=f(r.mean_y), clusters=int(r.clusters), label=r.label)
    for _, r in did.iterrows():
        tag = {"DiD_reduced_form": "DiD", "DiD_reduced_form_2way": "DiD_2way", "Wald_DiD_per_day": "Wald_DiD_per_zi",
               "Wald_DiD_per_day_2way": "Wald_DiD_per_zi_2way"}[r.spec]
        full = r["sample"].startswith("an_complet")
        cav = ("Comparabil: rezultatul în primul an complet după înregistrare, 2024 (FY2025) vs. 2023 (FY2024); 2025 nu are încă FY2026. "
               if full else
               "Comparabil: primul an PARȚIAL (anul înregistrării), 2024 (FY2024) vs. 2025 (FY2025); grupul pre-2024 e pe platforma veche, "
               "2025 integral pe portal - presupune tendințe paralele între ani pentru diferența aug.–nov. vs. iun.–iul. ")
        cav += "Fereastră pre = 1.06–25.07, șoc = 1.08–30.11, după cohortă; FE săpt.-din-an + oficiu×cohortă."
        add(f"A.DiD.{'an_complet' if full else 'an_partial'}.{tag}.{r.outcome}", r.coef, (r.ci_lo, r.ci_hi), int(r.n), r.design,
            "înmatriculări J admise, decise în anul depunerii", r["sample"], cav,
            unit=("zile" if r.outcome == "wait" and "Wald" not in r.spec else
                  (UNITS.get(r.outcome) if "Wald" in r.spec else "diferență totală (aug.–nov. 2024 vs control)")),
            p=f(r.p), first_stage_F=f(r.first_stage_F))
    for _, r in pl.iterrows():
        add(f"A.placebo.{r.attribute}", r.coef_per_day_instrument, (r.ci_lo, r.ci_hi), int(r.n),
            "atribut predeterminat regresat pe instrument (aceleași FE); trebuie ≈0", smp_main, win_main,
            ("Condiționat pe existența unui bilanț (2024 sau 2025) - capital/CAEN observate doar pentru depunători. " if r.conditional_on_any_balance_sheet else "")
            + f"p = {r.p:.3g}; 13 teste, la 5% ne așteptăm la ~0,65 respingeri din întâmplare.", p=f(r.p),
            mean=f(r["mean"]), unit="per zi a instrumentului")
    for c in A["partial_year_catchup"]:
        add(f"A.an_partial_{c['cohort']}.pondere_cifra_pierduta_per_zi", c["share_of_waiting_day_turnover_lost"], c["share_ci"], c["n"],
            "β(cifră de afaceri an parțial, IV) / rata zilnică medie după decizie", f"J {c['cohort']}, depuse până la 31.10, decise în {c['cohort']}",
            f"FY{c['cohort']}",
            "1 = fiecare zi de așteptare pierde exact o zi de cifră medie (fără recuperare); 0 = recuperare completă în același an. "
            "Valori >1 sunt compatibile cu o rampă de creștere: zilele pierdute sunt la sfârșitul anului, când cifra zilnică e peste medie.",
            unit="raport")
    for k, v in A["filing_volume_windows"].items():
        add(f"A.selectie.volum_depuneri_aug_nov_vs_iun_iul.{k}", v["ratio_shock_to_pre"], None, v["pre"] + v["shock"],
            "raport număr înmatriculări J admise depuse 1.08–30.11 / 1.06–25.07", "BERC", k,
            "Test de selecție în depunere: 2024 (șoc) nu arată o scădere a depunerilor față de 2023/2025.")
    rc = B["revenue_coef_per_waiting_day"]
    add("B.coef_venit_public_per_zi.an_urmator", rc["next_full_year_point"], (rc["next_full_year_draws"]["p025"], rc["next_full_year_draws"]["p975"]),
        A["bridge"]["n"], "combinație liniară a efectelor IV comune: impozit direct (I16−I17)−(I18−I19) + salariați×contribuții la salariul minim + 21%×pondere VA×cifra peste 395.000 lei",
        smp_main, win_main, "Lei venit public pe firmă pe an per zi de așteptare (negativ = pierdere). Interval din 2.000 de extrageri normale multivariate. "
        "Pondere VA 0,20–0,40 (presupunere).", unit="lei/firmă/an per zi")
    add("B.coef_venit_public_per_zi.an_partial", rc["partial_year_point"], (rc["partial_year_draws"]["p025"], rc["partial_year_draws"]["p975"]),
        None, "idem, efecte IV în primul an parțial (FY2024, depuse 1.01–31.10.2024)", "J 2024", "FY2024",
        "SENSIBILITATE (limită superioară) pentru canalul „amânat”: implică pierderea a mai mult de o zi matură de venit per zi de așteptare; ~90% din valoare vine din componenta TVA presupusă.", unit="lei/firmă per zi")
    add("B.venit_public_mediu_firma_noua_pe_zi", rc["mechanical_mean_revenue_per_firm_day"]["p50"],
        (rc["mechanical_mean_revenue_per_firm_day"]["p025"], rc["mechanical_mean_revenue_per_firm_day"]["p975"]), A["bridge"]["n"],
        "medie FY2025 (toate firmele 2024, 0 pentru nedepunători) / 365", smp_main, "FY2025",
        "CALIBRAREA CENTRALĂ a canalului „amânat”: venitul public pe care o firmă nouă medie l-ar fi generat într-o zi.", unit="lei/firmă/zi")
    t = pd.read_csv(TAB / "revenue_at_risk_2027.csv")
    for _, r in t.iterrows():
        add(f"B.risc_2027.{r.scenario}.{r.component}.{r.period}", r.p50, (r.p025, r.p975), 2000,
            "Monte Carlo: motor audit_forecast (2.000 variante, nemodificat) × raport durată înmatriculare/coadă κ × volume lunare × "
            "coeficienți PARTEA A (normal multivariat) × parametri statutari", "înmatriculări J (+ mențiuni, parametric)",
            r.period.replace("_", " "),
            "Milioane lei. estimate = P50; ci95 = P2,5–P97,5 al distribuției. Durate prognozate 55–150 zile, în afara suportului estimării (≤35 zile). "
            "Bază de acumulare (nu decalaj de încasare). Lectura A: venitul din fereastra de așteptare e doar amânat (recuperat după e zile); "
            "lectura B: nu e recuperat. Mențiunile folosesc parametrii din audit_costs.py (neestimați).",
            unit="mil. lei", distribution=dict(mean=r["mean"], p10=r.p10, p50=r.p50, p90=r.p90, p95=r.p95))
    s = pd.read_csv(TAB / "revenue_at_risk_sensitivity.csv")
    for _, r in s.iterrows():
        add(f"B.sensibilitate.{r.sensitivity}", r.B_nerecuperat_p50, None, 2000, "variantă a calculului central (continuitate, an 2027)",
            "idem", "2027", "estimate = P50 lectura B (mil. lei); vezi distribution pentru lectura A și componenta pierdută.",
            unit="mil. lei", distribution={k: f(v) for k, v in r.items() if k not in ("sensitivity", "note")})
    eng = B["engine"]
    add("B.motor.multiplicator_capacitate_coada_eliminata_iun2027", eng["cleared_uplift"], None, 2000,
        "bisecție: cel mai mic spor uniform de capacitate din 4.01.2027 cu care mediana duratei la 30.06.2027 ≤ 3 zile",
        "motor audit_forecast, continuitate", "2027", "Spor de capacitate de soluționare, nu o măsură identificată; arată ordinul de mărime necesar.",
        unit="fracțiune din capacitatea de bază")
    add("B.kappa_durata_inmatriculare_vs_coada", B["kappa"]["mode"], (B["kappa"]["low"], B["kappa"]["high"]), None,
        "raport mediană durată înmatriculări J / mențiuni, pe săptămâna deciziei, ultimele 4 săptămâni complete", "BERC 2026",
        ", ".join(B["kappa"]["weeks"]), "Până la mijlocul lui oct. 2026 raportul era ~1; de atunci înmatriculările sunt prioritizate. Triunghiular (min, medie, 1).")
    out = dict(_meta=dict(
        title="Efectul duratei de înregistrare ONRC asupra firmelor noi și venituri bugetare la risc 2027",
        created="2026-11-22", scripts="independent_audit/econometrics/0*_*.py; seeds 20261121 (motor), 20261122 (Monte Carlo)",
        privacy="doar agregate; fișierele la nivel de înregistrare au fost șterse",
        headline=dict(
            efect_cauzal_an_urmator="nedistinguibil de zero pe toate rezultatele (IV, DiD, IV național)",
            efect_an_partial_2024="semnificativ negativ: −1.434 lei cifră de afaceri și −43 lei impozit direct per zi de așteptare",
            first_stage_F=diag["first_stage_F_office"]),
        statutory_parameters=json.loads((HERE / "statutory_parameters.json").read_text(encoding="utf-8"))["parameters"]),
        results=entries)
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "duplicate ids"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("entries:", len(entries), "->", OUT)


if __name__ == "__main__":
    main()
