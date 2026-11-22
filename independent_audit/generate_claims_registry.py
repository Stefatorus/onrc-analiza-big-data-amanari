"""Claims registry v2 — every public number, traceable to a machine output.

Values are READ from machine outputs (never typed by hand):
  out/LOCKED_CONSTANTS.json   (reconcile_sources.py — BERC flow + portal stock, locked)
  out/recompute_from_raw.json (recompute_from_raw.py — audited Level-A windows)
  out/tandem_bottleneck.json  (tandem_bottleneck_analysis.py — tandem, MJ note, online, amânări)
  out/refiling_check.json     (check_refiling_rate.py)
  out/oug_rerun_compare.json  (rerun_oug_current.py — audited OUG model, June 2028)
Levels follow FAPTE_VERIFICATE: A = recalculated from raw data, B = model/estimate (intervals
only), C = official figure quoted with source. Badge (Lab style): E=A, P/M=B, S=C.
Status: PASS publishable; WARN only with `rezerva_obligatorie` glued to the number; FAIL never.
Gate M2 (CICERO-REELS, 22.11.2026) verdicts are applied: withdrawn claims stay listed as FAIL.
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); import config  # repo config.py
import json, csv, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DELIV = HERE.parent / "analysis" / "raport_executiv_2026-11"
DELIV.mkdir(parents=True, exist_ok=True)

def J(name): return json.loads((OUT / name).read_text(encoding="utf-8"))
def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""): h.update(ch)
    return h.hexdigest()

L = J("LOCKED_CONSTANTS.json"); RW = J("recompute_from_raw.json"); T = J("tandem_bottleneck.json")
RF = J("refiling_check.json"); OG = J("oug_rerun_compare.json")["june2028"]
H = json.loads((DELIV / "data_hashes.json").read_text(encoding="utf-8"))
SHA = {"BERC": H["BERC_analysis_decisions.pkl"]["sha256"], "PORTAL": H["portal_harvest_all"]["sha256"]}
for f in ("LOCKED_CONSTANTS.json", "recompute_from_raw.json", "tandem_bottleneck.json",
          "refiling_check.json", "oug_rerun_compare.json", "verify_v2_ledger.csv"):
    SHA[f] = sha(OUT / f)
CTY_F = OUT / "atlas_rerun" / "audit_data" / "county_indicators.csv"
SHA["county_indicators.csv"] = sha(CTY_F)
import pandas as _pd
_CT = _pd.read_csv(CTY_F, encoding="utf-8-sig").set_index("code")
_cmin, _cmax = _CT.median_nov.idxmin(), _CT.median_nov.idxmax()
DATE_BERC = "BERC până la " + L["berc_last_decision"]
DATE_PORT = "portal myportal, harvest 21–22.11.2026"
DATE_MJ = "Nota MJ, 6.11.2026"

ro = lambda x: f"{x:,.0f}".replace(",", ".")
rd = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
R = L["regimes_by_decision_date"]; DW = L["wait_of_dossiers_decided_by_week"]; TS = L["two_speed_2_19_nov"]
MJ = T["mj_tandem_conservation"]; CV = MJ["conventions"]["strict_finals"]
SEAS = {s["window"]: s["finals_per_wd"] for s in T["season_matched_c1_series"]}
SW = lambda y: SEAS[f"Oct-Nov {y} (1 Oct - 20 Nov)"]
PEAK25 = SEAS["Feb-Mar 2025 (peak, 1 Feb - 31 Mar)"]
TSC = T["tandem_scenarios_distinct_anchor"]; MJ_IN0 = TSC["S0_status_quo_baseline_inflow"]["inflow_wd"]; MJ_IN1 = TSC["W0_wave_6931_status_quo"]["inflow_wd"]
AM = [x for x in T["auto_amanari_timing"] if x["period"].startswith("Nov")][0]
ONL = [x for x in T["online_vs_office_hours"] if x["cat"] == "CERERE265"]
onl_lo = min(x["wmean_diff_med_d"] for x in ONL); onl_hi = max(x["wmean_diff_med_d"] for x in ONL)
SY = T["april_2026_synchronization"]; EU = RW["eu_directive"]["published_def_J_admis_firstpass"]
V1, CR = RW["windows"]["v1"], RW["windows"]["crisis"]
import re as _re, csv as _csv
PP = HERE.parent / "analysis" / "policy_paper_ro"
SOL_F = PP / "audit_data" / "solutions_feasibility_and_simulations.csv"
STM_F = PP / "audit_data" / "steelman_counterarguments_matrix.csv"
OSC_F = PP / "audit_data" / "oug_2026" / "scenarios.csv"
OUGR_F = PP / "build_oug_review.py"
LEDGER_F = OUT / "verify_v2_ledger.csv"
for _f in (SOL_F, STM_F, OSC_F, OUGR_F):
    SHA[_f.name] = sha(_f)
SOLS = {r["id"]: r for r in _csv.DictReader(open(SOL_F, encoding="utf-8"))}
OSC = {(r["scenario"], r["period"]): r for r in _csv.DictReader(open(OSC_F, encoding="utf-8"))}
LED = {r["claim"]: r for r in _csv.DictReader(open(LEDGER_F, encoding="utf-8"))}
_c16 = LED["CLAIM-16"]["detail"]
CAEN_PCT = float(_re.search(r"'caen_only_raw_pct': ([\d.]+)", _c16).group(1))
CAEN_SE = float(_re.search(r"'cluster_boot_se_pct': ([\d.]+)", _c16).group(1))
CAEN_N = int(_re.search(r"'n_bulletins': (\d+)", _c16).group(1))
CAEN_DEFF = float(_re.search(r"'deff': ([\d.]+)", _c16).group(1))
# PDF bulletins collected for 2026 (the CAEN sample uses CAEN_N of them); counted on disk when the archive is mounted
_PDF_DIR = config.BULLETINS_DIR
NPDF_2026 = 545
if _PDF_DIR.exists():
    assert len(list(_PDF_DIR.glob("*.pdf"))) == NPDF_2026, "PDF bulletin count changed: update NPDF_2026 and the texts"
_c30 = LED["CLAIM-30"]["detail"]
P5_FRAG = sorted(int(x) for x in _re.findall(r": (\d+)d", _c30))
_ougr = OUGR_F.read_text(encoding="utf-8")
POST = [int(x.replace(".", "")) for x in _re.search(r'"(\d\.\d{3}) / (\d\.\d{3}) / (\d\.\d{3})"', _ougr).groups()]
_stm = open(STM_F, encoding="utf-8").read()
_m3 = _re.search(r"(\d+)[–-](\d+) registratori net suplimentari \((\d+)[–-](\d+) u/zi\)", _stm)
FTE_LO, FTE_HI, U_LO, U_HI = (int(x) for x in _m3.groups())
W0, W1, W2 = TSC["W0_wave_6931_status_quo"], TSC["W1_wave_6931_stage2_only_plus_2050_starves"], TSC["W2_wave_6931_balanced_tandem_7327"]
AUGR = L["august_ratio_strict_finals_per_legal_wd"]
_AU = json.loads((PP / 'audit_data' / 'oug_2026' / 'audit.json').read_text(encoding='utf-8')); au_prev, au_cur = _AU['previous_backlog'], _AU['current_backlog']
# ---- forecast chapter sources (same files the figures read) ----
AD = PP / "audit_data"
TRJ_F, FTR_F, WAV_F, SEN_F, CBT_F, MPR_F = (AD / "oug_2026" / "trajectory.csv", AD / "forecast_trajectories.csv",
    AD / "forecast_wave_sensitivity.csv", AD / "forecast_sensitivity.csv", AD / "forecast_capacity_backtest.csv",
    AD / "forecast_monthly_profile.csv")
GRID_F = OUT / "forecast_grid.json"
for _f in (TRJ_F, FTR_F, WAV_F, SEN_F, CBT_F, MPR_F, GRID_F):
    SHA[_f.name] = sha(_f)
TRJ = list(_csv.DictReader(open(TRJ_F, encoding="utf-8")))
TR0 = [r for r in TRJ if r["scenario"] == "referinta"][0]
FTR = [r for r in _csv.DictReader(open(FTR_F, encoding="utf-8")) if r["scenario"] == "continuitate"][-1]
_G1 = next(r for r in json.loads((OUT / "stat_pack.json").read_text(encoding="utf-8"))["model_grila_completa"]["rows"] if r["d_in"] == 0 and r["d_out"] == 0)
WAV = {r["wave_removed"]: r for r in _csv.DictReader(open(WAV_F, encoding="utf-8"))}
SEN = list(_csv.DictReader(open(SEN_F, encoding="utf-8")))
CBT = [r for r in _csv.DictReader(open(CBT_F, encoding="utf-8")) if r["model"] == "ultimele_12_zile"]
MPR = {int(r["month"]): float(r["relative_to_november"]) for r in _csv.DictReader(open(MPR_F, encoding="utf-8"))}
GRID = json.loads(GRID_F.read_text(encoding="utf-8"))
GC = {(c["d_in"], c["d_out"]): c for c in GRID["cells"]}
def gw(di, do, k="june2028_p50"):
    v = GC[(di, do)][k]
    return "≤3" if v <= 3 else ro(v)
def osc(sname, per):
    r = OSC[(sname, per)]
    lo = "≤3" if float(r["p10"]) <= 3 else ro(float(r["p10"]))
    return f"≈{ro(float(r['median']))} ({lo}–{ro(float(r['p90']))})"
CBT_ERR = [float(r["error_percent"]) for r in CBT]
CBT_MAPE = sum(abs(float(r["predicted_per_day"]) / float(r["observed_per_day"]) - 1) for r in CBT) * 100 / len(CBT)
CBT_UP = sum(1 for e in CBT_ERR if e >= 0)
RATIO27 = GRID["reference"]["inflow_per_open_day_2027_p50"] / GRID["reference"]["capacity_per_open_day_p50"]
pm = lambda x: f"{x:+.0f}".replace("-", "−")
SPF = OUT / "stat_pack.json"; SHA["stat_pack.json"] = sha(SPF)
SPK = json.loads(SPF.read_text(encoding="utf-8"))
KM9 = [r for r in SPK["cohorte_KM_portal"]["rows"] if r["luna_dep"] == "2026-09"][0]
ADJ, CDS, LIT, BTS = SPK["adjourn_link"], SPK["county_dispersion"], SPK["little"], SPK["bootstrap_C14"]
LAG26 = [r for r in SPK["intarziere_publicare"]["rows"] if r["an"] == 2026][0]
import math as _m
_z = _m.atanh(CDS["spearman_2025_vs_nov"]); _se = 1 / _m.sqrt(CDS["n"] - 3)
RHO_LO, RHO_HI = _m.tanh(_z - 1.96 * _se), _m.tanh(_z + 1.96 * _se)
SPXF = OUT / "stat_pack_ext.json"; SHA["stat_pack_ext.json"] = sha(SPXF)
SPX = json.loads(SPXF.read_text(encoding="utf-8"))
EAP = {r["an"]: r for r in SPX["efort_aceeasi_perioada"]["rows"]}
EAN = {r["an"]: r for r in SPX["efort_anual"]["rows"]}
EAF = {r["an"]: r for r in SPX["efort_in_afara_programului"]["rows"]}
ESZ = {r["an"]: r for r in SPX["efort_sezon_MJ"]["rows"]}
RKF = OUT / "county_rankings.json"; SHA["county_rankings.json"] = sha(RKF)
RK = json.loads(RKF.read_text(encoding="utf-8"))
_rn = lambda k: RK[k]["rows"]
OSF = OUT / "osint_crosscheck.json"; SHA["osint_crosscheck.json"] = sha(OSF); OS = json.loads(OSF.read_text(encoding="utf-8"))
OSR = {r["id"]: r for r in OS["rows"]}
CCF = OUT / "forecast_caen_compliance.json"; SHA["forecast_caen_compliance.json"] = sha(CCF); CC = json.loads(CCF.read_text(encoding="utf-8"))
SRF = OUT / "serials_findings.json"; SHA["serials_findings.json"] = sha(SRF); SR = json.loads(SRF.read_text(encoding="utf-8"))
_st = SR["stock"]; _in = SR["inflow"]
BQF = OUT / "backtest_queue_mechanics.json"; SHA["backtest_queue_mechanics.json"] = sha(BQF); BQ = json.loads(BQF.read_text(encoding="utf-8"))["origini"]
_mech = [v["mecanism"] for v in BQ.values()]; _fore = [v["prognoza"] for v in BQ.values()]
def _cc(sh, auto=0.0, k="iun2027"):
    r = next(x for x in CC["scenarios"] if x["pondere"] == sh and x["automatizare_caen"] == auto); return ro(r[k][1])
_TIE = [r for r in RK["rang_asteptare_nov"]["rows"][1:] if round(r["median_nov"], 1) == round(RK["rang_asteptare_nov"]["rows"][1]["median_nov"], 1)]
NOVALL = [r for r in SPK["serie_lunara"]["rows"] if r["luna"] == "2026-11"][0]; LE2 = L["le2d_share_27apr_by_decision_date"]

def C(id, text, value, unit, level, status, source, script, data, date, caveat, public):
    badge = {"A": "E", "B": "P", "C": "S"}[level]
    return dict(id=id, text=text, value=value, unit=unit, level=f"{level}/{badge}", status=status,
                source=source, script=script, data_sha256=SHA[data], data_date=date,
                rezerva_obligatorie=caveat, public_ro=public)

B, LC, TB, RC, RF_, OGF, PO = "BERC", "LOCKED_CONSTANTS.json", "tandem_bottleneck.json", \
    "recompute_from_raw.json", "refiling_check.json", "oug_rerun_compare.json", "PORTAL"

KCF = OUT / "cost_check.json"; SHA["cost_check.json"] = sha(KCF); KC = json.loads(KCF.read_text(encoding="utf-8"))
_ADC = HERE.parent / "analysis" / "policy_paper_ro" / "audit_data"
for _f in ("cost_scenarios.csv", "formation_turnover.csv", "macro_substitution_stress_test.csv"):
    SHA[_f] = sha(_ADC / _f)
KFF = OUT / "cost_founded.json"; SHA["cost_founded.json"] = sha(KFF); KF = json.loads(KFF.read_text(encoding="utf-8"))
KEF = OUT / "cost_evidence.json"; SHA["cost_evidence.json"] = sha(KEF); KE = {x["id"]: x for x in json.loads(KEF.read_text(encoding="utf-8"))["findings"]}
_SC = KF["scenarios"]["fundamentat"]; _SC0 = KF["scenarios"]["initial"]; _FM = {(r["cohort_year"], r["financial_year"]): r for r in KC["formation"]}
_SUB = KF["substitution"]; _SENS = KF["sensitivity"][0]
_MAC = {r["regime"][:2]: r for r in KC["macro"]}
RPF = HERE.parent / "replicare_independenta" / "lucru" / "RAPORT_REPLICARE.md"; SHA["RAPORT_REPLICARE.md"] = sha(RPF)
_RPT = RPF.read_text(encoding="utf-8")
REPL = {k: int(_re.search(rf"\|\s*{k}\s*\|\s*(\d+)\s*\|", _RPT).group(1)) for k in ("CONFIRMAT", "DIFERIT", "NEVERIFICABIL")}
ECF = OUT / "econometrics.json"; SHA["econometrics.json"] = sha(ECF); ECR = {x["id"]: x for x in json.loads(ECF.read_text(encoding="utf-8"))["results"]}
_ec = lambda k: ECR[k]["estimate"]; _eci = lambda k: ECR[k]["ci95"]
_RK = "B.risc_2027.continuitate."
KMF = OUT / "cost_monthly.json"; SHA["cost_monthly.json"] = sha(KMF); KM = json.loads(KMF.read_text(encoding="utf-8"))
_KMR = {r["luna"]: r for r in KM["cost_lunar"]["rows"]}; _KMY = {r["an"]: r for r in KM["cost_anual"]["rows"]}
_norm = sorted(_KMR[m]["economic_central_mil"] for m in ("2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"))
mil = lambda x: rd(x / 1e6, 0) if x >= 1e8 else rd(x / 1e6, 1) if x >= 1e7 else rd(x / 1e6, 2)

_WORD = {2: "două", 3: "trei", 4: "patru", 5: "cinci", 6: "șase", 7: "șapte", 8: "opt", 9: "nouă", 10: "zece", 11: "unsprezece", 12: "douăsprezece"}
# Oct–Nov 2026 (mean of the two decision months; Nov is partial, so this cannot overstate) vs the median normal month
# (Jun–Dec 2025), central scenario; rounded to the nearest integer, never hard-coded
_NORM_MED = _norm[len(_norm) // 2]
_ORI_X = (_KMR['2026-10']['economic_central_mil'] + _KMR['2026-11']['economic_central_mil']) / 2 / _NORM_MED
ORI = _WORD[int(_ORI_X + 0.5)]
# C113: 2026 vs 2024 + 2025, computed on unrounded yearly totals (central); the sentence follows the data
_Y24, _Y25, _Y26 = (_KMY[y]['economic_central_mil'] for y in ('2024', '2025', '2026'))
_DE = lambda n: "" if 0 < int(round(n)) % 100 < 20 else "de "      # Romanian: «19 milioane», «20 de milioane», «105 milioane»
_y24, _y25, _y26 = (int(round(x)) for x in (_Y24, _Y25, _Y26))  # displayed (rounded) values; margin uses the same numbers
if _Y26 > _Y24 + _Y25:
    C113_PUB = (f"În 2026, întârzierile au costat deja mai mult decât în 2024 și 2025 la un loc: circa {_y26} {_DE(_y26)}milioane de lei, "
                f"față de circa {_y24} în 2024 și {_y25} în 2025, deci cu circa {_y26 - _y24 - _y25} {_DE(_y26 - _y24 - _y25)}milioane mai mult (scenariul central).")
elif _Y26 >= 0.9 * (_Y24 + _Y25):
    C113_PUB = (f"În 2026, întârzierile au costat deja aproape cât în 2024 și 2025 la un loc: circa {_y26} {_DE(_y26)}milioane de lei, "
                f"față de circa {_y24} în 2024 și {_y25} în 2025 (scenariul central).")
else:
    C113_PUB = (f"În 2026, întârzierile au costat deja circa {_y26} {_DE(_y26)}milioane de lei, față de circa {_y24} în 2024 "
                f"și {_y25} în 2025 (scenariul central).")
# C110: compare the full-substitution net cost with the OUG budget, for both prudent and central parameters
_OUGB = KC['oug_budget_mil_lei']; _FSP, _FSC = _SUB[4]['prudent_mil'], _SUB[4]['central_mil']
if _FSC < _OUGB:
    C110_CAV = (f"La substituție totală, costul net ({rd(_FSP, 1)} mil. cu parametri prudenți, {rd(_FSC, 1)} mil. în scenariul central) e sub bugetul OUG "
                f"({rd(_OUGB, 2)} mil.); comparația cu bugetul nu e robustă.")
elif _FSP < _OUGB:
    C110_CAV = (f"La substituție totală, costul net e sub bugetul OUG ({rd(_OUGB, 2)} mil.) doar cu parametri prudenți ({rd(_FSP, 1)} mil.); "
                f"în scenariul central ({rd(_FSC, 1)} mil.) îl depășește. Comparația cu bugetul nu e robustă.")
else:
    C110_CAV = (f"Chiar la substituție totală, costul net rămâne peste bugetul OUG ({rd(_OUGB, 2)} mil.): {rd(_FSP, 1)} mil. cu parametri prudenți "
                f"(de același ordin cu bugetul) și {rd(_FSC, 1)} mil. în scenariul central. Comparația cu bugetul nu e robustă.")
_ord = lambda x: "milioanelor" if x < 10 else "zecilor de milioane" if x < 100 else "sutelor de milioane"
_ORDS = sorted({_ord(_FSP), _ord(_FSC)}, key=["milioanelor", "zecilor de milioane", "sutelor de milioane"].index)
C110_PUB = ("Chiar dacă aproape toată activitatea pierdută ar fi preluată de alte firme, costul net rămâne de ordinul "
            + " sau ".join(_ORDS) + " de lei.")
assert 0.70 <= _SC['central']['channels_share']['C'] <= 0.80, "C109 public sentence ('circa trei sferturi') no longer true"

CLAIMS = [
 # ---------- capacity / production ----------
 C("C01", "Final decisions per legal working day, 1 Oct–19 Nov 2026 (last complete day)", f"≈{ro(round(EAP[2026]['finale_pe_zi_lucr'], -2))}", "decizii finale / zi lucrătoare",
   "A", "PASS", "BERC (finale: admis, respins, renunțat, certificări)", "stat_pack_ext.py (efort_aceeasi_perioada)", "stat_pack_ext.json", DATE_BERC,
   f"Nu e un record absolut: vârful a fost în feb.–mar. 2025 (≈{ro(PEAK25)}/zi). E un număr de decizii, nu un volum de muncă.",
   f"Registrul finalizează circa {ro(round(EAP[2026]['finale_pe_zi_lucr'], -2))} de dosare pe zi lucrătoare în octombrie–noiembrie 2026."),
 C("C30", "Same-period (1 Oct–19 Nov, last complete day) finals per legal working day, 2023→2026",
   f"{ro(EAP[2023]['finale_pe_zi_lucr'])} / {ro(EAP[2024]['finale_pe_zi_lucr'])} / {ro(EAP[2025]['finale_pe_zi_lucr'])} / {ro(EAP[2026]['finale_pe_zi_lucr'])}", "decizii finale / zi lucrătoare legală",
   "A", "PASS", "BERC, ferestre comparabile ale anului (20.11.2026, zi parțială, exclusă)", "stat_pack_ext.py (efort_aceeasi_perioada)", "stat_pack_ext.json", DATE_BERC,
   "Se compară doar aceeași perioadă a anului; nu se compară cu alte luni.",
   "Pe aceeași perioadă a anului, Registrul dă mai multe decizii ca în anii trecuți. Producția nu s-a prăbușit; cererile au crescut mai repede."),
 C("C07", "August finals vs June–July", f"≈{round(100*AUGR)}%", "% din nivelul iunie–iulie (finale stricte / zi lucrătoare legală)",
   "A", "PASS", "BERC; finale = admis, respins, renunțat; zile lucrătoare cu calendarul legal 2026", "reconcile_sources.py:main (august_ratio_strict_finals_per_legal_wd)", LC, DATE_BERC,
   "Definiție corectată la poarta v2 (înainte: împărțire la zile cu decizii, 0,918). O explicație posibilă sunt concediile; datele nu o măsoară direct.",
   f"În august s-au dat cu circa {100-round(100*AUGR)}% mai puține decizii pe zi lucrătoare decât în iunie–iulie."),
 C("C02", "Files per registrator per day vs a norm of 40", "≈25", "dosare/zi/registrator", "B", "FAIL",
   "aritmetică 4.176/165", "—", LC, DATE_BERC,
   "RETRAS (poarta M2): numitor nesigur (~91 la lucru), normă fără sursă, ton acuzator; plafonul per registrator e pe lista NU afirma.",
   "[NU SE PUBLICĂ]"),
 # ---------- wait times ----------
 C("C31", "Share decided within 1 working day: old platform vs crisis",
   f"{rd(V1['le1wd_pct'])}% → {rd(CR['le1wd_pct'],2)}%", "% din decizii", "A", "PASS", "BERC, calendar legal RO",
   "recompute_from_raw.py:windows", RC, DATE_BERC, "Platforma veche = apr. 2023–iul. 2024; criza = 1 aug.–20 nov. 2026.",
   f"Pe platforma veche, {rd(V1['le1wd_pct'])}% din dosare erau soluționate într-o zi lucrătoare. În criză, sub 1%."),
 C("C17", "Median wait on the old platform", f"{rd(R['platforma_veche_2023_iul2024']['median_wait'])}", "zile calendaristice",
   "A", "PASS", "BERC", "reconcile_sources.py:main", LC, DATE_BERC, "",
   f"Pe vechea platformă, un dosar aștepta în mod obișnuit {rd(R['platforma_veche_2023_iul2024']['median_wait'])} zile."),
 C("C18", "2024 new-portal launch: median wait and finals per day",
   f"{rd(R['colaps_portal_nou_2024']['median_wait'])} zile; {ro(R['colaps_portal_nou_2024']['finals_per_day'])}/zi", "zile; decizii/zi",
   "A", "PASS", "BERC (29 iul.–30 nov. 2024)", "reconcile_sources.py:main", LC, DATE_BERC,
   "Se raportează doar valorile; cauza nu e măsurată.",
   "După lansarea noului portal în 2024, s-au dat mai puține decizii pe zi și așteptarea a urcat la circa 12 zile; în decembrie a revenit la normal."),
 C("C19", "2025: median wait and finals per day",
   f"{rd(R['stabil_2025']['median_wait'])} zile; {ro(R['stabil_2025']['finals_per_day'])}/zi", "zile; decizii/zi",
   "A", "PASS", "BERC", "reconcile_sources.py:main", LC, DATE_BERC, "",
   f"În 2025, un dosar aștepta în mod obișnuit {rd(R['stabil_2025']['median_wait'])} zile."),
 C("C04", "Median wait by filing month May→Sep 2026 (decided dossiers only)", "5 / 5 / 7 / 19 / ≥39", "zile calendaristice",
   "A", "WARN", "BERC și portal, pe luna depunerii", "reconcile_sources.py:main", LC, DATE_BERC,
   "Septembrie e cenzurat: multe dosare din septembrie nu erau încă soluționate, deci valoarea reală e mai mare. Se spune «cel puțin».",
   "Pentru dosarele depuse în septembrie, așteptarea a fost de cel puțin 39 de zile, față de 5 zile în mai."),
 C("C05", "Wait growth May→September by filing month (lower bound)", "≥ ~7,5×", "ori", "A", "WARN", "BERC", "reconcile_sources.py:main", LC, DATE_BERC,
   "Derivat din C04, deci tot cenzurat: «cel puțin». Limita de jos (39 / 5) dă circa 7,6; estimarea Kaplan–Meier, circa 11.", "Așteptarea a crescut de peste șapte ori între mai și septembrie."),
 C("C14", "Median wait of modifications decided in the week of 16 Nov 2026", f"{rd(DW['CERERE265']['2026-11-16'])}", "zile calendaristice",
   "A", "PASS", "BERC (CERERE265 finale, după data deciziei)", "reconcile_sources.py:main", LC, DATE_BERC, "",
   f"Modificările soluționate în săptămâna 16–20 noiembrie au așteptat, în mod obișnuit, {rd(DW['CERERE265']['2026-11-16'])} zile."),
 C("C15", "Median wait of new registrations decided in the week of 16 Nov 2026", f"{rd(DW['INMATRIC265']['2026-11-16'])}", "zile calendaristice",
   "A", "PASS", "BERC (INMATRIC265 finale)", "reconcile_sources.py:main", LC, DATE_BERC, "",
   f"Firmele noi aprobate în aceeași săptămână au așteptat {rd(DW['INMATRIC265']['2026-11-16'])} zile."),
 C("C16", "Wait of decided modifications, week by week 28 Sep→16 Nov", f"{rd(DW['CERERE265']['2026-09-28'])} → {rd(DW['CERERE265']['2026-11-16'])}", "zile calendaristice",
   "A", "PASS", "BERC", "reconcile_sources.py:main", LC, DATE_BERC, "",
   "Așteptarea dosarelor soluționate a crescut în fiecare săptămână din octombrie și noiembrie."),
 C("C11", "Oct/Nov filing-month waits cannot be measured yet", "cenzurat", "—", "A", "WARN", "BERC (puține dosare decise)",
   "analyze_6month_trend.py", LC, DATE_BERC, "Se folosește în schimb așteptarea dosarelor decise pe săptămână (C14–C16).",
   "Pentru dosarele depuse în octombrie și noiembrie, timpul final nu se poate încă măsura."),
 C("C38", "Two-speed queue, decisions 2–19 Nov 2026: share decided within 14 days",
   f"{rd(TS['CERERE265']['share_le14d_pct'])}% modificări · {rd(TS['INMATRIC265']['share_le14d_pct'])}% înmatriculări", "% din decizii finale",
   "A", "PASS", "BERC", "reconcile_sources.py:main (two_speed_2_19_nov)", LC, DATE_BERC,
   "Cauza nu se vede în BERC (cereri mai simple sau priorități legale sunt plauzibile). NU se spune «favoritism» sau «sărit coada».",
   f"Unele dosare trec mult mai repede: {rd(TS['CERERE265']['share_le14d_pct'])}% din modificări au fost rezolvate în cel mult 14 zile, deși de obicei se așteaptă {ro(TS['CERERE265']['median_wait'])} de zile."),
 C("C12", "All judged dossiers follow the same chronological order", "—", "—", "B", "FAIL", "—", "—", LC, DATE_BERC,
   "RETRAS (poarta M2): echivalent «strict FIFO», pe lista NU afirma; contrazis de C38.", "[NU SE PUBLICĂ]"),
 # ---------- the two queues (tandem) ----------
 C("C28", "Official stock of unresolved requests (MJ note)", ro(MJ["nov06"]["total"]), "cereri", "C", "PASS",
   "Nota Ministerului Justiției, 6.11.2026", "tandem_bottleneck_analysis.py:mj_tandem_conservation", TB, DATE_MJ,
   "Cifră oficială preluată, nu recalculată.", f"La 6 noiembrie, Ministerul Justiției raporta {ro(MJ['nov06']['total'])} de cereri nesoluționate."),
 C("C29", "Of which not yet processed (Stage 1, operare)", f"{ro(MJ['nov06']['s1'])} ({rd(MJ['nov06']['s1_share_pct'])}%)", "cereri", "C", "PASS",
   "Nota MJ, 6.11.2026", "tandem_bottleneck_analysis.py:mj_tandem_conservation", TB, DATE_MJ, "Cifră oficială preluată.",
   f"Dintre ele, {ro(MJ['nov06']['s1'])} (circa jumătate) nu fuseseră încă prelucrate deloc."),
 C("C33", "Stock change 30 Oct→6 Nov: Stage 1 vs Stage 2", f"{ro(MJ['delta']['s1'])} / +{ro(MJ['delta']['s2'])}", "cereri în 5 zile lucrătoare",
   "C", "PASS", "Nota MJ (30.10 și 6.11) + identitatea de conservare", "tandem_bottleneck_analysis.py:mj_tandem_conservation", TB, DATE_MJ,
   "Bilanț pe două fotografii oficiale; nu arată ce s-a întâmplat între ele.",
   f"Într-o săptămână, coada de operare a scăzut cu {ro(-MJ['delta']['s1'])}, iar coada de la registrator a crescut cu {ro(MJ['delta']['s2'])}."),
 C("C34", "Operare outpaced soluționare by", f"≈{ro(CV['o1_premium_pct'])}%", "% (16–20% după convenție)", "B", "PASS",
   "Nota MJ + BERC 2–6 nov.", "tandem_bottleneck_analysis.py:conventions", TB, DATE_MJ,
   "Diferența variază între 16% și 20% după cum se numără deciziile.",
   "Operarea lucra cu circa 16–20% mai repede decât soluționarea. Blocajul principal e la registrator, dar operarea e aproape."),
 C("C06", "Portal sample: share of live judged dossiers at Stage 1", f"{rd(100*L['backlog_split_stage1'])}%", "% din dosarele în așteptare",
   "A", "PASS", "portal, eșantion de mențiuni/radieri", "analyze_portal_snapshot.py", PO, DATE_PORT,
   "Eșantion fără înmatriculările în curs; confirmă ordinul de mărime al cifrei oficiale (C29).",
   "În eșantionul nostru din portal, circa jumătate din dosarele în așteptare erau încă la operare."),
 C("C36", "Online filings outside office hours wait longer (same day, same county)", "+0,8 … +1,9", "zile (după definiția «în afara programului»)",
   "A", "WARN", "BERC, depuneri în afara programului vs în program", "tandem_bottleneck_analysis.py:online_vs_office_hours", TB, DATE_BERC,
   f"Sensibil la definiție: +{rd(onl_lo)} … +{rd(onl_hi)} în analiza noastră, +0,8 … +1,8 în recalculul independent. Semnul e același (online-ul nu e mai rapid); mărimea depinde de definiție.",
   "Cererile depuse online în afara programului nu trec mai repede: așteaptă chiar puțin mai mult. Online-ul nu ocolește operarea."),
 C("C32", "27 Apr 2026: share of finals decided within 2 calendar days, before→after",
   f"{rd(LE2['pre_1mar_26apr_pct'])}% → {rd(LE2['post_27apr_31jul_pct'])}%", "% din decizii finale cu așteptare ≤2 zile calendaristice (după data deciziei)",
   "A", "PASS", "BERC; ferestre 1.03–26.04 vs 27.04–31.07.2026", "reconcile_sources.py:main (le2d_share_27apr_by_decision_date)", LC, DATE_BERC,
   "Definiție corectată la poarta v2 (înainte: mediana pe județe, 13,4% → 0,96%). Scăderea apare în aproape toate județele. Cauza nu e documentată în date.",
   "Din 27 aprilie 2026, aproape niciun dosar nu mai e rezolvat în două zile, în aproape toate județele, cu luni înainte de valul de cereri."),
 # ---------- adjournments, rejections ----------
 C("C03", "Adjournments (amânări) per working day", f"≈{ro(round(L['adjournments_per_day'], -2))}", "amânări / zi lucrătoare",
   "A", "PASS", "BERC (sol = Amânat) + art. 106 Legea 265/2022", "reconcile_sources.py:main", LC, DATE_BERC,
   "Amânarea = termen de completare de cel mult 15 zile (art. 106); nu închide dosarul.",
   f"Pe lângă deciziile finale, se dau circa {ro(round(L['adjournments_per_day'], -2))} de amânări pe zi: solicitantul primește un termen de cel mult 15 zile să completeze dosarul."),
 C("C21", "Adjournments as share of all decisions", f"{rd(V1['aman_share_of_all_decisions_pct'])}% → {rd(CR['aman_share_of_all_decisions_pct'])}%", "% din toate actele",
   "A", "PASS", "BERC", "recompute_from_raw.py:windows", RC, DATE_BERC,
   "Ușor subestimat (~0,15 pp) din cauza unor pagini de amânări lipsă.", "Aproximativ una din cinci decizii e o amânare, la fel ca înainte de criză."),
 C("C37", "Adjourned dossiers, Nov 2026: filing→first adjournment; last adjournment→final",
   f"{rd(AM['app_to_first_am_med_d'])} / {rd(AM['last_am_to_res_med_d'])}", "zile (mediană)", "A", "PASS", "BERC (AUTO_AMANARI)",
   "tandem_bottleneck_analysis.py:auto_amanari_timing", TB, DATE_BERC, "",
   f"Un dosar amânat așteaptă circa {ro(AM['app_to_first_am_med_d'])} de zile până la prima amânare. După completare, decizia vine în circa {ro(AM['last_am_to_res_med_d'])} zile: nu se reia coada de la capăt."),
 C("C39", "Rejection rate: old platform vs crisis", f"{rd(V1['rej_pct'])}% → {rd(CR['rej_pct'])}%", "% din decizii finale",
   "A", "PASS", "BERC", "recompute_from_raw.py:windows", RC, DATE_BERC, "Nivelul era similar în 2025 și în prima jumătate a lui 2026: creșterea față de vechea platformă nu e specifică crizei.", "Aproximativ 1 din 12 dosare finale e respins în criză, față de 1 din 17 înainte."),
 C("C40", "Rejected firms that refile in the same category within a year",
   f"{rd(RF['no_empty_ids_same_category']['refiled_365d_pct'])}–{rd(RF['no_empty_ids_same_category_full_followup']['refiled_365d_pct'])}%", "% din respingeri",
   "A", "WARN", "BERC JSON brut (cu ID-ul firmei)", "check_refiling_rate.py · ledger RHO-78 (WARN)", RF_, DATE_BERC,
   "WARN în ledger-ul verificat (RHO-78): «redepune» = orice cerere ulterioară de același tip a aceleiași firme; arhiva tabelară nu are ID-ul firmei, calculul cere JSON-ul brut.",
   "Circa 8 din 10 firme respinse depun din nou în același an: o respingere înseamnă de obicei încă un dosar în coadă."),
 # ---------- demand ----------
 C("C47", "Daily intake (MJ): H1 2026 vs Aug–Oct 2026", f"{ro(MJ_IN0)} → {ro(MJ_IN1)} (+{round(100*(MJ_IN1/MJ_IN0-1))}%)", "cereri / zi", "C", "PASS",
   "Nota MJ, 6.11.2026 (citată în FAPTE_VERIFICATE §3)", "FAPTE_VERIFICATE_PENTRU_VIDEO_SI_RAPORT.md §3", TB, DATE_MJ,
   "Cifră oficială preluată; definiția «intrări» aparține MJ.", "Ministerul raportează că cererile zilnice au crescut cu circa jumătate, de la 4.533 la 6.931 pe zi."),
 C("C48", "MJ 'solutions' match BERC only if adjournments are counted", "4.912/5.098 vs 4.825/5.041", "pe zi (sept./oct.)", "C", "WARN",
   "Nota MJ vs BERC", "verify_v2.py → verify_v2_ledger.csv CLAIM-24 (EXT/WARN)", "verify_v2_ledger.csv", DATE_MJ,
   "Diferență de definiție, nu de date: se reproduce doar dacă amânările sunt numărate drept soluționări.",
   "Cifrele de «soluționări» ale Ministerului includ și amânările; de aceea par mai mari decât deciziile finale."),
 C("C22", "Peak weekly filing rate vs May–July (all request types)", "≈1,7×", "ori", "B", "WARN",
   "portal (creșterea numărului de înregistrare)", "onrc_queue_model.py / model_inputs_v2.json", PO, DATE_PORT,
   "Estimare din eșantion; include toate tipurile de cereri, nu doar cele supuse soluționării.",
   "În săptămâna de vârf din septembrie s-au depus de aproape două ori mai multe cereri decât într-o săptămână de vară."),
 # ---------- law & directive ----------
 C("C23", "Legal deadline for deciding a registration request", "1", "zi lucrătoare", "C", "PASS",
   "Legea 265/2022 art. 105 alin. (1) și art. 109 — forma consolidată, legislatie.just.ro (citită la 22.11.2026)", "verificare manuală pe text", LC, "22.11.2026",
   "Textul a fost verificat pe legislatie.just.ro la 22.11.2026 (forma consolidată); o versiune anterioară a raportului folosise extrasul publicat de ONRC.",
   "Legea cere ca registratorul să soluționeze cererea într-o zi lucrătoare de la înregistrare."),
 C("C41", "EU Directive 2017/1132 art. 13g(7): J first-pass admissions decided 1–20 Nov over 10 working days",
   f"{rd(EU['gt10'])}% peste 10 zile lucrătoare", "% din înmatriculările J admise din prima, decise 1–20.11.2026 (n ≈ 3.500)", "A", "PASS", "BERC + Directiva (UE) 2017/1132 art. 13g alin. (7)",
   "recompute_from_raw.py:eu_directive", RC, DATE_BERC,
   "Datele nu disting constituirile online cu model standard; NU se dă un «număr de încălcări».",
   f"{rd(EU['gt10'])}% dintre firmele noi admise fără amânare în noiembrie au așteptat peste 10 zile lucrătoare de la înregistrare; pragul european de 5/10 zile se aplică doar constituirilor online."),
 # ---------- OUG (audited model, intervals) ----------
 C("C42", "Audited model, June 2028: status quo", f"≈{ro(OG['referinta']['current_median'])} ({ro(OG['referinta']['current_p10_p90'][0])}–{ro(OG['referinta']['current_p10_p90'][1])})", "zile (mediană, interval p10–p90)",
   "B", "PASS", "model de coadă verificat", "rerun_oug_current.py / audit_forecast.py", OGF, DATE_BERC,
   "Scenariu: ±5% în capacitate mută rezultatul între ~102 și ~174 de zile. Se spune ca ordin de mărime.",
   "Fără măsuri, modelul arată o așteptare de ordinul a patru luni în iunie 2028 (interval larg)."),
 C("C43", "Audited model, June 2028: full OUG draft", f"≈{ro(OG['oug_central']['current_median'])} ({ro(OG['oug_central']['current_p10_p90'][0])}–{ro(OG['oug_central']['current_p10_p90'][1])})", "zile",
   "B", "PASS", "model de coadă verificat", "rerun_oug_current.py / audit_forecast.py", OGF, DATE_BERC,
   f"Scenariu, interval larg. Câștig median pe aceleași simulări: ≈{ro(float(OSC[('oug_central','2028-06-30')]['median_saved']))} zile. NU se dă procentul de «șanse».",
   "Cu proiectul OUG, modelul arată o îmbunătățire, dar așteptarea rămâne de ordinul a trei luni: proiectul singur nu readuce termenul la câteva zile."),
 C("C44", "Audited model, June 2028: only Art. III — gain on the same simulations", f"câștig ≈{ro(float(OSC[('doar_art_iii','2028-06-30')]['median_saved']))} zile", "zile câștigate (mediana diferențelor pe aceleași simulări)",
   "B", "PASS", "model de coadă verificat", "audit_data/oug_2026/scenarios.csv (median_saved)", "scenarios.csv", DATE_BERC,
   "Scenariu. NU se pun alăturat medianele 136 și 132 (s-ar citi «4 zile»); câștigul corect e pe aceleași simulări. Art. III se aplică după optimizarea IT (Art. IV).",
   "Doar transferul unor acte administrative (Art. III) schimbă foarte puțin. Efectul vine mai ales din capacitatea suplimentară de soluționare."),
 C("C35", "Tandem model: moving staff 1:1 from operare to soluționare (Art. I)",
   f"optim ≈{ro(CV['optimal_shift_delta_wd'])}/zi; câștig zero la ≈{ro(CV['o1_minus_o2_wd'])}/zi", "dosare / zi lucrătoare mutate",
   "B", "PASS", "model în tandem verificat (Lean T13c)", "tandem_bottleneck_analysis.py:conventions", TB, DATE_MJ,
   "Condiționat de ipoteza 1:1 și de ancora 2–6 nov.; nu e textul OUG, ci un mecanism.",
   "Dacă juriștii delegați sunt luați din operare, câștigul are o limită. Peste un anumit prag, mutarea scade producția totală."),
 # ---------- cross-validation & county ----------
 C("C09", "BERC vs portal: monthly medians (May–Sep) agree; modifications throughput differs", "5/5/7/19/39 pe ambele; debit 16%", "zile; %",
   "A", "WARN", "BERC + portal", "reconcile_sources.py:main", LC, DATE_BERC,
   "Ambele surse măsoară doar dosarele deja soluționate, deci acordul nu elimină cenzurarea.",
   "Două surse independente — buletinul oficial și portalul — dau aceleași mediane lunare."),
 C("C10", "County bottleneck classification (portal sample)", "—", "—",
   "A", "FAIL", "—", "—", PO, DATE_PORT,
   "RETRAS (revizuirea pe profiluri): clasificare pe oficii din eșantioane de 2–33 de dosare; nu se publică pe oficii.", "[NU SE PUBLICĂ]"),
 C("C49", "Median wait of decisions 1–18 Nov 2026 by county: lowest vs highest",
   f"{rd(_CT.loc[_cmin,'median_nov'])}–{rd(_CT.loc[_cmax,'median_nov'])}", "zile calendaristice (interval între cele 42 de județe)",
   "A", "PASS", "BERC pe oficiul de depunere", "audit_atlas.py → county_indicators.csv", "county_indicators.csv", DATE_BERC,
   f"Județul = oficiul de depunere; cel mai mic are ~{int(round(_CT.n_nov.min(), -1))} decizii în fereastră. Clasamentul pe oficii arată unde apar diferențele, nu performanța personalului.",
   "Așteptarea e aproape aceeași în toată țara: coada e practic națională, nu o problemă a unui județ anume."),
 C("C50", "Share of decisions that are CAEN-only updates (PDF bulletin sample)",
   f"≈{round(CAEN_PCT)}% (IC 95%: {rd(CAEN_PCT-1.96*CAEN_SE)}–{rd(CAEN_PCT+1.96*CAEN_SE)}%)", f"% din decizii · eșantion de {CAEN_N} buletine PDF",
   "A", "PASS", "buletine BERC PDF, eșantion pe clustere", "verify_v2.py → ledger CLAIM-16 (corectat)", "verify_v2_ledger.csv", "oct. 2026",
   f"Eșantion pe clustere (efect de design ≈{rd(CAEN_DEFF, 2)}). Arată componența, nu volumul de muncă pe dosar. Au fost descărcate {NPDF_2026} de buletine PDF din 2026; eșantionul analizat cuprinde {CAEN_N} dintre ele.",
   f"Circa un sfert din decizii sunt simple actualizări ale codului CAEN."),
 C("C51", "Staff posts: approved / funded / occupied → funded but unoccupied",
   f"{ro(POST[0])} / {ro(POST[1])} / {ro(POST[2])} → {POST[1]-POST[2]} neocupate", "posturi (toate funcțiile ONRC)",
   "C", "PASS", "Ministerul Justiției (fundamentarea proiectului OUG), preluat în evaluarea OUG", "build_oug_review.py", "build_oug_review.py", "nov. 2026",
   "Cifră preluată, nivel C. Diferența de 134 e aritmetică și presupune definiții aliniate între cele trei cifre.",
   f"Din {ro(POST[1])} de posturi finanțate, {POST[1]-POST[2]} nu sunt ocupate."),
 *[C(cid, f"Audited solution package {pid}, wait in June 2028", f"≈{ro(float(SOLS[pid]['wait_jun28_p50']))} ({'≤3' if float(SOLS[pid]['wait_jun28_p10']) <= 3 else ro(float(SOLS[pid]['wait_jun28_p10']))}–{ro(float(SOLS[pid]['wait_jun28_p90']))})",
     "zile (mediană, interval p10–p90)", "B", "WARN", "model de coadă verificat · " + _re.sub(r"\s*\([^)]*u/zi\)", "", SOLS[pid]["package"].split(":", 1)[1]).strip(),
     "steelman_and_solutions_engine.py → solutions_feasibility_and_simulations.csv", "solutions_feasibility_and_simulations.csv", DATE_BERC,
     note + " Efectele măsurilor sunt ipoteze de intrare (literali), nu măsurători.", pub)
   for cid, pid, note, pub in [
     ("C52", "P3", "Scenariu fragil: depinde de ocuparea a 40% din posturile finanțate.",
      "Un pachet cu OUG extins și ocuparea a 40% din posturile vacante finanțate ar coborî așteptarea, în model, la ordinul a cinci săptămâni, cu un interval larg."),
     ("C53", "P4", "Scenariu: conversie CAEN 1-la-1 prin lege (fără IT), ipoteza de −75% din cererile CAEN.",
      "Doar decongestionarea legislativă (conversia CAEN 1-la-1 și eșalonarea) ar reduce așteptarea, în model, la ordinul a două-trei luni."),
     ("C54", "P5", f"Foarte fragil: la o singură schimbare plauzibilă (CAEN −50%, prelungirea OUG, ancoră +5%), câștigul scade la {P5_FRAG[0]}–{P5_FRAG[-1]} de zile. NU se spune «economisește ≥100 de zile».",
      "Un pachet minim realist (OUG prelungit, conversie CAEN, eșalonare, triaj) ar coborî așteptarea, în model, la ordinul a trei săptămâni; rezultatul e sensibil la ipoteze.")]],
 C("C55", "Extra capacity needed to return to ~3 days through staffing alone",
   f"+{ro(U_LO)}–{ro(U_HI)} unități/zi (≈{FTE_LO}–{FTE_HI} FTE)", "unități de capacitate pe zi lucrătoare",
   "B", "WARN", "model verificat (matricea steelman, S11)", "steelman_and_solutions_engine.py → steelman_counterarguments_matrix.csv", "steelman_counterarguments_matrix.csv", DATE_BERC,
   "Ținta: coadă practic goală deja la sfârșitul lui 2027 și menținută în iunie 2028, în majoritatea variantelor (mai strictă decât grila C65, care privește doar iunie 2028). Conversia în FTE presupune circa 25 de dosare pe zi pe post, o ipoteză de model; alte scenarii folosesc alte ipoteze. Nu e o normă și nu măsoară performanța individuală.",
   f"Doar prin personal, revenirea la circa 3 zile ar cere o capacitate suplimentară de {ro(U_LO)}–{ro(U_HI)} de dosare pe zi, adică ordinul a 80–100 de posturi cu normă întreagă."),
 C("C56", "Tandem, wave of 6.931/day: Stage-2-only expansion vs balanced expansion (120 working days)",
   f"doar etapa 2: registratori fără dosare {W1['starved_days']} zile, operare ≈{ro(round(W1['end_s1'], -3))}; echilibrat: total ≈{ro(round(W2['end_total'], -3))} vs ≈{ro(round(W0['end_total'], -3))} fără măsuri",
   "cereri în stoc după 120 de zile lucrătoare", "B", "PASS", "model în tandem verificat (W0/W1/W2)", "tandem_bottleneck_analysis.py:tandem_scenarios_distinct_anchor", TB, DATE_MJ,
   "Scenariu condiționat de valul de 6.931/zi (media MJ aug.–oct.) și de ancora 2–6 nov.",
   "Dacă se întărește doar etapa registratorilor, aceștia rămân fără dosare, iar coada de operare crește. Doar întărirea ambelor etape reduce stocul total."),
 C("C57", "Rejection share of final decisions, H2 2025 (fast regime) vs now",
   f"{rd(L['rejection_share_strict_finals']['H2_2025']['respins_pct'])}% respingeri, mediana {rd(L['rejection_share_strict_finals']['H2_2025']['median_wait'])} zile (S2 2025) · {rd(L['rejection_share_strict_finals']['oct_1_nov_20_2026']['respins_pct'])}% acum",
   "% respinse din deciziile finale (admis, respins, renunțat), CERERE265 + INMATRIC265; mediana așteptării în zile",
   "A", "PASS", "BERC; S2 2025 = 1.07–31.12.2025; acum = 1.10–20.11.2026", "reconcile_sources.py:main (rejection_share_strict_finals)", LC, DATE_BERC,
   f"Pe tot anul 2025: {rd(L['rejection_share_strict_finals']['year_2025']['respins_pct'],2)}%. Comparație de cote, nu cauzalitate; tipurile de cereri diferă între perioade.",
   "În a doua jumătate a lui 2025, când dosarele se rezolvau în circa o zi și jumătate, respingerile erau aproape la fel de multe ca acum: creșterea respingerilor nu explică, singură, criza."),

 # ---------- forecast and risk (audited engine audit_forecast.py; grid = same engine) ----------
 C("C58", "Status quo: wait of a file filed now (23.11.2026)", f"≈{ro(float(TR0['median']))} ({ro(float(TR0['p10']))}–{ro(float(TR0['p90']))})",
   "zile calendaristice (mediană, p10–p90) pentru un dosar depus la acea dată", "B", "WARN", "model de coadă verificat, scenariul fără măsuri",
   "audit_forecast.py / audit_oug.py → oug_2026/trajectory.csv", "trajectory.csv", DATE_BERC,
   "Prognoză, nu măsurătoare. E așteptarea unui dosar depus ACUM, diferită de așteptarea dosarelor soluționate acum (C14).",
   "Un dosar depus acum ar aștepta, în modelul fără măsuri, de ordinul a două luni și jumătate."),
 C("C59", "Status quo: mid-2027 wait (30.06.2027)", osc("referinta", "2027-06-30"), "zile (mediană, p10–p90)",
   "B", "WARN", "model de coadă verificat", "oug_2026/scenarios.csv", "scenarios.csv", DATE_BERC,
   "Prognoză condiționată de valurile de cereri anunțate (CAEN, capital, fiscal).",
   "Fără măsuri, la mijlocul lui 2027 așteptarea ar urca la ordinul a patru-cinci luni."),
 C("C60", "Status quo: peak wait 2026–2028", osc("referinta", "peak"), "zile (mediană, p10–p90)",
   "B", "WARN", "model de coadă verificat", "oug_2026/scenarios.csv", "scenarios.csv", DATE_BERC,
   "Vârful fiecărei simulări, apoi mediana și intervalul lor. Momentul vârfului variază între simulări.",
   "În cazul central, vârful așteptării ar depăși cinci luni."),
 C("C61", "OUG delivery variants, June 2028: weak / strong", f"slab {osc('oug_redus', '2028-06-30')}, câștig ≈{ro(float(OSC[('oug_redus','2028-06-30')]['median_saved']))} · ridicat {osc('oug_ridicat', '2028-06-30')}, câștig ≈{ro(float(OSC[('oug_ridicat','2028-06-30')]['median_saved']))}",
   "zile (mediană, p10–p90); câștig = mediana diferențelor pe aceleași simulări", "B", "WARN", "model de coadă verificat; livrare OUG: 5 / 30 FTE net (policy_inputs.csv)",
   "oug_2026/scenarios.csv", "scenarios.csv", DATE_BERC,
   "Ipoteze de livrare, nu măsurători. «≤3» = limita metricii (coadă goală), nu «3 zile».",
   "Rezultatul OUG depinde mult de cât personal net ajunge efectiv la soluționare."),
 C("C62", "Status quo: stock at end of June 2028", f"≈{ro(round(float(_G1['stock_june2028_p50']), -3))} (săpt. 26.06: {ro(round(float(FTR['stock_p10']), -3))}–{ro(round(float(FTR['stock_p90']), -3))})",
   "dosare în așteptare, echivalent dosar standard (mediană, p10–p90)", "B", "WARN", "motorul de prognoză verificat",
   "audit_forecast.py → forecast_trajectories.csv", "forecast_trajectories.csv", DATE_BERC,
   "Unități de muncă (dosarele CAEN cântăresc mai puțin), nu număr de cereri; mediana la 30.06.2028, ca în tabelele de prognoză; intervalul p10–p90 e cel al ultimei săptămâni din iunie. Se compară doar cu punctul de pornire al modelului (≈200.000 dosare-echivalent), nu cu stocul oficial în cereri. Interval foarte larg.",
   "Fără măsuri noi, volumul de muncă în așteptare s-ar putea dubla față de punctul de pornire al modelului."),
 C("C63", "Grid: outflow ±10% with unchanged inflow, June 2028", f"+10% → ≈{gw(0, 10)} · −10% → ≈{gw(0, -10)} (față de ≈{gw(0, 0)})",
   "zile (mediană, iunie 2028)", "B", "WARN", "grilă pe motorul verificat (multiplicatori pe intrări și ieșiri totale)",
   "forecast_grid.py → out/forecast_grid.json", "forecast_grid.json", DATE_BERC,
   "Multiplicatori aplicați de la 19.11.2026 pe TOATE intrările (inclusiv valurile) și pe TOATĂ capacitatea.",
   "O schimbare de doar 10% în viteza de soluționare mută așteptarea din 2028 cu două-trei luni, în ambele sensuri."),
 C("C64", "Grid: inflow and outflow growing together", f"+10/+10 → ≈{gw(10, 10)} · +20/+20 → ≈{gw(20, 20)} · +30/+30 → ≈{gw(30, 30)}",
   "zile (mediană, iunie 2028)", "B", "WARN", "grilă pe motorul verificat", "forecast_grid.py → out/forecast_grid.json", "forecast_grid.json", DATE_BERC,
   "Arată că raportul dintre ieșiri și intrări decide coada, nu nivelul lor absolut.",
   "Dacă cererile și capacitatea cresc în același ritm, așteptarea scade doar puțin."),
 C("C65", "Grid: outflow increase needed with unchanged inflow", f"+20% → ≈{gw(0, 20)} (p90 ≈{gw(0, 20, 'june2028_p90')}) · +30% → {gw(0, 30)} (p90 ≈{gw(0, 30, 'june2028_p90')}) · +40% → {gw(0, 40)} (p90 {gw(0, 40, 'june2028_p90')})",
   "zile (iunie 2028; mediană și cazul nefavorabil p90)", "B", "WARN", "grilă pe motorul verificat",
   "forecast_grid.py → out/forecast_grid.json", "forecast_grid.json", DATE_BERC,
   "«≤3» = limita metricii (coadă goală). Creșterea e față de capacitatea modelului, din noiembrie 2026, fără întârziere de implementare.",
   "La cereri neschimbate, o capacitate cu circa o treime mai mare ar goli coada până la mijlocul lui 2028."),
 C("C66", "Grid: inflow +10% with unchanged outflow, June 2028", f"≈{gw(10, 0)} (p90 ≈{gw(10, 0, 'june2028_p90')})",
   "zile (mediană, p90)", "B", "WARN", "grilă pe motorul verificat", "forecast_grid.py → out/forecast_grid.json", "forecast_grid.json", DATE_BERC,
   "Scenariu; +10% pe toate intrările, inclusiv pe valuri.",
   "Cu 10% mai multe cereri și aceeași capacitate, așteptarea ar ajunge la ordinul a șapte luni."),
 C("C67", "Model 2027: incoming workload vs capacity", f"≈{rd(RATIO27, 2)}", "raport între munca intrată și capacitate (2027, mediană)",
   "B", "WARN", "motorul de prognoză verificat (intrări totale / capacitate pe zi lucrătoare)", "forecast_grid.py (reference)", "forecast_grid.json", DATE_BERC,
   "Unități de muncă (dosar standard), mediană pe simulări.",
   f"În 2027, în model, intră cu circa {round(100*(RATIO27-1))}% mai multă muncă decât poate ieși: de aceea coada crește fără măsuri."),
 C("C68", "Days avoided at the peak if a wave did not exist: CAEN / capital / fiscal",
   " · ".join(f"≈{ro(float(WAV[k]['peak_days_saved_p50']))} ({ro(float(WAV[k]['peak_days_saved_p10']))}–{ro(float(WAV[k]['peak_days_saved_p90']))})"
              for k in ("fara_caen_suplimentar", "fara_capital_suplimentar", "fara_sarcina_fiscala_suplimentara")),
   "zile evitate la vârf (CAEN · capital · fiscal; mediană, p10–p90)", "B", "WARN", "motorul de prognoză verificat",
   "audit_forecast.py → forecast_wave_sensitivity.csv", "forecast_wave_sensitivity.csv", DATE_BERC,
   "Contrafactual: valul eliminat complet. Arată unde e pârghia, nu ce e realizabil.",
   "Valul de actualizări CAEN cântărește cel mai mult: fără el, vârful ar fi cu peste două luni mai mic."),
 C("C69", "Strongest drivers of the peak (Spearman): recurring inflow / solving rate / CAEN wave",
   " / ".join(rd(float(r["spearman_peak"]), 2).replace("-", "−") for r in SEN[:3]), "corelație de rang cu vârful așteptării",
   "B", "PASS", "motorul de prognoză verificat (2.000 de simulări)", "audit_forecast.py → forecast_sensitivity.csv", "forecast_sensitivity.csv", DATE_BERC,
   "Corelație în model, nu cauzalitate observată. Arată ce incertitudine contează cel mai mult.",
   "Trei lucruri decid vârful: câte cereri obișnuite vin, câte dosare se soluționează pe zi și cât de mare e valul CAEN."),
 C("C70", "Backtest of the solving-rate input, 9 four-week windows (Mar–Nov 2026)",
   f"eroare absolută medie ≈{rd(CBT_MAPE)}% · real ≥ prognozat în {CBT_UP} din {len(CBT_ERR)} · maxim {pm(max(CBT_ERR, key=abs))}%",
   "% abatere observat față de prognozat", "B", "PASS", "BERC, test pe ferestre succesive", "audit_forecast.py → forecast_capacity_backtest.csv",
   "forecast_capacity_backtest.csv", DATE_BERC,
   "Eroarea medie e raportată la valoarea observată (definiția motorului); etichetele din figură sunt abateri față de prognoză. Validează ritmul de soluționare (intrarea principală), nu prognoza pe 2028 în ansamblu. Abaterea mare din septembrie = accelerarea neanticipată. Test în timp real: ultimele zile ale fiecărei origini sunt incomplete din cauza întârzierii publicării; pe datele complete, aceeași regulă supraestimează ritmul în majoritatea ferestrelor. «7 din 9» e valabil pentru regula de 12 zile folosită de motor; celelalte două reguli testate dau 5 și 3 din 9. Nu e semnificativ statistic (test al semnului, p ≈ 0,09). O deplasare sistematică de circa +5% a ritmului ar scurta prognoza centrală.",
   "Ritmul de soluționare se prognozează cu o eroare de circa 5% pe patru săptămâni, într-un test în timp real (doar cu deciziile publicate la fiecare dată)."),
 C("C71", "Seasonality of filings relative to November: Jan–Mar / Jul–Aug",
   f"{pm((min(MPR[m] for m in (1, 2, 3)) - 1) * 100)}…{pm((max(MPR[m] for m in (1, 2, 3)) - 1) * 100)}% · {pm((min(MPR[m] for m in (7, 8)) - 1) * 100)}…{pm((max(MPR[m] for m in (7, 8)) - 1) * 100)}%",
   "% cereri pe zi față de noiembrie", "B", "PASS", "BERC, profil lunar estimat", "audit_forecast.py → forecast_monthly_profile.csv",
   "forecast_monthly_profile.csv", DATE_BERC,
   "Profil mediu din anii anteriori, fără valurile excepționale. Vara (iul.–aug.) e mai plată în model decât în date: în 2025, cererile de vară au fost cu circa 10% sub noiembrie, nu cu 5–6%; modelul presupune deci mai multe cereri vara, adică e ușor pesimist pentru vara lui 2027.",
   "Începutul anului aduce în mod obișnuit cu circa o zecime mai multe cereri decât noiembrie."),
 C("C72", "Grid: peak wait with outflow +20% / +40% (inflow unchanged)", f"+20% → ≈{gw(0, 20, 'peak_p50')} · +40% → ≈{gw(0, 40, 'peak_p50')} (față de ≈{gw(0, 0, 'peak_p50')})",
   "zile (vârful 2026–2028, mediană)", "B", "WARN", "grilă pe motorul verificat", "forecast_grid.py → out/forecast_grid.json", "forecast_grid.json", DATE_BERC,
   "Capacitatea crescută din 19.11.2026; valul CAEN de la începutul lui 2027 produce totuși un vârf.",
   "Chiar și cu o capacitate mult mai mare, valul de la începutul lui 2027 ar produce un vârf de ordinul a două luni."),
 # ---------- advanced statistics (stat_pack.py)
 C("C73", "September 2026 filing cohort: median among resolved only vs Kaplan–Meier (portal sample)",
   f"{ro(KM9['mediana_naiva_doar_rezolvate'])} (doar rezolvate) → cel puțin ≈{ro(KM9['mediana_KM'])} (Kaplan–Meier, limită de jos)", f"zile (eșantion myportal, n = {KM9['n_portal']}, {rd(KM9['rezolvate_pct'])}% rezolvate)",
   "B", "WARN", "eșantion myportal; cenzurare la 21.11.2026", "stat_pack.py (cohorte_KM_portal)", "stat_pack.json", DATE_PORT,
   "Cenzurarea e informativă: cine a depus mai târziu așteaptă mai mult și e urmărit mai puțin (mediana pe săptămâni crește 28 → 35 → 50 de zile, iar ultimele săptămâni nu se pot încă măsura). Mediana lunară e deci tot o limită de jos.",
   "Pentru dosarele depuse în septembrie, așteptarea obișnuită e de cel puțin circa 58 de zile, iar pentru cele depuse spre sfârșitul lunii nu se poate încă măsura."),
 C("C74", "Final decisions 1–20 Nov 2026 with a prior adjournment of the same dossier",
   f"≈{round(100*ADJ['share_with_adjournment'])}% (mediana: {rd(ADJ['wait_med_with'])} vs {rd(ADJ['wait_med_without'])} zile)", "% din deciziile finale; zile de așteptare cu / fără amânare",
   "A", "WARN", "BERC, legătură prin număr și dată de depunere", "stat_pack.py (cicluri_amanare_nov2026)", "stat_pack.json", DATE_BERC,
   "Legătura prin număr și dată coincide cu legătura exactă prin identificatorul cererii din datele brute.",
   "Circa unul din cinci dosare soluționate în noiembrie fusese amânat înainte; aproape niciunul de mai multe ori."),
 C("C75", "County medians: dispersion and persistence 2025 → Nov 2026",
   f"CV {rd(CDS['cv_pct'])}% · Spearman 2025 vs nov. {rd(CDS['spearman_2025_vs_nov'], 2).replace('-', '−')} (IC 95%: {rd(RHO_LO, 2).replace('-', '−')}…{rd(RHO_HI, 2)})", "coeficient de variație; corelație de rang între județe",
   "A", "PASS", "BERC, 42 de oficii", "stat_pack.py (county_dispersion)", "stat_pack.json", DATE_BERC,
   "Ordinea oficiilor din 2025 nu prezice ordinea din 2026; regimul s-a schimbat (coadă națională), iar medianele nu sunt standardizate pe tipul cererii. Nu dovedește că diferențele din 2025 erau zgomot.",
   "Ordinea oficiilor din 2025 nu prezice ordinea din 2026, iar diferențele de azi sunt mici: nu susțin un clasament."),
 C("C76", "Little's law check, 2–20 Nov 2026: decisions per working day × mean wait vs official stock",
   f"≈{ro(round(LIT['L_implied'], -3))} vs {ro(LIT['L_official_MJ'])}", "dosare (stoc implicat vs stoc oficial MJ)",
   "B", "WARN", "BERC + Nota MJ", "stat_pack.py (little)", "stat_pack.json", DATE_BERC,
   "Legea lui Little cere un sistem staționar; coada crește, iar stocul oficial include și dosarele încă la operare. Se folosește doar ca verificare de ordin de mărime.",
   "Un calcul de tip Little dă un stoc de același ordin de mărime cu cel oficial, dar mai mic; nu e un estimator valid într-o coadă care crește."),
 C("C77", "Bootstrap 95% interval for the median wait of modifications decided 16–20 Nov",
   f"{rd(BTS['ci95'][0], 2)}–{rd(BTS['ci95'][1], 2)}", f"zile (n = {ro(BTS['n'])}, 2.000 de reeșantionări)",
   "A", "WARN", "BERC", "stat_pack.py (bootstrap_C14)", "stat_pack.json", DATE_BERC,
   "BERC conține toate deciziile (recensământ), deci mediana nu are eroare de eșantionare; intervalul bootstrap iid ignoră gruparea pe zile și loturi și nu trebuie citit ca precizie. Incertitudinea reală vine din definiții (C07, C32, C36).",
   "Cifra de 57 de zile vine din toate deciziile, nu dintr-un eșantion; ce o poate schimba e definiția, nu întâmplarea."),
 C("C78", "Publication lag in the bulletin (2026): median / p99", f"{rd(LAG26['p50'], 2)} / {rd(LAG26['p99'], 2)}", "zile între decizie și publicare",
   "A", "PASS", "BERC", "stat_pack.py (intarziere_publicare)", "stat_pack.json", DATE_BERC,
   "Măsoară întârzierea buletinului, nu a deciziei.",
   "Deciziile apar în buletin, în mod obișnuit, în mai puțin de o zi; datele sunt aproape în timp real."),
 # ---------- work effort (system level; stat_pack_ext.py)
 C("C79", "All decisions issued (finals + adjournments) per legal working day, 1 Oct–19 Nov (last complete day), 2023 → 2026",
   f"{ro(EAP[2023]['decizii_pe_zi_lucr'])} → {ro(EAP[2026]['decizii_pe_zi_lucr'])} (+{round(EAP[2026]['fata_de_2023_pct'])}%)", "decizii / zi lucrătoare legală",
   "A", "PASS", "BERC, aceeași perioadă a fiecărui an", "stat_pack_ext.py (efort_aceeasi_perioada)", "stat_pack_ext.json", DATE_BERC,
   "Volum al sistemului, nu productivitate individuală. Circa un sfert din decizii sunt actualizări CAEN simple (C50).",
   f"În aceeași perioadă a anului, Registrul emite cu circa {round(EAP[2026]['fata_de_2023_pct'])}% mai multe decizii pe zi lucrătoare decât în 2023."),
 C("C80", "Total decisions issued per year: 2025 / 2026 (until 20 Nov)", f"{ro(EAN[2025]['decizii_total'])} / {ro(EAN[2026]['decizii_total'])}",
   "decizii (finale + amânări)", "A", "PASS", "BERC", "stat_pack_ext.py (efort_anual)", "stat_pack_ext.json", DATE_BERC,
   "Include amânările: muncă efectuată care nu închide dosarul.",
   "Registrul a emis peste un milion de decizii în 2025 și aproape la fel de multe în 2026, până la 20 noiembrie."),
 C("C81", "Decisions time-stamped after 16:00 or before 08:00 on working days (2023 → 2026); decisions on weekends/holidays",
   f"{rd(EAF[2023]['pondere_dupa_16_sau_inainte_8_pct'])}% → {rd(EAF[2026]['pondere_dupa_16_sau_inainte_8_pct'])}% · în zile nelucrătoare: {EAF[2026]['decizii_in_zile_nelucratoare']} decizii în 2026",
   "% din decizii; număr", "A", "WARN", "BERC, marca temporală a deciziei", "stat_pack_ext.py (efort_in_afara_programului)", "stat_pack_ext.json", DATE_BERC,
   "Marca temporală e cea a sistemului; nu dovedește ore suplimentare individuale. Practic nu se emit decizii în weekend.",
   "Circa una din zece decizii poartă o oră de după program; în weekend practic nu se emit decizii."),
 C("C82", "Adjournments in 2026: count and share of all decisions", f"{ro(EAN[2026]['amanari'])} ({rd(EAN[2026]['pondere_amanari_pct'])}%)",
   "amânări; % din toate deciziile", "A", "PASS", "BERC", "stat_pack_ext.py (efort_anual)", "stat_pack_ext.json", DATE_BERC,
   "Fiecare amânare e muncă de analiză care nu apare ca «soluționare» în cifrele de decizii finale.",
   "Circa una din cinci decizii este o amânare: muncă făcută care nu închide dosarul și nu apare în cifrele de soluționări finale."),
 C("C83", "Budget of the draft OUG (Ministry of Justice substantiation note)", _re.search(r'budget_ron_est="([^"]*mil.[^"]*)"', open(PP / "steelman_and_solutions_engine.py", encoding="utf-8").read()).group(1).replace(" RON", " lei"),
   "lei", "C", "PASS", "Ministerul Justiției, nota de fundamentare a proiectului OUG (18.11.2026)", "build_oug_review.py (calcul reprodus)", "build_oug_review.py", "nov. 2026",
   "Cifră preluată; calculul bugetar a fost reprodus în evaluarea OUG. Fără posturi noi.",
   "Proiectul de OUG costă circa 5,76 milioane de lei și nu creează posturi noi."),
 C("C84", "Median wait of ALL final decisions (strict, all categories), 1–20 Nov 2026", f"≈{rd(NOVALL['W_med'])}", "zile calendaristice (de la înregistrare la decizie, inclusiv completările după amânare)",
   "A", "PASS", "BERC, toate categoriile, finale stricte", "stat_pack.py (serie_lunara)", "stat_pack.json", DATE_BERC,
   "Include înmatriculările, care așteaptă mai puțin; de aceea e sub cifra pentru modificări (C14).",
   "Pentru toate deciziile finale din 1–20 noiembrie, așteptarea obișnuită a fost de circa 50 de zile."),
 C("C85", "Official total stock, 30 Oct → 6 Nov 2026", f"{ro(au_prev)} → {ro(au_cur)} ({ro(au_cur - au_prev).replace('-', '−')})", "cereri nesoluționate",
   "C", "PASS", "Nota MJ (30.10 și 6.11.2026)", "build_oug_review.py / oug_2026/audit.json", "build_oug_review.py", "nov. 2026",
   "O singură săptămână nu arată tendința; așteptarea dosarelor soluționate a crescut în continuare (C16).",
   "În săptămâna dintre cele două note oficiale, stocul total a scăzut ușor."),
 C("C86", "All decisions per legal working day: Jan–Jun vs Aug–Oct, 2025 and 2026 (seasonality)",
   f"2025: {ro(ESZ[2025]['decizii_pe_zi_ian_iun'])} → {ro(ESZ[2025]['decizii_pe_zi_aug_oct'])} ({pm(ESZ[2025]['aug_oct_fata_de_ian_iun_pct'])}%) · 2026: {ro(ESZ[2026]['decizii_pe_zi_ian_iun'])} → {ro(ESZ[2026]['decizii_pe_zi_aug_oct'])} ({pm(ESZ[2026]['aug_oct_fata_de_ian_iun_pct'])}%)",
   "decizii / zi lucrătoare legală", "A", "PASS", "BERC, aceleași ferestre ca nota MJ", "stat_pack_ext.py (efort_sezon_MJ)", "stat_pack_ext.json", DATE_BERC,
   "Măsurat pe 2025 și 2026 (2024 e afectat de lansarea portalului: −24%). Scăderea din aug.–oct. e sezonieră. Cererile din nota MJ au crescut cu 53% exact în acest sezon (C47).",
   "Atât în 2025, cât și în 2026, august–octombrie a adus cu circa 13% mai puține decizii pe zi decât prima jumătate a anului; în 2026, cererile au crescut exact în acest sezon."),
 C("C87", "All decisions per legal working day, 1 Oct–19 Nov (last complete day): 2025 → 2026", f"{ro(EAP[2025]['decizii_pe_zi_lucr'])} → {ro(EAP[2026]['decizii_pe_zi_lucr'])} ({pm(100 * (EAP[2026]['decizii_pe_zi_lucr'] / EAP[2025]['decizii_pe_zi_lucr'] - 1))}%)",
   "decizii / zi lucrătoare legală", "A", "PASS", "BERC", "stat_pack_ext.py (efort_aceeasi_perioada)", "stat_pack_ext.json", DATE_BERC,
   "Saltul principal față de 2023 s-a produs în 2025; o parte din el poate veni din actualizările CAEN, mai simple, pe care nu le-am separat.",
   "Față de aceeași perioadă din 2025, Registrul emite cu circa 9% mai multe decizii pe zi; saltul mare s-a produs în 2025."),
 # ---------- office rankings (county_rankings.py) — where differences appear, not staff performance
 C("C88", "Offices with the largest local excess over the national median, Jan 2025 – Jul 2026 (before the national wave)",
   " · ".join(f"{r['name']} +{rd(r['exces_mediu_zile'])} (vârf {r['luna_excesului_maxim'][5:]}.{r['luna_excesului_maxim'][:4]})" for r in _rn("rang_probleme_locale_2025_2026")[:4]),
   "zile peste mediana națională, în medie pe lună", "A", "PASS", "BERC, mediana lunară pe oficiu vs națională", "county_rankings.py (rang_probleme_locale_2025_2026)", "county_rankings.json", DATE_BERC,
   "Oficiul = oficiul de depunere. Arată unde au existat probleme locale, nu cauza lor și nici performanța personalului.",
   "Înainte de valul național, câteva oficii au avut episoade locale de întârziere: " + ", ".join(r["name"] for r in _rn("rang_probleme_locale_2025_2026")[:4]) + "."),
 C("C89", "Longest and shortest office medians, decisions 1–18 Nov 2026 (ties reported as a group)",
   f"{_rn('rang_asteptare_nov')[0]['name']} {rd(_rn('rang_asteptare_nov')[0]['median_nov'])} · {len(_TIE)} oficii la ≈{rd(_rn('rang_asteptare_nov')[1]['median_nov'])} ({', '.join(r['name'] for r in _TIE)}) · cea mai scurtă: {_rn('rang_asteptare_nov')[-1]['name']} {rd(_rn('rang_asteptare_nov')[-1]['median_nov'])}",
   "zile (mediană pe oficiul de depunere)", "A", "PASS", "BERC, 42 de oficii", "county_rankings.py (rang_asteptare_nov)", "county_rankings.json", DATE_BERC,
   "Diferențele sunt mici (coada e comună), iar ordinea din 2025 nu prezice 2026 (C75). Oficiile cu aceeași valoare rotunjită sunt raportate ca grup, nu în ordine; în jurul grupului, diferențele sunt de ordinul orelor și nu sunt semnificative.",
   f"Acum, cea mai lungă așteptare e la oficiul {_rn('rang_asteptare_nov')[0]['name']}, urmat de un grup de {len(_TIE)} oficii cu valori aproape egale; diferențele sunt de câteva zile."),
 C("C90", "Highest and lowest rejection rates by office, Aug–Nov 2026",
   "cele mai mari: " + ", ".join(f"{r['name']} {rd(r['rejection_pct_crisis'])}%" for r in _rn("rang_respingeri")[:3]) + " · cea mai mică: " + f"{_rn('rang_respingeri')[-1]['name']} {rd(_rn('rang_respingeri')[-1]['rejection_pct_crisis'])}%",
   "% respinse din deciziile finale", "A", "PASS", "BERC, 42 de oficii", "county_rankings.py (rang_respingeri)", "county_rankings.json", DATE_BERC,
   "Respingerile depind și de ce depun solicitanții (tipuri de cereri, calitatea dosarelor), nu doar de oficiu.",
   "Ponderea respingerilor variază mult între oficii: unde e mare, verificările la depunere și ghidurile pentru solicitanți ar avea cel mai mare efect."),
 # ---------- public sources (press / OSINT) vs our data; CAEN compliance constrained by public figures
 C("C91", "Press/OSINT claims about the queue checked against our data (19 claims)",
   f"{OS['counts']['CONFIRMAT']} confirmate · {OS['counts']['COMPATIBIL']} compatibile · {OS['counts']['CONTRAZIS']} contrazise · {OS['counts']['NEVERIFICABIL']} neverificabile",
   "afirmații din compilația de presă (21.11.2026)", "A", "PASS", "BERC + eșantion myportal + nota MJ, față de compilația de presă", "osint_crosscheck.py", "osint_crosscheck.json", DATE_BERC,
   "Cifrele din presă sunt surse secundare (nivel C). Doar afirmațiile despre coadă; anchetele și acuzațiile despre persoane nu sunt analizate.",
   "Majoritatea cifrelor publicate în presă despre coadă se confirmă sau sunt compatibile cu datele noastre; două afirmații sunt contrazise."),
 C("C92", "Registrations: ONRC/press statistics vs our bulletin data",
   f"9 luni 2026: {OSR['P12']['valoarea_noastra'].split(' admise')[0]} (BERC) vs 100.975 (statistica ONRC) · aug.–oct.: {OSR['P13']['valoarea_noastra'].split(' (')[0]} vs −46,8%",
   "înmatriculări admise", "A", "PASS", "BERC INMATRIC265 (decizii Admis) vs statistica ONRC citată în presă", "osint_crosscheck.py (P12, P13)", "osint_crosscheck.json", DATE_BERC,
   "Definițiile nu sunt identice (statistica ONRC: persoane fizice și juridice înmatriculate), dar valorile coincid la sub 1% pe 9 luni.",
   "Statistica oficială a înmatriculărilor și buletinul de decizii dau practic același număr: datele noastre și sursele publice se confirmă reciproc."),
 C("C93", "Press claim of >26,000 applications/day vs Ministry of Justice inflow", "4.533/zi (MJ, ian.–iun. 2026) vs >26.000/zi (presă)",
   "cereri de înregistrare pe zi", "C", "PASS", "Nota MJ (C47) vs compilația de presă", "osint_crosscheck.py (P05)", "osint_crosscheck.json", "nov. 2026",
   "Nu se reproduce cu niciun numitor: toate numerele contorului (inclusiv certificate și informări) dau circa 21.000 pe zi lucrătoare în ianuarie–iulie; cererile de înregistrare, circa 4.400.",
   "Cifra de peste 26.000 de cereri pe zi din presă nu descrie dosarele de înregistrare: Ministerul raportează circa 4.500 pe zi."),
 C("C94", "If public CAEN figures hold: wait in June 2027 with 50% / 80% / 100% of the 902,243 remaining CAEN filings (no new measures)",
   f"50% → ≈{_cc(0.5)} · 80% → ≈{_cc(0.8)} · 100% → ≈{_cc(1.0)} (față de ≈{_cc('motor (140–390 mii)')} în prognoza de bază)",
   "zile de așteptare în iunie 2027 (mediană), ca pondere din 902.243 de cereri CAEN rămase (nota MJ)", "B", "WARN", "motorul verificat; valul CAEN scalat la nota MJ (902.243)", "forecast_caen_compliance.py", "forecast_caen_compliance.json", DATE_BERC,
   "Scenariu: aceeași formă în timp a valului (ian.–apr. 2027) și același efort pe dosar ca în motor. Arată riscul dacă firmele depun masiv înainte de sfârșitul perioadei de tranziție, cum au făcut înainte de 25 septembrie 2026 (C152).",
   "Dacă se confirmă cifrele publice despre CAEN și firmele depun în masă înainte de sfârșitul perioadei de tranziție (1 aprilie 2027, după calculul nostru), așteptarea ar putea ajunge la 6–11 luni în 2027."),
 C("C95", "Same CAEN scenarios with automatic 1-to-1 conversion of 75% of CAEN filings", f"80% + conversie → ≈{_cc(0.8, 0.75)} · 100% + conversie → ≈{_cc(1.0, 0.75)} (iunie 2027)",
   "zile de așteptare în iunie 2027 (mediană)", "B", "WARN", "motorul verificat; aceeași ipoteză de conversie ca pachetul P4", "forecast_caen_compliance.py", "forecast_caen_compliance.json", DATE_BERC,
   "Conservator: conversia se aplică doar valului suplimentar, nu și dosarelor CAEN din fluxul obișnuit. Efectul conversiei e o ipoteză de intrare.",
   "În scenariile cu val CAEN mare, conversia automată a codurilor CAEN simple ar reduce așteptarea la mai puțin de jumătate: devine măsura decisivă."),
 # ---------- backtest of the queue model on BERC (ground truth)
 C("C96", "Backtest on BERC: queue mechanism with realised inputs, 3 past origins (Mar, Jun, Aug 2026)",
   f"eroare medie {rd(min(x['mae'] for x in _mech))}–{rd(max(x['mae'] for x in _mech))} zile · corelație {rd(min(x['corelatie'] for x in _mech), 2)}–{rd(max(x['corelatie'] for x in _mech), 2)}",
   "zile (mediana prezisă vs observată, pe ziua depunerii)", "B", "PASS", "BERC: intrări și capacitate reale, cohorte decise până la 13.09.2026", "backtest_queue_mechanics.py", "backtest_queue_mechanics.json", DATE_BERC,
   "Validează mecanismul cozii (ordinea de servire și relația stoc–capacitate–așteptare), nu capacitatea de a prezice cererea. Modelul supraestimează ușor (1–3 zile), coerent cu existența unei benzi mai rapide.",
   "Pus să refacă trecutul cu intrările și capacitatea reale, modelul de coadă reproduce așteptarea observată cu o eroare medie de 1–3 zile."),
 C("C97", "Backtest on BERC: forecast using only information available at the origin (same origins)",
   f"eroare medie {rd(min(x['mae'] for x in _fore))}–{rd(max(x['mae'] for x in _fore))} zile · deplasare {rd(min(x['bias'] for x in _fore)).replace('-', '−')}…{rd(max(x['bias'] for x in _fore)).replace('-', '−')} zile",
   "zile (prognoză vs observat)", "B", "PASS", "BERC; capacitate = media ultimelor 12 zile, intrări = media ultimelor 8 săptămâni", "backtest_queue_mechanics.py", "backtest_queue_mechanics.json", DATE_BERC,
   "Prognoza fără informații despre valul de cereri subestimează așteptarea când cererea crește. De aceea raportul dă intervale, grile și scenarii, nu o singură cifră.",
   "Fără să știe de valul de cereri, o prognoză ar fi subestimat așteptarea cu până la circa 11 zile: incertitudinea principală e cererea, nu mecanismul."),
 # ---------- request-number serial counter (reserves_check/, consolidated by serials_consolidate.py)
 C("C98", "Registration requests filed per working day, measured from our data (counter + BERC), H1 2026", f"{ro(_in['h1_2026_berc_per_wd'])}/zi (MJ: 4.533)",
   "cereri de înregistrare pe zi lucrătoare", "A", "PASS", "contorul național al numerelor de cerere + BERC (cereri distincte cu decizie)", "reserves_check/11_inflow_counter.py → serials_consolidate.py", "serials_findings.json", DATE_BERC,
   "Lunile încheiate; BERC subnumără cu câteva procente (cereri încă nesoluționate sau nepublicate).",
   "Din datele noastre, intrările din prima jumătate a anului reproduc cifra Ministerului la câteva procente."),
 C("C99", "Requests filed per working day: May–Jul / September / October / 1–19 November 2026 (portal sample + counter + BERC)",
   f"{ro(_in['may_jul']['per_wd'])} / {ro(_in['sep']['per_wd'])} ({ro(_in['sep']['lo'])}–{ro(_in['sep']['hi'])}) / {ro(_in['oct']['per_wd'])} / {ro(_in['nov']['per_wd'])} · aug.–oct.: {ro(_in['aug_oct']['per_wd'])} (MJ: 6.931)",
   "cereri de înregistrare pe zi lucrătoare", "B", "WARN", "eșantion myportal ponderat pe intervale ale contorului, datat cu deciziile din BERC", "reserves_check/13_stock_estimate.py → serials_consolidate.py", "serials_findings.json", DATE_PORT,
   "Estimare din eșantion; exclude înmatriculările încă în curs (subestimare de circa 400–600 pe zi pentru oct.–nov.). Cu ele, octombrie e aproape de ritmul de soluționare; doar noiembrie e clar sub el.",
   "Coada a fost creată de un vârf de cereri în septembrie, de peste două ori nivelul obișnuit; în noiembrie, intrările au coborât sub ritmul de soluționare."),
 C("C100", "Pending stock estimated from our data (counter + portal sample + BERC): 30.10 / 6.11 / 20.11 2026",
   f"≈{ro(round(_st['2026-10-30']['central'], -3))} / ≈{ro(round(_st['2026-11-06']['central'], -3))} ({ro(round(_st['2026-11-06']['lo'], -3))}–{ro(round(_st['2026-11-06']['hi'], -3))}) / ≈{ro(round(_st['2026-11-20']['central'], -3))}",
   "cereri nesoluționate, fără înmatriculările încă în curs (MJ: 208.318 / 204.414)", "B", "WARN", "estimator pe eșantion (stratificat pe intervale ale contorului), cu deciziile din BERC", "reserves_check/13_stock_estimate.py → serials_consolidate.py", "serials_findings.json", DATE_PORT,
   f"Fără înmatriculările încă în curs (circa {ro(round(SR['inmatric_pending_little'], -3))} în plus). Compatibil cu cifrele MJ la circa ±10%.",
   "Estimat din datele noastre, stocul e apropiat de cel oficial și a început să scadă încet în noiembrie."),
 C("C101", "Since 27 April 2026, share of decisions issued exactly on the 3rd working day: modifications / registrations / adjournments",
   f"{rd(100*SR['april27']['share_at_3_working_days']['CERERE265'])}% / {rd(100*SR['april27']['share_at_3_working_days']['INMATRIC265'])}% / {rd(100*SR['april27']['share_at_3_working_days']['AUTO_AMANARI'])}% · percentila 5 a așteptării: {rd(SR['april27']['p05_wait_hours_before'])} → {rd(SR['april27']['p05_wait_hours_after'])} ore",
   "% din decizii (27.04–28.06.2026)", "A", "PASS", "BERC, zile lucrătoare între depunere și decizie", "reserves_check/23_april27_floor.py, 22_task2_measures.py", "serials_findings.json", DATE_BERC,
   "Valabil pentru aprilie–iunie 2026; din iulie, coada depășește pragul și el nu mai e vizibil. Arată un termen minim de fapt, inclusiv pentru amânări; cauza nu e documentată în date.",
   "Din 27 aprilie 2026, aproape niciun dosar nu mai e decis mai devreme de a treia zi lucrătoare: a apărut un termen minim de fapt."),
 C("C102", "Processing order, finals 2–20 Nov 2026: concordance with filing order; profile of files decided within 14 days",
   f"τ Kendall {rd(SR['order']['kendall_tau'], 2)} · rapide: {rd(100*SR['order']['fast_rejected'])}% respinse (față de {rd(100*SR['order']['all_rejected'])}%), {rd(100*SR['order']['fast_pfa'])}% PFA/II (față de {rd(100*SR['order']['all_pfa'])}%)",
   "corelație de rang; % din decizii", "A", "PASS", "BERC (numerele de cerere și momentul deciziei)", "reserves_check/22_task2_measures.py", "serials_findings.json", DATE_BERC,
   "Ordinea e aproximativ cronologică, cu o bandă mai rapidă; profilul arată dosare fără probleme, nu explică regula.",
   "Dosarele care trec repede sunt, în mare parte, dosare fără probleme: aproape niciunul nu e respins."),
 C("C103", "Firms filing again after a decision, exact firm identifier: within 30 / 90 / 365 days, after rejection vs after admission",
   f"după respingere: {rd(100*SR['refiling']['after_rejection']['30'])}% / {rd(100*SR['refiling']['after_rejection']['90'])}% / {rd(100*SR['refiling']['after_rejection']['365'])}% · după admitere: {rd(100*SR['refiling']['after_admission']['30'])}% / {rd(100*SR['refiling']['after_admission']['90'])}% / {rd(100*SR['refiling']['after_admission']['365'])}%",
   "% din firme care depun o nouă cerere", "A", "PASS", "BERC JSON brut (identificatorul exact al firmei)", "reserves_check/26_refiling_baseline.py", "serials_findings.json", DATE_BERC,
   "Orice cerere ulterioară a aceleiași firme; baza de comparație (după admitere) arată cât e redepunere și cât activitate obișnuită.",
   "După o respingere, aproape jumătate din firme depun o nouă cerere în 30 de zile, față de una din șapte după o admitere."),
 # ---------- economic and fiscal impact (audit_costs.py, verified by cost_check.py) ----------
 C("C104", "First-year net turnover of newly registered firms (Ministry of Finance balance sheets, firms matched by fiscal code): median, cohorts 2024 / 2025; match rate",
   f"{ro(_FM[(2024, 2024)]['median_turnover'])} lei / {ro(_FM[(2025, 2025)]['median_turnover'])} lei · potrivite {rd(100 * _FM[(2024, 2024)]['matched_n'] / _FM[(2024, 2024)]['onrc_n'])}% / {rd(100 * _FM[(2025, 2025)]['matched_n'] / _FM[(2025, 2025)]['onrc_n'])}%",
   "lei, cifră de afaceri netă în primul exercițiu", "B", "PASS", "Ministerul Finanțelor, situații financiare 2024–2025 (date deschise) + BERC înmatriculări", "audit_finance.py", "formation_turnover.csv", "situații financiare 2024–2025",
   "Primul exercițiu poate avea doar câteva luni; potrivirea acoperă circa jumătate din firme.",
   "O firmă nouă raportează, la mijloc, circa 65.000 de lei cifră de afaceri în primul exercițiu."),
 C("C105", "Measured delay inputs, decisions 1 Aug–18 Nov 2026: excess days over 3 calendar days for admitted J registrations / admitted amendments; postponement actions",
   f"{ro(KC['exposure_published']['observed_new_j_excess_days'])} / {rd(KC['exposure_published']['observed_changes_excess_days'] / 1e6, 2)} mil. zile · {ro(KC['exposure_published']['postpone_actions'])} amânări",
   "zile în exces; acțiuni", "A", "PASS", "BERC", "audit_costs.py; renumărat în cost_check.py", "cost_check.json", "BERC până la 18.11.2026",
   f"Pe arhiva curentă (decizii publicate ulterior) intrările măsurate sunt cu până la {rd(max(KC['exposure_change_pct'].values()))}% mai mari; totalurile cresc cu sub 1%.",
   "Zilele de întârziere peste trei zile, însumate pe toate dosarele admise din august până la 18 noiembrie."),
 C("C106", "Economic and private cost of the delay, Aug–18 Nov 2026 incl. the conditional exposure of the stock, FOUNDED scenario: prudent / central / stressed",
   f"{mil(_SC['prudent']['total'])} / {mil(_SC['central']['total'])} / {mil(_SC['tensionat']['total'])}", "milioane lei", "B", "WARN",
   "BERC (zile măsurate) + parametri din bilanțuri MF, Eurostat, buletine PDF + ipoteze declarate", "cost_founded.py", "cost_founded.json", "BERC până la 18.11.2026",
   f"Scenarii deterministe, fără probabilitate. {KF['n_founded']} din {KF['n_params']} parametri au bază în date sau surse oficiale; restul sunt ipoteze declarate. Intervalul contează, nu cifra centrală.",
   f"Costul economic al întârzierilor, august–18 noiembrie, este estimat între circa {rd(_SC['prudent']['total'] / 1e6, 0)} și {rd(_SC['tensionat']['total'] / 1e6, 0)} de milioane de lei, cu circa {rd(_SC['central']['total'] / 1e6, 0)} în scenariul central; e un interval de scenarii, nu o măsurătoare."),
 C("C107", "Budget revenues affected (taxes not collected or delayed), same window, founded scenario: prudent / central / stressed",
   f"{mil(_SC['prudent']['tax'])} / {mil(_SC['central']['tax'])} / {mil(_SC['tensionat']['tax'])}", "milioane lei", "B", "WARN",
   "BERC + cota fiscală efectivă construită din bilanțuri și cotele legale 2026", "cost_founded.py", "cost_founded.json", "BERC până la 18.11.2026",
   "Încasări nete afectate (o parte se încasează mai târziu), nu suma cotelor legale.",
   f"Încasările bugetare afectate sunt estimate între circa {rd(_SC['prudent']['tax'] / 1e6, 0)} și {rd(_SC['tensionat']['tax'] / 1e6, 0)} de milioane de lei, cu circa {rd(_SC['central']['tax'] / 1e6, 0)} în scenariul central."),
 C("C108", "Exposure of one more day with the reference stock (204.414): economic / fiscal, founded central scenario (prudent–stressed)",
   f"{mil(_SC['central']['daily_econ'])} ({mil(_SC['prudent']['daily_econ'])}–{mil(_SC['tensionat']['daily_econ'])}) / {mil(_SC['central']['daily_tax'])} ({mil(_SC['prudent']['daily_tax'])}–{mil(_SC['tensionat']['daily_tax'])})",
   "milioane lei pe zi", "B", "WARN", "MJ (stocul de referință) + scenariul fundamentat", "cost_founded.py", "cost_founded.json", "BERC până la 18.11.2026",
   "Indicator de sensibilitate: nu se înmulțește cu numărul de zile, pentru că stocul și compoziția lui se schimbă.",
   f"Fiecare zi în plus cu stocul actual costă, în scenariul central, circa {rd(_SC['central']['daily_econ'] / 1e6, 1)} milioane de lei în economie și circa {rd(_SC['central']['daily_tax'] / 1e6, 1)} milioane la buget."),
 C("C109", "Share of the founded central cost from the 'other blocked amendments' channel; largest single driver and its swing",
   f"{rd(100 * _SC['central']['channels_share']['C'])}% · costul pe zi blocată: {rd(_SENS['low'] / 1e6, 0)} / +{rd(_SENS['high'] / 1e6, 0)} mil. lei",
   "% din costul central; variația totalului la valorile prudentă / tensionată ale parametrului", "B", "WARN", "ipoteză nemăsurată (cost pe zi)", "cost_founded.py (sensitivity)", "cost_founded.json", "BERC până la 18.11.2026",
   "Cel mai mare canal se sprijină pe un cost pe zi presupus (35–110 lei), fără sursă publică; ca ordin de mărime e 2–6% din vânzările zilnice ale firmelor afectate.",
   "Circa trei sferturi din costul central vin dintr-o singură ipoteză, costul unei modificări blocate, care nu e măsurat nicăieri."),
 C("C110", "Net cost if lost activity is made up by other firms (founded scenario): central / prudent at 90%/75% and 100%/100% substitution; OUG budget",
   f"{rd(_SUB[3]['central_mil'], 1)} / {rd(_SUB[4]['central_mil'], 1)} · prudent {rd(_SUB[3]['prudent_mil'], 1)} / {rd(_SUB[4]['prudent_mil'], 1)} · buget OUG {rd(KC['oug_budget_mil_lei'], 2)}",
   "milioane lei", "B", "WARN", "ipoteze de substituție + MJ (bugetul OUG)", "cost_founded.py (substitution)", "cost_founded.json", "nov. 2026",
   C110_CAV, C110_PUB),
 C("C115", "Measured floor of the cost, Aug–18 Nov 2026: time value of delayed first-period activity and taxes of new firms (data + official rates only)",
   f"≈{rd(KF['floor']['total_value_added_plus_taxes'] / 1e6, 2)} (valoare adăugată {rd(KF['floor']['value_added_basis'] / 1e6, 2)} + taxe {rd(KF['floor']['taxes'] / 1e6, 2)})",
   "milioane lei", "A", "PASS", "BERC + bilanțuri MF + dobânda titlurilor de stat la 1 an (MF)", "cost_evidence/ (T5)", "cost_evidence.json", "BERC până la 18.11.2026",
   "Doar costul de finanțare al amânării, fără nicio ipoteză de comportament; e o limită de jos, " + ("de peste o mie de ori" if _SC['central']['total'] > 1000 * KF['floor']['total_value_added_plus_taxes'] else "de câteva sute de ori") + " sub scenariul central.",
   "Fără nicio ipoteză, doar costul amânării banilor, întârzierile firmelor noi costă cel puțin circa 0,1 milioane de lei; restul depinde de cât din activitate se pierde."),
 C("C116", "Founded vs initial central scenario; parameters with a basis in data or official sources",
   f"{rd(_SC['central']['total'] / 1e6, 0)} față de {rd(_SC0['central']['total'] / 1e6, 0)} · {KF['n_founded']} din {KF['n_params']} parametri fundamentați",
   "milioane lei; parametri", "B", "WARN", "cost_evidence.json (bilanțuri MF, Eurostat, buletine PDF, cote legale)", "cost_founded.py", "cost_founded.json", "nov. 2026",
   "Parametrii cu bază au coborât estimarea; cei fără bază (partea pierdută definitiv, costul pe zi blocată, canalul B, costul unei amânări din canalul D) rămân ipoteze. "
   "Ponderea amânărilor evitabile (canalul D) e măsurată din motivele amânărilor (buletine PDF, 19.10–18.11.2026), nu mai e presupusă: "
   "o amânare e evitată doar dacă toate motivele ei sunt evitabile (valoarea centrală; prudent = limita inferioară a intervalului de încredere), "
   "iar «cel puțin un motiv evitabil» e doar plafonul, folosit în scenariul tensionat.",
   f"Cu parametrii verificați pe date, estimarea centrală a scăzut cu circa {round(100 * (1 - _SC['central']['total'] / _SC0['central']['total']))}%."),
 C("C117", "Value-added share of turnover, Romanian business economy / micro-enterprises (Eurostat SBS 2024) vs 45% in the initial model",
   f"{rd(100 * KE['T4.a.va_share_BS_exclO_S94']['value'])}% / {rd(100 * KE['T4.a.va_share_micro_0_9']['value']['B-S_excl_O_S94'])}%",
   "% din cifra de afaceri", "C", "PASS", "Eurostat, statistici structurale ale întreprinderilor", "cost_evidence/ (T4.a)", "cost_evidence.json", "2024",
   "Medie pe economie; firmele noi, mai orientate spre servicii, pot avea o pondere mai mare.", "Valoarea adăugată e circa 28–30% din vânzări în economia românească de afaceri."),
 C("C118", "Ceiling on the share of amendment delay-days that can block economic activity (excluding office changes), Oct–Nov 2026 bulletin PDFs",
   f"{rd(100 * KE['T1.seat_excl_blocking_strict_excl_capital_with_caen']['value']['excess_day_share'])}–{rd(100 * KE['T1.seat_excl_blocking_strict']['value']['excess_day_share'])}% · numai CAEN: {rd(100 * KE['T1.any_of.caen_only']['value'])}% din modificări",
   "% din zilele în exces ale modificărilor; % din modificări", "A", "PASS", "buletine BERC PDF (modificările admise din oct.–nov. 2026, legate după număr de cerere)", "cost_evidence/ (T1)", "cost_evidence.json", "oct.–nov. 2026",
   "Plafon, nu estimare: nu orice modificare de acest tip blochează efectiv activitatea. Acoperă doar deciziile din octombrie–noiembrie.",
   "Cel mult circa o cincime din zilele de întârziere ale modificărilor privesc schimbări care pot bloca activitatea; circa 40% din modificări sunt doar actualizări CAEN."),
 C("C111", "Monthly realized economic / budget cost of delays (central scenario), by decision month: normal months 2025 (Jun–Dec range), peak of the 2024 portal launch (Oct 2024), Sep / Oct / Nov 2026 (Nov partial)",
   f"normal {rd(_norm[0])}–{rd(_norm[-1])} · oct. 2024 {rd(_KMR['2024-10']['economic_central_mil'])} · sept./oct./nov. 2026 {rd(_KMR['2026-09']['economic_central_mil'])} / {rd(_KMR['2026-10']['economic_central_mil'])} / {rd(_KMR['2026-11']['economic_central_mil'])} · buget nov. 2026 {rd(_KMR['2026-11']['buget_central_mil'])}",
   "milioane lei pe lună (cost realizat al dosarelor decise în lună)", "B", "WARN", "BERC (zile măsurate) + parametrii scenariului central", "cost_monthly.py", "cost_monthly.json", DATE_BERC,
   "Parametrii scenariului fundamentat, aceiași pentru toți anii: arată întârzierea exprimată în lei, comparabil în timp; nu e contabilitate. Noiembrie 2026 este parțial.",
   f"Într-o lună obișnuită, întârzierile costă economia câteva milioane de lei; în octombrie și noiembrie 2026, de circa {ORI} ori mai mult."),
 C("C112", "Central economic cost Aug–18 Nov 2026 split into realized (files already decided) and conditional exposure of the stock not yet decided",
   f"{rd(KM['window_realized_mil']['central'], 0)} realizat + {rd(_SC['central']['total'] / 1e6 - KM['window_realized_mil']['central'], 0)} expunere a stocului = {rd(_SC['central']['total'] / 1e6, 0)}",
   "milioane lei, scenariul central", "B", "WARN", "BERC + scenariul fundamentat", "cost_monthly.py; cost_founded.py", "cost_monthly.json", "BERC până la 18.11.2026",
   "Partea de stoc depinde de câte zile vor mai aștepta dosarele nedecise; e o expunere, nu un cost deja produs.",
   f"Din costul central, circa {rd(KM['window_realized_mil']['central'], 0)} {_DE(KM['window_realized_mil']['central'])}milioane de lei s-au produs deja la dosarele decise; restul depinde de cât vor mai aștepta dosarele din stoc."),
 C("C113", "Realized economic cost by calendar year, central scenario (2026 to 20 Nov)",
   f"2024 {rd(_KMY['2024']['economic_central_mil'], 0)} · 2025 {rd(_KMY['2025']['economic_central_mil'], 0)} · 2026 {rd(_KMY['2026']['economic_central_mil'], 0)} (buget: {rd(_KMY['2024']['buget_central_mil'], 0)} / {rd(_KMY['2025']['buget_central_mil'], 0)} / {rd(_KMY['2026']['buget_central_mil'], 0)})",
   "milioane lei", "B", "WARN", "BERC + parametrii scenariului central", "cost_monthly.py", "cost_monthly.json", DATE_BERC,
   "Aceiași parametri pentru toți anii; 2026 este parțial.", C113_PUB),
 C("C114", "Independent replication from raw data (separate analyst without access to our code): confirmed / different / not verifiable",
   f"{REPL['CONFIRMAT']} / {REPL['DIFERIT']} / {REPL['NEVERIFICABIL']} din {sum(REPL.values())}", "afirmații verificate", "A", "PASS",
   "BERC, eșantionul myportal, cifrele MJ, raportul", "replicare_independenta/lucru (scripturile analistului)", "RAPORT_REPLICARE.md", "22.11.2026",
   "Diferențele au fost corectate în text sau explicate; câteva cifre depind de date pe care analistul nu le-a avut (textul buletinelor PDF, identificatorul firmei, cifrele MJ).",
   "Un analist separat, fără acces la codul nostru, a refăcut cifrele din datele brute: aproape toate s-au confirmat, iar diferențele au fost corectate."),
 C("C119", "Instrument for the registration wait (leave-one-out median wait at the same office in the same week): first-stage coefficient, F statistic, sample",
   f"{rd(_ec('A.prima_etapa.LOO_oficiu_saptamana'), 2)} · F = 792 (pe oficii) · {ro(ECR['A.prima_etapa.LOO_oficiu_saptamana']['n'])} firme noi",
   "coeficient; statistică F; firme", "A", "PASS", "BERC (înmatriculări 2024) legat de bilanțurile MF 2025", "econometrics/ (02_*)", "econometrics.json", "înmatriculări 2024",
   "Instrument puternic (F mult peste pragul uzual de 10); variația lui după efectele fixe e de câteva zile.",
   "Folosim faptul că, în aceeași săptămână și la același oficiu, așteptarea a depins de aglomerare, nu de firmă: un experiment natural."),
 C("C120", "Effect of one extra waiting day on new firms in the first full year after registration (IV): probability of activity / direct tax",
   f"{rd(100 * _ec('A.an_urmator.IV.bs'), 2)} p.p. ({rd(100 * _eci('A.an_urmator.IV.bs')[0], 2)}…{rd(100 * _eci('A.an_urmator.IV.bs')[1], 2)}) / {rd(_ec('A.an_urmator.IV.taxA_w'), 0)} lei ({rd(_eci('A.an_urmator.IV.taxA_w')[0], 0)}…{rd(_eci('A.an_urmator.IV.taxA_w')[1], 0)})",
   "per zi de așteptare (IC 95%)", "B", "PASS", "BERC + bilanțuri MF (cohorta 2024, anul 2025)", "econometrics/ (02_*)", "econometrics.json", "cohorta 2024",
   "Efect nedistins de zero în toate metodele (variabilă instrumentală, diferențe în diferențe, instrument național); estimat pe așteptări de până la circa 35 de zile.",
   "Nu găsim un efect durabil al așteptării asupra firmelor noi în anul următor: activitatea și taxele lor nu diferă măsurabil."),
 C("C121", "Effect of one extra waiting day on new firms in their first (partial) year (IV): turnover / direct tax",
   f"{rd(_ec('A.an_partial_2024.IV.turn_w'), 0)} lei ({rd(_eci('A.an_partial_2024.IV.turn_w')[0], 0)}…{rd(_eci('A.an_partial_2024.IV.turn_w')[1], 0)}) / {rd(_ec('A.an_partial_2024.IV.taxB_w'), 0)} lei ({rd(_eci('A.an_partial_2024.IV.taxB_w')[0], 0)}…{rd(_eci('A.an_partial_2024.IV.taxB_w')[1], 0)})",
   "per zi de așteptare (IC 95%)", "B", "PASS", "BERC + bilanțuri MF (cohorta 2024, anul 2024)", "econometrics/ (02_*)", "econometrics.json", "cohorta 2024",
   "Efect de calendar: activitatea începe la decizie, deci vânzările și taxele primului an se mută mai târziu, nu dispar.",
   "Fiecare zi de așteptare mută mai târziu circa 1.400 de lei din vânzările primului an ale unei firme noi și circa 40 de lei de taxe."),
 C("C122", "2027 general-government revenue collected later because of the queue (status quo, net of within-year recovery): full year P50 (95% interval)",
   f"{rd(_ec(_RK + '1c_efect_net_numerar_amanare.an_2027'), 0)} ({rd(_eci(_RK + '1c_efect_net_numerar_amanare.an_2027')[0], 0)}–{rd(_eci(_RK + '1c_efect_net_numerar_amanare.an_2027')[1], 0)}) · brut amânat {rd(_ec(_RK + '1a_amanat_brut_total.an_2027'), 0)}, din care recuperat în 2027 {rd(_ec(_RK + '1b_recuperat_in_perioada.an_2027'), 0)}",
   "milioane lei, 2027", "B", "WARN", "motorul de prognoză (2.000 de variante) × volume BERC × efectele estimate × cote legale 2026", "econometrics/ (04_*)", "econometrics.json", "prognoză 2027",
   "Distribuție Monte Carlo; așteptările prognozate (55–150 de zile) depășesc intervalul pe care a fost estimat efectul; TVA pe valoarea adăugată e o ipoteză.",
   "În 2027, coada ar muta în anul următor, la mijloc, circa 270 de milioane de lei din veniturile bugetare, într-un interval de circa 60–550 de milioane."),
 C("C123", "Cost of the delay itself for the budget in 2027 (time value of revenue collected later, at the 10-year yield): P50 (95% interval)",
   f"{rd(_ec(_RK + '1d_cost_valoare_in_timp.an_2027'), 0)} ({rd(_eci(_RK + '1d_cost_valoare_in_timp.an_2027')[0], 0)}–{rd(_eci(_RK + '1d_cost_valoare_in_timp.an_2027')[1], 0)})",
   "milioane lei, 2027", "B", "WARN", "ca C122 + randamentul titlurilor de stat la 10 ani (Eurostat)", "econometrics/ (04_*)", "econometrics.json", "prognoză 2027",
   "Costul real al amânării, dacă veniturile se încasează până la urmă.", "Costul de finanțare al acestei amânări, pentru buget, e de circa 13 milioane de lei în 2027."),
 C("C124", "2027 upper bound if delayed revenue were never recovered / persistent loss estimated from the causal effect: P50 (95% interval)",
   f"{rd(_ec(_RK + 'B_nerecuperat_impact_(1a+2).an_2027'), 0)} ({rd(_eci(_RK + 'B_nerecuperat_impact_(1a+2).an_2027')[0], 0)}–{rd(_eci(_RK + 'B_nerecuperat_impact_(1a+2).an_2027')[1], 0)}) / {rd(_ec(_RK + '2_pierdut_persistent_(PARTEA_A).an_2027'), 0)} ({rd(_eci(_RK + '2_pierdut_persistent_(PARTEA_A).an_2027')[0], 0)}…{rd(_eci(_RK + '2_pierdut_persistent_(PARTEA_A).an_2027')[1], 0)})",
   "milioane lei, 2027", "B", "WARN", "ca C122", "econometrics/ (04_*)", "econometrics.json", "prognoză 2027",
   "Limita de sus nu e o prognoză: presupune că nimic nu se recuperează. Pierderea persistentă e centrată pe zero; intervalul reflectă incertitudinea statistică.",
   "Chiar în ipoteza extremă că nimic nu s-ar recupera, riscul pentru 2027 ar fi, la mijloc, de circa 740 de milioane de lei."),
 C("C125", "2027 revenue shift avoided by the best realistic package of measures vs status quo: P50 (95% interval)",
   f"{rd(_ec('B.risc_2027.combinat.evitat_vs_continuitate_A_numerar_(1c+2).an_2027'), 0)} ({rd(_eci('B.risc_2027.combinat.evitat_vs_continuitate_A_numerar_(1c+2).an_2027')[0], 0)}–{rd(_eci('B.risc_2027.combinat.evitat_vs_continuitate_A_numerar_(1c+2).an_2027')[1], 0)})",
   "milioane lei, 2027", "B", "WARN", "ca C122; scenariul „combinat” al motorului", "econometrics/ (04_*)", "econometrics.json", "prognoză 2027",
   "Comparație pe aceleași simulări; depinde de scenariul de măsuri.", "Un pachet realist de măsuri ar evita mutarea a circa 240 de milioane de lei din veniturile din 2027."),
 C("C08", "Union/press backlog figure", "≈210k", "cereri", "C", "WARN", "sindicate/presă", "—", LC, DATE_BERC,
   "Înlocuit de cifra oficială MJ (C28).", "[Se folosește C28]"),
 C("C13", "Oldest still-pending filing in the portal sample", ".".join(reversed(SPK["oldest_pending"]["date"].split("-"))), "dată (eșantion myportal, recoltat 21–22.11.2026)", "A", "PASS", "portal", "stat_pack.py (oldest_pending)", "stat_pack.json", DATE_PORT,
   "Doar în eșantionul nostru; o valoare anterioară (22.09) venea dintr-o recoltare mai veche.", f"Cel mai vechi dosar încă nerezolvat din eșantionul nostru fusese depus pe {int(SPK['oldest_pending']['date'][8:])} septembrie."),
 # withdrawn by gate M2
 *[C(i, "Withdrawn unaudited scenario (" + t + ")", "—", "—", "B", "FAIL", "—", "—", LC, DATE_BERC,
     "RETRAS (poarta M2): scenariu neverificat; înlocuit de C42–C44 și C35.", "[NU SE PUBLICĂ]")
   for i, t in [("C24", "status quo 710k–1,1 mil."), ("C25", "50 luați din operare"), ("C26", "doar prelungire termen"),
                ("C27", "combinat")]],
 C("C20", "Finals Nov 2026 vs 2025 average", "—", "—", "A", "FAIL", "—", "—", LC, DATE_BERC,
   "RETRAS: compară perioade diferite ale anului (NU afirma §2b).", "[NU SE PUBLICĂ]"),
]


# ---------- BEGIN delay_reasons claims (delay_reasons/patch_claims.py) ----------
# Motivele amânărilor (buletine PDF, 19.10–18.11.2026) și matricea de soluții. Valorile se citesc din
# out/delay_reasons.json (delay_reasons/07_results.py) și out/postponement_solutions.json (delay_reasons/08_solutions.py).
DRF = OUT / "delay_reasons.json"; SHA["delay_reasons.json"] = sha(DRF)
DRX = {x["id"]: x for x in json.loads(DRF.read_text(encoding="utf-8"))["findings"]}
PSF = OUT / "postponement_solutions.json"; SHA["postponement_solutions.json"] = sha(PSF)
PSX = json.loads(PSF.read_text(encoding="utf-8")); _DID = PSX["claim_ids"]
assert not ({_DID[k] for k in _DID} & {c["id"] for c in CLAIMS}), "delay_reasons: claim ids already used — renumber CLAIM_IDS in delay_reasons/08_solutions.py"
_pc = lambda x: f"{rd(100 * x)}%"
_pc0 = lambda x: f"{round(100 * x)}%"
_dci = lambda f: f"IC 95%: {rd(100 * f['ci95'][0])}–{rd(100 * f['ci95'][1])}%"
_DRC = DRX["DR.coverage"]["value"]; _VAL = DRX["DR.validation"]; _VV = _VAL["value"]
_DST, _DAN, _DDP = DRX["DR.avoidable.strict"], DRX["DR.avoidable.any"], DRX["DR.avoidable.da_or_partial_all"]
_AMZ = EAP[2026]["amanari_pe_zi_lucr"]          # same window and source as C79 / C30 (1 Oct–19 Nov 2026)
_r10 = lambda x: ro(round(x, -1))
_adj = lambda code: float(DRX["DR.category." + code]["method"].split("precision/recall-adjusted ")[1].split(";")[0])
_LH, _LI, _NM = PSX["levels_headline_count"], PSX["levels_involved_count"], len(PSX["matrix"])
DATE_DR = "buletine BERC PDF, încheieri de amânare 19.10–18.11.2026"
_DR_SRC = "buletine BERC PDF (încheieri de amânare, câmpul «Motivul amânării»); clasificare hibridă clustere + reguli"
_DR_SCR = "delay_reasons/01–07 (07_results.py)"
_DR_CAV = ("Estimare din clasificare automată, validată pe 100 de amânări (setul exact de motive corect în " + _pc0(_VV["exact_set_accuracy"]) +
           " din cazuri). O amânare poate invoca mai multe motive, deci ponderile nu se adună. Doar fereastra 19.10–18.11.2026.")
_DRCAT = [  # code, English text, Romanian subject for the public sentence, extra reserve
    ("CAEN", "activity object / CAEN codes and the activity-authorisation statement", "Obiectul de activitate și codurile CAEN",
     " Probabil subestimată (ajustat pentru precizie și recall: ≈" + _pc(_adj("CAEN")) + ")."),
    ("SEDIU", "registered office: proof of use, validity, consents, address", "Sediul (dovada folosinței, acordurile, adresa)", ""),
    ("CERERE", "application form and tax annex", "Cererea de înregistrare și anexa fiscală",
     " Categoria e supra-atribuită (precizie 0,37): ajustat ≈" + _pc(_adj("CERERE")) + "."),
    ("ACT", "articles of association, decisions, amending act, director mandate", "Actul constitutiv, hotărârile și mandatul administratorului", ""),
    ("SOLICITANT", "applicant identity, power of attorney, signatory capacity", "Solicitantul (identitate, împuternicire, calitate)", ""),
    ("ASOC_ID", "identification data of shareholders/directors vs the register", "Datele de identificare ale asociaților și administratorilor", ""),
    ("INSTIT", "other institutions (tax record, tax attestation, professional authorisations)", "Avizele altor instituții (cazier fiscal, ANAF, autorizații)",
     " Probabil subestimată (ajustat ≈" + _pc(_adj("INSTIT")) + ")."),
    ("CAPITAL", "share capital: payment proof, shares, contributions", "Capitalul social", ""),
    ("SEMN", "signature and form of documents", "Semnătura și forma actelor", ""),
    ("BEN_REAL", "beneficial-owner statement", "Declarația privind beneficiarii reali", ""),
    ("DENUM", "company name rules / reservation", "Denumirea", ""),
    ("TARIF", "publication fee / character counter", "Tariful de publicare", ""),
]
CLAIMS += [
 C(_DID["coverage"], "Postponement notices with a published reason, BERC PDF bulletins 19 Oct–18 Nov 2026: count, share of the archive's postponements in the window, decision days, bulletins",
   f"{ro(_DRC['parsed'])} ({_pc(_DRC['share'])} din {ro(_DRC['archive_postponements_window'])}) · {_DRC['decision_days']} zile de decizie · {_DRC['bulletins']} buletine",
   "amânări cu motivul publicat; % din amânările din arhivă în fereastră", "A", "PASS", _DR_SRC, _DR_SCR, "delay_reasons.json", DATE_DR,
   f"Eșantion de buletine, nu recensământ: acoperirea pe județe {_pc(_DRC['county_coverage_min_max'][0])}–{_pc(_DRC['county_coverage_min_max'][1])}, structura pe tipuri (J/F) ca în arhivă. "
   "Concluziile privesc doar această fereastră; nu se extind la ianuarie–septembrie.",
   f"Am citit motivul publicat pentru {ro(_DRC['parsed'])} de amânări din 19 octombrie–18 noiembrie 2026, circa una din opt amânări din perioadă; județele și tipurile de firme sunt reprezentate ca în arhivă."),
 *[C(_DID[code], f"Share of postponements citing {en} (any-of), 19 Oct–18 Nov 2026",
     f"{_pc(DRX['DR.category.' + code]['value'])} ({_dci(DRX['DR.category.' + code])})", "% din amânările cu motiv publicat",
     "B", "WARN", _DR_SRC, _DR_SCR, "delay_reasons.json", DATE_DR, _DR_CAV + extra,
     f"{subj}: motiv invocat în circa {_pc(DRX['DR.category.' + code]['value'])} din amânări.")
   for code, en, subj, extra in _DRCAT],
 C(_DID["avoidable"], "Postponements avoidable at filing: all cited reasons avoidable (strict) / at least one avoidable (upper bound) / all avoidable or partly avoidable",
   f"{_pc(_DST['value'])} ({_dci(_DST)}) · {_pc(_DAN['value'])} ({_dci(_DAN)}) · {_pc(_DDP['value'])}",
   "% din amânările cu motiv publicat", "B", "WARN", _DR_SRC + "; marcajele «evitabil» din taxonomy.csv", "delay_reasons/07_results.py", "delay_reasons.json", DATE_DR,
   "«Evitabil la depunere» e evaluarea auditorului (asistată de AI), neconfirmată de ONRC. Pe cele 100 de cazuri verificate manual: 27% strict, 47% cel puțin un motiv.",
   f"Circa una din cinci amânări ({_pc(_DST['value'])}) avea numai motive pe care o verificare la depunere le-ar fi prins; în aproape jumătate ({_pc(_DAN['value'])}), cel puțin unul."),
 C(_DID["validation"], "Validation of the reason classifier on a seeded random sample of 100 postponements: exact set / at least one correct reason / precision / recall",
   f"{_pc0(_VV['exact_set_accuracy'])} set identic ({_dci(_VAL)}) · {_pc0(_VV['any_overlap'])} cel puțin un motiv corect · precizie {rd(_VV['micro_precision'], 2)} / recall {rd(_VV['micro_recall'], 2)}",
   f"% din cele {_VAL['n']} de amânări verificate", "B", "WARN", "eșantion aleator cu seed fix, etichetat din textul anonimizat înainte de a vedea predicțiile", "delay_reasons/05–06",
   "delay_reasons.json", DATE_DR,
   "Un singur evaluator, un model AI, fără al doilea codificator uman; recomandăm o a doua etichetare umană.",
   f"Pe 100 de amânări verificate separat, clasificarea a găsit cel puțin un motiv corect în {_pc0(_VV['any_overlap'])} din cazuri și setul complet de motive în {_pc0(_VV['exact_set_accuracy'])}."),
 C(_DID["capacity"], "Postponement decisions per working day that checks at filing could remove (strict share) / make simpler (at-least-one share), out of all postponements per working day, 1 Oct–19 Nov 2026",
   f"≈{_r10(_AMZ * _DST['value'])} ({_r10(_AMZ * _DST['ci95'][0])}–{_r10(_AMZ * _DST['ci95'][1])}) evitate · ≈{_r10(_AMZ * _DAN['value'])} cu cel puțin un motiv mai puțin · din {ro(_AMZ)} amânări / zi",
   "amânări pe zi lucrătoare legală", "B", "WARN", "BERC (amânări pe zi lucrătoare, ca în C79) × ponderile evitabile (" + _DID["avoidable"] + ")",
   "stat_pack_ext.py (efort_aceeasi_perioada) × delay_reasons/07_results.py; calcul în delay_reasons/08_solutions.py", "postponement_solutions.json", DATE_BERC,
   "Plafon: presupune că verificarea prinde toate motivele evitabile. O amânare evitată scoate o decizie de amânare și o a doua analiză a dosarului, nu o decizie finală; "
   "în celelalte, dosarul se amână tot, dar pentru mai puține lipsuri. Ponderile vin din 19.10–18.11.2026.",
   f"Dacă lipsurile evitabile ar fi prinse la depunere, ar dispărea cel mult circa {_r10(_AMZ * _DST['value'])} de amânări pe zi lucrătoare din circa {ro(round(_AMZ, -3))}; în circa {_r10(_AMZ * _DAN['value'])} de amânări pe zi ar rămâne cel puțin un motiv mai puțin."),
 C(_DID["levels"], "Automation level of the main solution per postponement reason (12 reasons): Standard / AI only / advanced AI only / not automatable; reasons where the registrar's legal judgement remains",
   f"{_LH['Standard']} / {_LH['Doar cu AI']} / {_LH['Doar cu AI avansat']} / {_LH['Nu se poate automatiza']} din {_NM} · judecata registratorului rămâne în {_LI['Nu se poate automatiza']} din {_NM}",
   "motive de amânare (categorii)", "B", "PASS", "matricea de soluții (evaluarea auditorului, asistată de AI)", "delay_reasons/08_solutions.py", "postponement_solutions.json", "22.11.2026",
   "Nu vedem sistemele interne ONRC: o parte din verificări poate exista deja. Nivelul e cel al soluției principale; fiecare motiv are și soluții secundare.",
   f"Pentru {_LH['Standard']} din cele {_NM} motive, soluția principală e o verificare la depunere fără AI; doar concordanța actelor cere un model AI avansat, iar în {_LI['Nu se poate automatiza']} motive o parte rămâne la judecata registratorului."),
 C(_DID["legal"], "Legal frame for automating postponement checks: AI Act dates after the Digital Omnibus; who decides; automated-decision limits",
   "AI Act: risc ridicat (anexa III) de la 2.12.2027 (Reg. 2026/1744); art. 4 și art. 50 aplicabile · decizia rămâne la registrator (L 265/2022, art. 28 alin. (2); GDPR art. 22; L 242/2022, art. 13 alin. (9))",
   "prevederi legale", "C", "PASS",
   "EUR-Lex: Reg. (UE) 2024/1689, 2026/1744, GDPR, Dir. (UE) 2019/1151; legislatie.just.ro: Legea 265/2022, Legea 242/2022 (citite la 22.11.2026)",
   "delay_reasons/08_solutions.py (legal)", "postponement_solutions.json", "22.11.2026",
   "Încadrarea cazurilor ONRC în afara anexei III e interpretarea auditorului; art. 113 original și formularea anexei III au fost citite pe o sursă secundară.",
   "Legea cere ca registratorul să decidă; un program poate doar pregăti și semnala. Regulile pentru AI cu risc ridicat se aplică din decembrie 2027, iar instruirea personalului și transparența unui asistent AI se cer deja."),
]
# ---------- END delay_reasons claims ----------

# ---------- BEGIN rejection_reasons claims (rejection_reasons/patch_claims.py) ----------
# Motivele respingerilor (buletine PDF, 19.10–18.11.2026) + arhiva BERC (legătura cu amânarea anterioară);
# două afirmații juridice din stakeholders/LEGAL_BASIS.md (perioada de tranziție CAEN; suspendarea concursurilor în 2026).
import re
RRF = OUT / "rejection_reasons.json"; SHA["rejection_reasons.json"] = sha(RRF)
RRX = {x["id"]: x for x in json.loads(RRF.read_text(encoding="utf-8"))["findings"]}
SLF = OUT / "stakeholders_legal.json"; SHA["stakeholders_legal.json"] = sha(SLF)
_SLT = json.dumps(json.loads(SLF.read_text(encoding="utf-8")), ensure_ascii=False)
_RID = {'after_post': 'C144', 'unfulfilled': 'C145', 'outcomes': 'C146', 'causes': 'C147', 'types': 'C148', 'overlap': 'C149', 'avoidable': 'C150', 'coverage': 'C151', 'caen_transition': 'C152', 'hiring': 'C153'}
assert not (set(_RID.values()) & {c["id"] for c in CLAIMS}), "rejection_reasons: claim ids already used — renumber IDS in rejection_reasons/patch_claims.py"
_rp = lambda x: f"{rd(100 * x)}%"
_rp0 = lambda x: f"{round(100 * x)}%"
_rci = lambda f: f"IC 95%: {rd(100 * f['ci95'][0])}–{rd(100 * f['ci95'][1])}%"
_RAP = RRX["RR.archive_prior_postponement.ALL"]; _RAPM = RRX["RR.archive_prior_postponement.MENTIUNI"]; _RAPI = RRX["RR.archive_prior_postponement.INMATRICULARE"]
_RMED = float(re.search(r"Median days last postponement -> rejection (\d+(?:\.\d+)?)", _RAP["method"]).group(1))
_RMED0 = float(re.search(r"filing -> rejection (\d+(?:\.\d+)?)", _RAP["method"]).group(1))
assert _RMED == 16.0, _RMED                       # the public sentence reads it as "the day after the 15-day completion term"
_RUF = RRX["RR.mechanism.unfulfilled.ALL"]; _RPT = RRX["RR.mechanism.m_M_PARTIAL.ALL"]
_ROC = RRX["RR.postponement_outcomes"]; _ROCC = _ROC["value"]["outcome_counts"]; _ROCN = sum(_ROCC.values())
_ROR, _ROA, _ROW = (_ROCC[k] / _ROCN for k in ("Respins", "Admis", "Renuntat"))
assert abs(_ROR - _ROC["value"]["rejected_share_of_resolved"]) < 5e-4
_RCM = lambda c: RRX[f"RR.category.{c}.manual"]
_RTOP = sorted(("CAEN", "SEDIU", "ASOC_ID", "ACT", "SOLICITANT", "INSTIT"), key=lambda c: -_RCM(c)["value"])
assert _RTOP[:3] == ["CAEN", "SEDIU", "ASOC_ID"], _RTOP          # the public sentence names these three
_RNAME = {"CAEN": "CAEN / declarația de autorizare", "SEDIU": "sediu", "ASOC_ID": "date de identificare", "ACT": "act constitutiv",
          "SOLICITANT": "solicitant", "INSTIT": "avize/cazier fiscal"}
_RINI = RRX["RR.category.INSTIT.registrations"]; _RCAA = RRX["RR.category.CAEN.amendments"]
assert _RINI["value"] == max(RRX[f"RR.category.{c}.registrations"]["value"] for c in ("CAEN", "SEDIU", "ACT", "ASOC_ID", "SOLICITANT", "CERERE", "INSTIT", "CAPITAL"))
assert _RCAA["value"] == max(RRX[f"RR.category.{c}.amendments"]["value"] for c in ("CAEN", "SEDIU", "ACT", "ASOC_ID", "SOLICITANT", "CERERE", "INSTIT", "CAPITAL"))
_RPR = RRX["RR.pairs"]["value"]["hybrid_vs_rules"]
_RAS, _RAA = RRX["RR.avoidable.strict.manual"], RRX["RR.avoidable.any.manual"]
_RAS_C, _RAA_C = RRX["RR.avoidable.strict"], RRX["RR.avoidable.any"]
_RCV = RRX["RR.coverage"]["value"]; _RVV = RRX["RR.validation"]["value"]
DATE_RR = "buletine BERC PDF, încheieri de respingere 19.10–18.11.2026"
_RR_SRC = "buletine BERC PDF (încheieri de respingere: «urmează a respinge … pe motiv»), legate de arhiva BERC"
_RR_SCR = "rejection_reasons/01–07 (07_results.py)"
_m15 = re.search(r"cel mult (\d+)% din posturile vacantate după (\d\d\.\d\d\.\d{4})", _SLT); assert _m15, "Legea 141/2025 art. XXII text not found"
assert "01.04.2027" in _SLT and "25.09.2026" in _SLT and "HG nr. 656/1997, art. 5^1" in _SLT
_HPCT, _HDATE = _m15.group(1), _m15.group(2)
# C52 (OUG extins + 40% din posturile vacante): the scenario assumes the hiring-freeze exceptions are approved (C153)
HIRE_ASSUMPTION = (f"Scenariul presupune că Ministerul Justiției aprobă excepțiile de la suspendarea concursurilor din 2026 "
                   f"(cel mult {_HPCT}% din posturile vacantate după {_HDATE} sau posturi unice).")
for _c in CLAIMS:
    if _c["id"] == "C52":
        _c["rezerva_obligatorie"] = _c["rezerva_obligatorie"].replace("posturile finanțate.", "posturile finanțate. " + HIRE_ASSUMPTION + " (C153)", 1)
CLAIMS += [
 C(_RID["after_post"], "Share of archive rejections 19 Oct–18 Nov 2026 with an earlier postponement of the same request (census); by type; median days from the last postponement / from filing to the rejection",
   f"{_rp(_RAP['value'])} ({_rci(_RAP)}) · mențiuni {_rp(_RAPM['value'])} / înmatriculări {_rp(_RAPI['value'])} · mediana: {round(_RMED)} zile de la amânare, {round(_RMED0)} de la depunere",
   "% din respingerile din arhivă; zile calendaristice", "A", "PASS", "BERC (decizii Respins și amânările anterioare ale aceleiași cereri: același număr, aceeași zi de depunere)",
   _RR_SCR, "rejection_reasons.json", "BERC, decizii 19.10–18.11.2026",
   "Limită inferioară: arhiva pierde câteva amânări. Leagă cererea după număr și zi de depunere, nu după firmă.",
   f"Aproape toate respingerile ({_rp(_RAP['value'])}) din 19 octombrie–18 noiembrie 2026 au fost precedate de o amânare a aceleiași cereri; respingerea vine, la mijloc, la {round(_RMED)} zile după amânare, adică imediat după expirarea termenului de completare."),
 C(_RID["unfulfilled"], "Share of parsed rejection decisions whose text states that the postponement was not complied with (not remedied / only partly or wrongly remedied)",
   f"{_rp(_RUF['value'])} ({_rci(_RUF)}) · nerezolvat {_rp(_RUF['value'] - _RPT['value'])} · parțial {_rp(_RPT['value'])}",
   "% din respingerile cu text publicat", "B", "WARN", _RR_SRC, _RR_SCR, "rejection_reasons.json", DATE_RR,
   f"Din textul a {ro(_RCV['parsed'])} de încheieri ({_rp(_RCV['share'])} din respingerile din perioadă); mecanismul e citit corect în {_rp0(_RVV['mechanism_accuracy'])} din cazurile verificate. Doar fereastra 19.10–18.11.2026.",
   f"În textul încheierilor, circa {_rp0(_RUF['value'])} din respingeri spun explicit că lipsurile cerute la amânare nu au fost remediate sau au fost remediate doar parțial."),
 C(_RID["outcomes"], "Outcome of requests postponed 1 Sep–15 Oct 2026 and resolved by 20 Nov 2026: rejected / admitted / withdrawn by the applicant",
   f"{_rp(_ROR)} respinse / {_rp(_ROA)} admise / {_rp(_ROW)} renunțate (din {ro(_ROCN)} soluționate)",
   "% din cererile amânate și soluționate", "A", "PASS", "BERC (prima decizie care nu e amânare, după ultima amânare din fereastră)", _RR_SCR, "rejection_reasons.json",
   "BERC, amânări 1.09–15.10.2026, urmărite până la 20.11.2026",
   "Cererile încă nesoluționate la 20.11.2026 sunt excluse; «renunțat» e o soluție separată, nu o respingere.",
   f"Dintre cererile amânate în 1 septembrie–15 octombrie 2026 și soluționate până la 20 noiembrie, circa {_rp0(_ROR)} au fost respinse și circa {_rp0(_ROA)} admise."),
 C(_RID["causes"], "Main causes of rejection, manually labelled sample of 150 rejection decisions (any-of; Wilson CI): " + ", ".join(_RNAME[c] for c in _RTOP),
   " · ".join(f"{_RNAME[c]} {_rp(_RCM(c)['value'])} ({rd(100 * _RCM(c)['ci95'][0])}–{rd(100 * _RCM(c)['ci95'][1])})" for c in _RTOP),
   "% din respingeri (eșantion manual, n=150)", "B", "WARN", _RR_SRC + "; eșantion aleator cu seed fix, etichetat manual", "rejection_reasons/05–07", "rejection_reasons.json", DATE_RR,
   f"Ponderi din eșantionul manual (n={_RCM('CAEN')['n']}), recomandate de analiză pentru afirmații publice: clasificatorul automat subestimează cauzele (recall {rd(_RVV['micro_recall'], 2)}). "
   "Evaluatorul este un model AI, fără al doilea codificator. O respingere poate avea mai multe cauze; ponderile nu se adună.",
   f"Cele mai dese cauze ale respingerilor sunt aceleași ca la amânări: obiectul de activitate și codurile CAEN (circa {_rp0(_RCM('CAEN')['value'])}), sediul (circa {_rp0(_RCM('SEDIU')['value'])}) și datele de identificare ale asociaților (circa {_rp0(_RCM('ASOC_ID')['value'])})."),
 C(_RID["types"], "Dominant rejection cause by request type (automatic classifier): registrations — tax record / approvals of other institutions; amendments — CAEN codes",
   f"înmatriculări: avize/cazier fiscal {_rp(_RINI['value'])} (IC 95%: {rd(100 * _RINI['ci95'][0])}–{rd(100 * _RINI['ci95'][1])}%, n={_RINI['n']}) · mențiuni: CAEN {_rp(_RCAA['value'])} ({_rci(_RCAA)}, n={_RCAA['n']})",
   "% din respingerile de fiecare tip", "B", "WARN", _RR_SRC, _RR_SCR, "rejection_reasons.json", DATE_RR,
   f"Clasificare automată (estimări inferioare, recall {rd(_RVV['micro_recall'], 2)}); la înmatriculări n={_RINI['n']}, intervale largi: direcția e robustă, valoarea exactă nu.",
   f"La înmatriculări, cele mai multe respingeri țin de cazierul fiscal și de avizele altor instituții (circa {_rp0(_RINI['value'])}); la modificări, de codurile CAEN (circa {_rp0(_RCAA['value'])})."),
 C(_RID["overlap"], "Rejections whose own postponement notice is also in the collected bulletins: at least one cause in common / all rejection causes already in the postponement",
   f"{_rp0(_RPR['any_overlap'])} cel puțin o cauză comună · {_rp0(_RPR['rejection_subset_of_postponement'])} fără nicio cauză nouă (n={_RPR['n']})",
   "% din perechile amânare–respingere", "B", "WARN", _RR_SRC + "; încheierea de amânare a aceleiași cereri", _RR_SCR, "rejection_reasons.json", DATE_RR,
   f"Eșantion mic (n={_RPR['n']}): doar cererile la care ambele încheieri sunt în buletinele colectate. Pe amânare se aplică doar regulile pe cuvinte-cheie.",
   f"În {_RPR['n']} de cazuri în care am găsit și încheierea de amânare, respingerea reia cel puțin o cauză a amânării în {_rp0(_RPR['any_overlap'])} din cazuri; eșantionul e mic."),
 C(_RID["avoidable"], "Rejections avoidable at filing, manual sample of 150: all causes avoidable (strict) / at least one avoidable (upper bound); classifier values (lower bounds)",
   f"{_rp(_RAS['value'])} ({rd(100 * _RAS['ci95'][0])}–{rd(100 * _RAS['ci95'][1])}) · {_rp(_RAA['value'])} ({rd(100 * _RAA['ci95'][0])}–{rd(100 * _RAA['ci95'][1])}) · clasificator {_rp(_RAS_C['value'])} / {_rp(_RAA_C['value'])}",
   "% din respingeri (eșantion manual, IC Wilson)", "B", "WARN", _RR_SRC + "; marcajele «evitabil» din taxonomy.csv (aceleași ca la amânări)", "rejection_reasons/07_results.py",
   "rejection_reasons.json", DATE_RR,
   "«Evitabil la depunere» e evaluarea auditorului (asistată de AI), neconfirmată de ONRC; un singur evaluator AI. Valorile clasificatorului sunt limite de jos.",
   f"Pe {_RAS['n']} de respingeri verificate, circa {_rp0(_RAS['value'])} aveau numai cauze pe care o verificare la depunere le-ar fi prins, iar circa {_rp0(_RAA['value'])}, cel puțin una."),
 C(_RID["coverage"], "Rejection decisions with a published reason, BERC PDF bulletins 19 Oct–18 Nov 2026: count, share of the archive's rejections, bulletins, decision days",
   f"{ro(_RCV['parsed'])} ({_rp(_RCV['share'])} din {ro(_RCV['archive_rejections_window'])}) · {_RCV['bulletins']} buletine · {_RCV['decision_days']} zile de decizie",
   "respingeri cu motivul publicat; % din respingerile din arhivă", "A", "PASS", _RR_SRC, _RR_SCR, "rejection_reasons.json", DATE_RR,
   f"Eșantion de buletine, nu recensământ: acoperirea pe județe {_rp(_RCV['county_coverage_min_max'][0])}–{_rp(_RCV['county_coverage_min_max'][1])}; aceeași pe tipuri de cereri. Constatarea principală (respingere după amânare) vine din arhivă, pentru toate respingerile.",
   f"Am citit motivul publicat pentru {ro(_RCV['parsed'])} de respingeri din 19 octombrie–18 noiembrie 2026, circa una din nouă respingeri din perioadă."),
 C(_RID["caen_transition"], "CAEN Rev.3: legal nature of the update (transition period, not a deadline with forfeiture) and its end dates",
   "perioadă de tranziție (ambele versiuni valabile) · perioada inițială: 18 luni de la 25.03.2025, până la 25.09.2026 · prelungire: 6 luni de la 01.10.2026, până la ≈01.04.2027 (calculat)",
   "prevederi legale", "C", "PASS", "legislatie.just.ro: HG nr. 656/1997, art. 5^1 alin. (2), (2^1), (3); HG 284/2025, art. II; HG 788/2026 (MO din 01.10.2026); Codul civil, calculul termenelor (citite la 22.11.2026)",
   "stakeholders/LEGAL_BASIS.md", "stakeholders_legal.json", "22.11.2026",
   "Data de 1 aprilie 2027 e calculată de noi, nu e scrisă în HG. Nu am găsit în textele citite o obligație cu sancțiune ca firmele să depună actualizarea la ONRC; absența ei nu e dovedită.",
   "Pentru actualizarea la CAEN Rev. 3, HG nr. 656/1997 stabilește o perioadă de tranziție, în care ambele versiuni ale codurilor sunt valabile; în textele citite nu am găsit o sancțiune sau un termen de decădere. Perioada inițială s-a încheiat la 25 septembrie 2026; prelungirea de 6 luni duce, după calculul nostru, până la 1 aprilie 2027."),
 C(_RID["hiring"], "Filling vacant public posts in 2026: competitions suspended; exceptions the principal authorising officer (Ministry of Justice for ONRC) may approve",
   f"concursuri suspendate în 2026 · excepții: cel mult {_HPCT}% din posturile vacantate după {_HDATE}, plus posturile unice",
   "prevederi legale", "C", "PASS", "legislatie.just.ro: Legea nr. 141/2025, art. XXII alin. (1), (2), (4), (6), forma consolidată la 12.11.2026 (citită la 22.11.2026)",
   "stakeholders/LEGAL_BASIS.md", "stakeholders_legal.json", "22.11.2026",
   "Regimul pentru 2027 nu a fost verificat. Ocuparea unei părți mari din posturile vacante (de exemplu 40%, ca în scenariul C52) poate depăși excepția și ar cere atunci o derogare prin lege sau OUG.",
   f"În 2026, concursurile pentru posturile vacante din instituțiile publice sunt suspendate; Ministerul Justiției poate aproba excepții pentru ONRC, de cel mult {_HPCT}% din posturile vacantate după 1 ianuarie 2026, plus posturile unice."),
]
# ---------- END rejection_reasons claims ----------

def main():
    cols = ["id", "text", "value", "unit", "level", "status", "source", "script", "data_sha256",
            "data_date", "rezerva_obligatorie", "public_ro"]
    CLAIMS.sort(key=lambda c: int(c["id"][1:]))
    path = DELIV / "claims_registry.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for c in CLAIMS: w.writerow(c)
    n = {s: sum(1 for c in CLAIMS if c["status"] == s) for s in ("PASS", "WARN", "FAIL")}
    print(f"wrote {path} — {len(CLAIMS)} claims: {n['PASS']} PASS, {n['WARN']} WARN, {n['FAIL']} FAIL")
    for c in CLAIMS:
        print(f"  [{c['status']:4}] {c['id']:4} {c['level']:4} {c['value'][:34]:34} {c['text'][:52]}")


if __name__ == "__main__":
    main()
