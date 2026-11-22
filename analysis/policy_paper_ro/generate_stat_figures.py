"""Figurile Raportului statistic avansat (volumul 3). Citesc out/stat_pack.json (sursa unică a volumelor 2–3)
și, doar pentru ECDF, arhiva BERC. Aceeași paletă ca raportul principal. Fără nume de județe (nu e clasament)."""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import generate_institutii_figures as GI
G = GI.G
OUTD = os.path.join(GI.HERE, "figures_statistic"); os.makedirs(OUTD, exist_ok=True); G.OUT_DIR = OUTD
SP = json.load(open(os.path.join(GI.IA, "out", "stat_pack.json"), encoding="utf-8"))
T = lambda k: pd.DataFrame(SP[k]["rows"])
NAVY, NAVY_MID, NAVY_SOFT, ALERT, ALERT_SOFT, WARN, WARN_SOFT, SOL, SOL_SOFT = (G.NAVY, G.NAVY_MID, G.NAVY_SOFT, G.ALERT,
    G.ALERT_SOFT, G.WARN, G.WARN_SOFT, G.SOL, G.SOL_SOFT)
INK, INK2, INK3 = G.INK, G.INK2, G.INK3; W = G.W_IN; ron = G.ro_num; MO = GI.MO


def s01_ecdf():
    b = GI.berc(); s = b[b.sol.isin(GI.FIN) & (b.Wd >= 0) & (b.Wd < 400)]
    per = [("Platforma veche", "2023-04-03", "2024-07-17", NAVY_MID), ("Lansarea portalului 2024", "2024-07-29", "2024-11-30", WARN),
           ("Stabil 2025", "2025-01-01", "2025-12-31", SOL), ("Aug.–sep. 2026", "2026-08-01", "2026-09-30", "#D9776E"),
           ("Oct.–nov. 2026", "2026-10-01", "2026-11-20", ALERT)]
    fig, ax = plt.subplots(figsize=(W, 2.5))
    for lab, lo, hi, col in per:
        x = np.sort(s[(s.d >= lo) & (s.d <= hi)].Wd.to_numpy()); y = np.arange(1, len(x) + 1) / len(x)
        idx = np.linspace(0, len(x) - 1, 600).astype(int)
        ax.plot(np.maximum(x[idx], .1), y[idx], color=col, lw=1.6 if "Oct" in lab else 1.2, label=lab)
    ax.set_xscale("log"); ax.set_xticks([.5, 1, 2, 5, 10, 20, 50, 100]); ax.set_xticklabels(["0,5", "1", "2", "5", "10", "20", "50", "100"])
    ax.axhline(.5, color=INK3, lw=.6, ls=":"); ax.text(.12, .52, "mediana", fontsize=6.2, color=INK3)
    ax.set_xlim(.1, 200); ax.set_ylim(0, 1.01); ax.set_xlabel("zile de așteptare (scară logaritmică)", fontsize=6.6)
    ax.set_ylabel("proporția dosarelor decise\ncu așteptare cel mult x", fontsize=6.6)
    ax.legend(loc="upper left", fontsize=6.1, frameon=False); G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s01_ecdf")


def s02_monthly():
    d = T("serie_lunara"); d["dt"] = pd.to_datetime(d.luna)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, 3.6), sharex=True)
    a1.plot(d.dt, d.finale_largi_pe_zi_cu_decizii, color=NAVY_MID, lw=1.2, label="finale largi / zi cu decizii (definiția C01)")
    a1.plot(d.dt, d.finale_stricte_pe_zi_lucr, color=NAVY, lw=1.6, label="finale stricte / zi lucrătoare legală")
    a1.plot(d.dt, d.amanari_pe_zi_lucr, color=WARN, lw=1.2, label="amânări / zi lucrătoare legală")
    a1.set_ylabel("decizii pe zi", fontsize=6.6); a1.legend(fontsize=6, frameon=False, loc="upper left", ncol=2); a1.set_ylim(0, 6500)
    a2.fill_between(d.dt, d.W_p25, d.W_p75, color=ALERT_SOFT, lw=0, label="p25–p75")
    a2.plot(d.dt, d.W_med, color=ALERT, lw=1.6, label="mediana"); a2.plot(d.dt, d.W_p90, color=ALERT, lw=.8, ls="--", label="p90")
    a2.set_ylabel("zile de așteptare\n(finale stricte)", fontsize=6.6); a2.legend(fontsize=6, frameon=False, loc="upper left", ncol=3)
    for a in (a1, a2): G.style_axes(a)
    fig.tight_layout(); G.save_svg_and_png(fig, "s02_lunar")


def s03_km():
    cur = SP["km_curves"]; cols = {"2026-06": SOL, "2026-07": NAVY_MID, "2026-08": WARN, "2026-09": ALERT, "2026-10": INK2, "2026-11": INK3}
    fig, ax = plt.subplots(figsize=(W, 2.4))
    for m, col in cols.items():
        if m not in cur: continue
        c = np.array(cur[m]); t = np.r_[0, c[:, 0]]; s = np.r_[1, c[:, 1]]
        ax.step(t, s, where="post", color=col, lw=1.4, label=f"depuse în {MO[int(m[5:])]} 2026")
    ax.axhline(.5, color=INK3, lw=.6, ls=":"); ax.set_xlim(0, 90); ax.set_ylim(0, 1.02)
    ax.set_xlabel("zile de la depunere", fontsize=6.6); ax.set_ylabel("proporția încă nerezolvată\n(Kaplan–Meier)", fontsize=6.6)
    # legend in the empty lower-right corner (no curve goes past ~67 days), so it never overlaps the curves
    ax.legend(fontsize=6.1, frameon=False, loc="lower right", borderaxespad=0.6); G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s03_km")


def s04_censor():
    k = T("cohorte_KM_portal"); c = T("cohorte_depunere_BERC").set_index("luna_dep")
    x = np.arange(len(k)); fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.bar(x - .27, [c.W_med.get(m, np.nan) for m in k.luna_dep], .26, color=NAVY_SOFT, label="BERC, doar dosare decise")
    ax.bar(x, k.mediana_naiva_doar_rezolvate, .26, color=NAVY_MID, label="portal, doar dosare rezolvate")
    ax.bar(x + .27, k.mediana_KM.fillna(0), .26, color=ALERT, label="portal, Kaplan–Meier (corectat)")
    for i, r in k.iterrows():
        if pd.isna(r.mediana_KM):
            top = np.nanmax([c.W_med.get(r.luna_dep, np.nan), r.mediana_naiva_doar_rezolvate])   # label above the bars, not over them
            ax.text(i, top + 3, "KM: sub 50%\nrezolvate", ha="center", va="bottom", fontsize=5.4, color=ALERT, linespacing=1.15)
        ax.text(i, -9, f"{ron(r.rezolvate_pct)}% rez.", ha="center", fontsize=5.8, color=INK3)
    ax.set_xticks(x); ax.set_xticklabels([f"{MO[int(m[5:])]}" for m in k.luna_dep], fontsize=6.4); ax.set_ylim(-12, 70)
    ax.set_ylabel("mediana așteptării (zile)", fontsize=6.6); ax.legend(fontsize=6, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s04_cenzurare")


def s05_counties():
    d = T("judete_alfabetic"); rng = np.random.default_rng(1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 2.3), gridspec_kw=dict(width_ratios=[1, 1.2]))
    a1.scatter(d.median_nov, rng.uniform(-.25, .25, len(d)), s=12, color=NAVY_MID, alpha=.8)
    a1.boxplot(d.median_nov, vert=False, widths=.5, showfliers=False, medianprops=dict(color=ALERT))
    a1.set_yticks([]); a1.set_xlabel("mediana pe oficiu, decizii 1–18 nov. (zile)", fontsize=6.3)
    a2.scatter(d.median_y25, d.median_nov, s=12, color=NAVY_MID, alpha=.8)
    a2.set_xlabel("mediana pe oficiu, 2025 (zile)", fontsize=6.3); a2.set_ylabel("mediana, nov. 2026", fontsize=6.3)
    rho = SP["county_dispersion"]["spearman_2025_vs_nov"]
    a2.text(.03, .92, f"ρ Spearman = {ron(rho, 2)}".replace("-", "−"), transform=a2.transAxes, fontsize=6.4, color=ALERT)
    for a in (a1, a2): G.style_axes(a)
    fig.tight_layout(); G.save_svg_and_png(fig, "s05_judete")


def s06_profiles():
    z = T("profil_zile_saptamana_2026"); h = T("profil_ore_depunere_2026")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 2.1), gridspec_kw=dict(width_ratios=[1, 1.6]))
    x = np.arange(7); a1.bar(x - .2, z.depuneri_pct, .4, color=NAVY, label="depuneri"); a1.bar(x + .2, z.decizii_pct, .4, color=WARN, label="decizii")
    a1.set_xticks(x); a1.set_xticklabels(["L", "Ma", "Mi", "J", "V", "S", "D"], fontsize=6.3); a1.set_ylabel("% din săptămână", fontsize=6.4)
    a1.legend(fontsize=6, frameon=False)
    cols = [NAVY if 8 <= o < 16 else NAVY_SOFT for o in h.ora]
    a2.bar(h.ora, h.depuneri_pct, color=cols); a2.set_xlabel("ora înregistrării (închis = program de lucru 8–16)", fontsize=6.2)
    a2.set_ylabel("% din depuneri", fontsize=6.4)
    for a in (a1, a2): G.style_axes(a)
    fig.tight_layout(); G.save_svg_and_png(fig, "s06_profiluri")


def s07_adjourn():
    d = T("cicluri_amanare_nov2026")
    fig, ax = plt.subplots(figsize=(W * .6, 1.9))
    ax.bar(d.amanari_anterioare, d.decizii_finale_pct, color=[NAVY_SOFT, WARN, ALERT, ALERT, ALERT], width=.6)
    for i, v in enumerate(d.decizii_finale_pct):
        ax.text(i, v + 1.5, ron(v, 1) + "%", ha="center", fontsize=6.3)
    ax.set_ylim(0, 95); ax.set_xlabel("amânări anterioare ale aceluiași dosar", fontsize=6.4); ax.set_ylabel("% din deciziile finale", fontsize=6.4)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s07_amanari")


def s08_definitions():
    L = json.load(open(os.path.join(GI.IA, "out", "LOCKED_CONSTANTS.json"), encoding="utf-8"))
    TB = json.load(open(os.path.join(GI.IA, "out", "tandem_bottleneck.json"), encoding="utf-8"))["april_2026_synchronization"]
    le = L["le2d_share_27apr_by_decision_date"]
    panels = [("August față de iun.–iul.\n(raport)", [("pe zi cu decizii,\nfinale largi", L["august_capacity_ratio"]), ("pe zi lucrătoare\nlegală, stricte", L["august_ratio_strict_finals_per_legal_wd"])], "{:.3f}"),
              ("Ponderea ≤2 zile înainte\nde 27 aprilie (%)", [("mediana pe\njudețe", TB["pre_le2d_county_median_pct"]), ("toate deciziile,\nnațional", le["pre_1mar_26apr_pct"])], "{:.1f}"),
              ("Ponderea ≤2 zile după\n27 aprilie (%)", [("mediana pe\njudețe", TB["post_le2d_county_median_pct"]), ("toate deciziile,\nnațional", le["post_27apr_31jul_pct"])], "{:.2f}")]
    fig, axs = plt.subplots(1, 3, figsize=(W, 2.1))
    for a, (title, vals, fmt) in zip(axs, panels):
        a.bar([0, 1], [v for _, v in vals], color=[NAVY_SOFT, NAVY], width=.55)
        for i, (_, v) in enumerate(vals):
            a.text(i, v * 1.02, fmt.format(v).replace(".", ","), ha="center", fontsize=6.4)
        a.set_xticks([0, 1]); a.set_xticklabels([l for l, _ in vals], fontsize=5.8); a.set_title(title, fontsize=6.6, loc="left")
        a.set_ylim(0, max(v for _, v in vals) * 1.25); G.style_axes(a)
    fig.tight_layout(); G.save_svg_and_png(fig, "s08_definitii")


def s09_weekly():
    d = T("serie_saptamanala_2026"); d["dt"] = pd.to_datetime(d.saptamana)
    fig, ax = plt.subplots(figsize=(W, 2.1))
    ax.fill_between(d.dt, d.med_CERERE, d.p90_CERERE, color=ALERT_SOFT, lw=0, label="mediană–p90, modificări")
    ax.plot(d.dt, d.med_CERERE, color=ALERT, lw=1.5, label="mediana, modificări (CERERE265)")
    ax.plot(d.dt, d.med_INMATRIC, color=NAVY, lw=1.2, label="mediana, înmatriculări (INMATRIC265)")
    ax.set_ylabel("zile de așteptare", fontsize=6.6); ax.legend(fontsize=6, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s09_saptamanal")


def s10_lag():
    d = T("intarziere_publicare")
    fig, ax = plt.subplots(figsize=(W * .6, 1.9)); x = np.arange(len(d))
    for k, col, off in (("p50", NAVY, -.25), ("p90", WARN, 0), ("p99", ALERT, .25)):
        ax.bar(x + off, d[k], .24, color=col, label=k)
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(d.an.astype(str), fontsize=6.4)
    ax.set_ylabel("zile până la publicare\n(scară logaritmică)", fontsize=6.3); ax.legend(fontsize=6, frameon=False)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "s10_publicare")


if __name__ == "__main__":
    for fn in (s02_monthly, s03_km, s04_censor, s05_counties, s06_profiles, s07_adjourn, s08_definitions, s09_weekly, s10_lag, s01_ecdf):
        fn(); print("ok", fn.__name__)


# ---------------------------------------------------------------- volumes 4 (effort) and 5 (counties)
SPX = json.load(open(os.path.join(GI.IA, "out", "stat_pack_ext.json"), encoding="utf-8"))
TX = lambda k: pd.DataFrame(SPX[k]["rows"])


def e01_same_period():
    d = TX("efort_aceeasi_perioada"); x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(W, 2.2))
    ax.bar(x, d.finale_pe_zi_lucr, .55, color=NAVY, label="decizii finale")
    ax.bar(x, d.amanari_pe_zi_lucr, .55, bottom=d.finale_pe_zi_lucr, color=WARN, label="amânări (muncă care nu închide dosarul)")
    for i, r in d.iterrows():
        ax.text(i, r.decizii_pe_zi_lucr + 90, ron(r.decizii_pe_zi_lucr) + (f"  (+{ron(r.fata_de_2023_pct)}%)" if i else ""), ha="center", fontsize=6.6, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(d.an.astype(str)); ax.set_ylim(0, 6300)
    ax.set_ylabel("decizii / zi lucrătoare\n(1 oct.–19 nov.)", fontsize=6.6); ax.legend(fontsize=6.2, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "e01_aceeasi_perioada")


def e02_hour():
    d = TX("efort_ora_deciziei_2026")
    fig, ax = plt.subplots(figsize=(W, 1.9))
    ax.bar(d.ora, d.decizii_pct, color=[NAVY if 8 <= o < 16 else WARN for o in d.ora])
    ax.set_xlabel("ora mărcii temporale a deciziei, zile lucrătoare 2026 (portocaliu = în afara intervalului 8–16)", fontsize=6.3)
    ax.set_ylabel("% din decizii", fontsize=6.5); G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "e02_ora")


def e03_monthly_volume():
    d = T("serie_lunara"); d["dt"] = pd.to_datetime(d.luna)
    fig, ax = plt.subplots(figsize=(W, 2.0))
    ax.plot(d.dt, d.finale_stricte_pe_zi_lucr + d.amanari_pe_zi_lucr, color=NAVY, lw=1.6, label="toate deciziile / zi lucrătoare legală")
    ax.plot(d.dt, d.finale_stricte_pe_zi_lucr, color=NAVY_MID, lw=1, ls="--", label="doar finale stricte")
    ax.set_ylim(0, 6800); ax.set_ylabel("decizii / zi", fontsize=6.6); ax.legend(fontsize=6.2, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "e03_lunar")


def c01_sparklines():
    cm = TX("judete_lunar"); nat = TX("national_lunar").set_index("luna").mediana
    names = T("judete_alfabetic").set_index("code").name
    codes = sorted(cm.cod.unique(), key=lambda c: names.get(c, c))
    fig, axs = plt.subplots(7, 6, figsize=(W, 7.6), sharex=True, sharey=True)
    months = sorted(cm.luna.unique()); xi = {m: i for i, m in enumerate(months)}
    for ax, code in zip(axs.flat, codes):
        g = cm[cm.cod == code]
        ax.plot([xi[m] for m in months], [nat.get(m, np.nan) for m in months], color=INK3, lw=.8)
        ax.plot([xi[m] for m in g.luna], g.mediana, color=ALERT, lw=1.2)
        ax.set_title(f"{names.get(code, code)}", fontsize=6.2, loc="left", pad=1.5)
        ax.tick_params(labelsize=5); ax.set_ylim(0, 70)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    for ax in axs.flat[len(codes):]: ax.axis("off")
    ticks = [i for i, m in enumerate(months) if m.endswith("-01") or m.endswith("-07")]
    for ax in axs[-1]: ax.set_xticks(ticks); ax.set_xticklabels([f"{MO[int(months[i][5:])]}\n{months[i][2:4]}" for i in ticks], fontsize=4.8)
    fig.text(.01, .5, "mediana așteptării (zile), pe luna deciziei · roșu = oficiul, gri = național", rotation=90, va="center", fontsize=6.3, color=INK2)
    fig.tight_layout(rect=(.02, 0, 1, 1), h_pad=.4, w_pad=.3); G.save_svg_and_png(fig, "c01_judete_lunar")


if __name__ == "__main__":
    for fn in (e01_same_period, e02_hour, e03_monthly_volume, c01_sparklines):
        fn(); print("ok", fn.__name__)


RK = json.load(open(os.path.join(GI.IA, "out", "county_rankings.json"), encoding="utf-8"))


def c02_local_problems():
    d = pd.DataFrame(RK["rang_probleme_locale_2025_2026"]["rows"]).sort_values("exces_mediu_zile")
    fig, ax = plt.subplots(figsize=(W, 5.0))
    cols = [ALERT if v >= 1.5 else (WARN if v >= .5 else NAVY_SOFT) for v in d.exces_mediu_zile]
    ax.barh(d.name, d.exces_mediu_zile, color=cols, height=.72)
    for i, (_, r) in enumerate(d.iterrows()):
        if r.exces_mediu_zile >= 1:
            ax.text(r.exces_mediu_zile + .05, i, f"vârf {MO[int(r.luna_excesului_maxim[5:])]} {r.luna_excesului_maxim[:4]}", va="center", fontsize=5.4, color=INK2)
    ax.axvline(0, color=INK3, lw=.6); ax.tick_params(axis="y", labelsize=5.5)
    ax.set_xlabel("zile peste mediana națională, în medie pe lună, ianuarie 2025 – iulie 2026 (roșu = episoade locale marcate)", fontsize=6.2)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "c02_probleme_locale")
