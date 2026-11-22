# delay_reasons: de ce se amână dosarele la ONRC

> **Notă AI:** raport realizat cu ajutorul inteligenței artificiale (Claude Opus 5.5 și Gemini 4 Neon), sub îndrumarea și verificarea autorului (vezi anexa de la final). Cifrele sunt agregate și nu conțin date personale.

Aici sunt extrase, grupate și clasificate motivele de amânare („Motivul amânării”) din încheierile de amânare publicate în BERC.
Încheierile sunt date în temeiul art. 106 alin. (2) coroborat cu art. 15 din Legea 265/2022.
Lucrarea s-a făcut în regim de audit, doar în citire: nu s-a modificat niciun raport și niciun script al registrului.
S-a scris numai în acest dosar și în `../out/delay_reasons.json`.

## Pe scurt

- **Perioada.** Încheieri de amânare din **19 oct.–18 nov. 2026**: 17 zile de decizie pentru care există buletine colectate.
  Sunt **2.914 amânări** cu motiv publicat, din 289 de buletine. Ele reprezintă **12,5%** din cele 23.308 amânări din arhivă în aceeași fereastră
  și **16,2%** din amânările din zilele acoperite.
- **Motivele cele mai frecvente.** O amânare poate invoca mai multe motive, de aceea procentele adună peste 100%. IC 95% sunt grupate pe buletin.
  - obiect de activitate / coduri CAEN și declarația de autorizare: **31,7%** (30,0–33,4);
  - sediu: **21,9%** (20,4–23,4);
  - cererea, anexa fiscală și formularele: **20,7%** (19,2–22,3);
  - act constitutiv, hotărâri și mandat: **17,7%** (16,3–19,1).
- **Evitabil la depunere.** **22,9%** (21,5–24,3) dintre amânări au numai motive pe care o verificare automată la depunere le-ar fi prins.
  Aceasta este cifra principală, în varianta strictă. În **45,1%** (43,3–46,8) dintre amânări cel puțin un motiv era evitabil; aceasta este limita superioară.
- **Validare.** Am verificat manual un eșantion de 100 de amânări. Setul complet de motive al unei amânări a fost identic cu cel stabilit manual
  în **55%** din cazuri (IC 45–64%). Precizia este 0,76 și recall-ul 0,73. Clasificarea a găsit cel puțin un motiv corect în 82% din cazuri.
  Pe aceleași 100 de amânări, ponderea evitabilă strictă este 26% după clasificare și 27% după evaluarea manuală; cele două coincid în 89% din cazuri.

## Fișiere

| script | ce face | ieșire |
|---|---|---|
| `01_extract_postponements.py` | parcurge **toate cele 545** PDF-uri BERC 2026 cu PyMuPDF, ca în `cost_evidence/01`; extrage fiecare „Comunicare încheiere de amânare”: data încheierii, termenul, nr./data cererii, textul motivului | `_tmp/` (șters), `01_*.out.txt` |
| `02_normalize_split.py` | elimină dublurile; leagă fiecare amânare de arhivă (AUTO_AMANARI, nr. cerere + zi); anonimizează textul; separă motivul-standard și segmentele de motiv | `_tmp/` (șters) |
| `03_embed_cluster.py` | embeddings locale (multilingual-e5-small), UMAP, HDBSCAN; verificare încrucișată cu k-means | `_tmp/` (șters), `03_*.out.txt` |
| `04_classify.py` | numele clusterelor; maparea pe taxonomie; clasificatorul independent pe cuvinte-cheie; eticheta finală (hibridă) | `04_classify.out.json` |
| `05_manual_sample.py`, `05_manual_labels.py` | eșantionul de 100 (seed 20261122) și etichetele manuale, identificate numai prin poziția în eșantion | etichete fără text |
| `06_validate.py` | acuratețe, precizie și recall pe categorie, IC Wilson | `06_validate.out.json` |
| `07_results.py` | acoperire, ponderi, ponderi pe categorii cu IC, evoluție săptămânală, evitabilitate, durate, figuri, JSON | `07_results.out.json`, `taxonomy.csv`, `figures/`, `../out/delay_reasons.json` |

Ordinea de rulare: 01 → 07. Scripturile 03 și 05 sunt deterministe (seed 42 și 20261122).
Am rulat 03 de două ori din aceleași embeddings și am obținut clustere identice.
Dacă embeddings se recalculează pe alt hardware, numerotarea clusterelor se poate schimba, iar 04 se oprește cu mesaj.

## Metodă

1. **Extragere.** Fiecare notificare are câmpurile „Din data”, „Solutie: Amânat”, „Motivul amânării: …”, „Termen pentru soluționare”, „nr. cerere” și „data cerere”.
   Am găsit 3.232 de potriviri ale titlului. Dintre ele, 291 sunt titluri de cuprins (exact una pe buletin), iar 2.941 sunt notificări reale.
   După eliminarea dublurilor (nr. cerere + zi) rămân 2.930. Am exclus 16 din februarie 2026, deci rămân **2.914** în fereastră.
   Toate au putut fi legate de arhivă (AUTO_AMANARI) prin nr. cerere și ziua deciziei.
2. **Motivul-standard.** Programul registrului tipărește înaintea textului liber unul sau mai multe din patru motive-standard.
   Acestea sunt categoria oficială disponibilă: „nu sunt îndeplinite condițiile legale” 55,9%, „documentația este incompletă” 31,9%,
   „există neconcordanțe între documente” 10,3%, „actele nu îndeplinesc condițiile de formă” 5,8%.
   Sunt prea generale ca să explice cauza, de aceea am analizat textul liber.
3. **Anonimizare** (înainte de orice analiză):
   - textul a fost adus fără diacritice și cu litere mici;
   - au fost mascate e-mailurile, nr. de ordine din registru, CUI/CNP și orice număr lung, datele, sumele, adresele (cuvânt-cheie + elementele care urmează), numele precedate de „domnul/doamna/asociatul…” și inițialele;
   - a rămas o **listă albă de vocabular**: un cuvânt se păstrează doar dacă apare în ≥8 amânări, din ≥4 buletine și ≥3 județe. Restul devine `<x>` (3,4% din cuvinte);
   - trimiterile la lege s-au păstrat (ex. `legea_129_2019`), pentru că nu sunt date personale.
4. **Segmentare (mai multe motive pe amânare).** Textul fiecărui motiv-standard a fost separat în segmente la „;”, „*”, liniuțe precedate de spațiu (nu „declarația-tip”), enumerări și fraze care încep cu „se va depune / nu s-a…”.
   Fragmentele care conțin doar temei legal au fost lipite de segmentul anterior. Am eliminat formulele standard („documentele se vor depune cu cel puțin o zi lucrătoare…”).
   Rezultat: 5.882 de segmente, în medie 2 pe amânare (maximum 17).
5. **Embeddings și clustere.**
   - modelul `intfloat/multilingual-e5-small` rulează local, pe GPU; niciun text nu a fost trimis în afara calculatorului;
   - UMAP (10 dimensiuni, cosinus) urmat de HDBSCAN (min_cluster_size 20) au produs **68 de clustere**; 24% din segmente au rămas zgomot;
   - zgomotul a fost atașat la cel mai apropiat centroid (prag = percentila 10 a similarității membrilor), apoi prin cei 15 vecini cei mai apropiați;
   - pentru comparație, k-means cu k ales după silhouette (8–30) a dat k = 18 (silhouette 0,48). Concordanța cu HDBSCAN este modestă (ARI 0,35);
   - am citit fiecare cluster (termenii c-TF-IDF și frazele cele mai centrale, mascate) și l-am numit în română. Lista este în `04_classify.py` (`CLUSTER_MAP`) și în `taxonomy.csv`;
   - clusterele cu formule sau numai temei legal (8 clustere) sunt excluse din categorii;
   - clusterele au fost apoi grupate în **12 categorii** (tabelul de mai jos).
6. **Clasificator separat pe cuvinte-cheie** (`RULES` în 04). Este un mecanism diferit, dar a fost scris după citirea clusterelor, deci nu este complet independent.
   **Eticheta finală (hibridă)** a fost fixată înainte de verificarea manuală, după aceste reguli, în ordine:
   1. segmentele din clusterele generice rămân generice;
   2. altfel se păstrează categoria clusterului, dacă o confirmă o regulă;
   3. altfel se ia categoria regulii cu prioritate maximă;
   4. altfel se păstrează categoria clusterului.

   O amânare primește toate categoriile segmentelor ei.

## Taxonomie, ponderi și evitabilitate

„Pondere” înseamnă procentul de amânări care invocă categoria. IC 95% este estimat prin raport, cu grupare pe buletin, ca în `cost_evidence/03`.
Coloana „ponderată” este reponderată (raking) pe marginalele județ × săptămână din arhivă.
Ultima coloană numerică compară, pe aceleași 100 de amânări, clasificarea automată cu evaluarea manuală.
„Neclasificat” nu înseamnă „fără motiv”: la verificarea manuală, toate cele 5 cazuri de acest fel din eșantion aveau un motiv concret, ascuns după o formulă standard („amână cauza pentru…”).

| categorie | pondere | IC 95% | ponderată | eșantion 100: prezis / manual | evitabil la depunere |
|---|---|---|---|---|---|
| Obiect de activitate / coduri CAEN și declarația de autorizare | 31,7% | 30,0–33,4 | 32,5% | 26% / 32% | parțial |
| Sediu: dovada folosinței, valabilitate, acordul vecinilor/asociației, adresă | 21,9% | 20,4–23,4 | 21,9% | 14% / 14% | parțial |
| Cererea de înregistrare, anexa fiscală, formulare | 20,7% | 19,2–22,3 | 20,5% | 19% / 12% | da |
| Act constitutiv, hotărâri/decizii, act modificator, mandat administrator | 17,7% | 16,3–19,1 | 17,5% | 23% / 21% | parțial |
| Solicitant/deponent: identitate, împuternicire, calitatea semnatarului | 11,3% | 10,2–12,5 | 11,2% | 11% / 11% | da |
| Date de identificare asociați/administratori | 11,0% | 9,8–12,1 | 11,1% | 16% / 18% | da |
| Avize/atestări ale altor instituții (cazier fiscal, ANAF, profesii) | 9,5% | 8,5–10,6 | 9,1% | 7% / 11% | parțial |
| Capital social: vărsăminte, părți sociale, aport | 8,5% | 7,5–9,5 | 8,7% | 12% / 13% | parțial |
| Semnătură (electronică/olografă) și forma înscrisurilor | 4,8% | 4,0–5,6 | 4,8% | 5% / 6% | da |
| Neclasificat (clasificatorul nu a găsit nicio categorie) | 4,5% | 3,8–5,2 | 4,7% | 5% / 0% | n/a |
| Beneficiari reali | 3,6% | 2,9–4,4 | 3,7% | 4% / 3% | da |
| Denumire (rezervare, formă) | 2,5% | 1,9–3,0 | 2,3% | 0% / 0% | da |
| Tarife / contor de caractere | 1,7% | 1,2–2,2 | 1,7% | 1% / 2% | da |

O amânare are în medie 1,45 categorii: 62% au una singură, 23% au două, 11% au trei sau mai multe.
Evitabilitatea este evaluarea auditorului, nu o clasificare ONRC. Motivarea pe categorie este în `taxonomy.csv`, pe scurt:
- **da:** câmpuri și formulare, semnătura electronică (validator eIDAS), împuternicire, compararea datelor de identitate cu registrul, obligația de beneficiar real dedusă din tipul modificării, regulile de denumire, calculul tarifului;
- **parțial:** CAEN (validarea codurilor Rev.3 și a limitelor PFA se poate automatiza, activitățile condiționate nu), sediu (data expirării, acordul vecinilor), act constitutiv (prezența și ordinea datelor), capital, cazier/ANAF (interoperabilitate) față de autorizațiile profesionale.

Pentru evitabilitate există trei variante:
- **strictă**, cifra principală: toate motivele invocate sunt „da”, deci amânarea nu ar fi avut loc: **22,9%** (21,5–24,3); ponderat 22,4%.
  Fără cele neclasificate, ponderea este 24,0% (22,5–25,5). Pe eșantionul de 100: 26% după clasificare și 27% manual, cu acord în 89% din cazuri;
- **cel puțin un motiv „da”**, limita superioară: **45,1%** (43,3–46,8). Pe eșantion: 46% după clasificare și 47% manual, cu acord în 79% din cazuri;
- **toate motivele „da” sau „parțial”:** 95,5%. Aproape nicio amânare nu ține numai de judecata juridică a registratorului.

## Validare

- **Eșantion manual.** Am tras 100 de amânări aleator, cu seed fix, și le-am etichetat din textul anonimizat, înainte de a vedea predicțiile.

| clasificator | set identic | IC Wilson | ≥1 motiv corect | Jaccard mediu | precizie / recall | acuratețe pe etichetă |
|---|---|---|---|---|---|---|
| **final (hibrid)** | **55%** | 45–64 | 82% | 0,68 | **0,76 / 0,73** | 94,1% |
| numai clustere | 45% | 36–55 | 77% | 0,61 | 0,68 / 0,65 | 92,2% |
| numai reguli | 43% | 34–53 | 90% | 0,67 | 0,66 / 0,88 | 93,3% |

  Pe categorii, varianta finală:
  - sediu: precizie 0,93, recall 0,93;
  - capital: 1,00 și 0,92;
  - CAEN: 0,85 și 0,69;
  - solicitant: 0,82 și 0,82;
  - act constitutiv: 0,74 și 0,81;
  - asociați: 0,69 și 0,61;
  - alte instituții: 0,86 și 0,55;
  - **cererea/formularele: precizie 0,37**, categoria este supra-atribuită, pentru că textele pomenesc frecvent „cererea de înregistrare” ca vehicul al corecturii.

  Ajustată cu precizie/recall, ponderea categoriei „cererea” ar fi ~13%, nu 21%; ponderea CAEN ar fi ~39%, iar cea a altor instituții ~15%.
  Ponderile ajustate sunt în JSON (`precision_recall_adjusted`).
  Acuratețea pe etichetă este umflată de cazurile negative corecte: dacă nu s-ar prezice nimic, ea ar fi tot ~89%. De aceea măsura principală este setul identic.
- **Concordanța între cele două mecanisme**, clustere și reguli (kappa Cohen, la nivel de amânare):
  - alte instituții 0,81, beneficiari reali 0,80, capital 0,74, sediu 0,68, CAEN 0,65;
  - act constitutiv 0,39, asociați 0,34, denumire 0,36, **cererea 0,27**.

  Categoriile cu kappa mic sunt și cele mai nesigure în eșantionul manual.
- **Acoperire și reprezentativitate.**
  - Buletinele colectate acoperă 17 din 23 de zile lucrătoare din fereastră.
  - În zilele acoperite, proporția amânărilor din arhivă care au și motiv în PDF variază de la sub 1% (zile cu un singur buletin) la 30%.
  - Pe județe, acoperirea variază între 8,7% și 17,4%, cu coeficient de variație 0,15.
  - Structura pe tip de profesionist (J/F) este aceeași ca în arhivă: J 63,5% față de 63,6%.
  - Reponderarea pe județ × săptămână schimbă ponderile cu cel mult 0,9 puncte procentuale (efect de design Kish 1,19).
  - Pe săptămâni, acoperirea este între 5,7% (19–25 oct., 2 zile) și 15,8%.

## Evoluția săptămânală (figura b)

**Ponderile sunt stabile pe cele cinci săptămâni. Nu se poate demonstra nicio tendință.**
- Săptămâna 19–25 oct. este practic o singură zi: 252 din 260 de amânări sunt din 20 oct.
- Intervalele grupate pe buletin subestimează variația de la o zi la alta.
- CAEN scade de la 39% la ~30%.
- „Alte instituții” trece de la 5,0% (2,3–7,7) la 11,6% (9,6–13,5) în 9–15 nov., apoi revine la 7,6%.
- Ponderea evitabilă strictă trece de la 18,8% la 26,5%.

Toate aceste variații compară în esență o zi cu restul perioadei și nu trebuie citite ca tendințe.

## Durate (legate prin nr. cerere + data cererii)

- Termenul acordat la amânare are mediana **16 zile** pentru toate categoriile.
- De la depunere la amânare trec în mediană **43 de zile** (IQR 39–54). Coada de așteptare apare deci înaintea amânării, nu din cauza ei. Valoarea este similară între categorii: 42–48,5 zile.
- Până la 20 nov. 2026 (sfârșitul arhivei) se rezolvaseră 58% din dosarele amânate.
  - Mediana Kaplan-Meier de la depunere la decizia finală: **59 de zile** (57–63 pe categorii).
  - Mediana de la amânare la decizia finală: 16 zile; la capital 11,6 zile, la semnătură 14,4 zile.
  - Aceste valori sunt cenzurate: majoritatea termenelor cad după sfârșitul arhivei.
- Dintre dosarele rezolvate, 70% au fost admise.
  - Cel mai mare procent de admitere: beneficiari reali, 88%.
  - Cele mai mici: alte instituții, 59%; tarife, 56%.

## Limite

- **Eșantion de buletine, nu recensământ.** Arhiva de buletine conține doar ce s-a colectat. Ianuarie are buletine, dar nicio notificare de amânare.
  Concluziile se referă la 19 oct.–18 nov. 2026; nu se pot extinde la Jan–Sep.
  Intervalele de încredere reflectă numai eșantionarea între buletinele colectate, nu modul în care au fost colectate.
- **Numitorul.** Arhiva pierde amânări în câteva zile (vezi `../out/missing_postponements_sensitivity.json`), deci acoperirea reală poate fi puțin mai mică.
- **Clasificare imperfectă.** Setul exact de motive este corect în 55% din cazuri.
  Categoria „cererea/formulare” este supra-estimată (precizie 0,37). CAEN și „alte instituții” sunt probabil sub-estimate.
  Eșantionul manual are un singur evaluator, un model AI, fără al doilea codificator.
- **Granițe între categorii.** Același defect poate fi încadrat în categorii diferite, de exemplu o declarație de autorizare semnată de altcineva: CAEN sau semnătură.
  Regula aplicată este în `05_manual_labels.py`.
- **Evitabilitate.** Este o judecată normativă a auditorului despre ce poate verifica un formular sau un serviciu electronic. ONRC nu a confirmat-o.
- **Durate.** Sunt cenzurate. Timpul de la depunere la amânare are aceeași mediană în eșantion ca în arhivă (43 de zile), dar coada este puțin mai lungă: IQR 39–54 în eșantion, față de 38–50 în arhivă.
- **Clustere.** Ele depind de versiunile pachetelor și de embeddings; vezi mai jos.

## Confidențialitate

- Ieșirile conțin doar agregate.
- Exemplele din `taxonomy.csv` sunt fraze generice scrise de auditor, nu copiate din notificări.
- Etichetele manuale sunt indexate doar după poziția în eșantion.
- Toate fișierele intermediare la nivel de rând (`_tmp/`: texte, nr. cerere, embeddings, fișa de inspecție a clusterelor) au fost **șterse** la final. Se refac rulând 01–03.

## Mediul Python (modificări în `venv`)

- **Adăugate:** `anyio 4.16.0` (actualizat), `sentence-transformers 3.4.1`, `transformers 4.46.3`, `tokenizers 0.20.3`, `huggingface_hub 0.29.3`, `umap-learn 0.5.7`, `pynndescent 0.7.0`, `numba 0.68.1`, `llvmlite 0.50.0`, plus dependențe mici (`safetensors`, `hf_xet`, `typer`, `rich` etc.).
- **Incident.** O primă instalare a actualizat automat `numpy` (la 2.4.6), `scipy` și `scikit-learn`, ceea ce a stricat `pandas 2.2.1`. Le-am readus la `numpy 1.26.4`, `scikit-learn 1.4.1.post1` și `scipy 1.13.1`.
  Versiunile anterioare exacte ale lui scipy și numpy nu erau înregistrate; 1.13.1 și 1.26.4 sunt estimări compatibile cu instalarea din 2024.
- **Actualizate și lăsate așa:** `joblib 1.6.0`, `threadpoolctl 3.8.0`, `regex`, `typing_extensions`, `idna`, `pygments`.
- **Readus:** `h11` la 0.14.0, pentru `httpcore 1.0.4`.
- **Dezinstalate:** `httpx2` și `httpcore2`, orfane după instalare.
- `pip check`: fără conflicte. Test rapid de import (pandas, statsmodels, sklearnex, fitz, PyPDF2, matplotlib, torch, httpx, anthropic, openai): OK.
- Greutățile modelului `intfloat/multilingual-e5-small` au fost descărcate o dată de pe Hugging Face. Textul buletinelor nu a fost trimis nicăieri.

## Anexă: utilizarea AI

- **Modele.** Raportul este realizat cu Claude Opus 5.5 (Anthropic) și Gemini 4 Neon (Google), conform textului comun din `analysis/policy_paper_ro/ai_annex.py`.
  Această analiză (scripturi, clasificare, text) a fost produsă de Claude Opus 5.5. Modelul de embeddings `multilingual-e5-small` a rulat local.
- **Ce a făcut AI-ul:**
  - extragerea și anonimizarea textelor;
  - clusterizarea și denumirea clusterelor;
  - regulile pe cuvinte-cheie;
  - **eticheta manuală a celor 100 de cazuri**: evaluatorul este modelul AI, nu un om;
  - evaluarea evitabilității;
  - figurile și acest README.
- **Ce rămâne la autor:** cerințele, verificarea, decizia de publicare și răspunderea.
- **Incertitudini:** clasificarea are acuratețea de mai sus. Evitabilitatea este o judecată, nu o măsurătoare. Acoperirea buletinelor este parțială.
- **Recomandat:** o a doua etichetare umană pe un eșantion nou și validarea categoriilor „evitabile” cu ONRC.
