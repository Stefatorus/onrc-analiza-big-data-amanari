# Coada de la Registrul Comerțului — raport, date și cod (noiembrie 2026)

O analiză independentă, din date deschise, a cozii de la Registrul Comerțului (ONRC), făcută de **Ștefan-Lucian Deleanu**. Datele
sunt 4.077.510 decizii BERC până la 20.11.2026, un eșantion myportal, notele Ministerului Justiției și bilanțurile depuse la MF.
Depozitul conține rapoartele, datele care le susțin și codul care le produce.

## Ce să citești

1. **[Ediția executivă](reports/actuale/Raport_ONRC_Coada_2026-11_EXECUTIV.pdf)** (9 p.): situația, cauzele, ce se poate decide acum.
2. **[Raportul complet](reports/actuale/Raport_ONRC_Coada_2026-11_COMPLET.pdf)** (138 p., 23.11.2026): documentul de referință.
   Cuprinsul arată pentru cine e fiecare parte. Fiecare cifră are un cod `[Cxx]`, cu legătură spre registrul afirmațiilor.
3. **Analize complementare** (21.11.2026, date până la 18–20.11.2026), în [`reports/analize_complementare/`](reports/analize_complementare/).
   Pentru orice cifră, referința este raportul complet din 23.11.2026.
   * [Atlasul județean, 42 de fișe](reports/analize_complementare/Atlas_judetean_ONRC_42_fise_2026-11-21.pdf) (32 p.)
   * [Criza Registrului Comerțului, raport 2026–2028](reports/analize_complementare/Raport_ONRC_2026_2028_analiza_complementara.pdf) (36 p.)
   * [Evaluarea proiectului de OUG din 18.11.2026](reports/analize_complementare/Evaluarea_proiectului_OUG_18-11-2026.pdf) (19 p.)
   * [Analiza steelman: OUG și soluții](reports/analize_complementare/Analiza_steelman_OUG_si_solutii_2026-11-21.pdf) (18 p.)
   * [Costul economic și fiscal al cozii](reports/analize_complementare/Costul_economic_si_fiscal_al_cozii_2026-11-21.pdf) (8 p.)
   * [Cele două blocaje succesive (analiza tandem)](reports/analize_complementare/Analiza_blocajului_tandem_ONRC_2026-11-21.pdf) (4 p.)
4. **Date:**
   * [`claims_registry.csv`](analysis/raport_executiv_2026-11/claims_registry.csv): registrul afirmațiilor, 151 de rânduri.
   * Rezultatele agregate în [`independent_audit/out/`](independent_audit/out/) și figurile (SVG) în `analysis/policy_paper_ro/figures_*`.
   * În [release-ul v1.0.0](https://github.com/Stefatorus/onrc-analiza-big-data-amanari/releases/tag/v1.0.0):
     * `Date_ONRC_Coada_2026-11.xlsx`, cu toate tabelele;
     * deciziile BERC fără identificatori (`berc_decisions_min.csv.gz`);
     * contorul zilnic al numerelor de cerere;
     * `SHA256SUMS`.
   * Surse, licențe și ce se poate reface din ce: [`docs/DATA.md`](docs/DATA.md).

## Cum verificați o cifră `[Cxx]`

1. **Registru.** Găsiți rândul în `claims_registry.csv`: valoarea, nivelul, starea (PASS, sau WARN doar cu rezerva), sursa și
   scriptul.
2. **Script.** Scriptul numit în rând produce fișierul de rezultate. `independent_audit/generate_claims_registry.py` citește
   valoarea din acel fișier.
3. **Date.** `data_sha256` este amprenta datelor pe care stă cifra. `python -X utf8 run_all.py --offline` reface registrul și
   dovezile Lean din datele din depozit, iar `git diff` arată orice diferență.

Pași detaliați: [`docs/VERIFY.md`](docs/VERIFY.md). Intrările preluate din etape anterioare, cu amprentă și producător:
[`docs/FROZEN.md`](docs/FROZEN.md).

## Licență

Cod și documentație: **MIT** (© 2026 Ștefan-Lucian Deleanu). Fonturile din `analysis/policy_paper_ro/fonts/` rămân sub **SIL OFL 1.1**.
Datele rămân sub termenii surselor: bilanțurile MF sunt CC BY 4.0, iar BERC și myportal au termenii ONRC. Citare: `CITATION.cff`.

## Utilizarea AI

Raport realizat cu ajutorul inteligenței artificiale (Claude Opus 5.5 și Gemini 4 Neon), sub îndrumarea și verificarea autorului.
Același lucru e valabil pentru acest cod. Detalii: anexa „Utilizarea AI, cerințe, surse și limite” din raportul complet.

## Declarație de interes

Autorul a avut o activitate de înființare de societăți, acum închisă. În 2024, autorul a semnalat public vulnerabilități ale
platformei myportal. Contact: contact@stefandeleanu.ro.

---

*English:* an independent, open-data analysis of the Romanian Trade Registry (ONRC) queue, November 2026.
* **Read:** the executive edition first, then the 138-page complete report (the reference), the companion analyses of 21.11.2026,
  then the data.
* **Verify:** each figure `[Cxx]` → its row in `claims_registry.csv` → the script → the data and its SHA-256.
* **Licence:** code MIT, fonts SIL OFL 1.1.
* **AI use:** produced with AI assistance (Claude Opus 5.5, Gemini 4 Neon) under the author's guidance and verification.
