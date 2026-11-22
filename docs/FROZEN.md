# Intrări înghețate / Frozen inputs

Unele fișiere citite de registrul afirmațiilor sau de figuri **nu sunt refăcute** de `run_all.py`. Ele sunt livrate exact cum au
intrat în ediția publicată. Pentru fiecare, `docs/frozen_manifest.csv` dă SHA-256-ul, mărimea, tipul, scriptul care l-a produs și o notă.
`python -X utf8 run_all.py --only verify-inputs` verifică amprentele. Afirmațiile care depind de aceste fișiere sunt reproductibile
doar **de la aceste fișiere încolo** (nivelul F în `docs/claims_reproducibility.csv`).

| Tip | Câte | Ce înseamnă |
|---|---|---|
| `frozen` | 24 | rezultat al unei etape anterioare a analizei (atlas județean, analiza tandem, modelul OUG anterior, motorul de soluții, ledger-ul ediției v2, seria zilnică master), al unui script care nu e publicat aici sau scris de mână (`model_inputs_v2.json`, `persona_review.json`, `per_county_tandem_2026-11-21.csv`). `build_oug_review.py` și `steelman_and_solutions_engine.py` sunt incluse doar ca **text**: registrul citește din ele câteva cifre (C83 și cifrele postate de MJ). Nu se rulează aici. |
| `curated` | 8 | intrări scrise de autor sau de auditor: baza legală (`stakeholders/`), taxonomiile motivelor, cifrele oficiale cu URL, parametrii legali ai econometriei, compilația de presă |
| `portal-derived` | 32 | agregate din eșantionul myportal (`LOCKED_CONSTANTS.json`, `stat_pack.json` și `stat_pack/*.csv`, `reserves_check/12–13*`). Eșantionul la nivel de cerere nu e publicat, așa că etapele `[portal]` din `run_all.py` sunt sărite și se folosesc aceste fișiere. |

Amprenta `PORTAL` din registru (`data_hashes.json`, `portal_harvest_all`) este SHA-256 al concatenării celor 9 fișiere de
recoltare brute, în ordinea numelui. Doar autorul o poate verifica.

## Probleme cunoscute

* `data_hashes.json` a fost scris de mână. Intrarea lui pentru `LOCKED_CONSTANTS.json` nu corespunde versiunii finale a fișierului.
  Registrul folosește doar intrările BERC și PORTAL; `tools/hash_inputs.py` îl regenerează.
* Fișierele `audit_data/cost_*.csv` au fost produse de `audit_costs.py` dintr-o versiune anterioară a arhivei BERC (21.11, 01:18;
  arhiva finală e din 21.11, 03:31). O rulare nouă poate schimba ușor cifrele de cost care depind de ele.
* `generate_claims_registry.py` verifică numărul de buletine PDF doar când arhiva e montată (`ONRC_BULLETINS_DIR`). În sursa originală,
  calea era stricată de caractere de control, așa că verificarea nu rula; aici e reparată.
