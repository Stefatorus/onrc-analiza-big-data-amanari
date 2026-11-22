# Datele folosite / Data used

Mărimile și amprentele sunt cele ale fișierelor folosite de ediția publicată (22–23.11.2026). Licențele marcate
„DE VERIFICAT” nu au fost confirmate. Listele complete de SHA-256 pe fișier sunt în `docs/hashes/`.

| # | Set de date | Mărime | În depozit? | Licență / termeni |
|---|---|---|---|---|
| D1 | Arhiva BERC — articole JSON pe zi și categorie, 2023–2026 | 9,3 GB, 5.643 fișiere | **Nu** (crawler + SHA-256) | ONRC / Legea 265/2022 — **DE VERIFICAT de autor** |
| D2 | Arhiva BERC — colectare veche pe dosar (2023–2024), `results/counties*` | 2,9 GB, 80 fișiere | **Nu** (SHA-256) | ca D1 — **DE VERIFICAT** |
| D3 | `analysis_decisions.pkl` (o linie pe decizie, derivat din D1+D2) | 196.660.006 B | **Nu** (peste limita git); versiunea fără identificatori e în release (R1) | derivat; fără nume/CUI |
| D4 | Buletinele BERC 2026 (PDF) | 1,1 GB, 545 fișiere | **Nu** (downloader + SHA-256) | ca D1 — **DE VERIFICAT** |
| D5 | Bilanțuri MF 2024 și 2025 (`WEB_UU_AN2024/2025`) | 77.227.907 B + 79.502.766 B | **Nu** (descărcare automată + SHA-256) | **CC BY 4.0** (confirmat din metadatele CKAN data.gov.ro, 22.11.2026) |
| D6 | Eșantion myportal (7.469 cereri sondate, 21–22.11.2026) | 7,6 MB brut, 9 fișiere | **Nu** la nivel de cerere; doar agregatele (`docs/FROZEN.md`) | ONRC — termenii platformei; date nepublicate de ONRC |
| D7 | Notele Ministerului Justiției (30.10 și 6.11.2026) | — | cifrele, în cod (`audit_forecast.py`, `oug_2026/audit.json`) | document public, just.ro |
| D8 | Cifre oficiale (Eurostat, BNR, MF, legislație, Banca Mondială) | — | `cost_evidence/08_write_official_sources.py` (URL-uri) | termenii fiecărei surse |
| D9 | Compilația de presă (doar afirmațiile despre coadă) | 7 KB | **Da** `independent_audit/osint/` | text propriu + citări (surse indicate) |
| D10 | Intrări înghețate și derivate din portal | 64 de fișiere | **Da**, în locul lor, cu SHA-256 (`docs/FROZEN.md`, `docs/frozen_manifest.csv`) | derivate, agregate |

---

## D1 — Arhiva BERC (Buletinul Electronic al Registrului Comerțului), articole JSON

* **Sursă:** API-ul public al portalului BERC: `https://api.berc.onrc.ro/backoffice/api/article/filter-article`
  (listare pe fereastră de date) și `https://api.berc.onrc.ro/client/api/publicitySituations` (categoriile). Portal: `https://portal.berc.onrc.ro`.
* **Cum s-a obținut:** `tools/crawlBercArticles.py` (o zi pe cerere, paginat, ≤0,3 cereri/s, pauză la orice semn de blocare), condus de
  `tools/backfill_berc.sh`. API-ul cere un token „Bearer”, dat printr-un fișier (`--token-file`), care **nu se publică niciodată**.
  **DE VERIFICAT de autor:** cum se obține tokenul și dacă termenii ONRC permit colectarea automată de către terți —
  de asta depinde dacă un cititor poate reface arhiva și dacă crawlerul are loc în depozit.
* **Ce conține:** pentru fiecare publicare: număr și dată cerere, oficiu, soluție (Admis/Respins/…), data soluției, plus denumirea firmei,
  CUI, EUID, adresa, numele lichidatorului — de aceea nu se publică rând cu rând.
* **Categorii folosite:** `CERERE265`, `INMATRIC265`, `AUTO_AMANARI`, `CERERE_HJ265` (decizii); fișiere `<YYYY-MM-DD>_<CATEGORIE>.json`.
* **Acoperire la autor:** 2023-03-20 … 2026-11-20. 2023: 1.143 fișiere (1,7 GB); 2024: 1.464 (2,1 GB); 2025: 1.460 (2,9 GB); 2026: 1.576 (2,7 GB).
* **SHA-256:** `docs/hashes/articles_<an>.sha256` (amprenta listelor: 2023 `f5cd173b…`, 2024 `b231d5e1…`, 2025 `0a70cf4f…`, 2026 `38451059…`).
* **Atenție la reproducere:** BERC corectează articole (`idCorrectedArticle`) — o colectare nouă poate diferi ușor. Testul este
  numărul total de decizii din D3: **4.077.510**.

## D2 — Colectarea veche pe dosar (2023–2024)

* Fișiere `results/counties/<Județ>_results.json` și `results/counties_backup/<Județ>.json`, colectate cu un crawler mai vechi pe număr
  de dosar (aceleași endpointuri). `build_decisions.py` le unește cu D1 (fără dubluri, pe `id`).
* **SHA-256:** `docs/hashes/results_counties.sha256` (`2486f1f7…`). **De decis în faza 2:** dacă D1 singur dă tot 4.077.510 decizii, D2 devine opțional.

## D3 — `analysis_decisions.pkl`

* **Construit de:** `python -X utf8 analysis/build_decisions.py data/analysis_decisions.pkl` (din D1 + D2).
* **Coloane:** `cat, app_nr, app, res, pub, county, sol, office, code4, jtype` — fără denumiri, CUI sau adrese.
* **SHA-256 (ediția publicată):** `a63e6824311efd5c5d092a3b0aa35f5c369c8038ab6e1d666369bdc77e0cabda` · 196.660.006 octeți.
* O reconstrucție are aproape sigur **alt** SHA-256 (pickle + ordinea fișierelor + corecturi BERC); contează valorile (registrul).

## D4 — Buletinele BERC 2026 (PDF)

* **Sursă:** `https://api.berc.onrc.ro/backoffice/api/publication` (`getPublicationByYearAndNumber`, `viewPublication`) și `https://dms.berc.onrc.ro` (descărcare).
* **Cum:** `tools/downloadBulletinsSafe.py --year 2026 --start … --end … --token-file …` (limitat la rată).
* **La autor:** 545 de buletine 2026 (după `cost_evidence/README.md`: 60 din ianuarie, 1 din februarie, 482 din octombrie–noiembrie) — eșantionul nu e uniform; vezi
  `independent_audit/cost_evidence/README.md`.
* **SHA-256:** `docs/hashes/bulletins_2026.sha256` (`3ef5ed3d…`).

## D5 — Bilanțurile depuse la Ministerul Finanțelor (data.gov.ro)

* **Seturi:** `situatii_financiare_2024` (id `d3caacb6-2c08-445e-94e6-8d36d00ab250`) și `situatii_financiare_2025`
  (id `e2266fdc-0a6b-43b8-9c9f-7a6943d85b28`), organizația „Ministerul Finanțelor”.
* **URL-uri:**
  `https://data.gov.ro/dataset/d3caacb6-2c08-445e-94e6-8d36d00ab250/resource/25098618-f6a5-4610-8c7f-c0bdb801635f/download/web_uu_an2024.txt` ·
  `https://data.gov.ro/dataset/e2266fdc-0a6b-43b8-9c9f-7a6943d85b28/resource/eeecc692-d914-4d3b-b7f5-d1a8a9791979/download/web_uu_an2025.txt`
  (+ dicționarele `web_uu_an202X.csv`, 483 B).
* **Licență:** Creative Commons Attribution 4.0 (`license_id` = `CC-BY-4.0` în metadatele CKAN, citite la 22.11.2026).
* **Cum:** automat, `analysis/policy_paper_ro/audit_finance.py` (API CKAN `package_show`, verifică mărimea). Cache: `ONRC_FIN_CACHE`
  (implicit `data/mf_balances`).
* **SHA-256:** `WEB_UU_AN2024.txt` `0cc2496a17b3a7bf3405294ac26cda85f5aa2e258717027d63119e78492d21aa` ·
  `WEB_UU_AN2025.txt` `2c7e67d51f6700a28fb31644e8e2abf4334ee788f1c5fb07cb6df1a9321683e2` ·
  `WEB_UU_AN2025.csv` `c24bcdbd423ebc5c6d619ac0a9ce5bb2ff21121c151336609d1fb6c4cfa0d8ef`.
  Dacă MF republică fișierele, mărimea se schimbă și scriptul le descarcă din nou → valori posibil diferite (de semnalat).
* **Conținut:** câte un rând pe CUI cu indicatori financiari — se folosesc doar agregat, legat local de cohortele BERC.

## D6 — Eșantionul myportal

* Sondare a 7.469 de numere de cerere pe platforma myportal a ONRC (21–22.11.2026), cu stadiul fiecărei cereri (operare / registrator / soluționată).
  Folosit pentru stocul pe etape și pentru estimările din `reserves_check/`.
* **Nu se publică brut**: răspunsurile conțin UUID-uri interne, codul de înregistrare al firmei și observații în text liber.
  Amprenta brută folosită în registru (`PORTAL`): `f7ff4b0665946fa0067332c389aaae2cddd52a6b7c1f41e450220456a622fb8e`
  = SHA-256 al concatenării celor 9 fișiere `harvest_*.jsonl` în ordinea numelui — verificabilă doar de autor.
* Decizia autorului: nu se publică niciun fișier la nivel de cerere. Se publică doar rezultatele agregate derivate din eșantion
  (`docs/FROZEN.md`, tipul `portal-derived`).

## D10 — Rezultate intermediare înghețate

Lista, SHA-256 și scriptul producător pentru fiecare: `docs/frozen_manifest.csv` (explicații în `docs/FROZEN.md`). Sunt agregate (pe zi, săptămână, județ, scenariu);
scanarea de confidențialitate din faza 1 nu a găsit nume de persoane, CUI, e-mailuri sau telefoane în ele.

---

## Datele din release-ul v1.0.0 (pentru verificare încrucișată)

Generate de `tools/make_release_data.py` din `analysis_decisions.pkl`. Oricine are o colectare BERC completă le poate regenera
(`analysis/build_decisions.py`, apoi acest script). Mărimile și amprentele exacte sunt în `SHA256SUMS`, în release.

| # | Fișier | Conținut |
|---|---|---|
| R1 | `berc_decisions_min.csv.gz` | 4.077.510 decizii: `category, filed_at, decided_at, published_at, outcome, county, office, juridical_type`. **Fără** denumiri, CUI, companyCode, numere J, numere de cerere sau coduri de document. Rândurile sunt ordonate după timp, nu după vreun identificator. |
| R2 | `counter_daily_national.csv.gz` | pe zi de depunere: decizii, numere de cerere distincte (toate / cu soluție finală), numărul minim și maxim (contorul național) |
| R3 | `counter_daily_by_category.csv.gz` | aceleași valori pe zi × categorie de decizie |
| R4 | `counter_daily_by_county.csv.gz` | aceleași valori pe zi × județ (înainte de 26.07.2024, contoarele erau pe județ) |
| R5 | PDF-urile finale, `Date_ONRC_Coada_2026-11.xlsx`, `claims_registry.csv` | ediția publicată |

Verificare încorporată: din R2, scriptul reface nivelul zilnic al contorului și seriile de cereri distincte din
`reserves_check/11_inflow_counter.py`. Rezultatul coincide pe 100% din zile cu `11_daily_counter_vs_berc.csv`.
`tools/release_to_pkl.py` transformă R1 într-un `data/analysis_decisions.pkl` cu numele de coloane așteptate de scripturi,
cu `app_nr` și `code4` goale.

## Ce se poate reface din ce (fiecare afirmație: `docs/claims_reproducibility.csv`)

Toate cele 143 de afirmații publicate (PASS/WARN) sunt recalculate de `generate_claims_registry.py` din rezultatele agregate din
depozit (`run_all.py --offline`). Mai jos: ce trebuie ca să le refaceți **de la zero**.

| Nivel | Ce trebuie | Afirmații publicate | Exemple de scripturi |
|---|---|---|---|
| R | doar datele din release (R1–R4) + agregatele din depozit | 40 | `audit_forecast.py`, `forecast_grid.py`, `backtest_queue_mechanics.py`, `cost_*`, `stat_pack_ext.py`, `county_rankings.py`, `11_inflow_counter.py` (din R2) |
| J | colectarea BERC completă (identitatea firmei, numerele de cerere pe înregistrare) și/sau bilanțurile MF | 13 | `econometrics/`, `audit_finance.py`, `reserves_check/22, 23, 26`, `cost_evidence` T3–T5 |
| B | buletinele BERC 2026 (PDF) | 27 | `delay_reasons/`, `rejection_reasons/`, `cost_evidence` T1 |
| P | eșantionul myportal (nepublicat) | 25 | `reconcile_sources.py`, `stat_pack.py`, `13_stock_estimate.py` |
| F | intrare înghețată dintr-o etapă anterioară | 34 | vezi `docs/FROZEN.md` |
| D | document (lege, notă oficială, verificare manuală) | 4 | `stakeholders/LEGAL_BASIS.md` |

`stat_pack.py` rulează doar cu eșantionul myportal, deși multe dintre tabelele lui vin numai din BERC. De aceea toate afirmațiile
lui sunt la nivelul P. Clasificarea e automată, după coloana `script` a registrului (`tools/claims_tiers.py`).

**Limite:** colectarea BERC e o captură a unui API viu: BERC corectează articole, iar MF poate republica bilanțurile. O colectare
nouă poate diferi ușor. Testul este numărul de decizii (4.077.510) și valorile din registru, nu amprenta fișierelor.
