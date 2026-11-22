# Metoda / Method

Metoda completă, în proză, este anexa **„Metodologia”** a raportului complet (`reports/actuale/Raport_ONRC_Coada_2026-11_COMPLET.pdf`,
la final), generată de `analysis/policy_paper_ro/methodology.py`. Detaliile statistice sunt în **Volumul 3 / Partea 5**
(`Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat.pdf`). Verificarea fiecărei cifre este în **Volumul 6 / Partea 8**.

Pe scurt, unde e fiecare piesă în cod:

| Piesă | Script(uri) |
|---|---|
| arhiva de decizii (o linie pe decizie) | `analysis/build_decisions.py` |
| reconcilierea BERC (flux) × myportal (stoc), constantele blocate | `independent_audit/reconcile_sources.py` → `out/LOCKED_CONSTANTS.json` |
| tabelele statistice, cohortele Kaplan–Meier, bootstrap | `independent_audit/stat_pack.py`, `stat_pack_ext.py` |
| contorul numerelor de cerere (intrări, stoc, ordine) | `independent_audit/reserves_check/`, `serials_consolidate.py` |
| motorul de prognoză (Monte Carlo, 2.000 de extrageri, sămânță 20261121) și grila | `analysis/policy_paper_ro/audit_forecast.py`, `independent_audit/forecast_grid.py`, `forecast_caen_compliance.py`, `backtest_queue_mechanics.py` |
| motivele amânărilor și ale respingerilor (text din buletine, embeddings locale, validare manuală) | `independent_audit/delay_reasons/`, `rejection_reasons/` (vezi README-urile lor) |
| costul economic și bugetar | `analysis/policy_paper_ro/audit_costs.py`, `independent_audit/cost_check.py`, `cost_evidence/`, `cost_founded.py`, `cost_monthly.py` |
| efectul cauzal și veniturile la risc 2027 | `independent_audit/econometrics/` (README) |
| registrul afirmațiilor | `independent_audit/generate_claims_registry.py` |
| verificarea formală | `independent_audit/gen_lean_v3_witnesses.py`, `formal_proofs/` (Lean 4, `lake build`) |
| verificarea textului | `analysis/raport_executiv_2026-11/lint_numbers.py` |
| replicarea independentă | `replicare_independenta/lucru/` (`RAPORT_REPLICARE.md`) |
