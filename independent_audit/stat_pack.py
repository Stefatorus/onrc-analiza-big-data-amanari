"""Statistics pack for Volume 2 (statistical annexes) and Volume 3 (advanced statistical report).

Computes every table ONCE from BERC (analysis_decisions.pkl), the myportal sample and the audited
model outputs, and writes out/stat_pack.json (+ one CSV per table in out/stat_pack/). Both volumes
read only this file, so their numbers cannot drift from each other. Definitions are explicit in every
table: "finale stricte" = Admis/Respins/Renunțat; "finale largi" = + certificări (definition of C01);
"zi lucrătoare legală" = Mon–Fri minus Romanian public holidays; "zi cu decizii" = day with >=1 decision.

Run:  ..\\venv\\Scripts\\python.exe -X utf8 stat_pack.py
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); import config  # repo config.py
import json, hashlib, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"; SP = OUT / "stat_pack"; SP.mkdir(exist_ok=True)
PP = HERE.parent / "analysis" / "policy_paper_ro"; AD = PP / "audit_data"
BERC = Path(str(config.BERC_PKL))
STRICT = ["Admis", "Respins", "Renunțat"]
BROAD = STRICT + ["Certificare înscriere în registrul comerțului", "certificare inscriere mentiuni", "Renunțat din oficiu"]
HOL = pd.to_datetime([
    "2023-01-01", "2023-01-02", "2023-01-06", "2023-01-07", "2023-01-24", "2023-04-14", "2023-04-16", "2023-04-17", "2023-05-01",
    "2023-06-01", "2023-06-04", "2023-06-05", "2023-08-15", "2023-11-30", "2023-12-01", "2023-12-25", "2023-12-26",
    "2024-01-01", "2024-01-02", "2024-01-06", "2024-01-07", "2024-01-24", "2024-05-01", "2024-05-03", "2024-05-05", "2024-05-06",
    "2024-06-01", "2024-06-23", "2024-06-24", "2024-08-15", "2024-11-30", "2024-12-01", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-01-02", "2025-01-06", "2025-01-07", "2025-01-24", "2025-04-18", "2025-04-20", "2025-04-21", "2025-05-01",
    "2025-06-01", "2025-06-08", "2025-06-09", "2025-08-15", "2025-11-30", "2025-12-01", "2025-12-25", "2025-12-26",
    "2026-01-01", "2026-01-02", "2026-01-06", "2026-01-07", "2026-01-24", "2026-04-10", "2026-04-12", "2026-04-13", "2026-05-01",
    "2026-05-31", "2026-06-01", "2026-08-15", "2026-11-30", "2026-12-01", "2026-12-25", "2026-12-26"])
HOL_NP = HOL.values.astype("datetime64[D]")
R = {}   # result tables


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""): h.update(ch)
    return h.hexdigest()


def legal_wd(lo, hi):
    return int(np.busday_count(np.datetime64(lo, "D"), np.datetime64(hi, "D") + 1, holidays=HOL_NP))


def q(s, ps=(10, 25, 50, 75, 90, 99)):
    return {f"p{p}": round(float(np.percentile(s, p)), 2) for p in ps} if len(s) else {f"p{p}": None for p in ps}


def put(name, df, meta):
    df.to_csv(SP / f"{name}.csv", index=False, encoding="utf-8")
    R[name] = dict(meta=meta, columns=list(df.columns), rows=json.loads(df.to_json(orient="records", force_ascii=False)))
    print(f"  {name:28} {len(df):>4} rows")


def main():
    print("loading BERC …")
    b0 = pd.read_pickle(BERC)
    n_raw = len(b0)
    b = b0[b0.res.notna() & b0.app.notna()].copy()
    b["d"] = b.res.dt.normalize(); b["W"] = (b.res - b.app).dt.total_seconds() / 86400
    b["strict"] = b.sol.isin(STRICT); b["broad"] = b.sol.isin(BROAD); b["aman"] = b.sol.eq("Amânat")

    # ---------------- data quality
    dq = pd.DataFrame([
        ("Înregistrări în arhivă", n_raw, ""),
        ("Fără dată de depunere sau de decizie", int(n_raw - len(b)), "excluse"),
        ("Decizii înainte de 2023-04-01", int((b.d < "2023-04-01").sum()), "în afara ferestrei analizate"),
        ("Așteptare negativă (decizie înainte de depunere)", int((b.W < 0).sum()), "excluse din statisticile de timp"),
        ("Așteptare peste 400 de zile", int((b.W >= 400).sum()), "excluse din statisticile de timp (dosare istorice)"),
        ("Soluții cu grafie atipică (ADMIS, certificări cu ţ etc.)", int(b.sol.isin(["ADMIS", "Certificare înscriere în registrul comerţului", "Admis inițial(respins-Hotărâre judecătorească)", "Dosar transmis la tribunal spre soluționare", "Mențiune radiată"]).sum()), "nu intră în nicio definiție de «finală»"),
        ("Decizii finale stricte (admis, respins, renunțat)", int(b.strict.sum()), ""),
        ("Amânări (AUTO_AMANARI)", int(b.aman.sum()), ""),
        ("Ultima decizie din arhivă", str(b.res.max())[:16], ""),
    ], columns=["indicator", "valoare", "observație"])
    dq["valoare"] = dq["valoare"].astype(str)
    put("calitatea_datelor", dq, "Auditul arhivei BERC (analysis_decisions.pkl).")

    cat = b.groupby("cat", observed=True).size().reset_index(name="decizii")
    cat["pondere_pct"] = (100 * cat.decizii / cat.decizii.sum()).round(2)
    put("categorii", cat, "Decizii pe categorie de buletin, toată arhiva.")

    # ---------------- monthly series (decision month)
    w = b[(b.d >= "2023-04-01")]
    rows = []
    for m, g in w.groupby(w.d.dt.to_period("M")):
        lo, hi = m.start_time, min(m.end_time.normalize(), b.d.max())
        lwd = legal_wd(lo, hi); ndd = g.d.nunique()
        s = g[g.strict & (g.W >= 0) & (g.W < 400)]
        rows.append(dict(luna=str(m), zile_lucr_legale=lwd, zile_cu_decizii=ndd,
                         finale_largi=int(g.broad.sum()), finale_largi_pe_zi_cu_decizii=round(g.broad.sum() / max(ndd, 1)),
                         finale_stricte_pe_zi_lucr=round(g.strict.sum() / max(lwd, 1)), amanari_pe_zi_lucr=round(g.aman.sum() / max(lwd, 1)),
                         cota_amanari_pct=round(100 * g.aman.mean(), 1), cota_respinse_pct=round(100 * (s.sol == "Respins").mean(), 2) if len(s) else None,
                         W_p25=q(s.W)["p25"], W_med=q(s.W)["p50"], W_p75=q(s.W)["p75"], W_p90=q(s.W)["p90"],
                         cota_le2z_pct=round(100 * (s.W <= 2).mean(), 1) if len(s) else None,
                         med_CERERE=round(float(s[s.cat == "CERERE265"].W.median()), 1) if (s.cat == "CERERE265").any() else None,
                         med_INMATRIC=round(float(s[s.cat == "INMATRIC265"].W.median()), 1) if (s.cat == "INMATRIC265").any() else None))
    put("serie_lunara", pd.DataFrame(rows),
        "Pe luna DECIZIEI. Timpii: finale stricte, 0 ≤ W < 400 zile calendaristice. Noiembrie 2026 e parțial (până la ultima decizie din arhivă).")

    # ---------------- weekly 2026
    s26 = b[b.strict & (b.W >= 0) & (b.W < 400) & (b.d >= "2026-01-05")].copy()
    s26["sapt"] = s26.d.dt.to_period("W-SUN").apply(lambda p: str(p.start_time.date()))
    wk = []
    for k, g in s26.groupby("sapt"):
        c, i = g[g.cat == "CERERE265"].W, g[g.cat == "INMATRIC265"].W
        wk.append(dict(saptamana=k, n=len(g), med_CERERE=round(float(c.median()), 1) if len(c) else None,
                       p90_CERERE=round(float(c.quantile(.9)), 1) if len(c) else None,
                       med_INMATRIC=round(float(i.median()), 1) if len(i) else None, cota_le14z_pct=round(100 * (g.W <= 14).mean(), 1)))
    put("serie_saptamanala_2026", pd.DataFrame(wk), "Pe săptămâna DECIZIEI (luni–duminică), finale stricte, 2026.")

    # ---------------- filing-month cohorts (BERC decided only) + portal Kaplan–Meier
    f26 = b[b.strict & (b.W >= 0) & (b.W < 400) & (b.app >= "2026-01-01")].copy()
    f26["luna_dep"] = f26.app.dt.to_period("M").astype(str)
    coh = f26.groupby("luna_dep").W.agg(n="size", W_med="median", W_p90=lambda x: x.quantile(.9)).round(1).reset_index()
    sys.path.insert(0, str(HERE))
    from analyze_portal_snapshot import load
    p = load(None)
    flow = [("Dosare în recoltarea myportal (toate rulările)", int(p.req_nr.nunique()) if "req_nr" in p else len(p))]
    det = p[p.details_found].copy(); flow.append(("…cu detaliile dosarului găsite", int(det.req_nr.nunique())))
    if "is_judged" in det: det = det[det.is_judged == 1]
    flow.append(("…cereri supuse soluționării (nu acte administrative arhivate)", int(det.req_nr.nunique())))
    det = det.drop_duplicates("req_nr")
    det["rq"] = pd.to_datetime(det.request_date.str[:10], errors="coerce")
    det["so"] = pd.to_datetime(det.solution_term.str[:10], errors="coerce")
    RES = ["12", "13", "14", "15", "27"]; PEND = ["04", "05", "08"]
    det = det[det.phase_code.isin(RES + PEND) & det.rq.notna()]
    flow.append(("…în etapă cunoscută (rezolvat / operare / registrator) și cu dată de depunere", len(det)))
    det = det[~(det.phase_code.isin(RES) & det.so.isna())]          # resolved but no solution date: excluded, NOT censored
    flow.append(("…excluzând dosarele rezolvate fără dată a soluției", len(det)))
    CENS = pd.Timestamp("2026-11-21")
    det["event"] = det.phase_code.isin(RES)
    det["dur"] = np.where(det.event, (det.so - det.rq).dt.days, (CENS - det.rq).dt.days).astype(float)
    det = det[det["dur"] >= 0]
    flow.append(("…cu durată nenegativă: eșantionul Kaplan–Meier", len(det)))
    _pend = det[~det.event]
    R["oldest_pending"] = dict(date=str(_pend.rq.min().date()) if len(_pend) else None, n_pending=int(len(_pend)),
                               harvest="21–22.11.2026")
    put("portal_flux_includere", pd.DataFrame(flow, columns=["pas", "dosare"]), "Regula de includere a eșantionului myportal folosit pentru Kaplan–Meier (cenzurare la 21.11.2026).")

    def km(T, E):
        T, E = np.asarray(T, float), np.asarray(E, bool)
        times = np.sort(np.unique(T[E])); S = 1.0; v = 0.0; curve = []
        for t in times:
            n_ = (T >= t).sum(); d = ((T == t) & E).sum()
            S *= 1 - d / n_
            v += d / (n_ * (n_ - d)) if n_ > d else 0.0
            if 0 < S < 1 and v > 0:                                   # Greenwood, log-log transform
                se = np.sqrt(v) / abs(np.log(S)); lo = S ** np.exp(1.96 * se); hi = S ** np.exp(-1.96 * se)
            else:
                lo = hi = S
            curve.append((t, S, lo, hi))
        med = next((t for t, s, _, _ in curve if s <= .5), None)
        med_lo = next((t for t, _, l, _ in curve if l <= .5), None)   # lower CI bound of the median: lower band crosses .5 first
        med_hi = next((t for t, _, _, h in curve if h <= .5), None)   # upper CI bound: upper band crosses .5 later
        return curve, med, med_lo, med_hi

    def at_risk(T, t): return int((np.asarray(T) >= t).sum())
    kmrows, kmcurves = [], {}
    for m in ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]:
        g = det[det.rq.dt.to_period("M").astype(str) == m]
        if len(g) < 30:
            continue
        curve, med, mlo, mhi = km(g["dur"], g.event)
        naive = float(g[g.event]["dur"].median()) if g.event.any() else None
        kmrows.append(dict(luna_dep=m, n_portal=len(g), rezolvate_pct=round(100 * g.event.mean(), 1),
                           urmarire_min_zile=int((CENS - g.rq.max()).days),
                           mediana_naiva_doar_rezolvate=naive, mediana_KM=med, mediana_KM_IC95_inf=mlo, mediana_KM_IC95_sup=mhi,
                           la_risc_50z=at_risk(g["dur"], 50), la_risc_58z=at_risk(g["dur"], 58), la_risc_66z=at_risk(g["dur"], 66),
                           S_30z=round(next((s for t, s, _, _ in reversed(curve) if t <= 30), 1.0), 3)))
        kmcurves[m] = [(float(t), round(float(s), 4)) for t, s, _, _ in curve]
    # September by filing week: informative censoring check (later filers wait longer AND are followed less)
    sw = det[(det.rq >= "2026-09-01") & (det.rq <= "2026-09-30")].copy()
    sw["sapt"] = sw.rq.dt.to_period("W-SUN").apply(lambda q: str(q.start_time.date()))
    wrows = []
    for k, g in sw.groupby("sapt"):
        curve, med, mlo, mhi = km(g["dur"], g.event)
        wrows.append(dict(saptamana_depunerii=k, n=len(g), rezolvate_pct=round(100 * g.event.mean(), 1),
                          urmarire_min_zile=int((CENS - g.rq.max()).days), mediana_KM=med))
    put("KM_septembrie_pe_saptamani", pd.DataFrame(wrows), "Cohorta din septembrie, pe săptămâna depunerii: dacă mediana crește cu săptămâna, cenzurarea e informativă și mediana lunară e o limită de jos.")
    kmdf = pd.DataFrame(kmrows)
    put("cohorte_depunere_BERC", coh, "Pe luna DEPUNERII, doar dosare deja decise (BERC). Lunile recente sunt cenzurate: medianele lor sunt prea mici.")
    put("cohorte_KM_portal", kmdf, "Eșantion myportal: Kaplan–Meier pe luna depunerii; dosarele încă nerezolvate sunt cenzurate la 21.11.2026. «mediana_KM» lipsă = mai puțin de jumătate rezolvate.")
    R["km_curves"] = kmcurves

    # ---------------- regimes, distributions
    REG = {"Platforma veche (apr. 2023–17.07.2024)": ("2023-04-03", "2024-07-17"),
           "Lansarea portalului (29.07–30.11.2024)": ("2024-07-29", "2024-11-30"),
           "Stabil 2025": ("2025-01-01", "2025-12-31"), "2026 până în iulie": ("2026-01-01", "2026-07-31"),
           "August–septembrie 2026": ("2026-08-01", "2026-09-30"), "Octombrie–noiembrie 2026": ("2026-10-01", "2026-11-20")}
    dist = []
    for name, (lo, hi) in REG.items():
        s = b[b.strict & (b.W >= 0) & (b.W < 400) & (b.d >= lo) & (b.d <= hi)]
        dist.append(dict(perioada=name, n=len(s), medie=round(float(s.W.mean()), 2), **q(s.W),
                         cota_le1z_pct=round(100 * (s.W <= 1).mean(), 1), cota_peste30z_pct=round(100 * (s.W > 30).mean(), 1)))
    put("distributii_pe_perioade", pd.DataFrame(dist), "Distribuția așteptării (zile calendaristice), finale stricte, pe data deciziei.")

    # bootstrap CI for the latest-week median (C14 window)
    rng = np.random.default_rng(20261122)
    lw = b[b.strict & (b.W >= 0) & (b.W < 400) & (b.cat == "CERERE265") & (b.d >= "2026-11-16") & (b.d <= "2026-11-20")].W.to_numpy()
    boots = np.median(rng.choice(lw, (2000, len(lw)), replace=True), axis=1)
    R["bootstrap_C14"] = dict(n=int(len(lw)), median=round(float(np.median(lw)), 2),
                              ci95=[round(float(np.percentile(boots, 2.5)), 2), round(float(np.percentile(boots, 97.5)), 2)])

    # ---------------- weekday / hour profiles (2026)
    a26 = b[(b.app >= "2026-01-01") & b.cat.isin(["CERERE265", "INMATRIC265"])]
    wd = a26.app.dt.dayofweek.value_counts(normalize=True).sort_index()
    dd = b[(b.d >= "2026-01-01") & b.strict].d.dt.dayofweek.value_counts(normalize=True).sort_index()
    names = ["luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică"]
    put("profil_zile_saptamana_2026", pd.DataFrame({"zi": names, "depuneri_pct": [round(100 * wd.get(i, 0), 2) for i in range(7)],
                                                   "decizii_pct": [round(100 * dd.get(i, 0), 2) for i in range(7)]}),
        "Ponderea depunerilor (CERERE265 + INMATRIC265, după data depunerii) și a deciziilor finale stricte, pe zi a săptămânii, 2026.")
    hr = a26.app.dt.hour.value_counts(normalize=True).sort_index()
    put("profil_ore_depunere_2026", pd.DataFrame({"ora": list(range(24)), "depuneri_pct": [round(100 * hr.get(h, 0), 2) for h in range(24)]}),
        "Ponderea depunerilor pe ora înregistrării, 2026 (ora din marca temporală a cererii).")

    # ---------------- publication lag (pub − res)
    pl = b[(b.d >= "2023-04-01") & b.pub.notna()].copy()
    pl["lag"] = (pl.pub - pl.res).dt.total_seconds() / 86400
    lagrows = [dict(an=int(y), n=len(g), **{k: v for k, v in q(g.lag, (50, 90, 99)).items()}) for y, g in pl.groupby(pl.d.dt.year)]
    put("intarziere_publicare", pd.DataFrame(lagrows), "Diferența dintre momentul publicării în buletin și momentul deciziei (zile).")

    # ---------------- adjournment cycles per decided dossier (Nov 2026)
    key = lambda df: df.app_nr.astype("Int64").astype(str) + "|" + df.app.dt.strftime("%Y-%m-%d")
    fin_nov = b[b.strict & (b.d >= "2026-11-01") & b.cat.isin(["CERERE265", "INMATRIC265"])].copy()
    am = b[b.aman & (b.app >= "2026-01-01")].copy()
    fin_nov["k"] = key(fin_nov); am["k"] = key(am)
    cnt = am.groupby("k").size()
    fin_nov["n_aman"] = fin_nov.k.map(cnt).fillna(0).astype(int)
    vc = fin_nov.n_aman.clip(upper=4).value_counts().sort_index()
    linked = (fin_nov.n_aman > 0).mean()
    put("cicluri_amanare_nov2026", pd.DataFrame({"amanari_anterioare": ["0", "1", "2", "3", "4+"],
                                                 "decizii_finale_pct": [round(100 * vc.get(i, 0) / len(fin_nov), 2) for i in range(5)]}),
        "Decizii finale din 1–20.11.2026: câte amânări a avut același dosar (legat prin număr și dată de depunere). Legătura poate rata dosare renumerotate.")
    R["adjourn_link"] = dict(n_final=int(len(fin_nov)), share_with_adjournment=round(float(linked), 4),
                             wait_med_with=round(float(fin_nov[fin_nov.n_aman > 0].W.median()), 1),
                             wait_med_without=round(float(fin_nov[fin_nov.n_aman == 0].W.median()), 1))

    # ---------------- Little's law consistency (Nov 2026)
    nov = b[b.strict & (b.W >= 0) & (b.W < 400) & (b.d >= "2026-11-02") & (b.d <= "2026-11-20")].copy()
    nov["Wwd"] = np.busday_count(nov.app.values.astype("datetime64[D]"), nov.d.values.astype("datetime64[D]"), holidays=HOL_NP)
    lam_wd = len(b[b.broad & (b.d >= "2026-11-02") & (b.d <= "2026-11-20")]) / legal_wd("2026-11-02", "2026-11-20")
    R["little"] = dict(lambda_finals_per_legal_wd=round(lam_wd), W_med_cal=round(float(nov.W.median()), 1),
                       W_mean_wd=round(float(nov.Wwd.mean()), 1), W_med_wd=round(float(nov.Wwd.median()), 1),
                       L_implied=round(lam_wd * float(nov.Wwd.mean())), L_official_MJ=204414)

    # ---------------- counties (alphabetical; NOT a ranking)
    ct = pd.read_csv(OUT / "atlas_rerun" / "audit_data" / "county_indicators.csv", encoding="utf-8-sig").sort_values("name")
    cols = ["code", "name", "region", "n_nov", "median_nov", "p90_nov", "median_y25", "rejection_pct_2025", "rejection_pct_crisis",
            "postponement_action_pct", "formation_gt10_pct"]
    ctd = ct[cols].round(4)
    put("judete_alfabetic", ctd, "42 de oficii, în ordine alfabetică (NU e clasament). Județ = oficiul de depunere.")
    med = ct.median_nov
    R["county_dispersion"] = dict(n=int(len(ct)), min=round(float(med.min()), 1), max=round(float(med.max()), 1),
                                  iqr=[round(float(med.quantile(.25)), 1), round(float(med.quantile(.75)), 1)],
                                  cv_pct=round(float(100 * med.std() / med.mean()), 1),
                                  spearman_2025_vs_nov=round(float(ct[["median_y25", "median_nov"]].corr("spearman").iloc[0, 1]), 2))

    # ---------------- audited model tables (copied verbatim, with hashes)
    def copy_csv(name, path, meta, rename=None, keep=None):
        d = pd.read_csv(path)
        if keep: d = d[keep]
        if rename: d = d.rename(columns=rename)
        put(name, d.round(3), meta + f" Sursă: {path.name}, SHA-256 {sha(path)[:16]}….")
    copy_csv("model_ipoteze_intrare", AD / "forecast_inputs.csv", "Ipotezele motorului de prognoză (distribuții triunghiulare: minim, mod, maxim).",
             rename={"Unnamed: 0": "parametru", "low": "minim", "mode": "mod", "high": "maxim"})
    copy_csv("model_scenarii_OUG", AD / "oug_2026" / "scenarios.csv", "Scenarii OUG, toate perioadele: p10 / mediană / p90 (zile) și câștigul pe aceleași simulări.",
             keep=["scenario", "period", "p10", "median", "p90", "median_saved", "median_stock"])
    copy_csv("model_pachete", AD / "solutions_feasibility_and_simulations.csv", "Pachete de măsuri P0–P5 (P6–P7 omise: ating limita metricii de ~3 zile).",
             keep=["id", "package", "time_to_effect_days", "wait_jun28_p10", "wait_jun28_p50", "wait_jun28_p90", "days_saved_jun28_med"])
    R["model_pachete"]["rows"] = [r for r in R["model_pachete"]["rows"] if r["id"] not in ("P6", "P7")]
    copy_csv("model_validare_capacitate", AD / "forecast_capacity_backtest.csv", "Test pe date nevăzute al ritmului de soluționare: 9 ferestre × 3 reguli.")
    copy_csv("model_validare_cerere", AD / "forecast_demand_check.csv", "Verificarea profilului cererii pe lunile mature.")
    copy_csv("model_sensibilitate", AD / "forecast_sensitivity.csv", "Corelația de rang (Spearman) a fiecărei ipoteze cu vârful așteptării (2.000 de variante).")
    copy_csv("model_valuri", AD / "forecast_wave_sensitivity.csv", "Zile evitate dacă un val de cereri nu ar exista (la vârf și în iunie 2028).")
    copy_csv("model_sezonalitate", AD / "forecast_monthly_profile.csv", "Profilul lunar al cererilor, relativ la noiembrie.")
    g = json.loads((OUT / "forecast_grid.json").read_text(encoding="utf-8"))
    gdf = pd.DataFrame(g["cells"]).drop(columns=["beyond_horizon", "june_p50_at_floor", "june_p90_at_floor"], errors="ignore").round(1)
    put("model_grila_completa", gdf, f"Grila intrări × ieșiri pe motorul auditat (forecast_grid.json, SHA-256 {sha(OUT / 'forecast_grid.json')[:16]}…). Valori ≤3 = limita metricii.")
    L = json.loads((OUT / "LOCKED_CONSTANTS.json").read_text(encoding="utf-8"))
    rg = pd.DataFrame([dict(perioada=k, **v) for k, v in L["regimes_by_decision_date"].items()])
    put("regimuri_LOCKED", rg, "Regimuri pe data deciziei, din LOCKED_CONSTANTS.json (sursa unică).")
    au = json.loads((AD / "oug_2026" / "audit.json").read_text(encoding="utf-8"))
    put("stocuri_oficiale_MJ", pd.DataFrame([
        dict(data="30.10.2026", neprelucrate_operare=au["prior_unprocessed"], la_registrator=au["prior_processed"], total=au["previous_backlog"]),
        dict(data="06.11.2026", neprelucrate_operare=au["current_unprocessed"], la_registrator=au["current_processed"], total=au["current_backlog"])]),
        "Stocuri oficiale, Nota de fundamentare MJ (nivel C, citate).")

    # ---------------- validation checklist (run, parse)
    try:
        out = subprocess.run([sys.executable, "-X", "utf8", str(HERE / "validation_checklist.py")], capture_output=True, text=True,
                             encoding="utf-8", timeout=900, cwd=str(HERE)).stdout
        chk, cur = [], None
        for line in out.splitlines():
            t = line.strip()
            if t[:3] in ("[✓]", "[!]", "[✗]"):
                cur = dict(stare={"[✓]": "PASS", "[!]": "WARN", "[✗]": "FAIL"}[t[:3]], verificare=t[4:], detaliu="")
                chk.append(cur)
            elif cur is not None and t and not t.startswith("SUMMARY") and not t.startswith("===="):
                cur["detaliu"] = (cur["detaliu"] + " " + t).strip()
        put("lista_verificari_sigure", pd.DataFrame(chk), "Rezultatul validation_checklist.py (verificări sigure, fără supra-ajustare).")
    except Exception as e:
        print("checklist failed:", e)

    R["_meta"] = dict(generated="2026-11-22", berc_sha256=sha(BERC), berc_last_decision=str(b.res.max())[:16],
                      portal_n=int(len(det)), definitions={"strict": STRICT, "broad": BROAD}, holidays_n=len(HOL))
    (OUT / "stat_pack.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("wrote out/stat_pack.json · bootstrap", R["bootstrap_C14"], "· little", R["little"], "· adjourn", R["adjourn_link"],
          "· county", R["county_dispersion"])


if __name__ == "__main__":
    main()
