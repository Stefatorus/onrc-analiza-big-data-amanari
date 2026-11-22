"""Classify every registry claim by what is needed to recompute it from scratch -> docs/claims_reproducibility.csv.

Tiers (the lowest tier that suffices):
  R  release data alone: berc_decisions_min.csv.gz / counter_daily_*.csv.gz (+ the committed aggregates)
  J  full BERC crawl (raw JSON: firm identity, request numbers per record) and/or MF balance sheets
  B  BERC bulletin PDFs (2026) - text of the decisions
  P  the unpublished myportal sample (only its aggregates are in the repo)
  F  frozen input from an earlier analysis stage (docs/FROZEN.md): reproducible from the committed file onwards only
  D  documentary (law, official notes, manual check) - verify against the cited source
Every claim, whatever the tier, is re-derived by generate_claims_registry.py from the committed outputs (`run_all.py --offline`).

  python -X utf8 tools/claims_tiers.py
"""
import csv, re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = [  # first match wins
    ("F", r"recompute_from_raw|tandem_bottleneck|steelman|oug_2026|rerun_oug|check_refiling|verify_v2|build_oug_review|audit_atlas|onrc_queue_model|FAPTE_VERIFICATE|replicare_independenta|analyze_6month"),
    ("P", r"reconcile_sources|stat_pack\.py|13_stock_estimate|analyze_portal_snapshot"),
    ("B", r"delay_reasons|rejection_reasons|cost_evidence/ \(T1\)"),
    ("J", r"econometrics|audit_finance|22_task2|23_april27|26_refiling|cost_evidence/ \(T[345]"),
    ("R", r"audit_forecast|forecast_grid|forecast_caen|backtest_queue|cost_monthly|cost_founded|cost_check|audit_costs|stat_pack_ext|county_rankings|osint_crosscheck|11_inflow_counter"),
    ("D", r"stakeholders|LEGAL_BASIS|manual|^—$|^$"),
]


def tier(script):
    for t, rx in RULES:
        if re.search(rx, script):
            return t
    return "D"


def main():
    rows = list(csv.DictReader(open(REPO / "analysis" / "raport_executiv_2026-11" / "claims_registry.csv", encoding="utf-8")))
    out = [dict(id=r["id"], status=r["status"], tier=tier(r["script"].strip()), script=r["script"], source=r["source"][:120]) for r in rows]
    with open(REPO / "docs" / "claims_reproducibility.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    pub = [o for o in out if o["status"] != "FAIL"]
    print("all:", dict(Counter(o["tier"] for o in out)), "| published (PASS/WARN):", dict(Counter(o["tier"] for o in pub)))


if __name__ == "__main__":
    main()
