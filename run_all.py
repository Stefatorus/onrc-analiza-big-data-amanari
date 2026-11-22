"""Rebuild the report «Coada de la Registrul Comerțului» (Nov 2026), stage by stage.

  python -X utf8 run_all.py --list                  # stages and scripts
  python -X utf8 run_all.py --offline               # only the stages that run from the committed data (no raw crawl):
                                                    #   verify-inputs, serials, registry, lean, figures*, volumes, complete, lint
  python -X utf8 run_all.py                         # everything (needs the raw data, see docs/DATA.md)
  python -X utf8 run_all.py --from registry         # resume from a stage
  python -X utf8 run_all.py --only lean lint

  * figures: generate_institutii_figures.py also reads data/analysis_decisions.pkl (built from the crawl, see docs/DATA.md).
Afterwards: `git status` / `git diff` show exactly what a re-run changed against the committed (published) outputs, and
`python -X utf8 tools/compare_outputs.py <published snapshot>` compares at value level (registry, JSON, CSV, xlsx, PDF text).

Portal sample: not published (row level). Steps marked [portal] are skipped unless ONRC_PORTAL_DIR holds harvest_*.jsonl;
their committed outputs (LOCKED_CONSTANTS.json, stat_pack.json, reserves_check/12-13*) are used instead.
"""
from __future__ import annotations
import argparse, csv, hashlib, os, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
import config  # noqa: E402

PY = sys.executable
IA, PP, RC, CE, EC, DR, RR = ("independent_audit", "analysis/policy_paper_ro", "independent_audit/reserves_check",
                              "independent_audit/cost_evidence", "independent_audit/econometrics",
                              "independent_audit/delay_reasons", "independent_audit/rejection_reasons")
RAW = [config.ARTICLES_DIR]; PDFS = [config.BULLETINS_DIR]; PKL = [config.BERC_PKL]; FIN = [config.FIN_CACHE]


def S(cwd, script, *args, capture=None, portal=False, needs=(), soft=False):
    return dict(cwd=cwd, script=script, args=list(args), capture=capture, portal=portal, needs=list(needs), soft=soft)


# (name, offline?, description, steps) in dependency order
STAGES = [
    ("verify-inputs", True, "SHA-256 of every frozen / curated input (docs/frozen_manifest.csv)", []),
    ("raw-data", False, "BERC JSON -> analysis_decisions.pkl; compact raw table; 2026 CERERE JSON and bulletin PDFs (record level, data/work)", [
        S("analysis", "build_decisions.py", str(config.BERC_PKL), needs=RAW),
        S(RC, "20_extract_raw_json.py", capture="20_extract_raw_json.out.txt", needs=RAW),
        S(CE, "02_load_cerere_json.py", needs=RAW), S(CE, "01_extract_bulletins.py", needs=PDFS)]),
    ("finance", False, "Ministry of Finance balance sheets (data.gov.ro, CC BY 4.0; network)", [S(PP, "audit_finance.py", needs=RAW)]),
    ("reconcile", False, "BERC flow x myportal stock -> LOCKED_CONSTANTS.json [portal]; OUG scenarios", [
        S(IA, "reconcile_sources.py", portal=True, needs=PKL), S(IA, "oug_scenarios.py")]),
    ("hashes", False, "data_hashes.json (after reconcile, so the LOCKED hash is current)", [S("tools", "hash_inputs.py", needs=PKL)]),
    ("models", False, "Forecast engine and grid, CAEN compliance, queue back-test, cost model inputs", [
        S(PP, "audit_forecast.py", needs=PKL), S(IA, "forecast_grid.py"), S(IA, "forecast_caen_compliance.py"),
        S(IA, "backtest_queue_mechanics.py", needs=PKL), S(PP, "audit_costs.py", needs=PKL)]),
    ("serials-raw", False, "Request-number counter analysis (stdout captured: serials_consolidate parses it)", [
        S(RC, "11_inflow_counter.py", capture="11_inflow_counter.out.txt", needs=PKL),
        S(RC, "12_portal_berc_join.py", capture="12_portal_berc_join.out.txt", portal=True, needs=PKL),
        S(RC, "13_stock_estimate.py", capture="13_stock_estimate.out.txt", portal=True),
        S(RC, "14_inmatric_lowerbound.py", capture="14_inmatric_lowerbound.out.txt", needs=PKL),
        S(RC, "22_task2_measures.py", capture="22_task2_measures.out.txt", needs=[config.WORK_DIR / "raw_compact.pkl"]),
        S(RC, "23_april27_floor.py", capture="23_april27_floor.out.txt", needs=[config.WORK_DIR / "raw_compact.pkl"]),
        S(RC, "26_refiling_baseline.py", capture="26_refiling_baseline.out.txt", needs=[config.WORK_DIR / "raw_compact.pkl"])]),
    ("serials", True, "serials_findings.json from the reserves_check outputs", [S(IA, "serials_consolidate.py")]),
    ("stat-packs", False, "stat_pack [portal] (+validation_checklist), stat_pack_ext (+xlsx), county rankings, press cross-check", [
        S(IA, "stat_pack.py", portal=True, needs=PKL), S(IA, "stat_pack_ext.py", needs=PKL), S(IA, "county_rankings.py"),
        S(IA, "osint_crosscheck.py", needs=PKL)]),
    ("reasons", False, "Postponement and rejection reasons from the 2026 bulletin PDFs (local embeddings; see READMEs)", [
        *[S(DR, f, needs=PDFS) for f in ("01_extract_postponements.py", "02_normalize_split.py", "03_embed_cluster.py", "04_classify.py",
                                          "06_validate.py", "07_results.py", "08_solutions.py")],
        *[S(RR, f, needs=PDFS) for f in ("01_extract_rejections.py", "02_normalize_split.py", "03_embed_cluster.py", "04_classify.py",
                                          "06_validate.py", "07_results.py")]]),
    ("costs", False, "Economic and budgetary impact: re-check, evidence base, founded scenario, monthly series", [
        S(IA, "cost_check.py", needs=PKL),
        S(CE, "03_amendment_types.py"), S(CE, "04_amendment_firms_finance.py", needs=FIN), S(CE, "05_new_firms_tax.py", needs=RAW + FIN),
        S(CE, "08_write_official_sources.py"), S(CE, "06_measured_floor.py", needs=PKL), S(CE, "07_build_evidence_json.py"),
        S(IA, "cost_founded.py"), S(IA, "cost_monthly.py", needs=PKL)]),
    ("econometrics", False, "Event study / DiD and revenue at risk 2027 -> out/econometrics.json", [
        S(EC, "test_econ_lib.py"), S(EC, "01_build_sample.py", needs=RAW + FIN), S(EC, "02_part_a.py"), S(EC, "03_part_b.py", needs=PKL),
        S(EC, "04_figures.py"), S(EC, "05_build_json.py"), S(EC, "99_cleanup.py")]),
    ("registry", True, "Claims registry: every published number, read from the outputs above", [S(IA, "generate_claims_registry.py")]),
    ("lean", True, "Lean 4 data witnesses for the registry + lake build", [S(IA, "gen_lean_v3_witnesses.py")]),
    ("figures", True, "SVG figures for all volumes", [
        S(PP, "generate_institutii_figures.py", needs=PKL), S(PP, "generate_prognoza_figures.py"), S(PP, "generate_stat_figures.py"),
        S(PP, "generate_impact_figures.py"), S(PP, "generate_postponement_figures.py")]),
    ("volumes", True, "Main report, executive edition, volumes 0-7 (HTML -> PDF via Edge headless)", [
        S(PP, "build_all_volumes.py"), S(PP, "build_volume_stat.py", "--vol7")]),
    ("complete", True, "The single complete PDF (two passes, continuous pages, internal links, embedded attachments)", [
        S(PP, "build_raport_complet.py", needs=[REPO / "analysis/raport_executiv_2026-11/Date_ONRC_Coada_2026-11.xlsx"])]),
    ("lint", True, "Number linter on the final HTML (failures reported, exit 1 at the end); reel package", [
        *[S("analysis/raport_executiv_2026-11", "lint_numbers.py", f"../policy_paper_ro/{h}", soft=True) for h in (
            "Raport_ONRC_Coada_2026-11.html", "Raport_ONRC_Coada_2026-11_EXECUTIV.html", "Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil.html",
            "Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat.html", "Raport_ONRC_Coada_2026-11_VOL4_Munca_din_spatele_cozii.html")],
        S(IA, "generate_reel_package.py")]),
]
FAILED_SOFT = []


def portal_available():
    return any(config.PORTAL_DIR.glob("harvest_*.jsonl"))


def verify_inputs():
    bad = 0
    for r in csv.DictReader(open(REPO / "docs" / "frozen_manifest.csv", encoding="utf-8")):
        p = REPO / r["path"]
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"
        if got != r["sha256"]:
            bad += 1; print(f"  CHANGED {r['path']}")
    print(f"  frozen/curated inputs checked; {bad} changed")
    if bad:
        sys.exit("  inputs differ from docs/frozen_manifest.csv")


def run_step(st):
    if st["portal"] and not portal_available():
        print(f"  SKIP {st['script']} [portal: committed outputs used]"); return
    for n in st["needs"]:
        if not Path(n).exists():
            sys.exit(f"  MISSING input for {st['script']}: {n}  (see docs/DATA.md; or use --offline)")
    env = dict(os.environ, PYTHONPATH=str(REPO) + os.pathsep + os.environ.get("PYTHONPATH", ""), PYTHONIOENCODING="utf-8")
    cmd = [PY, "-X", "utf8", st["script"], *st["args"]]
    cwd = REPO / st["cwd"]; t = time.time()
    print(f"  > ({st['cwd']}) {' '.join(cmd[3:])}", flush=True)
    if st["capture"]:
        with open(cwd / st["capture"], "w", encoding="utf-8", newline="\n") as f:
            r = subprocess.run(cmd, cwd=cwd, env=env, stdout=f)
    else:
        r = subprocess.run(cmd, cwd=cwd, env=env)
    if r.returncode != 0:
        if st["soft"]:
            FAILED_SOFT.append(f"{st['script']} {' '.join(st['args'])}"); print(f"    FAILED (recorded) {r.returncode}"); return
        sys.exit(f"  FAILED ({r.returncode}) {st['script']}")
    print(f"    ok {time.time() - t:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true"); ap.add_argument("--offline", action="store_true")
    ap.add_argument("--from", dest="start"); ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    names = [s[0] for s in STAGES]
    if a.list:
        for n, off, d, steps in STAGES:
            print(f"{n:14}{'[offline] ' if off else '          '}{d}" + "".join(f"\n{'':24}{s['cwd']}/{s['script']} {' '.join(s['args'])}" for s in steps))
        return
    sel = names[names.index(a.start):] if a.start else names
    if a.only:
        sel = [n for n in names if n in a.only]
    if a.offline:
        sel = [n for n, off, _, _ in STAGES if off and n in sel]
    print(f"python {sys.version.split()[0]} · edge: {config.EDGE_PATH} · lake: {config.LAKE} · portal sample: {portal_available()}")
    for n, _, d, steps in STAGES:
        if n not in sel:
            continue
        print(f"\n=== {n}: {d}")
        if n == "verify-inputs":
            verify_inputs()
        for st in steps:
            run_step(st)
    if FAILED_SOFT:
        sys.exit("\nLINT FAILURES:\n  " + "\n  ".join(FAILED_SOFT))
    print("\nDONE. `git status` shows what changed; tools/compare_outputs.py compares with a published snapshot.")


if __name__ == "__main__":
    main()
