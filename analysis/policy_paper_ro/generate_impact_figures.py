"""Figurile raportului „Impactul economic și bugetar al cozii”. Citesc out/cost_monthly.json, out/cost_check.json și
audit_data/cost_sensitivity.csv. Aceeași paletă ca raportul principal."""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import generate_institutii_figures as GI
G = GI.G
OUTD = os.path.join(GI.HERE, "figures_impact"); os.makedirs(OUTD, exist_ok=True); G.OUT_DIR = OUTD
KM = json.load(open(os.path.join(GI.IA, "out", "cost_monthly.json"), encoding="utf-8"))
KC = json.load(open(os.path.join(GI.IA, "out", "cost_check.json"), encoding="utf-8"))
KF = json.load(open(os.path.join(GI.IA, "out", "cost_founded.json"), encoding="utf-8"))
NAVY, NAVY_MID, NAVY_SOFT, ALERT, ALERT_SOFT, WARN, WARN_SOFT, SOL, SOL_SOFT = (G.NAVY, G.NAVY_MID, G.NAVY_SOFT, G.ALERT,
    G.ALERT_SOFT, G.WARN, G.WARN_SOFT, G.SOL, G.SOL_SOFT)
INK, INK2, INK3 = G.INK, G.INK2, G.INK3; W = G.W_IN; MO = GI.MO
rd = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def i01_monthly():
    d = pd.DataFrame(KM["cost_lunar"]["rows"]); d["xd"] = pd.to_datetime(d.luna + "-15")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, 3.9), sharex=True, gridspec_kw=dict(height_ratios=[1.45, 1]))
    for ax, k, col, soft, lab in ((a1, "economic", NAVY, NAVY_SOFT, "cost economic și privat"), (a2, "buget", WARN, WARN_SOFT, "încasări bugetare afectate")):
        partial = d.luna == d.luna.max()
        ax.bar(d.xd[~partial], d[f"{k}_central_mil"][~partial], width=24, color=col, label=f"{lab}, scenariul central")
        ax.bar(d.xd[partial], d[f"{k}_central_mil"][partial], width=24, color="white", edgecolor=col, hatch="////", lw=.8, label="noiembrie 2026, parțial (până la 20.11)")
        ax.vlines(d.xd, d[f"{k}_prudent_mil"], d[f"{k}_tensionat_mil"], color=INK3, lw=.7, label="interval prudent – tensionat")
        ax.set_ylabel("milioane lei / lună", fontsize=6.4); G.style_axes(ax)
        ax.legend(fontsize=5.8, frameon=False, loc="upper left")
    pk = d.loc[d.luna == "2024-10"].iloc[0]
    a1.annotate("lansarea portalului\n(toamna 2024)", (pk.xd, pk.economic_central_mil), xytext=(0, 26), textcoords="offset points", ha="center", fontsize=5.8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=INK3, lw=.6))
    for m in ("2026-10", "2026-11"):
        r = d.loc[d.luna == m].iloc[0]
        off = -9 if m == "2026-10" else 9
        a1.annotate(rd(r.economic_central_mil), (r.xd, r.economic_central_mil), xytext=(off, 3), textcoords="offset points", ha="center", fontsize=5.8, color=INK)
        a2.annotate(rd(r.buget_central_mil), (r.xd, r.buget_central_mil), xytext=(off, 3), textcoords="offset points", ha="center", fontsize=5.8, color=INK)
    a1.set_ylim(0, d.economic_tensionat_mil.max() * 1.06); a2.set_ylim(0, d.buget_tensionat_mil.max() * 1.06)
    a2.set_xlabel("luna deciziei; cost realizat al dosarelor decise în lună, fără expunerea stocului încă nedecis", fontsize=6.2)
    fig.tight_layout(); G.save_svg_and_png(fig, "i01_cost_lunar")


def i02_channels():
    d = pd.DataFrame(KM["cost_lunar_canale"]["rows"]); d = d[d.luna >= "2025-01"]; d["xd"] = pd.to_datetime(d.luna + "-15")
    fig, ax = plt.subplots(figsize=(W, 2.3))
    bottom = np.zeros(len(d))
    for k, col, lab in (("canal_C_mil", NAVY, "C · alte modificări blocate (ipoteză: cost pe zi)"), ("canal_A_mil", SOL, "A · activitate nouă pierdută (firme noi)"),
                        ("canal_D_mil", WARN, "D · amânări evitabile"), ("canal_B_mil", ALERT, "B · inactivare după expirarea sediului")):
        ax.bar(d.xd, d[k], bottom=bottom, width=24, color=col, label=lab); bottom += d[k].to_numpy()
    ax.set_ylabel("milioane lei / lună\n(scenariul central)", fontsize=6.4); ax.legend(fontsize=5.8, frameon=False, loc="upper left")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "i02_canale_lunar")


def i03_account():
    sc = KF["scenarios"]["fundamentat"]; real = KM["window_realized_mil"]
    names = [("prudent", "prudent"), ("central", "central"), ("tensionat", "tensionat")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 1.9), gridspec_kw=dict(width_ratios=[1.6, 1]))
    y = np.arange(3)
    r = np.array([real[k] for k, _ in names]); t = np.array([sc[k]["total"] / 1e6 for k, _ in names])
    a1.barh(y, r, color=NAVY, height=.55, label="realizat (dosare decise)")
    a1.barh(y, t - r, left=r, color=NAVY_SOFT, height=.55, label="expunerea stocului nedecis")
    for i in y: a1.text(t[i] + 12, i, rd(t[i], 0), va="center", fontsize=6.2, color=INK)
    a1.set_yticks(y); a1.set_yticklabels([n for _, n in names], fontsize=6.4); a1.invert_yaxis(); a1.set_xlim(0, t.max() * 1.18)
    a1.set_xlabel("cost economic și privat, mil. lei, 1.08–18.11.2026", fontsize=6); a1.legend(fontsize=5.6, frameon=False, loc="upper right")   # upper right is empty (short prudent/central bars); lower right collides with the stressed label
    b = np.array([sc[k]["tax"] / 1e6 for k, _ in names])
    a2.barh(y, b, color=WARN, height=.55)
    for i in y: a2.text(b[i] + 4, i, rd(b[i], 0) if b[i] >= 10 else rd(b[i], 1), va="center", fontsize=6.2, color=INK)
    a2.set_yticks(y); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, b.max() * 1.25)
    a2.set_xlabel("încasări bugetare afectate, mil. lei", fontsize=6)
    for ax in (a1, a2): G.style_axes(ax, ygrid=False, xgrid=True)
    fig.tight_layout(); G.save_svg_and_png(fig, "i03_cont_de_impact")


LBL = {"blocked_change_cost": "cost pe zi al unei modificări blocate", "pending": "mărimea stocului", "disjoint_blocked_changes_share": "ponderea modificărilor cu impact separat",
       "lost_turnover_fraction": "partea de vânzări pierdută definitiv", "net_turnover_per_day": "vânzări pe zi ale unei firme noi",
       "pending_changes_excess_days": "zile de așteptare rămase, mențiuni", "pending_new_excess_days": "zile de așteptare rămase, înmatriculări",
       "pending_new_j_share": "ponderea înmatriculărilor în stoc", "value_added_share": "ponderea valorii adăugate", "preventable_post_share": "amânări evitabile",
       "inactivation_increment": "probabilitatea inactivării", "seat_share": "ponderea dosarelor de sediu", "private_cost_per_post": "cost privat pe amânare",
       "seat_private_cost": "cost privat pe inactivare"}


def i04_sensitivity():
    s = pd.DataFrame(KF["sensitivity"]).rename(columns={"low": "economic_low", "high": "economic_high"})
    s["sw"] = s.economic_high - s.economic_low; s = s[s.sw > 0].sort_values("sw").tail(10)
    fig, ax = plt.subplots(figsize=(W, 2.6)); y = np.arange(len(s))
    ax.barh(y, s.economic_low / 1e6, color=SOL, height=.6, label="valoarea prudentă a parametrului")
    ax.barh(y, s.economic_high / 1e6, color=ALERT, height=.6, label="valoarea tensionată a parametrului")
    ax.set_yticks(y); ax.set_yticklabels([LBL.get(p, p) for p in s.parameter], fontsize=6); ax.axvline(0, color=INK, lw=.7)
    ax.set_xlabel("schimbarea costului central (scenariul fundamentat), în mil. lei, când se schimbă un singur parametru", fontsize=6)
    ax.legend(fontsize=5.8, frameon=False, loc="lower right"); G.style_axes(ax, ygrid=False, xgrid=True)
    fig.tight_layout(); G.save_svg_and_png(fig, "i04_sensibilitate")


def i05_substitution():
    m = pd.DataFrame(KF["substitution"]).rename(columns={"central_mil": "central_net_all_mron", "prudent_mil": "prudent_net_all_mron"}); bud = KC["oug_budget_mil_lei"]
    lab = ["nimic", "50% / 25%", "75% / 50%", "90% / 75%", "100% / 100%"]
    fig, ax = plt.subplots(figsize=(W, 2.2)); x = np.arange(len(m))
    ax.bar(x - .2, m.central_net_all_mron, .38, color=NAVY, label="scenariul central")
    ax.bar(x + .2, m.prudent_net_all_mron, .38, color=NAVY_SOFT, label="scenariul prudent")
    ax.axhline(bud, color=ALERT, lw=1, ls="--"); ax.text(len(m) - .5, bud * 1.15, f"bugetul proiectului de OUG ≈ {rd(bud, 2)} mil. lei", ha="right", fontsize=5.8, color=ALERT)
    ax.set_yscale("log"); ax.set_yticks([2, 5, 10, 20, 50, 100, 200, 500]); ax.set_yticklabels(["2", "5", "10", "20", "50", "100", "200", "500"], fontsize=6)
    ax.minorticks_off(); ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=6.2)
    ax.set_xlabel("cât se recuperează: din activitatea nouă pierdută (A) / din costul modificărilor blocate (C)", fontsize=6)
    ax.set_ylabel("cost net, mil. lei (scară log.)", fontsize=6.2); ax.legend(fontsize=5.8, frameon=False, loc="upper right")
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "i05_substitutie")


if __name__ == "__main__":
    for f in (i01_monthly, i02_channels, i03_account, i04_sensitivity, i05_substitution):
        f(); print("ok", f.__name__)


ECR = {x["id"]: x for x in json.load(open(os.path.join(GI.IA, "out", "econometrics.json"), encoding="utf-8"))["results"]}


def i06_causal():
    rows = [("Primul an (parțial)", "A.an_partial_2024.IV.taxB_w", ALERT), ("Anul următor (primul an complet)", "A.an_urmator.IV.taxA_w", NAVY)]
    fig, ax = plt.subplots(figsize=(W, 1.6))
    for i, (lab, k, col) in enumerate(rows):
        e, (lo, hi) = ECR[k]["estimate"], ECR[k]["ci95"]
        ax.plot([lo, hi], [i, i], color=col, lw=2.2); ax.plot([e], [i], "o", color=col, ms=6)
        ax.text(max(hi, 0) + 3, i, f"{rd(e, 0)} lei (IC 95%: {rd(lo, 0)}…{rd(hi, 0)})", va="center", fontsize=6.2, color=INK,   # keep the label clear of the zero line
                bbox=dict(facecolor="white", edgecolor="none", pad=.6))
    ax.axvline(0, color=INK, lw=.8); ax.set_yticks([0, 1]); ax.set_yticklabels([r[0] for r in rows], fontsize=6.6)
    ax.set_xlim(-80, 110); ax.invert_yaxis()
    ax.set_xlabel("efectul unei zile în plus de așteptare asupra impozitului direct plătit de o firmă nouă (lei); variabilă instrumentală", fontsize=6)
    G.style_axes(ax, ygrid=False, xgrid=True); fig.tight_layout(); G.save_svg_and_png(fig, "i06_efect_cauzal")


def i07_risk_2027():
    q = ["T1_2027", "T2_2027", "T3_2027", "T4_2027"]; x = np.arange(4)
    fig, ax = plt.subplots(figsize=(W, 2.2))
    for off, sc, col, lab in ((-.2, "continuitate", WARN, "fără măsuri noi"), (.2, "combinat", SOL, "cu un pachet realist de măsuri")):
        ks = [f"B.risc_2027.{sc}.1c_efect_net_numerar_amanare.{t}" for t in q]
        e = np.array([ECR[k]["estimate"] for k in ks]); lo = np.array([ECR[k]["ci95"][0] for k in ks]); hi = np.array([ECR[k]["ci95"][1] for k in ks])
        ax.bar(x + off, e, .38, color=col, label=lab)
        ax.vlines(x + off, np.maximum(lo, 0), hi, color=INK3, lw=.8)
    ax.set_xticks(x); ax.set_xticklabels(["T1 2027", "T2 2027", "T3 2027", "T4 2027"], fontsize=6.6)
    ax.set_ylabel("milioane lei pe trimestru", fontsize=6.4); ax.legend(fontsize=6, frameon=False, loc="upper left")
    ax.set_xlabel("venituri bugetare care nu intră în bugetul anului din cauza cozii (net de ce se recuperează în același an); bare = mediana, linii = interval de simulare de 95%", fontsize=6)
    G.style_axes(ax); fig.tight_layout(); G.save_svg_and_png(fig, "i07_risc_venituri_2027")


if __name__ == "__main__":
    i06_causal(); i07_risk_2027(); print("ok econ figs")
