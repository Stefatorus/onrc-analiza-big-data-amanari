"""Figurile capitolului de prognoză și risc (stil Lab, aceeași paletă ca generate_institutii_figures).
Toate cifrele vin din ieșirile verificate: audit_data/oug_2026/trajectory.csv + scenarios.csv (aceeași familie ca C42–C44),
audit_data/forecast_*.csv (motorul audit_forecast.py) și independent_audit/out/forecast_grid.json (grila, același motor).
Riscul e arătat ca intervale (p10–p90), nu ca procente de «șanse».
"""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap

import generate_institutii_figures as GI
G = GI.G
HERE = GI.HERE; AD = os.path.join(HERE, "audit_data"); IA = GI.IA
NAVY, NAVY_MID, NAVY_SOFT = G.NAVY, G.NAVY_MID, G.NAVY_SOFT
ALERT, ALERT_SOFT, WARN, WARN_SOFT, SOL, SOL_SOFT = G.ALERT, G.ALERT_SOFT, G.WARN, G.WARN_SOFT, G.SOL, G.SOL_SOFT
INK, INK2, INK3, TINT = G.INK, G.INK2, G.INK3, G.TINT
W = G.W_IN; HALO = G.HALO; ron = G.ro_num
TR = pd.read_csv(os.path.join(AD, "oug_2026", "trajectory.csv"), parse_dates=["date"])
SC = pd.read_csv(os.path.join(AD, "oug_2026", "scenarios.csv"))
FT = pd.read_csv(os.path.join(AD, "forecast_trajectories.csv"), parse_dates=["week"])
GRID = json.load(open(os.path.join(IA, "out", "forecast_grid.json"), encoding="utf-8"))
MONTHS_RO = GI.MO


def _date_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{MONTHS_RO[mdates.num2date(x).month]} {mdates.num2date(x).year}"))
    ax.tick_params(axis="x", labelsize=6.3)


def sc(s, period):
    r = SC[(SC.scenario == s) & (SC.period == period)].iloc[0]
    return r.p10, r["median"], r.p90


def f_forecast():
    r = TR[TR.scenario == "referinta"]
    fig, ax = plt.subplots(figsize=(W, 2.5))
    ax.fill_between(r.date, r.p10, r.p90, color=ALERT_SOFT, lw=0, label="interval p10–p90 (8 din 10 simulări)")
    ax.plot(r.date, r["median"], color=ALERT, lw=1.8, label="mijlocul simulărilor (mediana)")
    ax.axhline(3, color=SOL, ls="--", lw=0.9); ax.text(r.date.iloc[2], 9, "reper: 3 zile calendaristice ≈ 1 zi lucrătoare peste weekend", fontsize=6.2, color=SOL)
    for per, lab in [("2027-06-30", "iun. 2027"), ("2027-12-31", "dec. 2027"), ("2028-06-30", "iun. 2028")]:
        lo, m, hi = sc("referinta", per); d = pd.Timestamp(per)
        ax.plot([d], [m], "o", color=ALERT, ms=4)
        ax.text(d, m + 14, f"≈{ron(m)}", ha="center", fontsize=6.6, color=ALERT, fontweight="bold", path_effects=HALO)
    f0 = r.iloc[0]
    ax.annotate(f"dosar depus acum: ≈{ron(f0['median'])} zile", (f0.date, f0["median"]), (f0.date + pd.Timedelta(days=40), 20),
                fontsize=6.3, color=INK2, arrowprops=dict(arrowstyle="-", color=INK3, lw=0.6))
    ax.set_ylim(0, 250); ax.set_ylabel("zile de așteptare pentru un\ndosar depus la data respectivă", fontsize=6.6)
    _date_axis(ax); ax.legend(loc="upper left", fontsize=6.2, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi12_prognoza")


def f_hypotheses():
    rows = [("referinta", "Fără măsuri noi", ALERT), ("oug_redus", "OUG, livrare slabă", WARN),
            ("oug_central", "OUG, livrare centrală", NAVY), ("oug_ridicat", "OUG, livrare ridicată", SOL)]
    fig, ax = plt.subplots(figsize=(W, 2.5))
    for s, lab, col in rows:
        r = TR[TR.scenario == s]
        if s in ("referinta", "oug_ridicat"):
            ax.fill_between(r.date, r.p10, r.p90, color=col, alpha=.10, lw=0)
        ax.plot(r.date, r["median"], color=col, lw=1.5, label=lab)
        m = sc(s, "2028-06-30")[1]
        ax.text(r.date.iloc[-1] + pd.Timedelta(days=8), m, f"≈{ron(m)}", va="center", fontsize=6.6, color=col, fontweight="bold")
    ax.axhline(3, color=SOL, ls="--", lw=0.8)
    ax.set_ylim(0, 250); ax.set_xlim(TR.date.min(), TR.date.max() + pd.Timedelta(days=60))
    ax.set_ylabel("zile de așteptare (mediană)", fontsize=6.6); _date_axis(ax)
    ax.legend(loc="upper left", ncol=2, fontsize=6.2, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi13_ipoteze")


def f_stock():
    c = FT[FT.scenario == "continuitate"]
    fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.fill_between(c.week, c.stock_p10 / 1e3, c.stock_p90 / 1e3, color=NAVY_SOFT, lw=0, label="interval p10–p90")
    ax.plot(c.week, c.stock_p50 / 1e3, color=NAVY, lw=1.8, label="mediana simulărilor")
    ax.plot([pd.Timestamp("2026-11-06")], [204.414], "D", color=INK, ms=4)
    ax.text(pd.Timestamp("2026-11-20"), 175, "stocul oficial MJ (6.11.2026)", fontsize=6.2, color=INK)
    ax.set_ylim(0, 620); ax.set_ylabel("dosare în așteptare (mii,\nechivalent dosar standard)", fontsize=6.6)
    _date_axis(ax); ax.legend(loc="upper right", fontsize=6.2, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi14_stoc")


def _grid_matrix(key):
    ins, outs = GRID["in_steps"], GRID["out_steps"]
    M = np.full((len(ins), len(outs)), np.nan)
    for c in GRID["cells"]:
        if not c["beyond_horizon"]:
            M[ins.index(c["d_in"]), outs.index(c["d_out"])] = c[key]
    return ins, outs, M


CMAP = LinearSegmentedColormap.from_list("risk", [SOL_SOFT, "#FFFFFF", WARN_SOFT, ALERT_SOFT, ALERT])


def _heat(ax, key, title):
    ins, outs, M = _grid_matrix(key)
    ax.imshow(M[::-1], cmap=CMAP, vmin=0, vmax=440, aspect="auto")
    for i, di in enumerate(ins[::-1]):
        for j, do in enumerate(outs):
            v = M[len(ins) - 1 - i, j]
            txt = "≤3" if v <= 3 else ron(v)
            ax.text(j, i, txt, ha="center", va="center", fontsize=6.4,
                    color="#FFFFFF" if v > 300 else INK, fontweight="bold" if (di == 0 and do == 0) else "normal")
    bi, bj = ins[::-1].index(0), outs.index(0)
    ax.add_patch(plt.Rectangle((bj - .5, bi - .5), 1, 1, fill=False, ec=INK, lw=1.3))
    ax.set_xticks(range(len(outs))); ax.set_xticklabels([f"{o:+d}%" for o in outs], fontsize=6.2)
    ax.set_yticks(range(len(ins))); ax.set_yticklabels([f"{x:+d}%" for x in ins[::-1]], fontsize=6.2)
    ax.set_xlabel("schimbarea vitezei de ieșire (capacitate)", fontsize=6.4)
    ax.set_ylabel("schimbarea vitezei de intrare", fontsize=6.4)
    ax.set_title(title, fontsize=7, color=INK, loc="left")
    for s in ax.spines.values():
        s.set_visible(False)


def f_grid():
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.75))
    _heat(axs[0], "june2028_p50", "Cazul central (mediana), iunie 2028")
    _heat(axs[1], "june2028_p90", "Cazul nefavorabil (p90), iunie 2028")
    fig.tight_layout(); G.save_svg_and_png(fig, "fi15_grila")


def f_grid_peak():
    fig, ax = plt.subplots(figsize=(W * .62, 2.6))
    _heat(ax, "peak_p50", "Vârful așteptării 2026–2028 (mediana)")
    fig.tight_layout(); G.save_svg_and_png(fig, "fi16_grila_varf")


def f_waves():
    d = pd.read_csv(os.path.join(AD, "forecast_wave_sensitivity.csv"))
    lab = {"fara_caen_suplimentar": "valul CAEN", "fara_capital_suplimentar": "valul de capital social",
           "fara_sarcina_fiscala_suplimentara": "valul fiscal (ANAF, dosare preventive)"}
    fig, ax = plt.subplots(figsize=(W, 1.9)); y = np.arange(len(d))[::-1]
    for i, (_, r) in zip(y, d.iterrows()):
        ax.plot([r.peak_days_saved_p10, r.peak_days_saved_p90], [i + .14] * 2, color=ALERT, lw=5, alpha=.3, solid_capstyle="butt")
        ax.plot([r.peak_days_saved_p50], [i + .14], "o", color=ALERT, ms=5)
        ax.plot([r.june_days_saved_p10, r.june_days_saved_p90], [i - .14] * 2, color=NAVY, lw=5, alpha=.3, solid_capstyle="butt")
        ax.plot([r.june_days_saved_p50], [i - .14], "o", color=NAVY, ms=5)
        ax.text(r.peak_days_saved_p90 + 2, i + .14, f"≈{ron(r.peak_days_saved_p50)} la vârf", va="center", fontsize=6.2, color=ALERT)
        ax.text(r.june_days_saved_p90 + 2, i - .14, f"≈{ron(r.june_days_saved_p50)} în iun. 2028", va="center", fontsize=6.2, color=NAVY)
    ax.set_yticks(y); ax.set_yticklabels([lab[w] for w in d.wave_removed], fontsize=6.7)
    ax.set_xlim(0, 135); ax.set_ylim(-.6, len(d) - .4)
    ax.set_xlabel("zile de așteptare evitate dacă valul nu ar exista (punct = mediană, bară = p10–p90)", fontsize=6.4)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi17_valuri")


FACT = {"flux_zilnic_recurent": "cererile obișnuite pe zi", "rezolvari_observate_pe_zi": "dosarele soluționate pe zi",
        "dosare_caen_suplimentare": "mărimea valului CAEN", "stoc_initial": "stocul de pornire",
        "populatie_capital": "firmele vizate de capitalul minim", "dosare_defensive": "dosarele depuse preventiv",
        "efort_caen": "efortul pe un dosar CAEN", "pondere_caen_iesiri": "ponderea CAEN în soluționări",
        "efort_capital": "efortul pe un dosar de capital", "fractie_anaf_capacitate_comuna": "dosarele ANAF în fluxul comun",
        "conformare_ulterioara": "conformarea ulterioară", "crestere_anuala_flux": "creșterea anuală a cererilor"}


def f_drivers():
    d = pd.read_csv(os.path.join(AD, "forecast_sensitivity.csv")).head(6).iloc[::-1]
    fig, ax = plt.subplots(figsize=(W, 2.3))
    cols = [ALERT if v > 0 else SOL for v in d.spearman_peak]
    ax.barh([FACT.get(p, p) for p in d.parameter], d.spearman_peak, color=cols, height=.6)
    for i, v in enumerate(d.spearman_peak):
        ax.text(v + (.015 if v > 0 else -.015), i, ron(v, 2), va="center", ha="left" if v > 0 else "right", fontsize=6.3, color=INK)
    ax.axvline(0, color=INK3, lw=.6); ax.set_xlim(-.75, .75); ax.tick_params(axis="y", labelsize=6.5)
    ax.set_xlabel("corelația de rang (Spearman) cu vârful așteptării — roșu: crește riscul, verde: îl scade", fontsize=6.3)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi18_factori")


def f_validation():
    d = pd.read_csv(os.path.join(AD, "forecast_capacity_backtest.csv")).query("model == 'ultimele_12_zile'")
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(W, 2.1))
    ax.bar(x - .18, d.predicted_per_day, width=.36, color=NAVY_SOFT, label="prognozat (media ultimelor 12 zile)")
    ax.bar(x + .18, d.observed_per_day, width=.36, color=NAVY, label="observat în următoarele 4 săptămâni")
    for i, e in zip(x, d.error_percent):
        ax.text(i, max(d.predicted_per_day.iloc[i], d.observed_per_day.iloc[i]) + 70, f"{e:+.0f}%".replace("-", "−"),
                ha="center", fontsize=6.2, color=ALERT if abs(e) > 10 else INK2)
    ax.set_xticks(x); ax.set_xticklabels([f"{pd.Timestamp(t).day} {MONTHS_RO[pd.Timestamp(t).month]}" for t in d.test_start], fontsize=6.2)
    ax.set_ylim(0, 5200); ax.set_ylabel("dosare soluționate / zi lucrătoare", fontsize=6.5)
    ax.set_xlabel("începutul ferestrei de test, 2026 (eticheta = abaterea observat față de prognozat)", fontsize=6.3)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.3), ncol=2, fontsize=6.2, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi19_validare")


def f_season():
    d = pd.read_csv(os.path.join(AD, "forecast_monthly_profile.csv"))
    fig, ax = plt.subplots(figsize=(W, 1.9))
    cols = [ALERT if v > 1.05 else (NAVY_SOFT if v >= .97 else SOL_SOFT) for v in d.relative_to_november]
    ax.bar([MONTHS_RO[m] for m in d.month], (d.relative_to_november - 1) * 100, color=cols, width=.6)
    for i, v in enumerate(d.relative_to_november):
        p = (v - 1) * 100
        lab = "0%" if round(p) == 0 else f"{p:+.0f}%".replace("-", "−")
        ax.text(i, p + (.5 if p >= 0 else -1.4), lab, ha="center", fontsize=6.2, color=INK)
    ax.axhline(0, color=INK3, lw=.6); ax.set_ylim(-9, 16)
    ax.set_ylabel("cereri pe zi față de\nnoiembrie (%)", fontsize=6.5)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi20_sezon")


def f_packages():
    d = pd.read_csv(os.path.join(AD, "solutions_feasibility_and_simulations.csv")).set_index("id")
    rows = [("P0", "Fără măsuri noi", ALERT), ("P2", "Proiectul OUG, neamendat", NAVY), ("P4", "Decongestionare legislativă (CAEN 1-la-1)", WARN),
            ("P3", "OUG extins + 40% din posturile vacante", NAVY_MID), ("P5", "Pachet minim realist (OUG, CAEN, eșalonare, triaj)", SOL)]
    fig, ax = plt.subplots(figsize=(W, 2.3)); y = np.arange(len(rows))[::-1]
    for i, (pid, lab, col) in zip(y, rows):
        r = d.loc[pid]; lo, m, hi = r.wait_jun28_p10, r.wait_jun28_p50, r.wait_jun28_p90
        ax.plot([lo, hi], [i, i], color=col, lw=6, alpha=.35, solid_capstyle="butt"); ax.plot([m], [i], "o", color=col, ms=6)
        ax.text(m, i + .3, f"≈{ron(m)} zile", ha="center", fontsize=6.7, color=col, fontweight="bold")
        ax.text(hi + 3, i, f"interval {'≤3' if lo <= 3 else ron(lo)}–{ron(hi)}", va="center", fontsize=6.2, color=INK2)
    ax.axvline(3, color=SOL, ls="--", lw=.9)
    ax.set_yticks(y); ax.set_yticklabels([r[1] for r in rows], fontsize=6.6); ax.set_xlim(0, 260); ax.set_ylim(-.7, len(rows) - .2)
    ax.set_xlabel("așteptare estimată în iunie 2028 (zile) — punct = mediană, bară = p10–p90", fontsize=6.5)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi21_pachete")


if __name__ == "__main__":
    for fn in (f_packages, f_forecast, f_hypotheses, f_stock, f_grid, f_grid_peak, f_waves, f_drivers, f_validation, f_season):
        fn(); print("ok", fn.__name__)


def f_caen_compliance():
    CC = json.load(open(os.path.join(IA, "out", "forecast_caen_compliance.json"), encoding="utf-8"))["scenarios"]
    lab = {None: "prognoza de bază", 0.5: "50% din 902.243", 0.8: "80%", 1.0: "100%"}
    base = [r for r in CC if r["automatizare_caen"] == 0]; auto = {r["pondere"]: r for r in CC if r["automatizare_caen"] > 0}
    fig, ax = plt.subplots(figsize=(W, 2.3)); x = np.arange(len(base))
    for i, r in enumerate(base):
        k = None if isinstance(r["pondere"], str) else r["pondere"]
        ax.bar(i - .18, r["iun2027"][1], .34, color=ALERT if k else NAVY_SOFT)
        ax.plot([i - .18] * 2, [r["iun2027"][0], r["iun2027"][2]], color=INK3, lw=.8)
        ax.text(i - .18, r["iun2027"][2] + 6, f"≈{ron(r['iun2027'][1])}", ha="center", fontsize=6.4, color=INK)
        if k in auto:
            a = auto[k]; ax.bar(i + .18, a["iun2027"][1], .34, color=SOL)
            ax.plot([i + .18] * 2, [a["iun2027"][0], a["iun2027"][2]], color=INK3, lw=.8)
            ax.text(i + .18, a["iun2027"][2] + 6, f"≈{ron(a['iun2027'][1])}", ha="center", fontsize=6.4, color=SOL)
    ax.set_xticks(x); ax.set_xticklabels([lab[None if isinstance(r['pondere'], str) else r['pondere']] for r in base], fontsize=6.6)
    ax.set_ylim(0, 430); ax.set_ylabel("zile de așteptare, iunie 2027\n(mediană; bara subțire = p10–p90)", fontsize=6.4)
    ax.set_xlabel("câte din cele 902.243 de cereri CAEN rămase (nota MJ) se depun până la 1 aprilie 2027 · roșu = fără măsuri noi, verde = cu conversie automată CAEN", fontsize=6.0)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi22_caen")


def f_backtest():
    BQ = json.load(open(os.path.join(IA, "out", "backtest_queue_mechanics.json"), encoding="utf-8"))["origini"]["2026-06-01"]["saptamanal"]
    d = pd.DataFrame(BQ); d["dt"] = pd.to_datetime(d.sapt)
    fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.plot(d.dt, d.observat, color=INK, lw=2.0, marker="o", ms=3, label="observat (BERC, mediana pe ziua depunerii)")
    ax.plot(d.dt, d.mecanism, color=SOL, lw=1.4, ls="--", label="modelul cu intrările și capacitatea reale")
    ax.plot(d.dt, d.prognoza, color=ALERT, lw=1.2, ls=":", label="prognoza făcută la 1 iunie, fără să știe de val")
    ax.set_ylabel("zile de așteptare", fontsize=6.6); _date_axis(ax)
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.legend(fontsize=6.1, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi23_backtest")
