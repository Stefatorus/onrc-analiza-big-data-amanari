"""Generate Lean 4 data witnesses for the v3 claims registry, build them, record the result.

Reads the SAME files the registry reads (Nota MJ via oug_2026/audit.json, build_oug_review posts, stat_pack.json,
forecast_grid.json, forecast_capacity_backtest.csv), writes formal_proofs/OnrcProofs/RegistryV3Witnesses.lean,
runs `lake build`, and writes out/lean_v3_results.json (theorem, claim, plain-language meaning, status).
If a data refresh changes a published number so that a statement no longer holds, `lake build` fails.

Run:  ..\\venv\\Scripts\\python.exe -X utf8 gen_lean_v3_witnesses.py
"""
from __future__ import annotations
import json, csv, re, subprocess, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FP = ROOT / "formal_proofs"
AD = ROOT / "analysis" / "policy_paper_ro" / "audit_data"
OUT = HERE / "out"

au = json.loads((AD / "oug_2026" / "audit.json").read_text(encoding="utf-8"))
ougr = (ROOT / "analysis" / "policy_paper_ro" / "build_oug_review.py").read_text(encoding="utf-8")
POST = [int(x.replace(".", "")) for x in re.search(r'"(\d\.\d{3}) / (\d\.\d{3}) / (\d\.\d{3})"', ougr).groups()]
SP = json.loads((OUT / "stat_pack.json").read_text(encoding="utf-8"))
GRID = json.loads((OUT / "forecast_grid.json").read_text(encoding="utf-8"))
CBT = [r for r in csv.DictReader(open(AD / "forecast_capacity_backtest.csv", encoding="utf-8")) if r["model"] == "ultimele_12_zile"]
lit = SP["little"]

T = []   # (name, claim, meaning, lean statement)
def th(name, claims, meaning, stmt):
    T.append((name, claims, meaning, stmt))

pu, pp, cu, cp = au["prior_unprocessed"], au["prior_processed"], au["current_unprocessed"], au["current_processed"]
th("mj_stock_totals", "C28",
   "Stocul oficial total este suma exactă a celor două etape, la ambele date (30.10 și 6.11.2026).",
   f"{pu} + {pp} = {au['previous_backlog']} ∧ {cu} + {cp} = {au['current_backlog']}")
th("mj_weekly_deltas", "C33",
   "Într-o săptămână, operarea a scăzut exact cu 8.300 de cereri, iar etapa registratorului a crescut exact cu 4.396.",
   f"{pu} - {cu} = 8300 ∧ {cp} - {pp} = 4396")
th("mj_stage1_share_between_51_and_52pct", "C29",
   "La 6.11.2026, cererile încă la operare reprezintă între 51% și 52% din stocul oficial: cele două etape sunt aproape egale.",
   f"51 * {au['current_backlog']} ≤ 100 * {cu} ∧ 100 * {cu} < 52 * {au['current_backlog']}")
th("funded_vacancies_134", "C51",
   "Diferența dintre posturile finanțate și cele ocupate este exact 134; ocupate < finanțate < aprobate.",
   f"{POST[1]} - {POST[2]} = 134 ∧ {POST[2]} < {POST[1]} ∧ {POST[1]} < {POST[0]}")
lam, wm = lit["lambda_finals_per_legal_wd"], lit["W_mean_wd"]
wlo, whi = int(wm), int(wm) + 1
th("little_implied_two_thirds", "C76",
   f"Cu ritmul de {lam:,} decizii".replace(",", ".") + f" pe zi lucrătoare și un timp mediu între {wlo} și {whi} zile lucrătoare, stocul implicat de legea lui Little este între 66% și 69% din stocul oficial: același ordin de mărime, dar mai mic.",
   f"66 * {lit['L_official_MJ']} ≤ 100 * ({lam} * {wlo}) ∧ 100 * ({lam} * {whi}) ≤ 69 * {lit['L_official_MJ']}")
ref = GRID["reference"]
inn, cap = round(ref["inflow_per_open_day_2027_p50"]), round(ref["capacity_per_open_day_p50"])
th("load_ratio_2027_between_118_and_120", "C67",
   "În model, în 2027, munca intrată pe zi este între 1,18 și 1,20 ori capacitatea: intră mai mult decât iese.",
   f"118 * {cap} ≤ 100 * {inn} ∧ 100 * {inn} ≤ 120 * {cap}")
# grid monotonicity (medians x10, integers)
ins, outs = GRID["in_steps"], GRID["out_steps"]
G = {(c["d_in"], c["d_out"]): round(10 * c["june2028_p50"]) for c in GRID["cells"]}
rows = " ∧ ".join(f"{G[(i, outs[k + 1])]} ≤ {G[(i, outs[k])]}" for i in ins for k in range(len(outs) - 1))
cols = " ∧ ".join(f"{G[(ins[k], o)]} ≤ {G[(ins[k + 1], o)]}" for o in outs for k in range(len(ins) - 1))
th("grid_more_capacity_never_longer", "C63, C65",
   "În toate cele 36 de celule ale grilei, mai multă capacitate nu dă niciodată o așteptare mai lungă (pe fiecare rând).", rows)
th("grid_more_inflow_never_shorter", "C63, C66",
   "În toate celulele grilei, mai multe cereri nu dau niciodată o așteptare mai scurtă (pe fiecare coloană).", cols)
base = G[(0, 0)]
th("grid_baseline_reproduces_audit", "C42, C63",
   "Celula fără schimbări a grilei reproduce exact prognoza verificată fără măsuri: 136 de zile în iunie 2028.", f"{base} = 1360")
errs = [round(100 * float(r["error_percent"])) for r in CBT]
nonneg = sum(1 for e in errs if e >= 0)
th("backtest_errors_mostly_nonnegative", "C70",
   f"În {nonneg} din {len(errs)} ferestre de test, ritmul observat a fost cel puțin cel prognozat (abatere ≥ 0).",
   f"([{', '.join(f'({e} : Int)' for e in errs)}].filter (fun e => decide (0 ≤ e))).length = {nonneg}")
adj = SP["cicluri_amanare_nov2026"]["rows"]
one = round(100 * adj[1]["decizii_finale_pct"]); more = sum(round(100 * r["decizii_finale_pct"]) for r in adj[2:])
th("adjournment_mostly_single", "C74",
   "Dintre deciziile finale cu amânare anterioară, amânările multiple sunt sub 2% din cele unice: aproape niciun dosar nu e amânat de mai multe ori.",
   f"50 * {more} < {one}")

lean = ["/-",
        "  OnrcProofs/RegistryV3Witnesses.lean — AUTO-GENERATED by independent_audit/gen_lean_v3_witnesses.py",
        "  from the same files the claims registry reads. DO NOT EDIT BY HAND.",
        "-/", "namespace OnrcProofs.RegistryV3", ""]
for name, claims, meaning, stmt in T:
    lean += [f"/-- [{claims}] {meaning} -/", f"theorem {name} : {stmt} := by decide", ""]
lean += ["end OnrcProofs.RegistryV3", ""]
(FP / "OnrcProofs" / "RegistryV3Witnesses.lean").write_text("\n".join(lean), encoding="utf-8")
root = (FP / "OnrcProofs.lean").read_text(encoding="utf-8")
if "OnrcProofs.RegistryV3Witnesses" not in root:
    (FP / "OnrcProofs.lean").write_text(root.rstrip() + "\nimport OnrcProofs.RegistryV3Witnesses\n", encoding="utf-8")

env = dict(os.environ); env["PATH"] = str(Path.home() / ".elan" / "bin") + os.pathsep + env.get("PATH", "")
r = subprocess.run(["lake", "build"], cwd=str(FP), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=1800)
ok = r.returncode == 0 and "error" not in r.stdout.lower()
sorry = "sorry" in (FP / "OnrcProofs" / "RegistryV3Witnesses.lean").read_text(encoding="utf-8")
summary = [dict(theorem=f"OnrcProofs.RegistryV3.{n}", claims=c, meaning=m, status="VERIFICAT (lake build, 0 sorry)" if ok and not sorry else "EȘUAT")
           for n, c, m, _ in T]
(OUT / "lean_v3_results.json").write_text(json.dumps(dict(build_ok=ok, lean_toolchain=(FP / "lean-toolchain").read_text().strip(),
                                                         theorems=summary, build_tail=r.stdout[-1500:] + r.stderr[-800:]),
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
print("lake build", "OK" if ok else "FAILED", "·", len(T), "theorems")
if not ok:
    print(r.stdout[-3000:], r.stderr[-2000:])
