"""Patch for independent_audit/generate_claims_registry.py: adds the rejection-reason claims (C144–C151) and two
legal claims checked in stakeholders/LEGAL_BASIS.md (C152 CAEN transition period, C153 hiring suspension in 2026).

    ..\\..\\venv\\Scripts\\python.exe -X utf8 patch_claims.py            # patches ../generate_claims_registry.py
    ..\\..\\venv\\Scripts\\python.exe -X utf8 patch_claims.py --check    # only reports whether the ids are free

Same pattern as delay_reasons/patch_claims.py:
- one block inserted right before `def main():`; main() sorts CLAIMS by id;
- out/rejection_reasons.json (rejection_reasons/07_results.py) and out/stakeholders_legal.json are loaded with their
  SHA-256 in SHA[...]; every number is READ from those files (never typed); the 16-day median, which exists only in a
  `method` string, is parsed and asserted;
- the block asserts at import time that none of its ids is already used; idempotent (marker line).
Written with AI assistance (Claude Opus 5.5), under the author's direction.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / "generate_claims_registry.py"
IDS = {k: f"C{144 + i}" for i, k in enumerate(("after_post", "unfulfilled", "outcomes", "causes", "types", "overlap", "avoidable", "coverage",
                                                 "caen_transition", "hiring"))}
MARK = "# ---------- BEGIN rejection_reasons claims (rejection_reasons/patch_claims.py) ----------"
ANCHOR = "\n\ndef main():"

BLOCK = r'''
# ---------- BEGIN rejection_reasons claims (rejection_reasons/patch_claims.py) ----------
# Motivele respingerilor (buletine PDF, 19.10–18.11.2026) + arhiva BERC (legătura cu amânarea anterioară);
# două afirmații juridice din stakeholders/LEGAL_BASIS.md (perioada de tranziție CAEN; suspendarea concursurilor în 2026).
import re
RRF = OUT / "rejection_reasons.json"; SHA["rejection_reasons.json"] = sha(RRF)
RRX = {x["id"]: x for x in json.loads(RRF.read_text(encoding="utf-8"))["findings"]}
SLF = OUT / "stakeholders_legal.json"; SHA["stakeholders_legal.json"] = sha(SLF)
_SLT = json.dumps(json.loads(SLF.read_text(encoding="utf-8")), ensure_ascii=False)
_RID = __RID__
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
   "Data de 1 aprilie 2027 e calculată de noi, nu e scrisă în HG. Nu am găsit în textele citite o obligație cu sancțiune ca firmele să depună actualizarea la ONRC; absența ei nu e dovedită. Nu e aviz juridic.",
   "Pentru actualizarea la CAEN Rev. 3, HG nr. 656/1997 stabilește o perioadă de tranziție, în care ambele versiuni ale codurilor sunt valabile; în textele citite nu am găsit o sancțiune sau un termen de decădere. Perioada inițială s-a încheiat la 25 septembrie 2026; prelungirea de 6 luni duce, după calculul nostru, până la 1 aprilie 2027."),
 C(_RID["hiring"], "Filling vacant public posts in 2026: competitions suspended; exceptions the principal authorising officer (Ministry of Justice for ONRC) may approve",
   f"concursuri suspendate în 2026 · excepții: cel mult {_HPCT}% din posturile vacantate după {_HDATE}, plus posturile unice",
   "prevederi legale", "C", "PASS", "legislatie.just.ro: Legea nr. 141/2025, art. XXII alin. (1), (2), (4), (6), forma consolidată la 12.11.2026 (citită la 22.11.2026)",
   "stakeholders/LEGAL_BASIS.md", "stakeholders_legal.json", "22.11.2026",
   "Regimul pentru 2027 nu a fost verificat. Ocuparea unei părți mari din posturile vacante (de exemplu 40%, ca în scenariul C52) poate depăși excepția și ar cere atunci o derogare prin lege sau OUG. Nu e aviz juridic.",
   f"În 2026, concursurile pentru posturile vacante din instituțiile publice sunt suspendate; Ministerul Justiției poate aproba excepții pentru ONRC, de cel mult {_HPCT}% din posturile vacantate după 1 ianuarie 2026, plus posturile unice."),
]
# ---------- END rejection_reasons claims ----------
'''.replace("__RID__", repr(IDS))


def main():
    target = TARGET
    src = target.read_text(encoding="utf-8")
    used = set(re.findall(r'C\("(C\d+)"', src)) | set(re.findall(r'"(C1[2-9]\d)"', src.split("BEGIN delay_reasons")[0]))
    clash = sorted(set(IDS.values()) & used)
    if "--check" in sys.argv:
        print(f"{target}: ids {min(IDS.values())}–{max(IDS.values())}; clashes: {clash or 'none'}; patched: {MARK in src}")
        return
    if MARK in src:
        sys.exit(f"{target} is already patched — nothing to do.")
    if clash:
        sys.exit(f"ids already used: {clash}")
    if src.count(ANCHOR) != 1:
        sys.exit("anchor not found exactly once")
    target.write_text(src.replace(ANCHOR, "\n" + BLOCK.rstrip("\n") + ANCHOR, 1), encoding="utf-8")
    print(f"patched {target}: +{len(IDS)} claims ({', '.join(IDS.values())})")


if __name__ == "__main__":
    main()
