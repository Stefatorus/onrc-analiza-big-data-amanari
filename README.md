# Coada de la Registrul Comerțului — raport, date și cod (noiembrie 2026, versiunea 1.0.1)

O analiză independentă, din date deschise, a cozii de la Registrul Comerțului (ONRC), făcută de **Ștefan-Lucian Deleanu**. Datele
sunt 4.077.510 decizii BERC până la 20.11.2026, un eșantion myportal, notele Ministerului Justiției și bilanțurile depuse la MF.
Depozitul conține rapoartele, datele care le susțin și codul care le produce.

## Ce să citești

**Estimator interactiv:** [stefatorus.github.io/onrc-analiza-big-data-amanari](https://stefatorus.github.io/onrc-analiza-big-data-amanari/) — motorul de prognoză din raport, rulat în browser, cu scenarii și măsuri; [pagina de audit](https://stefatorus.github.io/onrc-analiza-big-data-amanari/audit.html) arată că reproduce exact motorul Python și cifrele raportului, plus testul pe trecut.

1. **[Ediția executivă](reports/actuale/Raport_ONRC_Coada_2026-11_EXECUTIV.pdf)** (12 p.): situația, prognoza, ce schimbă fiecare măsură, cele două cozi, costul, în grafice explicate.
2. **[Analiza proiectului de OUG](reports/actuale/Analiza_proiectului_OUG_2026-11.pdf)** (25 p.): textul integral al proiectului și nota de fundamentare, verificate față de date; efectul fiecărui articol; propuneri de completare.
3. **[Raportul complet](reports/actuale/Raport_ONRC_Coada_2026-11_COMPLET.pdf)** (140 p., versiunea 1.0.1, 23.11.2026): documentul de referință.
   Cuprinsul arată pentru cine e fiecare parte. Fiecare cifră are un cod `[Cxx]`, cu legătură spre registrul afirmațiilor.
4. **Sinteze pe instituții** (9–11 p. fiecare), în [`reports/sinteze_institutii/`](reports/sinteze_institutii/): ce se cere fiecărei instituții, în limitele competențelor ei.
   * [Ministerul Justiției](reports/sinteze_institutii/Sinteza_MJ.pdf) · [Ministerul Finanțelor și ANAF](reports/sinteze_institutii/Sinteza_MF_ANAF.pdf) · [MEDAT și ADR](reports/sinteze_institutii/Sinteza_MEDAT_ADR.pdf)
   * [Guvernul](reports/sinteze_institutii/Sinteza_Guvern.pdf) · [Parlamentul](reports/sinteze_institutii/Sinteza_Parlament.pdf) · [ONRC](reports/sinteze_institutii/Sinteza_ONRC.pdf)
5. **Analize complementare** (21.11.2026, date până la 18–20.11.2026), în [`reports/analize_complementare/`](reports/analize_complementare/).
   Pentru orice cifră, referința este raportul complet din 23.11.2026.
   * [Atlasul județean, 42 de fișe](reports/analize_complementare/Atlas_judetean_ONRC_42_fise_2026-11-21.pdf) (32 p.)
   * [Criza Registrului Comerțului, raport 2026–2028](reports/analize_complementare/Raport_ONRC_2026_2028_analiza_complementara.pdf) (36 p.)
   * [Evaluarea proiectului de OUG din 18.11.2026](reports/analize_complementare/Evaluarea_proiectului_OUG_18-11-2026.pdf) (19 p.)
   * [Analiza steelman: OUG și soluții](reports/analize_complementare/Analiza_steelman_OUG_si_solutii_2026-11-21.pdf) (18 p.)
   * [Costul economic și fiscal al cozii](reports/analize_complementare/Costul_economic_si_fiscal_al_cozii_2026-11-21.pdf) (8 p.)
   * [Cele două blocaje succesive (analiza tandem)](reports/analize_complementare/Analiza_blocajului_tandem_ONRC_2026-11-21.pdf) (4 p.)
6. **Date:**
   * [`claims_registry.csv`](analysis/raport_executiv_2026-11/claims_registry.csv): registrul afirmațiilor (fiecare cifră: sursă, script, amprentă, stare).
   * Rezultatele agregate în [`independent_audit/out/`](independent_audit/out/) și figurile (SVG) în `analysis/policy_paper_ro/figures_*`.
   * În [release-ul v1.0.0](https://github.com/Stefatorus/onrc-analiza-big-data-amanari/releases/tag/v1.0.0):
     * `Date_ONRC_Coada_2026-11.xlsx`, cu toate tabelele;
     * deciziile BERC fără identificatori (`berc_decisions_min.csv.gz`);
     * contorul zilnic al numerelor de cerere;
     * `SHA256SUMS`.
   * Surse, licențe și ce se poate reface din ce: [`docs/DATA.md`](docs/DATA.md).

## Versiuni

* **1.0.1** (23.11.2026): corecturi după revizuirea critică de către patru modele AI (formulări, coerența cifrelor, încadrarea riscului bugetar pentru 2027, definiția intervalelor, textul integral al proiectului de OUG). Valorile din registrul afirmațiilor sunt neschimbate.
* **1.0.0** (23.11.2026): prima publicare.

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
