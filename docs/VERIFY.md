# Cum verificați o afirmație [Cxx] / How to check a [Cxx] claim

Fiecare cifră din rapoarte are un cod `[Cxx]`. În raportul complet, codul este o legătură către rândul lui din registru.

1. **Rândul din registru.** Căutați id-ul în `analysis/raport_executiv_2026-11/claims_registry.csv`. Coloanele:
   `text`, `value`, `unit`, `level` (A/E = recalculat din date brute; B/P = model sau estimare, doar cu interval;
   C/S = cifră oficială citată), `status` (PASS = publicabil; WARN = doar împreună cu `rezerva_obligatorie`;
   FAIL = retras, nu se publică), `source`, `script`, `data_sha256`, `data_date`, `public_ro`.
2. **Scriptul.** Coloana `script` numește scriptul și, de obicei, secțiunea care produce valoarea (de ex.
   `stat_pack.py (little)` sau `forecast_grid.py → out/forecast_grid.json`). Valoarea este citită de
   `independent_audit/generate_claims_registry.py` din fișierul de rezultate. Căutați id-ul în acest script ca să vedeți din ce câmp vine.
3. **Datele.** `data_sha256` este amprenta fișierului pe care stă afirmația: arhiva BERC (`a63e6824…`, vezi `docs/DATA.md`),
   eșantionul myportal (`f7ff4b06…`, nepublicat) sau unul dintre fișierele din `independent_audit/out/` și `audit_data/`.
   Verificați cu `sha256sum <fișier>` (Windows: `certutil -hashfile <fișier> SHA256`).
4. **Refaceți valoarea.**
   * Din depozit: `python -X utf8 run_all.py --offline` regenerează registrul. `git diff analysis/raport_executiv_2026-11/claims_registry.csv`
     trebuie să nu arate nicio diferență.
   * De la zero: `docs/claims_reproducibility.csv` spune, pentru fiecare id, de ce aveți nevoie (R = doar datele din release;
     J = colectarea BERC completă / MF; B = buletinele PDF; P = eșantionul myportal; F = intrare înghețată; D = document).
5. **Dovezi formale.** Pentru afirmațiile marcate în Volumul 6, `formal_proofs/OnrcProofs/RegistryV3Witnesses.lean` conține
   enunțul cu cifrele din registru. `lake build` (în `formal_proofs/`) eșuează dacă o cifră nu-l mai satisface.
   `independent_audit/out/lean_v3_results.json` dă rezultatul.
6. **Textul.** `lint_numbers.py <raport.html>` verifică faptul că fiecare număr din proză are acoperire în registru și că nu este
   citată nicio afirmație FAIL.
7. **Comparație cu ediția publicată.** `python -X utf8 tools/compare_outputs.py <director cu ediția publicată>` compară la nivel de
   valori: registrul, JSON-urile, CSV-urile, foile xlsx și textul paginilor PDF.

Afirmațiile retrase (FAIL) rămân listate în registru, cu motivul: C02, C10, C12, C20 și C24–C27. Nu apar în rapoartele publicate.
