# cost_evidence — evidence base for the four-channel delay-cost model

Read-only audit of `analysis/policy_paper_ro/audit_costs.py`. Nothing outside this folder and `out/cost_evidence.json` was modified.
All outputs are aggregates; no names, CUI or row-level identifiers. The record-level intermediates (`_tmp/`) were deleted after use.
Run `02` and `01` to rebuild them.

| script | task | output |
|---|---|---|
| `00_explore_templates.py` | decision-template feasibility (25 bulletins) | stdout |
| `01_extract_bulletins.py` | parse **all 545** 2026 bulletin PDFs (PyMuPDF); object flags from "având ca obiect" | `_tmp/` (deleted) |
| `02_load_cerere_json.py` | 2026 CERERE265 raw JSON (request nr, CUI, dates, outcome) | `_tmp/` (deleted) |
| `03_amendment_types.py` | T1: type shares, cluster CIs (bulletin), blocking tiers, coverage checks | `_t1_amendment_types.json` |
| `04_amendment_firms_finance.py` | T2: amendment firms × MF balance sheets 2025 (2024 fallback) | `_t2_amendment_firms.json` |
| `05_new_firms_tax.py` | T3: 2024/2025 J cohorts: direct tax, employees, margins, daily turnover | `_t3_new_firms.json` |
| `08_write_official_sources.py` | T4: official figures with URLs (fetched 2026-11-22) | `official_sources.json`, `official_rates.json` |
| `06_measured_floor.py` | T5: measured lower bound | `_t5_floor.json` |
| `07_build_evidence_json.py` | assemble one entry per finding | `../out/cost_evidence.json` |

Order of execution: 02, 01, 03, 04, 05, 08, 06, 07.

## Key caveats
- The bulletin archive has 60 Jan, 1 Feb and 482 Oct–Nov 2026 bulletins. Amendment-type shares therefore rest on decisions of
  1 Oct–18 Nov 2026: 8,957 linked admitted amendments, 455 bulletins, 7.4% of the population. Monthly shares for Jan–Sep and Aug–Sep cannot be established.
  The CIs reflect sampling among the collected bulletins only, not how those bulletins were collected.
- The sample over-represents long waits. The type mix depends on the application month: CAEN Rev.3 requests dominate those filed in September.
  Results re-weighted by application month and by county barely move.
- A "blocking type" share is a **ceiling** for channel C's "share with separate economic impact", not an estimate of it.
- PFA/II/IF (type F, ~20% of amendments) file no balance sheets. The J match rate is ~70%.
- The floor assumes only that cash flows are shifted, not lost. It counts realised J registrations only.
- The strict blocking tier is also reported without bare "capital social" mentions that only accompany activity-code items:
  15.0% of excess days once seat-related entries are excluded, against 21.8% with them.
- Task 4 status labels: three figures were re-read by the auditor (T-bill 5 Nov 2026, HG 146/2026, OUG 89/2025 art. III).
  The others are marked as confirmed by the delegated research run.
