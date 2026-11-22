"""Figurile raportului pentru instituții, în stilul Lab (generate_lab_figures):
aceeași paletă semantică, IBM Plex Sans, lățime 166 mm, fără titluri coapte în imagine.
Toate cifrele vin din LOCKED_CONSTANTS.json, oug_scenarios.json, BERC și portal.
"""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

import generate_lab_figures as G          # reuse palette, rcParams, style_axes, save routine
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IA = os.path.join(ROOT, "independent_audit")
OUTD = os.path.join(HERE, "figures_institutii"); os.makedirs(OUTD, exist_ok=True)
G.OUT_DIR = OUTD                          # save_svg_and_png writes here
sys.path.insert(0, IA)

L = json.load(open(os.path.join(IA, "out", "LOCKED_CONSTANTS.json"), encoding="utf-8"))
OUG = json.load(open(os.path.join(IA, "out", "oug_scenarios.json"), encoding="utf-8"))
NAVY, NAVY_MID, NAVY_SOFT = G.NAVY, G.NAVY_MID, G.NAVY_SOFT
ALERT, ALERT_SOFT, WARN, WARN_SOFT, SOL, SOL_SOFT = G.ALERT, G.ALERT_SOFT, G.WARN, G.WARN_SOFT, G.SOL, G.SOL_SOFT
INK, INK2, INK3, RULE, RULE2, TINT = G.INK, G.INK2, G.INK3, G.RULE, G.RULE2, G.TINT
W = G.W_IN; HALO = G.HALO; ron = G.ro_num
MO = {1:"ian.",2:"feb.",3:"mar.",4:"apr.",5:"mai",6:"iun.",7:"iul.",8:"aug.",9:"sep.",10:"oct.",11:"nov.",12:"dec."}
FIN = ["Admis", "Respins", "Renunțat"]

_B = None
def berc():
    global _B
    if _B is None:
        b = pd.read_pickle(str(config.BERC_PKL))
        b = b[b.res.notna() & b.app.notna()].copy()
        b["Wd"] = (b.res - b.app).dt.total_seconds() / 86400
        b["d"] = b.res.dt.normalize()
        _B = b
    return _B


# ---------------------------------------------------------------- F1 history
def f_history():
    b = berc(); f = b[b.sol.isin(FIN) & (b.Wd >= 0) & (b.Wd < 400)]
    f = f[f.d >= "2023-04-03"]
    wk = f.groupby(f.d.dt.to_period("W-SUN").apply(lambda p: p.start_time)).agg(
        med=("Wd", "median"), n=("Wd", "size"))
    days = b[b.d >= "2023-04-03"].groupby(b.d.dt.to_period("W-SUN").apply(lambda p: p.start_time))["d"].nunique()
    wk["perday"] = wk["n"] / days.reindex(wk.index).clip(lower=1)
    wk.loc[wk["perday"] < 500, "med"] = np.nan          # migration-shutdown weeks
    fig, ax = plt.subplots(figsize=(W, 2.55))
    bands = [("2023-04-03", "2024-07-17", "Platforma veche", NAVY_SOFT),
             ("2024-07-29", "2024-11-30", "Lansarea portalului nou", WARN_SOFT),
             ("2025-01-01", "2025-12-31", "Regim stabil 2025", NAVY_SOFT),
             ("2026-08-01", "2026-11-20", "Valul din 2026", ALERT_SOFT)]
    for a, z, lab, c in bands:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(z), color=c, lw=0, zorder=0)
        ax.text(pd.Timestamp(a) + (pd.Timestamp(z) - pd.Timestamp(a)) / 2, 55, lab,
                ha="center", va="top", fontsize=6.4, color=INK2)
    ax.plot(wk.index, wk["med"], color=NAVY, lw=1.5, zorder=3)
    last = wk["med"].dropna()
    ax.annotate(f"{ron(last.iloc[-1],1)} zile", (last.index[-1], last.iloc[-1]), xytext=(-46, -2),
                textcoords="offset points", fontsize=7.2, color=ALERT, fontweight="bold", path_effects=HALO)
    ax.set_ylim(0, 60); ax.set_ylabel("zile de așteptare\n(mediană, săptămânal)", fontsize=6.8)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(G.ro_date_fmt))
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi01_istoric")


# ---------------------------------------------------------------- F2 filing-month collapse, two sources
def f_collapse():
    from analyze_portal_snapshot import load
    b = berc(); f = b[b.sol.isin(FIN) & (b.Wd >= 0) & (b.Wd < 400) & (b.app >= "2026-01-01")]
    bw = f.groupby(f.app.dt.month)["Wd"].median()
    p = load(None); d = p[(p.details_found) & (p.is_judged == 1)].copy()
    d["rq"] = pd.to_datetime(d.request_date.str[:10], errors="coerce")
    d["so"] = pd.to_datetime(d.solution_term.str[:10], errors="coerce")
    r = d[d.phase_code.isin(["12", "13", "14", "15", "27"])].copy(); r["W"] = (r.so - r.rq).dt.days
    pw = r[(r.W >= 0) & (r.W < 400)].groupby(r.rq.dt.month)["W"].median()
    mo = list(range(1, 10))
    fig, ax = plt.subplots(figsize=(W, 2.45))
    ax.plot(mo, [bw.get(m) for m in mo], "-o", color=NAVY, lw=1.6, ms=3.8, label="BERC — buletinul oficial (toate deciziile)")
    ax.plot([m for m in mo if m >= 5], [pw.get(m) for m in mo if m >= 5], "--s", color=WARN, lw=1.3, ms=3.4,
            label="Portalul myportal — eșantion independent")
    for m in mo:
        v = bw.get(m)
        if v is not None and not np.isnan(v):
            ax.annotate(("≥" if m == 9 else "") + ron(v), (m, v), xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=7, color=ALERT if m == 9 else INK, path_effects=HALO)
    ax.axvspan(9.5, 11.5, color=RULE2, lw=0)
    ax.text(10.5, 20, "oct.–nov.:\nîncă nu se\npot măsura", ha="center", fontsize=6.4, color=INK3)
    ax.set_xlim(0.5, 11.5); ax.set_xticks(range(1, 12)); ax.set_xticklabels([MO[m] for m in range(1, 12)])
    ax.set_ylim(0, 46); ax.set_ylabel("zile până la decizie\n(mediană, pe luna depunerii)", fontsize=6.8)
    ax.legend(loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi02_colaps_doua_surse")


# ---------------------------------------------------------------- F3 decided-this-week wait
def f_now():
    dw = L["wait_of_dossiers_decided_by_week"]
    fig, ax = plt.subplots(figsize=(W, 2.3))
    for cat, col, lab in [("CERERE265", ALERT, "modificări ale firmelor existente"),
                          ("INMATRIC265", NAVY_MID, "înmatriculări (firme noi)")]:
        x = [pd.Timestamp(k) for k in dw[cat]]; y = list(dw[cat].values())
        ax.plot(x, y, "-o", color=col, lw=1.6, ms=3.6, label=lab)
        ax.annotate(f"{ron(y[-1],1)} zile", (x[-1], y[-1]), xytext=(6, -2), textcoords="offset points",
                    fontsize=7, color=col, fontweight="bold", path_effects=HALO)
        ax.annotate(f"{ron(y[0],1)}", (x[0], y[0]), xytext=(-4, 7), textcoords="offset points",
                    ha="right", fontsize=6.6, color=col, path_effects=HALO)
    ax.axhline(1, color=SOL, lw=1, ls="--")
    ax.text(pd.Timestamp("2026-09-28"), 3, "termenul din lege: 1 zi lucrătoare", fontsize=6.4, color=SOL)
    ax.set_ylim(0, 66); ax.set_ylabel("zile așteptate de dosarele\nsoluționate în săptămâna respectivă", fontsize=6.6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.set_xlim(pd.Timestamp("2026-09-23"), pd.Timestamp("2026-11-26"))
    ax.legend(loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi03_acum")


# ---------------------------------------------------------------- F4 flow diagram (two queues + loop)
def f_flow():
    s1 = L["backlog_split_stage1"]
    fig, ax = plt.subplots(figsize=(W, 1.85)); ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.axis("off")
    def box(x, w, t, sub, fc, ec):
        ax.add_patch(FancyBboxPatch((x, 9), w, 13, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, 18.2, t, ha="center", va="center", fontsize=7.6, fontweight="bold", color=INK)
        ax.text(x + w / 2, 12.6, sub, ha="center", va="center", fontsize=6.3, color=INK2)
    box(0, 15, "Depunere", "online, ghișeu, poștă", TINT, RULE)
    box(24, 22, "1 · Operare", f"{round(100*s1)}% din dosarele\nîn așteptare", NAVY_SOFT, NAVY)
    box(55, 22, "2 · Registrator", f"{round(100*(1-s1))}% din dosarele\nîn așteptare", WARN_SOFT, WARN)
    box(86, 14, "Decizie", "admis / respins", SOL_SOFT, SOL)
    for a, z in [(15.6, 23.4), (46.6, 54.4), (77.6, 85.4)]:
        ax.add_patch(FancyArrowPatch((a, 15.5), (z, 15.5), arrowstyle="-|>", mutation_scale=9, color=INK2, lw=0.9))
    ax.add_patch(FancyArrowPatch((66, 8.6), (35, 8.6), connectionstyle="arc3,rad=-0.45",
                                 arrowstyle="-|>", mutation_scale=9, color=ALERT, lw=1.0))
    ax.text(50.5, 1.2, "amânare: dosarul se întoarce la operare (≈1 din 5 decizii)", ha="center",
            fontsize=6.5, color=ALERT)
    fig.tight_layout(); G.save_svg_and_png(fig, "fi04_flux")


# ---------------------------------------------------------------- F5 demand vs capacity
def f_demand_capacity():
    b = berc(); fin = b[b.sol.isin(FIN) & (b.d >= "2026-05-04")]
    wk = fin.groupby(fin.d.dt.to_period("W-SUN").apply(lambda p: p.start_time)).size()
    nd = b[b.d >= "2026-05-04"].groupby(b.d.dt.to_period("W-SUN").apply(lambda p: p.start_time))["d"].nunique()
    cap = (wk / nd.reindex(wk.index).clip(lower=1))
    inp = json.load(open(os.path.join(IA, "out", "model_inputs_v2.json"), encoding="utf-8"))
    iw = pd.Series(inp["intake_wk"], index=pd.date_range("2026-05-04", periods=len(inp["intake_wk"]), freq="W-MON"))
    iw.iloc[0] = iw.iloc[1]
    # ESTIMATE: judged share of all filings calibrated so that May-Jul arrivals = May-Jul measured
    # capacity (the queue was stable then: wait 5-7 days). Both per WORKING day (week / 5).
    mj = (iw.index < "2026-08-01")
    cap_mj = cap[(cap.index >= "2026-05-04") & (cap.index < "2026-08-01")].mean()
    y = cap_mj * 5 / iw[mj].mean()
    arr = iw * y / 5
    arr = arr.rolling(2, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(W, 2.4))
    cap = cap[cap.index <= pd.Timestamp("2026-11-16")]
    ax.plot(cap.index, cap.values, color=NAVY, lw=1.7, label="dosare finalizate pe zi lucrătoare (BERC)")
    ax.plot(arr.index, arr.values, color=ALERT, lw=1.5, ls="--", label="dosare judecate care intră pe zi lucrătoare (estimare)")
    ci = cap.reindex(arr.index, method="nearest")
    ax.fill_between(arr.index, ci.values, arr.values, where=(arr.values > ci.values), color=ALERT_SOFT, lw=0)
    ax.set_ylim(0, max(arr.max(), cap.max()) * 1.18)
    ax.set_ylabel("dosare / zi lucrătoare", fontsize=6.8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(G.ro_date_fmt)); ax.legend(loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi05_cerere_capacitate")


# ---------------------------------------------------------------- F6 productivity
def f_productivity():
    v = L["files_per_day_per_registrator_finals"]
    fig, ax = plt.subplots(figsize=(W, 1.35))
    ax.barh([1], [40], color=RULE2, height=0.5); ax.barh([0], [v], color=ALERT, height=0.5)
    ax.text(40.6, 1, "norma internă: 40", va="center", fontsize=7.2, color=INK2)
    ax.text(v + 0.6, 0, f"realitatea măsurată: ≈{ron(v)}", va="center", fontsize=7.4, color=ALERT, fontweight="bold")
    ax.set_yticks([]); ax.set_xlim(0, 52); ax.set_xlabel("dosare finalizate pe zi, de un registrator", fontsize=6.8)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi06_productivitate")


# ---------------------------------------------------------------- F7 decision mix by regime
def f_mix():
    b = berc()
    regs = [("Platforma veche", "2023-04-03", "2024-07-17"), ("Lansare portal 2024", "2024-07-29", "2024-11-30"),
            ("Anul 2025", "2025-01-01", "2025-12-31"), ("2026 până în iulie", "2026-01-01", "2026-07-31"),
            ("Valul aug.–nov. 2026", "2026-08-01", "2026-11-21")]
    rows = []
    for lab, a, z in regs:
        s = b[(b.d >= a) & (b.d <= z)]; n = len(s)
        rows.append((lab, (s.sol == "Admis").sum() / n, (s.sol == "Amânat").sum() / n, (s.sol == "Respins").sum() / n))
    fig, ax = plt.subplots(figsize=(W, 2.05)); y = np.arange(len(rows))[::-1]
    for i, (lab, ad, am, re_) in zip(y, rows):
        ax.barh(i, ad * 100, color=NAVY_SOFT, height=0.6)
        ax.barh(i, am * 100, left=ad * 100, color=WARN, height=0.6)
        ax.barh(i, re_ * 100, left=(ad + am) * 100, color=ALERT, height=0.6)
        ax.text(ad * 100 + am * 50, i, f"{round(am*100)}%", ha="center", va="center", fontsize=6.8,
                color="white", fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=6.8); ax.set_xlim(0, 100)
    ax.set_xlabel("% din toate deciziile  ·  bleu = admise · ocru = amânate · roșu = respinse", fontsize=6.6)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi07_amanari")


# ---------------------------------------------------------------- F8 counties
def f_counties():
    from analyze_portal_snapshot import load
    p = load(None); d = p[(p.details_found) & (p.is_judged == 1)]; lv = d[d.phase_code.isin(["04", "08"])]
    g = pd.DataFrame({"s1": lv[lv.phase_code == "04"].groupby("county_mn").size(),
                      "s2": lv[lv.phase_code == "08"].groupby("county_mn").size()}).fillna(0)
    g = g[g.index != ""]; g["t"] = g.s1 + g.s2; g = g.sort_values("t").tail(18)
    fig, ax = plt.subplots(figsize=(W, 3.3))
    ax.barh(g.index, g.s1, color=NAVY, height=0.62, label="așteaptă la operare (etapa 1)")
    ax.barh(g.index, g.s2, left=g.s1, color=WARN, height=0.62, label="așteaptă la registrator (etapa 2)")
    ax.set_xlabel("dosare în așteptare în eșantionul nostru", fontsize=6.8); ax.legend(loc="lower right")
    ax.tick_params(axis="y", labelsize=6.8)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi08_judete")


# ---------------------------------------------------------------- F9 OUG scenarios
def f_oug():
    sc = OUG["scenarios"]
    fig, ax = plt.subplots(figsize=(W, 2.55)); y = np.arange(len(sc))[::-1]
    for i, s in zip(y, sc):
        lo, hi = s["backlog_lo"] / 1000, s["backlog_hi"] / 1000; mid = (lo + hi) / 2
        col = SOL if mid < 300 else (WARN if mid < 650 else ALERT)
        ax.plot([lo, hi], [i, i], color=col, lw=7, solid_capstyle="butt", alpha=.9)
        ax.text(hi + 18, i, f"{ron(lo)}–{ron(hi)} mii", va="center", fontsize=6.8, color=INK)
    ax.axvline(L["backlog_total_report"] / 1000, color=INK3, lw=0.8, ls=":")
    ax.text(L["backlog_total_report"] / 1000 + 6, len(sc) - 0.35, "stocul de azi ≈210 mii", fontsize=6.3, color=INK3)
    ax.set_yticks(y); ax.set_yticklabels([s["label"] for s in sc], fontsize=6.9)
    ax.set_xlim(0, 1400); ax.set_xlabel("dosare rămase nesoluționate la 1 aprilie 2027 (mii) — interval", fontsize=6.8)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi09_oug")


# ---------------------------------------------------------------- F10 cannibalisation
def f_cannibal():
    sw = OUG["cannibalisation_sweep"]; x = [s["from_operare"] for s in sw]; y = [s["backlog_mid"] / 1000 for s in sw]
    fig, ax = plt.subplots(figsize=(W, 2.1))
    ax.plot(x, y, "-o", color=ALERT, lw=1.6, ms=3.6)
    ax.annotate(f"{ron(y[0])} mii", (x[0], y[0]), xytext=(4, -12), textcoords="offset points", fontsize=6.8, color=INK2)
    ax.annotate(f"{ron(y[-1])} mii", (x[-1], y[-1]), xytext=(-40, 5), textcoords="offset points", fontsize=7, color=ALERT, fontweight="bold")
    ax.set_xlabel("câți dintre registratorii delegați sunt luați din operare", fontsize=6.8)
    ax.set_ylabel("stoc la 1 apr. 2027 (mii)", fontsize=6.8)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi10_canibalizare")


# ---------------------------------------------------------------- F11 censoring explainer
def f_censoring():
    b = berc(); f = b[b.sol.isin(FIN) & (b.Wd >= 0) & (b.app >= "2026-01-01")]
    n = f.groupby(f.app.dt.month).size() / 1000; mo = list(range(1, 12))
    fig, ax = plt.subplots(figsize=(W, 1.9))
    ax.bar(mo, [n.get(m, 0) for m in mo], color=[NAVY if m <= 9 else RULE for m in mo], width=0.62)
    ax.set_xticks(mo); ax.set_xticklabels([MO[m] for m in mo])
    ax.set_ylabel("dosare deja soluționate\n(mii, pe luna depunerii)", fontsize=6.6)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi11_cenzurare")


# ================= v2: audited replacements (gate M2) =================
T = json.load(open(os.path.join(IA, "out", "tandem_bottleneck.json"), encoding="utf-8"))
OGA = json.load(open(os.path.join(IA, "out", "oug_rerun_compare.json"), encoding="utf-8"))["june2028"]

def f_flow():   # official MJ split; adjournment = completion term on the registrar step (art. 106)
    nov = T["mj_tandem_conservation"]["nov06"]; s1 = nov["s1"] / nov["total"]
    fig, ax = plt.subplots(figsize=(W, 1.95)); ax.set_xlim(0, 100); ax.set_ylim(0, 32); ax.axis("off")
    def box(x, w, t, sub, fc, ec):
        ax.add_patch(FancyBboxPatch((x, 7), w, 13, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, 16.2, t, ha="center", va="center", fontsize=7.6, fontweight="bold", color=INK)
        ax.text(x + w / 2, 10.6, sub, ha="center", va="center", fontsize=6.3, color=INK2)
    box(0, 15, "Depunere", "online, ghișeu, poștă", TINT, RULE)
    box(24, 22, "1 · Operare", f"{ron(nov['s1'])} cereri\n({round(100*s1)}%) neprelucrate", NAVY_SOFT, NAVY)
    box(55, 22, "2 · Registrator", f"{ron(nov['s2'])} cereri\n({round(100*(1-s1))}%) prelucrate", WARN_SOFT, WARN)
    box(86, 14, "Decizie", "admis / respins", SOL_SOFT, SOL)
    for a, z in [(15.6, 23.4), (46.6, 54.4), (77.6, 85.4)]:
        ax.add_patch(FancyArrowPatch((a, 13.5), (z, 13.5), arrowstyle="-|>", mutation_scale=9, color=INK2, lw=0.9))
    ax.add_patch(FancyArrowPatch((72, 20.6), (60, 20.6), connectionstyle="arc3,rad=1.1",
                                 arrowstyle="-|>", mutation_scale=8, color=ALERT, lw=1.0))
    ax.text(66, 29.6, "amânare: termen de completare de cel mult 15 zile (≈1 din 5 decizii)",
            ha="center", fontsize=6.4, color=ALERT)
    ax.text(50, 1.5, "Stocuri oficiale, Nota MJ, 6 noiembrie 2026", ha="center", fontsize=6.0, color=INK3)
    fig.tight_layout(); G.save_svg_and_png(fig, "fi04_flux")

def f_tandem():
    mj = T["mj_tandem_conservation"]
    fig, ax = plt.subplots(figsize=(W, 2.15)); x = np.arange(2); wd = 0.36
    s1 = [mj["oct30"]["s1"] / 1000, mj["nov06"]["s1"] / 1000]; s2 = [mj["oct30"]["s2"] / 1000, mj["nov06"]["s2"] / 1000]
    b1 = ax.bar(x - wd / 2, s1, wd, color=NAVY, label="1 · operare (neprelucrate)")
    b2 = ax.bar(x + wd / 2, s2, wd, color=WARN, label="2 · registrator (prelucrate, nesoluționate)")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 2, ron(r.get_height() * 1000),
                    ha="center", fontsize=6.8, color=INK, path_effects=HALO)
    ax.annotate(ron(mj['delta']['s1']), (0.74, s1[1] + 14), fontsize=7.2, color=NAVY, fontweight="bold")
    ax.annotate("+" + ron(mj['delta']['s2']), (1.12, s2[1] + 14), fontsize=7.2, color=ALERT, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(["30 octombrie 2026", "6 noiembrie 2026"]); ax.set_ylim(0, 140)
    ax.set_ylabel("cereri (mii)", fontsize=6.8); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=6.4, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi06_tandem")

def f_production():
    ser = {s["window"]: s["finals_per_wd"] for s in T["season_matched_c1_series"]}
    _e = {r["an"]: r for r in json.load(open(os.path.join(IA, "out", "stat_pack_ext.json"), encoding="utf-8"))["efort_aceeasi_perioada"]["rows"]}
    yrs = [2023, 2024, 2025, 2026]; v = [_e[y]["finale_pe_zi_lucr"] for y in yrs]       # 1 Oct – 19 Nov (20.11.2026 partial, excluded)
    pk = ser["Feb-Mar 2025 (peak, 1 Feb - 31 Mar)"]
    fig, ax = plt.subplots(figsize=(W, 2.05))
    bars = ax.bar([str(y) for y in yrs], v, color=[NAVY_SOFT, NAVY_SOFT, NAVY_SOFT, NAVY], width=0.55)
    for r, val in zip(bars, v):
        ax.text(r.get_x() + r.get_width() / 2, val + 80, ron(val), ha="center", fontsize=7.2, color=INK, path_effects=HALO)
    ax.axhline(pk, color=INK3, ls=":", lw=0.9)
    ax.text(-0.35, pk + 90, f"vârful absolut: feb.–mar. 2025, ≈{ron(pk)}/zi", fontsize=6.4, color=INK3)
    ax.set_ylim(0, pk * 1.18); ax.set_ylabel("decizii finale / zi lucrătoare\n(1 oct.–19 nov.)", fontsize=6.6)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi05_productie")

def f_counties():   # ranking by office (office of FILING), longest wait at the top
    d = pd.read_csv(os.path.join(IA, "out", "atlas_rerun", "audit_data", "county_indicators.csv"), encoding="utf-8-sig").sort_values("median_nov")
    fig, ax = plt.subplots(figsize=(W, 5.0))
    med = d.median_nov.median()
    cols = [ALERT if v >= d.median_nov.quantile(.9) else (SOL if v <= d.median_nov.quantile(.1) else NAVY_SOFT) for v in d.median_nov]
    ax.barh(d.name, d.median_nov, color=cols, height=0.72)
    ax.axvline(med, color=NAVY, lw=0.9); ax.text(med + 0.15, -1.2, f"mediana oficiilor: {ron(med, 1)} zile", fontsize=6.2, color=NAVY)
    for i_, (_, r) in enumerate(d.iterrows()):
        ax.text(r.median_nov + 0.15, i_, ron(r.median_nov, 1), va="center", fontsize=5.2, color=INK2)
    ax.set_xlim(44, 58); ax.tick_params(axis="y", labelsize=5.5); ax.set_ylim(-1.8, len(d) - .3)
    ax.set_xlabel("zile de așteptare ale deciziilor din 1–18 noiembrie (mediană pe oficiul de depunere) · roșu = cele mai lungi 10%, verde = cele mai scurte 10%", fontsize=6.1)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi08_judete")


def _old_counties():
    d = None
    fig, ax = plt.subplots(figsize=(W, 4.3))
    ax.barh(d.code, d.median_nov, color=NAVY_SOFT, height=0.7)
    med = d.median_nov.median(); ax.axvline(med, color=NAVY, lw=0.9)
    ax.text(med + 0.3, 0.2, f"mediana județelor: {ron(med, 1)} zile", fontsize=6.4, color=NAVY)
    for _, r in d.iloc[[0, -1]].iterrows():
        ax.text(r.median_nov + 0.4, r.code, ron(r.median_nov, 1), va="center", fontsize=6.4, color=INK)
    ax.set_xlim(40, 60); ax.tick_params(axis="y", labelsize=5.6)
    ax.set_xlabel("zile de așteptare ale deciziilor din 1–18 noiembrie (mediană, pe oficiul de depunere)", fontsize=6.6)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi08_judete")

def f_oug():
    rows = [("Fără măsuri noi", OGA["referinta"], ALERT), ("Doar Art. III (acte administrative)", OGA["doar_art_iii"], WARN),
            ("Proiectul OUG complet", OGA["oug_central"], NAVY)]
    fig, ax = plt.subplots(figsize=(W, 1.75)); y = np.arange(len(rows))[::-1]
    for i, (lab, r, col) in zip(y, rows):
        lo, hi = r["current_p10_p90"]; m = r["current_median"]
        ax.plot([lo, hi], [i, i], color=col, lw=6, alpha=.35, solid_capstyle="butt")
        ax.plot([m], [i], "o", color=col, ms=6)
        ax.text(m, i + 0.3, f"≈{ron(m)} zile", ha="center", fontsize=6.9, color=col, fontweight="bold")
        ax.text(hi + 3, i, f"interval {ron(lo)}–{ron(hi)}", va="center", fontsize=6.3, color=INK2)
    ax.axvline(3, color=SOL, ls="--", lw=0.9); ax.text(5, -0.62, "reper: 3 zile calendaristice ≈ 1 zi lucrătoare peste weekend", fontsize=6.2, color=SOL)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=6.9); ax.set_xlim(0, 260); ax.set_ylim(-0.8, 2.75)
    ax.set_xlabel("așteptare estimată în iunie 2028 (zile) — punct = mediană, bară = interval p10–p90", fontsize=6.6)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "fi09_oug")

def f_cannibal():
    sw = pd.read_csv(os.path.join(IA, "out", "tandem_cannibalization_sweep.csv"))
    fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.plot(sw.delta_wd, sw.c1_wd, color=NAVY, lw=1.1, ls="--", label="capacitatea de operare, după mutare")
    ax.plot(sw.delta_wd, sw.c2_wd, color=WARN, lw=1.1, ls="--", label="capacitatea de soluționare, după mutare")
    ax.plot(sw.delta_wd, sw.min_cap_wd, color=ALERT, lw=2.0, label="ce poate procesa sistemul (minimul celor două)")
    cv = T["mj_tandem_conservation"]["conventions"]["strict_finals"]
    lo = sw.min_cap_wd.min() * 0.97
    ax.axvline(cv["optimal_shift_delta_wd"], color=SOL, lw=0.8, ls=":"); ax.axvline(cv["o1_minus_o2_wd"], color=ALERT, lw=0.8, ls=":")
    ax.text(cv["optimal_shift_delta_wd"] + 15, lo + 40, "optim", fontsize=6.3, color=SOL)
    ax.text(cv["o1_minus_o2_wd"] + 15, lo + 40, "câștig zero", fontsize=6.3, color=ALERT)
    ax.set_ylim(lo, max(sw.c1_wd.max(), sw.c2_wd.max()) * 1.03)
    ax.set_xlabel("dosare/zi de capacitate mutate din operare la soluționare", fontsize=6.6)
    ax.set_ylabel("dosare / zi lucrătoare", fontsize=6.6); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3, fontsize=6.2)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "fi10_canibalizare")


if __name__ == "__main__":
    for fn in (f_history, f_collapse, f_now, f_flow, f_production, f_tandem, f_mix,
               f_counties, f_oug, f_cannibal, f_censoring):
        if fn is f_collapse and not any(config.PORTAL_DIR.glob("harvest_*.jsonl")):
            print("skip f_collapse: needs the unpublished myportal sample; committed fi02_colaps_doua_surse.svg kept"); continue
        fn(); print("ok", fn.__name__)
