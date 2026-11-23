"""Schema celor două cozi (operare → soluționare), cu valorile din registrul afirmațiilor (C99, C28, C29, C01, C35, C56)."""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import generate_institutii_figures as GI
G = GI.G
G.OUT_DIR = os.path.join(GI.HERE, "figures_institutii")
REG = {r["id"]: r for r in csv.DictReader(open(os.path.join(GI.HERE, "..", "raport_executiv_2026-11", "claims_registry.csv"), encoding="utf-8"))}
V = lambda c: REG[c]["value"]
NAVY, ORANGE, INK, INK2, SOL, ALERT = G.NAVY, G.WARN, G.INK, G.INK2, G.SOL, G.ALERT

total = V("C28"); op = V("C29").split(" (")[0]; share = V("C29").split("(")[1].rstrip(")")
reg = f"{int(total.replace('.', '')) - int(op.replace('.', '')):,}".replace(",", ".")
inflow_nov = V("C99").split(" / ")[3].split(" ·")[0]
out = V("C01").replace("≈", "")
opt = V("C35").split(";")[0].replace("optim ", "").replace("≈", "")
zero = V("C35").split("zero la ")[1].replace("≈", "")


def box(ax, x, y, w, h, title, big, sub, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=col, ec="none", alpha=.95))
    ax.text(x + w / 2, y + h * .74, title, ha="center", va="center", fontsize=8.2, color="white", weight="bold")
    ax.text(x + w / 2, y + h * .45, big, ha="center", va="center", fontsize=15, color="white", weight="bold")
    ax.text(x + w / 2, y + h * .17, sub, ha="center", va="center", fontsize=6.8, color="white")


def arrow(ax, x0, y0, x1, y1, col=INK2, lw=1.6, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=12, color=col, lw=lw, linestyle=ls))


fig, ax = plt.subplots(figsize=(G.W_IN, 2.45))
ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
ax.text(0.55, 2.5, "cereri noi\n(noiembrie, fără\nînmatriculări în curs)", ha="center", va="center", fontsize=6.4, color=INK2)
ax.text(0.55, 1.55, f"≈{inflow_nov} / zi", ha="center", va="center", fontsize=8.5, color=INK, weight="bold")
arrow(ax, 1.15, 2.0, 1.75, 2.0)
box(ax, 1.8, 1.0, 2.6, 2.0, "COADA 1 · OPERARE", op, f"cereri neprelucrate ({share})", NAVY)
arrow(ax, 4.45, 2.0, 5.05, 2.0)
box(ax, 5.1, 1.0, 2.6, 2.0, "COADA 2 · REGISTRATOR", reg, "cereri prelucrate, nesoluționate", ORANGE)
arrow(ax, 7.75, 2.0, 8.35, 2.0)
ax.text(9.2, 2.35, "decizii finale", ha="center", va="center", fontsize=7, color=INK2)
ax.text(9.2, 1.55, f"≈{out} / zi", ha="center", va="center", fontsize=8.5, color=INK, weight="bold")
# moving staff from operation to decisions
ax.add_patch(FancyArrowPatch((3.1, 3.05), (6.4, 3.05), connectionstyle="arc3,rad=-0.35", arrowstyle="-|>", mutation_scale=12, color=ALERT, lw=1.4, linestyle="--"))
ax.text(4.75, 3.78, f"mutarea consilierilor din operare la soluționare: ajută până la ≈{opt}, câștig zero la ≈{zero}",
        ha="center", va="center", fontsize=6.8, color=ALERT)
ax.text(5.0, 0.45, "Stocul total la 6 noiembrie: " + total + " de cereri. Întărirea unei singure etape mută blocajul; doar ambele etape reduc stocul.",
        ha="center", va="center", fontsize=6.8, color=INK2)
fig.tight_layout(pad=0.2); G.save_svg_and_png(fig, "fi24_doua_cozi_schema")
print("ok fi24")
