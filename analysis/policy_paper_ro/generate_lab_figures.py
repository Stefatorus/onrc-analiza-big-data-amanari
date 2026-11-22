"""Genereaza cele 7 figuri vectoriale SVG cu paleta semantica de nivel editorial
(OECD / Bruegel / Brookings — corelare intre salienta vizuala si relevanta):
  - Navy (#14324D): date de baza, capacitate reala, economie
  - Crimson-teracota (#A63228): criza, infringement absolut, respingeri, Status Quo S1, pierderi
  - Ocru-chihlimbar (#B86E14): avertisment, prag UE 5 zl, capcana ANAF, solutie partiala S2
  - Verde-smarald (#16665C): tinta 3 zile, reforma digitala S3, Pachet Combinat S4, economii

Latime exacta 166 mm, font IBM Plex Sans, fara titluri coapte in imagine, accesibil si alb-negru.
"""
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.patheffects as pe

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "figures_lab")
DATA_DIR = os.path.join(HERE, "data")
os.makedirs(OUT_DIR, exist_ok=True)

# Paleta semantica editoriala (4 roluri clare + neutre calde)
NAVY = "#14324D"        # Baza, capacitate, linie de referinta
NAVY_MID = "#3C6487"    # Serie secundara institutionala
NAVY_SOFT = "#DCE6F0"   # Banda discreta navy
ALERT = "#A63228"       # Criza, infringement >10 zl, respingeri, S1 Status Quo
ALERT_SOFT = "#F6DDDA"  # Banda criza / risc
WARN = "#B86E14"        # Avertisment, prag UE 5 zl, OUG partial S2, ANAF
WARN_SOFT = "#F9EBD4"   # Banda avertisment
SOL = "#16665C"         # Tinta 3 zile, Solutie S4, economii, drenare coada
SOL_SOFT = "#D7EBE8"    # Banda solutie
INK = "#1B2128"
INK2 = "#46505C"
INK3 = "#687380"
RULE = "#C2BEB4"
RULE2 = "#E6E3DC"
TINT = "#F5F3EE"
PAPER = "#FFFFFF"

HALO = [pe.withStroke(linewidth=2.7, foreground=PAPER)]
W_IN = 166.0 / 25.4

RO_MONTHS = {
    1: "ian.", 2: "feb.", 3: "mar.", 4: "apr.", 5: "mai", 6: "iun.",
    7: "iul.", 8: "aug.", 9: "sep.", 10: "oct.", 11: "nov.", 12: "dec.",
}


def ro_date_fmt(x, _pos=None):
    dt = mdates.num2date(x)
    return f"{RO_MONTHS[dt.month]} '{dt.year % 100:02d}"


def ro_num(val, decimals=0):
    if decimals == 0:
        return f"{val:,.0f}".replace(",", ".")
    return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "svg.fonttype": "none",
    "font.size": 7.4,
    "axes.facecolor": PAPER,
    "figure.facecolor": PAPER,
    "axes.edgecolor": NAVY,
    "axes.linewidth": 0.55,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.major.size": 2.5,
    "ytick.major.size": 0,
    "xtick.major.width": 0.5,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "text.color": INK,
    "legend.frameon": False,
    "legend.fontsize": 6.8,
})


def style_axes(ax, ygrid=True, xgrid=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(RULE)
    ax.spines["left"].set_linewidth(0.55)
    ax.spines["bottom"].set_color(NAVY)
    ax.spines["bottom"].set_linewidth(0.65)
    ax.grid(False)
    if ygrid:
        ax.grid(axis="y", color=RULE2, linewidth=0.5, zorder=0)
    if xgrid:
        ax.grid(axis="x", color=RULE2, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)


def save_svg_and_png(fig, stem):
    svg_path = os.path.join(OUT_DIR, f"{stem}.svg")
    png_path = os.path.join(OUT_DIR, f"{stem}.png")
    fig.savefig(svg_path, format="svg", bbox_inches=None)
    fig.savefig(png_path, format="png", dpi=200, bbox_inches=None)
    plt.close(fig)
    with open(svg_path, "r", encoding="utf-8") as f:
        txt = f.read()
    txt = re.sub(r'<\?xml[^>]*\?>\s*', '', txt)
    txt = re.sub(r'<!DOCTYPE[^>]*>\s*', '', txt)
    txt = txt.replace("'Arial'", "'IBM Plex Sans', Arial")
    txt = txt.replace("Arial,", "'IBM Plex Sans', Arial,")
    txt = re.sub(r'<svg([^>]*?)width="[^"]*"([^>]*?)height="[^"]*"', r'<svg class="fig"\1\2', txt, count=1)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(txt)


def main():
    daily = pd.read_csv(os.path.join(ANALYSIS, "master_stats", "daily_solved_and_inflow.csv"), parse_dates=["date"]).set_index("date")
    wk = pd.read_csv(os.path.join(ANALYSIS, "master_stats", "weekly_master.csv"), parse_dates=["week"]).set_index("week")
    legal = pd.read_csv(os.path.join(DATA_DIR, "legal_infringement_weekly.csv"), parse_dates=["res_week"]).set_index("res_week")
    cost26 = pd.read_csv(os.path.join(DATA_DIR, "cost_accounting_2026.csv"))
    proj_c = pd.read_csv(os.path.join(DATA_DIR, "projected_cost_2026_2028.csv"))
    mix = pd.read_csv(os.path.join(ANALYSIS, "sample2026", "out", "mix_overall.csv"))
    rw = pd.read_csv(os.path.join(ANALYSIS, "results", "situation_deep_dive", "rework_tax_by_period.csv"))
    comp = pd.read_csv(os.path.join(ANALYSIS, "deep_model", "monte_carlo", "weekly_obligation_inflow_central.csv"), parse_dates=["week"]).set_index("week")
    traj = pd.read_csv(os.path.join(ANALYSIS, "deep_model", "monte_carlo", "monte_carlo_trajectories_2026_2028.csv"), parse_dates=["week"])
    vd = pd.read_csv(os.path.join(ANALYSIS, "deep_model", "monte_carlo", "uncertainty_variance_decomposition.csv"))

    # =========================================================================
    # FIGURA 1: Cele patru regimuri ale ONRC (2023-2026) — Semantica colorata
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W_IN, 4.20), gridspec_kw={"height_ratios": [1.22, 1.0]}, sharex=True)
    wk_all = wk.loc["2023-04-03":"2026-11-16"].copy()
    low_vol = wk_all["finals_solved"] < 500
    wk_all.loc[low_vol, ["wait_med_d", "wait_p90_d", "wait_med_cerere_d", "wait_med_inmatric_d"]] = np.nan

    for ax in (ax1, ax2):
        style_axes(ax)
        ax.axvspan(pd.Timestamp("2024-07-18"), pd.Timestamp("2024-07-26"), color="#D9D5CA", alpha=0.95, zorder=1)
        ax.axvspan(pd.Timestamp("2024-07-27"), pd.Timestamp("2024-11-30"), color=WARN_SOFT, alpha=0.58, zorder=0)
        ax.axvspan(pd.Timestamp("2026-08-01"), pd.Timestamp("2026-11-18"), color=ALERT_SOFT, alpha=0.65, zorder=0)
        ax.axvline(pd.Timestamp("2026-04-27"), color=WARN, ls=":", lw=0.95, zorder=1)

    ax1.fill_between(wk_all.index, wk_all["wait_med_d"], wk_all["wait_p90_d"], color=ALERT_SOFT, alpha=0.65, label="Interval mediană – p90", zorder=2)
    ax1.plot(wk_all.index, wk_all["wait_p90_d"], color=ALERT, lw=0.9, ls="--", alpha=0.85, label="Percentila 90 (p90)", zorder=3)
    ax1.plot(wk_all.index, wk_all["wait_med_d"], color=NAVY, lw=1.7, label="Mediană săptămânală (toate deciziile finale)", zorder=4)
    ax1.axhline(3.0, color=SOL, ls="--", lw=1.1, zorder=3)
    ax1.text(pd.Timestamp("2023-04-12"), 5.1, "Țintă operațională: 3 zile (standard legal Art. 105: 1 zi lucrătoare)",
             fontsize=6.7, fontweight="bold", color=SOL, path_effects=HALO, zorder=5)

    ax1.annotate("Oprire migrare portal\n18–26 iul. 2024 (0 zile lucr.)",
                 xy=(pd.Timestamp("2024-07-22"), 2.0), xytext=(pd.Timestamp("2023-12-15"), 23.0),
                 arrowprops=dict(arrowstyle="-", color=INK3, lw=0.65, connectionstyle="angle,angleA=0,angleB=90,rad=0"),
                 fontsize=6.5, color=INK2, ha="center", va="bottom", path_effects=HALO)
    ax1.annotate("Criza 2024 (colaps portal):\nvârf 21,9 zile med. (23 sep.)\n30,9 zile p90",
                 xy=(pd.Timestamp("2024-09-23"), 21.9), xytext=(pd.Timestamp("2024-11-28"), 38.5),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.75),
                 fontsize=6.6, color=WARN, fontweight="bold", ha="left", path_effects=HALO)
    ax1.annotate("27 apr. 2026:\nprag rutare 3 zile\n(≤1 zi: 14,4% → 1,1%)",
                 xy=(pd.Timestamp("2026-04-27"), 19.0), xytext=(pd.Timestamp("2025-11-18"), 34.5),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.65),
                 fontsize=6.5, color=INK2, ha="center", path_effects=HALO)
    ax1.annotate("16–18 nov. 2026:\n57,0 z CERERE265\n61,7 z (p90)",
                 xy=(pd.Timestamp("2026-11-16"), 56.9), xytext=(pd.Timestamp("2026-05-15"), 53.0),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.85),
                 fontsize=6.8, fontweight="bold", color=ALERT, ha="right", path_effects=HALO)

    ax1.set_ylabel("Zile calendaristice", fontsize=7.2, color=NAVY)
    ax1.set_ylim(0, 66)
    ax1.set_yticks([0, 15, 30, 45, 60])
    ax1.legend(loc="upper left", ncol=1, bbox_to_anchor=(0.0, 1.01))
    ax1.set_title("A. Timp de soluționare (depunere → decizie finală), săptămâni cu ≥500 decizii",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)

    wk_v = wk_all.copy()
    wk_v.loc[wk_v["workdays"] < 3, ["decisions_per_workday", "finals_per_workday"]] = np.nan
    ax2.fill_between(wk_v.index, wk_v["finals_per_workday"], wk_v["decisions_per_workday"],
                     color=NAVY_SOFT, alpha=0.85, label="Amânări / reluări (~20% din decizii)", zorder=2)
    ax2.plot(wk_v.index, wk_v["decisions_per_workday"], color=NAVY_MID, lw=0.95, ls="--", label="Toate deciziile / zi lucrătoare", zorder=3)
    ax2.plot(wk_v.index, wk_v["finals_per_workday"], color=NAVY, lw=1.65, label="Decizii finale / zi lucrătoare (Admis + Respins)", zorder=4)

    ax2.annotate("Aug. 2024: producția a căzut\ncu 64% (1.236–1.808 finale / zi)",
                 xy=(pd.Timestamp("2024-08-05"), 1320), xytext=(pd.Timestamp("2023-07-15"), 750),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.75),
                 fontsize=6.6, color=WARN, fontweight="bold", path_effects=HALO)
    ax2.annotate("Nov. 2026: producție record\n4.238–4.448 finale / zi\n(5.367–5.581 decizii totale / zi)",
                 xy=(pd.Timestamp("2026-11-09"), 4433), xytext=(pd.Timestamp("2025-07-05"), 1150),
                 arrowprops=dict(arrowstyle="->", color=NAVY, lw=0.75),
                 fontsize=6.7, color=NAVY, fontweight="bold", path_effects=HALO)

    ax2.set_ylabel("Decizii / zi lucrătoare", fontsize=7.2, color=NAVY)
    ax2.set_ylim(0, 6800)
    ax2.set_yticks([0, 2000, 4000, 6000])
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: ro_num(x)))
    ax2.legend(loc="upper left", ncol=2, bbox_to_anchor=(0.0, 1.01))
    ax2.set_title("B. Producția ONRC pe zi lucrătoare (săptămâni cu ≥3 zile lucrătoare)",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(ro_date_fmt))
    ax2.set_xlim(pd.Timestamp("2023-03-25"), pd.Timestamp("2026-12-05"))

    fig.subplots_adjust(left=0.085, right=0.985, top=0.94, bottom=0.075, hspace=0.26)
    save_svg_and_png(fig, "fig1_regimuri_onrc")

    # =========================================================================
    # FIGURA 2: Flux zilnic (intrări vs soluționate) & Stoc reconciliat (2026)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W_IN, 4.15), gridspec_kw={"height_ratios": [1.18, 1.0]}, sharex=True)
    wd26 = daily.loc["2026-01-05":"2026-11-17"]
    wd26 = wd26[wd26["is_workday"]].copy()
    cut = pd.Timestamp("2026-09-17")
    wd_obs, wd_est = wd26.loc[:cut], wd26.loc[cut:]

    for ax in (ax1, ax2):
        style_axes(ax)
        ax.axvline(cut, color=INK3, ls=":", lw=0.85, zorder=1)

    ax1.fill_between(wd26.index, wd26["solved_finals_5wd_avg"], wd26["inflow_5wd_avg"],
                     where=wd26["inflow_5wd_avg"] >= wd26["solved_finals_5wd_avg"],
                     color=ALERT_SOFT, alpha=0.85, interpolate=True, label="Acumulare restanțe (intrări > soluționate)", zorder=1)
    ax1.fill_between(wd26.index, wd26["solved_finals_5wd_avg"], wd26["inflow_5wd_avg"],
                     where=wd26["inflow_5wd_avg"] < wd26["solved_finals_5wd_avg"],
                     color=SOL_SOFT, alpha=0.9, interpolate=True, label="Drenare coadă (soluționate > intrări)", zorder=1)
    ax1.fill_between(wd_est.index, wd_est["inflow_low_5wd_avg"], wd_est["inflow_high_5wd_avg"],
                     color=WARN_SOFT, alpha=0.65, zorder=2)
    ax1.plot(wd_obs.index, wd_obs["inflow_5wd_avg"], color=ALERT, lw=1.7, label="Dosare intrate / zi lucr. (observat, medie 5 zile)", zorder=4)
    ax1.plot(wd_est.index, wd_est["inflow_5wd_avg"], color=ALERT, lw=1.5, ls="--", label="Dosare intrate / zi lucr. (estimat DiD din app_nr)", zorder=4)
    ax1.plot(wd26.index, wd26["solved_finals_5wd_avg"], color=NAVY, lw=1.7, label="Dosare finale soluționate / zi lucr. (medie 5 zile)", zorder=5)

    peak_idx = wd_obs["inflow_5wd_avg"].idxmax()
    peak_val = wd_obs.loc[peak_idx, "inflow_5wd_avg"]
    ax1.annotate(f"Vârf CAEN Rev. 3: {ro_num(peak_val)} / zi (medie 5z)\n~13.800 vârf zilnic pe 14–15 sep.",
                 xy=(peak_idx, peak_val), xytext=(pd.Timestamp("2026-04-18"), 7650),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.75),
                 fontsize=6.6, fontweight="bold", color=ALERT, path_effects=HALO)
    ax1.text(cut + pd.Timedelta(days=3), 10850, "Frontiera de cenzurare\n(estimare app_nr →)",
             fontsize=6.3, color=INK3, va="top", path_effects=HALO)
    ax1.annotate("Soluționate 2–17 nov.:\n4.448 finale / zi lucr.",
                 xy=(wd26.index[-1], wd26["solved_finals_5wd_avg"].iloc[-1]),
                 xytext=(pd.Timestamp("2026-09-24"), 1550),
                 arrowprops=dict(arrowstyle="->", color=NAVY, lw=0.75),
                 fontsize=6.6, fontweight="bold", color=NAVY, path_effects=HALO)
    ax1.annotate("Intrări est. 2–17 nov.:\n~4.030–4.514 / zi lucr.",
                 xy=(wd_est.index[-2], wd_est["inflow_5wd_avg"].iloc[-2]),
                 xytext=(pd.Timestamp("2026-09-26"), 7250),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.7),
                 fontsize=6.5, color=ALERT, path_effects=HALO)

    ax1.set_ylabel("Dosare / zi lucrătoare", fontsize=7.2, color=NAVY)
    ax1.set_ylim(0, 14600)
    ax1.set_yticks([0, 3000, 6000, 9000, 12000])
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: ro_num(x)))
    ax1.legend(loc="upper left", ncol=2, fontsize=6.4, columnspacing=1.2, bbox_to_anchor=(0.0, 1.02))
    ax1.set_title("A. Cerere zilnică vs. dosare finale soluționate (medie mobilă 5 zile lucrătoare, 2026)",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)

    d_sub = daily.loc["2026-01-05":"2026-11-18"].copy()
    jun_idx = pd.Timestamp("2026-06-01")
    pend_mid = pd.Series(index=d_sub.index, dtype=float)
    pend_lo = pd.Series(index=d_sub.index, dtype=float)
    pend_hi = pd.Series(index=d_sub.index, dtype=float)
    pre_net = (d_sub.loc[:jun_idx, "inflow_observed_decided"] - d_sub.loc[:jun_idx, "finals_solved"]).cumsum()
    pend_mid.loc[:jun_idx] = pre_net + (19769.0 - pre_net.iloc[-1])
    pend_lo.loc[:jun_idx] = pend_mid.loc[:jun_idx]
    pend_hi.loc[:jun_idx] = pend_mid.loc[:jun_idx]
    post = d_sub.loc[jun_idx:].copy()
    raw_in_lo = np.where(post.index <= cut, post["inflow_observed_decided"], post["inflow_est_low"].fillna(0) * 1.15)
    raw_in_mid = np.where(post.index <= cut, post["inflow_observed_decided"], post["inflow_best_est"] * 1.13)
    raw_in_hi = np.where(post.index <= cut, post["inflow_observed_decided"], post["inflow_est_high"].fillna(0) * 1.07)
    pend_lo.loc[jun_idx:] = 19769.0 + (raw_in_lo - post["finals_solved"]).cumsum()
    pend_mid.loc[jun_idx:] = 19769.0 + (raw_in_mid - post["finals_solved"]).cumsum()
    pend_hi.loc[jun_idx:] = 19769.0 + (raw_in_hi - post["finals_solved"]).cumsum()

    ax2.fill_between(pend_mid.index, pend_lo / 1000.0, pend_hi / 1000.0, color=ALERT_SOFT, alpha=0.85, label="Interval reconciliat 80% (180–240 mii)")
    ax2.plot(pend_mid.index, pend_mid / 1000.0, color=ALERT, lw=1.75, label="Stoc estimat de dosare în așteptare (central: ~208 mii)")
    ax2.scatter([pd.Timestamp("2026-11-15")], [210.0], color=NAVY, s=36, zorder=6, marker="D",
                label="Ancoră externă SAONRC / presă (>210 mii dosare)")
    ax2.annotate("18 nov. 2026: ~208 mii restanțe\nconfirmă cifra sindicală >210 mii\n(≈47 zile lucrătoare de muncă)",
                 xy=(pd.Timestamp("2026-11-15"), 210), xytext=(pd.Timestamp("2026-06-18"), 172),
                 arrowprops=dict(arrowstyle="->", color=NAVY, lw=0.8),
                 fontsize=6.7, fontweight="bold", color=NAVY, path_effects=HALO)
    ax2.set_ylabel("Mii dosare blocate", fontsize=7.2, color=NAVY)
    ax2.set_ylim(0, 265)
    ax2.set_yticks([0, 50, 100, 150, 200, 250])
    ax2.legend(loc="upper left", ncol=1)
    ax2.set_title("B. Stocul cumulat de dosare nesoluționate în 2026 (calibrat pe contorul app_nr)",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(ro_date_fmt))
    ax2.set_xlim(pd.Timestamp("2026-01-01"), pd.Timestamp("2026-11-24"))

    fig.subplots_adjust(left=0.085, right=0.985, top=0.94, bottom=0.075, hspace=0.26)
    save_svg_and_png(fig, "fig2_flux_zilnic_stoc")

    # =========================================================================
    # FIGURA 3: Infringement UE (Directiva 2019/1151) & Art. 105 Legea 265/2022
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W_IN, 4.25), gridspec_kw={"height_ratios": [1.18, 1.0]}, sharex=True)
    leg = legal.loc["2023-04-03":"2026-11-16"].copy()
    leg.loc[leg["n_inmatric"] < 100, ["med_wd", "p90_wd", "pct_gt_1wd", "pct_gt_5wd", "pct_gt_10wd"]] = np.nan

    for ax in (ax1, ax2):
        style_axes(ax)
        ax.axvspan(pd.Timestamp("2024-08-12"), pd.Timestamp("2024-11-18"), color=WARN_SOFT, alpha=0.55, zorder=0)
        ax.axvspan(pd.Timestamp("2026-07-24"), pd.Timestamp("2026-11-18"), color=ALERT_SOFT, alpha=0.68, zorder=0)
        ax.axvline(pd.Timestamp("2026-07-24"), color=WARN, ls=":", lw=1.0, zorder=2)
        ax.axvline(pd.Timestamp("2026-08-27"), color=ALERT, ls=":", lw=1.05, zorder=2)

    ax1.fill_between(leg.index, leg["med_wd"], leg["p90_wd"], color=NAVY_SOFT, alpha=0.75, label="Interval mediană – p90 (INMATRIC265)", zorder=2)
    ax1.plot(leg.index, leg["p90_wd"], color=NAVY_MID, lw=0.85, ls="--", label="Percentila 90 înmatriculări noi", zorder=3)
    ax1.plot(leg.index, leg["med_wd"], color=NAVY, lw=1.7, label="Mediană înmatriculări noi (zile lucrătoare)", zorder=4)

    ax1.axhline(1.0, color=SOL, ls=":", lw=1.05, zorder=3)
    ax1.axhline(5.0, color=WARN, ls="--", lw=1.15, zorder=3)
    ax1.axhline(10.0, color=ALERT, ls="-.", lw=1.2, zorder=3)

    ax1.text(pd.Timestamp("2023-04-12"), 1.7, "Legea 265/2022, Art. 105(1): 1 zi lucr.", fontsize=6.4, fontweight="bold", color=SOL, path_effects=HALO)
    ax1.text(pd.Timestamp("2023-04-12"), 6.0, "Directiva (UE) 2019/1151: 5 zile lucr. (formulare-tip PF)", fontsize=6.5, fontweight="bold", color=WARN, path_effects=HALO)
    ax1.text(pd.Timestamp("2023-04-12"), 11.2, "Directiva (UE) 2019/1151: 10 zile lucr. (prag absolut)", fontsize=6.5, fontweight="bold", color=ALERT, path_effects=HALO)

    ax1.annotate("Episod 2024:\n>5 zl: 12 aug.\n>10 zl: 26 aug.",
                 xy=(pd.Timestamp("2024-08-26"), 10.5), xytext=(pd.Timestamp("2023-12-01"), 25.0),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.7),
                 fontsize=6.5, color=WARN, fontweight="bold", path_effects=HALO)
    ax1.annotate("Infringement susținut 2026:\n• >5 zl (UE PF): 24 iul. 2026\n• >10 zl (UE abs.): 27 aug. 2026\n• Nov. 2026: 30–32 zl median",
                 xy=(pd.Timestamp("2026-08-27"), 11.5), xytext=(pd.Timestamp("2025-05-05"), 25.5),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.8),
                 fontsize=6.7, fontweight="bold", color=ALERT, path_effects=HALO)

    ax1.set_ylabel("Zile lucrătoare", fontsize=7.2, color=NAVY)
    ax1.set_ylim(0, 44)
    ax1.set_yticks([0, 10, 20, 30, 40])
    ax1.legend(loc="upper left", ncol=2, bbox_to_anchor=(0.0, 1.01))
    ax1.set_title("A. Durata constituirii de firme noi (INMATRIC265) în zile lucrătoare vs. pragurile legale",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)

    ax2.plot(leg.index, leg["pct_gt_1wd"], color=SOL, lw=1.1, alpha=0.85, label="INMATRIC265 > 1 zi lucr. (Legea 265/2022)")
    ax2.plot(leg.index, leg["pct_gt_5wd"], color=WARN, lw=1.55, label="INMATRIC265 > 5 zile lucr. (UE formular-tip)")
    ax2.plot(leg.index, leg["pct_gt_10wd"], color=ALERT, lw=1.75, label="INMATRIC265 > 10 zile lucr. (UE prag absolut)")
    ax2.plot(leg.index, leg["cer_pct_gt_30cal"], color=NAVY, lw=1.25, ls="--", label="CERERE265 > 30 zile cal. (risc inactivare ANAF sediu)")

    ax2.annotate("16–18 nov. 2026:\n>1 zl: 100,0% · >5 zl: 94,5%\n>10 zl: 87,1% · >30 z cal.: 84,7%",
                 xy=(pd.Timestamp("2026-11-16"), 87.1), xytext=(pd.Timestamp("2025-07-01"), 62.0),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.75),
                 fontsize=6.6, fontweight="bold", color=NAVY, path_effects=HALO)

    ax2.set_ylabel("Dosare neconforme (%)", fontsize=7.2, color=NAVY)
    ax2.set_ylim(0, 109)
    ax2.set_yticks([0, 25, 50, 75, 100])
    ax2.legend(loc="upper left", ncol=2, bbox_to_anchor=(0.0, 1.01))
    ax2.set_title("B. Ponderea săptămânală a dosarelor care depășesc pragurile naționale, europene și ANAF",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(ro_date_fmt))
    ax2.set_xlim(pd.Timestamp("2023-03-25"), pd.Timestamp("2026-12-05"))

    fig.subplots_adjust(left=0.085, right=0.985, top=0.94, bottom=0.075, hspace=0.26)
    save_svg_and_png(fig, "fig3_infringement_ue")

    # =========================================================================
    # FIGURA 4: Anatomia cozii & Spirala amânărilor / respingerilor
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_IN, 2.90), gridspec_kw={"width_ratios": [1.18, 1.0]})
    style_axes(ax1, ygrid=False, xgrid=True)
    style_axes(ax2, ygrid=True, xgrid=False)

    ro_labels = {
        "multiple changes": "Modificări multiple",
        "CAEN Rev.3 only": "Doar CAEN Rev. 3",
        "registration": "Înmatriculare firmă nouă",
        "activity codes only (no Rev.3)": "Coduri activitate (non-Rev. 3)",
        "shareholders/share transfers": "Asociați / cesiuni",
        "dissolution/deregistration": "Dizolvare / radiere",
        "branches/secondary offices": "Puncte de lucru",
        "registered office/address": "Sediu social / prelungire",
    }
    time_map = {
        "multiple changes": "6,7 min",
        "CAEN Rev.3 only": "4,2 min",
        "registration": "6,9 min",
        "activity codes only (no Rev.3)": "7,8 min",
        "shareholders/share transfers": "8,9 min*",
        "dissolution/deregistration": "7,0 min*",
        "branches/secondary offices": "8,9 min*",
        "registered office/address": "8,9 min*",
    }
    top8 = mix.head(8).iloc[::-1].copy()
    top8["ro_type"] = top8["type"].map(ro_labels)
    # Semantic: SOL = automatizabil CAEN-only, NAVY = firme noi prioritare, NAVY_MID = restul
    bar_cols = [SOL if "CAEN" in t else (NAVY if t == "registration" else "#8FA5B8") for t in top8["type"]]
    bars = ax1.barh(top8["ro_type"], top8["pct"], color=bar_cols, edgecolor=NAVY, linewidth=0.4, height=0.62)
    for b, (_, row) in zip(bars, top8.iterrows()):
        tm = time_map.get(row["type"], "")
        ax1.text(row["pct"] + 0.6, b.get_y() + b.get_height() / 2,
                 f"{ro_num(row['pct'], 1)}% ({tm})", va="center", fontsize=6.5,
                 fontweight="bold", color=SOL if "CAEN" in row["type"] else NAVY)
    ax1.set_xlim(0, 38)
    ax1.set_xticks([0, 10, 20, 30])
    ax1.set_xlabel("% din deciziile finale (n = 11.414)", fontsize=6.9, color=NAVY)
    ax1.set_title("A. Mixul cererilor 2026 (verde = automatizabil)", loc="left", fontsize=7.5, fontweight="bold", color=NAVY, pad=5)

    x = np.arange(len(rw))
    w = 0.36
    ax2.bar(x - w / 2, rw["extra_decisions_pct"], w, color=WARN_SOFT, edgecolor=WARN, linewidth=0.6, label="Decizii suplimentare din amânări (%)")
    ax2.bar(x + w / 2, rw["reject_rate_if_postponed_pct"], w, color=NAVY, edgecolor=NAVY, linewidth=0.5, label="Respingere dacă a fost amânat (%)")
    ax2.bar(4 + w / 2, rw["reject_rate_if_postponed_pct"].iloc[-1], w, color=ALERT, edgecolor=ALERT, linewidth=0.5)
    for xi, v1, v2 in zip(x, rw["extra_decisions_pct"], rw["reject_rate_if_postponed_pct"]):
        ax2.text(xi - w / 2, v1 + 0.9, f"{ro_num(v1, 1)}", ha="center", fontsize=6.2, color=WARN, fontweight="bold")
        ax2.text(xi + w / 2, v2 + 0.9, f"{ro_num(v2, 1)}", ha="center", fontsize=6.4, fontweight="bold", color=ALERT if xi == 4 else NAVY)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["2023\nVechi", "2024\nVechi", "2025\nNou", "2026\nIan–Iul", "2026\nAug–Nov"], fontsize=6.6)
    ax2.set_ylim(0, 51)
    ax2.set_yticks([0, 10, 20, 30, 40, 50])
    ax2.set_ylabel("Procent (%)", fontsize=6.9, color=NAVY)
    ax2.legend(loc="upper left", fontsize=6.3, bbox_to_anchor=(0.0, 1.02))
    ax2.set_title("B. Reluări și respingeri după amânare", loc="left", fontsize=7.5, fontweight="bold", color=NAVY, pad=5)
    ax2.annotate("78% redepun (med. 15z)\n50,2% prevenibile de portal",
                 xy=(4 + w / 2, 37.8), xytext=(0.15, 34.5),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.75),
                 fontsize=6.3, fontweight="bold", color=ALERT, path_effects=HALO)

    fig.subplots_adjust(left=0.235, right=0.985, top=0.88, bottom=0.17, wspace=0.25)
    save_svg_and_png(fig, "fig4_structura_rework")

    # =========================================================================
    # FIGURA 5: Recensământ firme & Sarcina pe obligații legale (2026-2028)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_IN, 3.00), gridspec_kw={"width_ratios": [0.78, 1.52]})
    style_axes(ax1)
    style_axes(ax2)

    x = np.arange(2)
    touched = np.array([702.5, 178.6])
    active_left = np.array([265.0, 194.4])
    zombies = np.array([359.5, 100.0])
    ax1.bar(x, touched, width=0.52, color=SOL, edgecolor=NAVY, lw=0.45, label="Atinse 2025–26 (CUI exact)")
    ax1.bar(x, active_left, bottom=touched, width=0.52, color=WARN, edgecolor=NAVY, lw=0.45, label="Active neactualizate (~460k)")
    ax1.bar(x, zombies, bottom=touched + active_left, width=0.52, color="#D8D5CC", edgecolor=NAVY, lw=0.45, hatch="///", label="Inactive / dormante (~460k)")
    for xi, t_v, a_v, z_v in zip(x, touched, active_left, zombies):
        ax1.text(xi, t_v / 2, f"{t_v:.0f}k", ha="center", va="center", color=PAPER, fontweight="bold", fontsize=6.9)
        ax1.text(xi, t_v + a_v / 2, f"~{a_v:.0f}k", ha="center", va="center", color=PAPER, fontweight="bold", fontsize=6.7)
        ax1.text(xi, t_v + a_v + z_v / 2, f"~{z_v:.0f}k", ha="center", va="center", color=INK, fontweight="bold", fontsize=6.5, path_effects=HALO)
        ax1.text(xi, t_v + a_v + z_v + 35, f"{t_v+a_v+z_v:.0f}k", ha="center", fontweight="bold", fontsize=7.0, color=NAVY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(["Persoane Juridice\n(SRL / SA)", "Persoane Fizice\n(PFA / II / IF)"], fontsize=6.8)
    ax1.set_ylabel("Entități înregistrate (mii)", fontsize=7.0, color=NAVY)
    ax1.set_ylim(0, 1880)
    ax1.set_yticks([0, 500, 1000, 1500])
    ax1.legend(loc="upper right", fontsize=6.2)
    ax1.set_title("A. Recensământ ONRC (~1,80 mil.)", loc="left", fontsize=7.6, fontweight="bold", color=NAVY, pad=5)

    weeks = comp.index
    w_org = comp["organic"].values / 1000.0
    w_inact = (comp["inact_def"].values * 0.95 + comp["inact_anaf"].values * 0.50) / 1000.0
    w_caen = (comp["caen_mar27"].values * 0.54) / 1000.0
    w_cap26 = (comp["cap_dec26"].values * 1.35) / 1000.0
    w_cap27 = (comp["cap_dec27"].values * 1.35) / 1000.0
    ax2.stackplot(
        weeks, w_org, w_inact, w_caen, w_cap26, w_cap27,
        labels=[
            "Cerere organică (cu vârf T1)",
            "Inactivări & dizolvări ANAF",
            "Val CAEN rămas (mar. '27, 0,54×)",
            "Capital MO −50% (dec. '26, 1,35×)",
            "Capital 5.000 lei (dec. '27, 1,35×)",
        ],
        colors=["#C8D6E2", "#D9A441", WARN, "#6A538C", ALERT],
        alpha=0.90,
    )
    ax2.plot(weeks, comp["capacity_status_quo"].values / 1000.0, color=PAPER, lw=2.4, zorder=5)
    ax2.plot(weeks, comp["capacity_status_quo"].values / 1000.0, color=NAVY, lw=1.35, ls="--",
             label="Capacitate actuală (~21,4k/săpt.)", zorder=6)
    ax2.annotate("31 dec. '26\nMO −50%", xy=(pd.Timestamp("2026-12-28"), 27), xytext=(pd.Timestamp("2026-11-15"), 42),
                 arrowprops=dict(arrowstyle="->", color="#6A538C", lw=0.7), fontsize=6.4, fontweight="bold", color="#6A538C", path_effects=HALO)
    ax2.annotate("25 mar. '27\nCAEN + T1", xy=(pd.Timestamp("2027-03-22"), 47), xytext=(pd.Timestamp("2027-05-05"), 49),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.75), fontsize=6.6, fontweight="bold", color=WARN, path_effects=HALO)
    ax2.annotate("18 dec. '27\ncapital 5.000 lei", xy=(pd.Timestamp("2027-12-13"), 50), xytext=(pd.Timestamp("2028-01-22"), 47),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.8), fontsize=6.6, fontweight="bold", color=ALERT, path_effects=HALO)
    ax2.set_ylabel("Mii dosare-echiv. / săpt.", fontsize=7.0, color=NAVY)
    ax2.set_ylim(0, 68)
    ax2.set_yticks([0, 20, 40, 60])
    ax2.legend(loc="upper center", ncol=2, fontsize=6.2, bbox_to_anchor=(0.5, 1.02))
    ax2.set_title("B. Sarcina săptămânală pe obligații legale vs. capacitate (2026–2028)", loc="left", fontsize=7.6, fontweight="bold", color=NAVY, pad=5)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(ro_date_fmt))

    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.14, wspace=0.22)
    save_svg_and_png(fig, "fig5_recensamant_obligatii")

    # =========================================================================
    # FIGURA 6: Contabilitatea completă a costurilor (#1 Economie + #2 Buget Stat)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_IN, 3.00), gridspec_kw={"width_ratios": [1.04, 1.12]})
    style_axes(ax1)
    style_axes(ax2)

    mid_r = cost26[cost26["case"] == "mid"].iloc[0]
    cats_a = ["Firme noi\nîntârziate", "Mențiuni\nsubstanțiale", "Inactivări\nsediu expirat", "Conformare\n& redepuneri"]
    econ_vals = [mid_r["chA_econ_meur"], mid_r["chC_econ_meur"], mid_r["chB_econ_meur"], mid_r["chD_econ_meur"]]
    fisc_vals = [mid_r["chA_fisc_meur"], mid_r["chC_fisc_meur"], mid_r["chB_fisc_meur"], mid_r["chD_fisc_meur"]]
    x = np.arange(len(cats_a))
    w = 0.36
    ax1.bar(x - w / 2, econ_vals, w, color=NAVY, edgecolor=NAVY, lw=0.45, label="#1 Cost Economie (200,7 mil. €)")
    ax1.bar(x + w / 2, fisc_vals, w, color=ALERT, edgecolor=ALERT, lw=0.45, alpha=0.88, hatch="///", label="#2 Impact Buget Stat (36,3 mil. €)")
    for xi, v1, v2 in zip(x, econ_vals, fisc_vals):
        ax1.text(xi - w / 2, v1 + 2.0, f"{ro_num(v1, 1)}", ha="center", fontsize=6.5, fontweight="bold", color=NAVY)
        ax1.text(xi + w / 2, v2 + 2.0, f"{ro_num(v2, 1)}", ha="center", fontsize=6.4, fontweight="bold", color=ALERT)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cats_a, fontsize=6.6)
    ax1.set_ylabel("Milioane EUR", fontsize=7.0, color=NAVY)
    ax1.set_ylim(0, 118)
    ax1.set_yticks([0, 25, 50, 75, 100])
    ax1.legend(loc="upper right", fontsize=6.4)
    ax1.text(0.98, 0.72, "Ritm zilnic nov. 2026:\n2,42 mil. €/zi economie\n0,44 mil. €/zi buget",
             transform=ax1.transAxes, ha="right", va="top", fontsize=6.4, color=ALERT, fontweight="bold",
             bbox=dict(boxstyle="square,pad=0.38", fc=ALERT_SOFT, ec=ALERT, lw=0.55))
    ax1.set_title("A. Costul crizei 2026 pe canale (central)", loc="left", fontsize=7.6, fontweight="bold", color=NAVY, pad=5)

    sc_labs = ["S1: Status\nQuo", "S2: Doar\nOUG MJ", "S3: Reformă\nDigitală", "S4: Pachet\nCombinat"]
    y_e = proj_c["econ_cost_meur_mid"].values / 1000.0
    y_f = proj_c["fisc_cost_meur_mid"].values / 1000.0
    x2 = np.arange(len(sc_labs))
    bar_cols_b = [ALERT, WARN, NAVY_MID, SOL]
    ax2.bar(x2 - w / 2, y_e, w, color=bar_cols_b, edgecolor=NAVY, lw=0.45, label="#1 Economie (mld. €)")
    ax2.bar(x2 + w / 2, y_f, w, color="#E8E4DC", edgecolor=NAVY, lw=0.45, hatch="///", label="#2 Buget Stat (mld. €)")
    for xi, ve, vf in zip(x2, y_e, y_f):
        c_txt = SOL if xi == 3 else (ALERT if xi == 0 else NAVY)
        ax2.text(xi - w / 2, ve + 0.07, f"{ro_num(ve, 2)}", ha="center", fontsize=6.6, fontweight="bold", color=c_txt)
        ax2.text(xi + w / 2, vf + 0.07, f"{ro_num(vf, 2)}", ha="center", fontsize=6.3, color=INK2)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(sc_labs, fontsize=6.6)
    ax2.set_ylabel("Miliarde EUR (nov. 2026 – iun. 2028)", fontsize=7.0, color=NAVY)
    ax2.set_ylim(0, 3.60)
    ax2.set_yticks([0, 1.0, 2.0, 3.0])
    ax2.legend(loc="upper right", fontsize=6.4)
    ax2.annotate("Pachetul S4 salvează\n2,56 mld. € în economie\nși 465 mil. € la buget",
                 xy=(3 - w / 2, y_e[3] + 0.16), xytext=(1.55, 2.10),
                 arrowprops=dict(arrowstyle="->", color=SOL, lw=0.85),
                 fontsize=6.6, fontweight="bold", color=SOL, path_effects=HALO)
    ax2.set_title("B. Cost cumulat pe scenarii (roșu = inacțiune, verde = soluție)", loc="left", fontsize=7.4, fontweight="bold", color=NAVY, pad=5)

    fig.subplots_adjust(left=0.08, right=0.985, top=0.88, bottom=0.16, wspace=0.22)
    save_svg_and_png(fig, "fig6_costuri_economie_buget")

    # =========================================================================
    # FIGURA 7: Monte Carlo (2.000 rulări) + Descompunerea incertitudinii
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(W_IN, 4.85), gridspec_kw={"height_ratios": [1.18, 1.12]})
    style_axes(ax1)
    style_axes(ax2, ygrid=False, xgrid=True)

    w_mc = traj["week"]
    sc_styles = [
        ("S1", ALERT, "-", 1.8, ALERT_SOFT, "S1: Status Quo — toate valurile legale (mediană & IC 80%)"),
        ("S2", WARN, "--", 1.4, WARN_SOFT, "S2: Doar proiect OUG MJ (+17% capacitate temporară)"),
        ("S3", NAVY_MID, "-.", 1.3, NAVY_SOFT, "S3: Reformă Digitală — CAEN automat + validare portal Tier A"),
        ("S4", SOL, "-", 1.85, SOL_SOFT, "S4: Pachet Combinat — OUG + Digital + eșalonare capital 2027"),
    ]
    for tag, col, ls, lw, fill, lab in sc_styles:
        ax1.fill_between(w_mc, traj[f"{tag}_p10"], traj[f"{tag}_p90"], color=fill, alpha=0.55)
        ax1.plot(w_mc, traj[f"{tag}_p50"], color=col, ls=ls, lw=lw, label=lab)
    ax1.axhline(3.0, color=SOL, ls=":", lw=1.05, zorder=4)
    ax1.text(pd.Timestamp("2026-11-24"), 7.5, "Țintă operațională: 3 zile (lege: 1 zi lucr.)",
             fontsize=6.5, fontweight="bold", color=SOL, path_effects=HALO)
    ax1.annotate("S1 (iun. '28): 196 z [175–210]\nP(>120 z) = 100%",
                 xy=(w_mc.iloc[-1], traj["S1_p50"].iloc[-1]), xytext=(pd.Timestamp("2027-10-15"), 184),
                 arrowprops=dict(arrowstyle="->", color=ALERT, lw=0.8),
                 fontsize=6.6, fontweight="bold", color=ALERT, path_effects=HALO)
    ax1.annotate("S2 (iun. '28): 105 z [42–147]",
                 xy=(w_mc.iloc[-1], traj["S2_p50"].iloc[-1]), xytext=(pd.Timestamp("2027-11-25"), 132),
                 arrowprops=dict(arrowstyle="->", color=WARN, lw=0.7),
                 fontsize=6.5, fontweight="bold", color=WARN, path_effects=HALO)
    ax1.annotate("S4 revine la ≤3 zile\ndin octombrie 2027",
                 xy=(pd.Timestamp("2027-10-18"), 3.5), xytext=(pd.Timestamp("2027-11-15"), 26),
                 arrowprops=dict(arrowstyle="->", color=SOL, lw=0.85),
                 fontsize=6.6, fontweight="bold", color=SOL, path_effects=HALO)

    ax1.set_ylabel("Timp median așteptare (zile cal.)", fontsize=7.1, color=NAVY)
    ax1.set_ylim(0, 224)
    ax1.set_yticks([0, 50, 100, 150, 200])
    ax1.legend(loc="upper left", ncol=1, fontsize=6.5)
    ax1.set_title("A. Traiectorii mediane și benzi de încredere 80% (p10–p90) pentru patru scenarii",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(ro_date_fmt))

    ro_vd_map = {
        "Baseline registrar weekly capacity": "Capacitatea de bază a registratorilor",
        "Organic recurring baseline inflow": "Cererea organică recurentă de bază",
        "Remaining active CAEN Rev. 3 wave size": "Mărimea valului CAEN activ rămas",
        "CAEN-only processing time weight": "Ponderea de timp CAEN-only",
        "Share capital dossier complexity weight": "Complexitatea dosarelor de capital",
        "Total SRLs complying w/ 5,000 RON capital": "Nr. SRL care majorează capitalul",
        "ANAF mandatory ex-officio dissolutions": "Volumul dizolvărilor din oficiu ANAF",
        "ANAF dissolution processing weight": "Timpul pe dizolvările ANAF",
        "Current Nov 2026 pending backlog size": "Stocul exact de restanțe (nov. '26)",
        "Fiscal inactivation defensive filings": "Cereri defensive inactivare ANAF",
        "Dec 2026 50%-discount capital rush": "Afluxul dec. '26 (reducere 50% MO)",
    }
    top_vd = vd.head(10).iloc[::-1].copy()
    top_vd["ro_lab"] = top_vd["label"].map(lambda s: ro_vd_map.get(s, s))
    y_pos = np.arange(len(top_vd))
    h = 0.39
    ax2.barh(y_pos + h / 2, top_vd["var_share_jun27_pct"], h, color=NAVY_SOFT, edgecolor=NAVY, lw=0.45,
             label="Varianță iunie 2027 (post-CAEN)")
    ax2.barh(y_pos - h / 2, top_vd["var_share_jun28_pct"], h, color=NAVY, edgecolor=NAVY, lw=0.45,
             label="Varianță iunie 2028 (post-Capital)")
    for yi, v1, v2 in zip(y_pos, top_vd["var_share_jun27_pct"], top_vd["var_share_jun28_pct"]):
        if v1 >= 1.5:
            ax2.text(v1 + 0.6, yi + h / 2 + 0.03, f"{ro_num(v1, 1)}%", va="center", fontsize=6.0, color=NAVY_MID)
        if v2 >= 1.5:
            ax2.text(v2 + 0.6, yi - h / 2 - 0.03, f"{ro_num(v2, 1)}%", va="center", fontsize=6.1, fontweight="bold", color=NAVY)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(top_vd["ro_lab"], fontsize=6.5)
    ax2.set_xlabel("Pondere în varianța prognozei (ρ² Spearman normalizat, %)", fontsize=7.0, color=NAVY)
    ax2.set_xlim(0, 44)
    ax2.set_xticks([0, 10, 20, 30, 40])
    ax2.legend(loc="lower right", fontsize=6.5)
    ax2.set_title("B. Parametrii care explică incertitudinea prognozei (Status Quo)",
                  loc="left", fontsize=7.8, fontweight="bold", color=NAVY, pad=5)

    fig.subplots_adjust(left=0.33, right=0.985, top=0.94, bottom=0.08, hspace=0.30)
    pos1 = ax1.get_position()
    ax1.set_position([0.085, pos1.y0, 0.90, pos1.height])
    save_svg_and_png(fig, "fig7_monte_carlo")

    print("All 7 semantic-color editorial SVG + PNG figures written to:", OUT_DIR)


if __name__ == "__main__":
    main()
