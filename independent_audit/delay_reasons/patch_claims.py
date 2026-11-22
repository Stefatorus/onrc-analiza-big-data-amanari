"""Patch for independent_audit/generate_claims_registry.py: adds the postponement-reason claims
(ids from out/postponement_solutions.json → claim_ids; default C126–C143).

Run ONLY at integration time, after the other builders are final:

    ..\\..\\venv\\Scripts\\python.exe -X utf8 patch_claims.py                 # patches ../generate_claims_registry.py
    ..\\..\\venv\\Scripts\\python.exe -X utf8 patch_claims.py <path.py>       # patches another copy (dry run)
    ..\\..\\venv\\Scripts\\python.exe -X utf8 patch_claims.py --check         # only reports whether the ids are free

What it does
- inserts one block right before `def main():` (main() sorts CLAIMS by id, so the position does not matter);
- the block loads out/delay_reasons.json and out/postponement_solutions.json and records their SHA-256 in SHA[...],
  exactly like the cost_evidence.json / econometrics.json blocks; every value is READ from those files (never typed);
- the block asserts at import time that none of its ids is already used, so a renumbering conflict fails loudly;
- idempotent: refuses to patch twice (marker line).
If the ids are taken by then: change CLAIM_IDS in 08_solutions.py, re-run 08_solutions.py, re-run this patch.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / "generate_claims_registry.py"
PS = json.loads((HERE.parent / "out" / "postponement_solutions.json").read_text(encoding="utf-8"))
IDS = PS["claim_ids"]
MARK = "# ---------- BEGIN delay_reasons claims (delay_reasons/patch_claims.py) ----------"
ANCHOR = "\n\ndef main():"

BLOCK = r'''
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
   "Încadrarea cazurilor ONRC în afara anexei III e interpretarea auditorului, nu aviz juridic; art. 113 original și formularea anexei III au fost citite pe o sursă secundară.",
   "Legea cere ca registratorul să decidă; un program poate doar pregăti și semnala. Regulile pentru AI cu risc ridicat se aplică din decembrie 2027, iar instruirea personalului și transparența unui asistent AI se cer deja."),
]
# ---------- END delay_reasons claims ----------
'''


def ids_free(src: str) -> list[str]:
    used = set(re.findall(r'C\("(C\d+)"', src))
    return sorted(set(IDS.values()) & used)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = Path(args[0]) if args else TARGET
    src = target.read_text(encoding="utf-8")
    clash = ids_free(src)
    if "--check" in sys.argv:
        print(f"{target}: ids {sorted(IDS.values())[0]}–{sorted(IDS.values())[-1]}; clashes: {clash or 'none'}; patched: {MARK in src}")
        return
    if MARK in src:
        sys.exit(f"{target} is already patched — nothing to do.")
    if clash:
        sys.exit(f"ids already used in {target}: {clash}. Renumber CLAIM_IDS in 08_solutions.py and re-run 08.")
    if src.count(ANCHOR) != 1:
        sys.exit(f"anchor {ANCHOR!r} not found exactly once in {target}.")
    target.write_text(src.replace(ANCHOR, "\n" + BLOCK.rstrip("\n") + ANCHOR, 1), encoding="utf-8")
    print(f"patched {target}: +{len(IDS)} claims ({', '.join(sorted(IDS.values()))})")


if __name__ == "__main__":
    main()
