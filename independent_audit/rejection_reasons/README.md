# rejection_reasons: de ce sunt respinse cererile la ONRC

> **Notă AI:** analiză realizată cu ajutorul inteligenței artificiale (Claude Opus 5.5), sub îndrumarea și verificarea autorului (vezi anexa de la final). Cifrele sunt agregate și nu conțin date personale.

Aici sunt extrase, grupate și clasificate motivele de respingere scrise în încheierile de respingere publicate integral în BERC
(„… urmează a respinge prezenta cerere, pe motiv: … DISPUNE Respinge …”). Metoda este cea validată pentru amânări în `../delay_reasons`
(aceleași funcții de anonimizare, același model local de embeddings, aceleași 12 categorii și reguli, aceleași IC grupate pe buletin).
Lucrarea s-a făcut în regim de audit, doar în citire: nu s-a modificat niciun raport, niciun script al registrului și nimic din `delay_reasons`.
S-a scris numai în acest dosar și în `../out/rejection_reasons.json`.

## Pe scurt

- **Respingerea este, aproape mereu, capătul unei amânări neîndeplinite.** Cifra nu depinde de clasificare: în arhivă, **97,6%** (IC 97,3–97,9)
  din cele 8.710 respingeri din 19 oct.–18 nov. 2026 au o amânare anterioară a aceleiași cereri (același nr. și aceeași zi de depunere):
  97,9% la mențiuni, 94,5% la înmatriculări. Respingerea vine în mediană la **16 zile** după amânare (IQR 16–17), adică exact la termenul acordat,
  și la 51 de zile de la depunere. Cifra este o limită inferioară, pentru că arhiva pierde câteva amânări.
  - În text, **84,6%** (82,1–87,1) dintre respingeri spun explicit că observațiile din încheierea de amânare nu au fost remediate (77,5%)
    sau au fost remediate doar parțial / completarea era ea însăși greșită (7,1%). Pe eșantionul manual de 150: 86,7% (80,3–91,2).
  - Și respingerile care nu pomenesc amânarea în text („directe”, 12,8%) au, în 90% din cazuri (112 din 124), o amânare anterioară în arhivă.
  - Pentru context: dintre cererile amânate în 1 sep.–15 oct. 2026 și soluționate până la 20 nov., **36,1%** au fost respinse, 62,2% admise și 1,7% retrase („Renunțat”).
- **Cauzele respingerii sunt aceleași ca ale amânării.** Pentru 47 de respingeri a căror încheiere de amânare este și ea în buletinele colectate,
  cauzele respingerii se suprapun cu cele ale amânării în 96% din cazuri. În 85% din cazuri, respingerea nu adaugă nicio cauză nouă.
  Structura pe categorii este apropiată de cea a amânărilor. Singura diferență consistentă ca direcție la toate cele trei măsuri (clasificator, ajustat, manual; IC-urile manuale se suprapun),
  este **capitalul social, mai rar la respingeri** (raport ≈0,5): problemele de vărsământ se rezolvă de obicei la termen.
- **Cauze principale** (% din respingeri; o respingere poate avea mai multe cauze; clasificatorul subestimează, vezi coloana „manual”):
  obiect de activitate / CAEN și declarația de autorizare **36,2%** (32,9–39,6); sediu 15,1%; act constitutiv/hotărâri 16,2%; solicitant/împuternicire 12,1%;
  avize ale altor instituții (cazier fiscal, ANAF la cesiune, atestate) 9,0%; date de identificare 9,0%.
- **Înmatriculări vs. mențiuni.** La înmatriculări (n=83, IC largi) domină **cazierul fiscal / avizele** (36,1%, IC Wilson 26,6–46,9, față de 6,4% la mențiuni),
  sediul (22,9%) și denumirea (10,8%). La mențiuni domină CAEN (37,9%), mai ales actualizarea la CAEN Rev.3 și declarația de autorizare.
- **Evitabil la depunere.** Evaluarea manuală pe 150 de respingeri: **28%** (IC 21–36) au numai cauze pe care o verificare automată la depunere le-ar fi prins
  (strict). În **55%** (47–62) cel puțin o cauză era evitabilă (limita superioară). Clasificatorul dă 16,6% și 30,6%; acestea sunt **estimări inferioare**,
  pentru că recall-ul lui este ~0,65.
- **Validare.** Am etichetat manual 100 de respingeri înainte de a construi clasificatorul și încă 50, eșantion nou, după ce l-am fixat.
  Pe ambele loturi (150), mecanismul procedural este corect în 92,7% din cazuri. Setul exact de cauze este corect în 44% din cazuri (IC 36–52),
  cu precizie 0,80 și recall 0,65. Pe lotul nou de 50, setul exact este corect în 38% din cazuri, cu precizie 0,79 și recall 0,59.

## Fișiere

| script | ce face | ieșire |
|---|---|---|
| `01_extract_rejections.py` | parcurge **toate cele 545** PDF-uri BERC 2026 (PyMuPDF); scoate antetele de pagină înainte de lipire; extrage încheierile de respingere (doar textul dintre „urmează a respinge … pe motiv” și „DISPUNE”), intrările din cuprins (secțiunea înmatriculare / alte cereri) și, prin `delay_reasons/01.parse` (importat, doar citire), notificările de amânare ale acelorași cereri | `_tmp/` (șters), `01_*.out.txt` |
| `02_normalize_split.py` | elimină dublurile; leagă de arhivă (decizia Respins + amânările anterioare); citește stratul procedural (A); anonimizează și segmentează stratul cauzal (B) cu funcțiile din `delay_reasons/02` | `_tmp/` (șters), `02_*.out.txt` |
| `03_embed_cluster.py` | embeddings locale (multilingual-e5-small, funcția din `delay_reasons/03`), UMAP, HDBSCAN (min_cluster_size 12); verificare cu k-means | `_tmp/` (șters), `03_*.out.txt` |
| `04_classify.py` | numele celor 61 de clustere (`CLUSTER_MAP`), taxonomia, regulile (cele din `delay_reasons/04` + 2 reguli noi), eticheta finală (hibridă) | `04_classify.out.json` |
| `05_manual_sample.py`, `05_manual_labels.py` | două eșantioane (seed 20261122: 100; seed 20261123: 50, disjunct); etichetele manuale sunt indexate doar după poziție | etichete fără text |
| `06_validate.py` | acuratețe, precizie și recall, pe fiecare lot și cumulat, IC Wilson | `06_validate.out.json` |
| `07_results.py` | acoperire, legătura cu arhiva, mecanism, ponderi pe categorii (total / mențiuni / înmatriculări), reponderare, comparația cu amânările, perechi, evitabilitate, serie săptămânală, figuri, JSON | `07_results.out.json`, `taxonomy.csv`, `figures/`, `../out/rejection_reasons.json` |

Ordinea de rulare este 01 → 07. Scripturile sunt deterministe (seed 42 pentru UMAP și k-means, 20261122 și 20261123 pentru eșantioane).
Am rulat 03 de două ori din aceleași embeddings și am obținut clustere identice. Am rulat apoi tot lanțul 01 → 07 de la zero, cu embeddings recalculate pe GPU: ieșirile 02, 03, 04 și 06 sunt identice byte cu byte. Pe alt hardware, numerotarea clusterelor se poate schimba; atunci `CLUSTER_MAP` din 04 trebuie recitit. Scripturile nu scriu bytecode, deci nu lasă nimic în `delay_reasons`.

## Metodă

1. **Extragere.** Buletinul publică, pentru fiecare decizie, o intrare în cuprins (secțiune, nr. încheiere, dată, soluție, nr. cerere)
   și, de regulă, textul integral al încheierii.
   - Am găsit 980 de încheieri de respingere, dintre care 979 au motiv. După eliminarea dublurilor (nr. cerere + zi) rămân 977.
   - 8 sunt din afara ferestrei (dec. 2025, feb., sep. 2026), deci rămân **969** în 19 oct.–18 nov. 2026: 886 la mențiuni și 83 la înmatriculări.
   - Toate s-au putut lega de decizia Respins din arhivă. Secțiunea din cuprins coincide cu categoria din arhivă (INMATRIC265 / CERERE265) în toate cazurile.
   - Cuprinsul are 999 de respingeri în fereastră. Pentru 31 din cele 32 lipsă, textul nu este publicat în buletin (de exemplu, un buletin cu doar cuprins).
     Nu este o scăpare a parserului.
2. **Două straturi.** Programul registrului tipărește înaintea cauzei una din trei formule:
   - „la termenul de soluționare se constată că profesionistul nu a remediat observațiile dispuse prin încheierea de amânare”: 62,8%;
   - „… nu a depus precizări în susținerea cererii”: 9,6%;
   - „cererea de înregistrare nu îndeplinește cerințele legale …”: 19,1%.

   Urmează, de obicei, motivele amânării, reluate.
   - **Stratul A (mecanismul)** se citește cu expresii regulate:
     - `M_NEREMEDIAT`: amânare nerespectată;
     - `M_PARTIAL`: completare parțială sau greșită;
     - `M_AMANARE_ALT`: amânare pomenită, fără mențiune despre remediere;
     - `M_DIRECT`: nicio amânare pomenită.
   - **Stratul B (cauza)** este textul rămas după eliminarea formulelor și a textului standard
     (explicațiile art. 106 alin. 4–5, citatul din art. 77, „prin încheierea … s-a acordat termen …”). Doar acesta este grupat și clasificat.
3. **Anonimizare**, cu aceleași funcții ca la amânări, aplicate înainte de orice analiză:
   - textul este adus fără diacritice;
   - sunt mascate e-mailurile, numerele de registru, CUI, datele, sumele, adresele, numele precedate de „domnul/asociatul…” și inițialele;
   - se aplică o listă albă de vocabular: un cuvânt se păstrează doar dacă apare în ≥8 respingeri, din ≥4 buletine și ≥3 județe. Restul devine `<x>` (5,2% din cuvinte);
   - antetul încheierii (firmă, CUI, registrator, solicitant) nu este păstrat deloc.
4. **Segmente, embeddings, clustere.**
   - Textul a fost împărțit în **2.203 segmente** (în medie 2,3 pe respingere);
   - modelul `multilingual-e5-small` a rulat local, pe GPU; niciun text nu a ieșit de pe calculator;
   - UMAP (10 dimensiuni) urmat de HDBSCAN a dat **61 de clustere**; 25% din segmente au rămas zgomot, iar după atașarea la cel mai apropiat centroid, 7%;
   - k-means (cel mai bun k = 8 după silhouette, 0,47) se potrivește slab cu HDBSCAN (ARI 0,04): k-means taie mai grosier;
   - am citit fiecare cluster și l-am numit. Dintre ele, 27 sunt **formule procedurale** („nu s-au depus completări”, „lipsită de interes”, temei legal), excluse din cauze;
   - 9 clustere sunt eterogene și primesc categoria din reguli sau de la vecini.
5. **Clasificarea finală (hibridă).**
   - Regulile sunt cele din `delay_reasons`, neschimbate, plus două reguli noi (`FARA_OBIECT`, `IMPOSIBIL`);
   - înainte de aplicarea regulilor se șterg frazele procedurale de tipul „cererea de înregistrare urmează a fi respinsă”, care altfel declanșează regula „cererea”;
   - ordinea de decizie: întâi cele două reguli noi; apoi clusterele procedurale rămân procedurale; apoi categoria clusterului, dacă o confirmă o regulă; altfel prima regulă; altfel categoria clusterului.

   Regulile au fost fixate înainte de validare.

## Taxonomie

Am păstrat cele **12 categorii ale amânărilor**, cu aceleași coduri și aceleași marcaje de evitabilitate, pentru ca respingerile și amânările să se compare direct.
Am adăugat **2 categorii specifice respingerii**:
- `FARA_OBIECT`: cererea a rămas fără obiect, de exemplu actualizarea CAEN Rev.3 era deja înregistrată pe altă cerere;
- `IMPOSIBIL`: impediment legal care nu se remediază cu acte în termen, de exemplu regula unei singure forme PFA/II/IF, termenele de la dizolvare, opoziție sau litigiu.

Categoriile mici (denumire, tarife, beneficiari reali) sunt păstrate separat numai pentru comparație. În lectură pot fi grupate.

Unde au ajuns cauzele propuse în sarcină:
- **neîndeplinirea cerințelor în termenul acordat** este mecanismul (stratul A), nu o categorie de cauză;
- **activitate nepermisă** (cod CAEN incompatibil cu forma juridică, cabinet medical, activități sub condiție) intră la CAEN, ca la amânări;
- **avize ale altor instituții** intră la `INSTIT`;
- **denumire indisponibilă** intră la `DENUM`; în eșantioane nu a apărut niciun caz de indisponibilitate propriu-zisă;
- **renunțarea solicitantului** este o soluție separată în arhivă („Renunțat”: 809 în fereastră, față de 8.710 respingeri), deci nu e o cauză de respingere.
  Cuvântul „renunțare” apare în 4,6% din respingeri, dar mai ales în sensul „renunțarea la autorizarea unor activități”, așa că nu l-am folosit ca indicator.

`taxonomy.csv` conține: cluster → etichetă → categorie → evitabil → motivare → 3 exemple generice scrise de auditor (nu copiate din încheieri).

| categorie | toate (IC 95%) | mențiuni | înmatriculări (Wilson) | ajustat P/R | **manual n=150** | evitabil |
|---|---|---|---|---|---|---|
| Obiect de activitate / CAEN, declarația de autorizare | 36,2% (32,9–39,6) | 37,9% | 18,1% (11,3–27,7) | 40,8% | **36,0%** (28,8–43,9) | parțial |
| Sediu (dovadă, valabilitate, acordul vecinilor) | 15,1% (12,9–17,2) | 14,3% | 22,9% (15,2–33,0) | 20,3% | **23,3%** (17,3–30,7) | parțial |
| Act constitutiv, hotărâri, mandat | 16,2% (13,8–18,6) | 16,9% | 8,4% (4,2–16,4) | 13,2% | **14,7%** (9,9–21,2) | parțial |
| Solicitant/deponent: identitate, împuternicire | 12,1% (10,0–14,1) | 12,9% | 3,6% (1,2–10,1) | 12,1% | **14,7%** (9,9–21,2) | da |
| Avize/atestări (cazier fiscal, ANAF, profesii) | 9,0% (7,1–10,9) | 6,4% | **36,1%** (26,6–46,9) | 14,5% | **14,0%** (9,3–20,5) | parțial |
| Date de identificare asociați/administratori | 9,0% (7,0–11,0) | 9,1% | 7,2% (3,4–14,9) | 15,6% | **17,3%** (12,1–24,2) | da |
| Cererea, anexa fiscală, formulare | 6,8% (5,2–8,4) | 6,3% | 12,0% (6,7–20,8) | 8,2% | **12,0%** (7,7–18,2) | da |
| Capital social, vărsăminte | 5,0% (3,5–6,4) | 5,3% | 1,2% (0,2–6,5) | 4,5% | **6,0%** (3,2–11,0) | parțial |
| Cerere rămasă fără obiect *(nou)* | 2,6% (1,6–3,6) | 2,5% | 3,6% | 4,3% | **6,7%** (3,7–11,8) | da |
| Semnătură și forma înscrisurilor | 2,3% (1,4–3,1) | 2,3% | 2,4% | 3,8% | **6,7%** (3,7–11,8) | da |
| Denumire | 1,4% (0,7–2,2) | 0,6% | 10,8% (5,8–19,3) | 1,0% | 1,3% | da |
| Impediment legal *(nou)* | 1,0% (0,4–1,7) | 0,8% | 3,6% | 0,8% | 2,0% (0,7–5,7) | parțial |
| Tarife / contor de caractere | 0,8% (0,3–1,4) | 0,9% | 0,0% (0–4,4) | – | 3,3% (1,4–7,6) | da |
| Beneficiari reali | 0,7% (0,2–1,2) | 0,4% | 3,6% | 1,7% | 4,7% (2,3–9,3) | da |
| Neclasificat (nicio cauză detectată automat) | 16,6% (14,3–19,0) | 17,0% | 12,0% | 4,5% | **4,0%** (1,8–8,5) | n/a |

Coloanele explicate:
- „toate”, „mențiuni” și „ponderat”: clasificatorul. Reponderarea (raking) pe județ × săptămână × tip schimbă ponderile cu cel mult 1,5 puncte procentuale (efect de design Kish 1,23);
- „ajustat P/R”: ponderea × precizie / recall, calculate pe eșantionul de 150;
- „manual”: eșantionul de 150 etichetat manual, cu IC Wilson. Este cea mai puțin părtinitoare estimare, dar are IC mai largi.

**„Neclasificat” nu înseamnă „fără cauză”.** Manual, doar 4% din respingeri nu reiau nicio cauză. Restul de ~13 puncte sunt cauze pe care clasificatorul nu le-a găsit,
pentru că erau ascunse în fraze procedurale. După clasificator, o respingere are în medie 1,18 categorii (1,42 dintre cele cu cel puțin o cauză detectată).

## Comparația cu amânările (figura b)

Ponderile amânărilor vin din `../out/delay_reasons.json`. Pentru fiecare categorie am calculat raportul dintre ponderea la respingeri și ponderea la amânări, în trei feluri:
brut, ajustat cu precizie/recall și manual cu manual (150 de respingeri față de 100 de amânări).

| categorie | brut | ajustat | manual | concluzie |
|---|---|---|---|---|
| CAEN | 1,14 | 1,05 | 1,13 | neconcludent (ușor mai frecvent) |
| Sediu | 0,69 | 0,93 | 1,67 | neconcludent |
| Act constitutiv | 0,92 | 0,82 | 0,70 | neconcludent (ușor mai rar) |
| Date de identificare | 0,82 | 1,26 | 0,96 | neconcludent |
| Solicitant | 1,07 | 1,07 | 1,33 | neconcludent (ușor mai frecvent) |
| Avize/cazier fiscal | 0,94 | 0,97 | 1,27 | neconcludent |
| Cererea, formulare | 0,33 | 0,62 | 1,00 | neconcludent (la amânări categoria era supra-atribuită) |
| **Capital social** | **0,58** | **0,48** | **0,46** | **mai rar la respingeri** |
| Semnătură, beneficiari reali, denumire, tarife | – | – | – | n prea mic |

**Lectura:** cauzele care duc la amânare sunt aceleași care duc la respingere, cu ponderi apropiate.
Clasificatorul de respingeri are recall mai mic decât cel de amânări, deci comparația brută exagerează diferențele. De aceea concluzia se trage pe toate cele trei măsuri.
Rezultatul se potrivește cu ce arată `delay_reasons` despre soarta amânărilor pe categorii (ponderea „neadmis” între cele soluționate):
- capital 22%, beneficiari reali 12%, semnătură 23%: se remediază des;
- cazier/avize 41%, tarife 44%, solicitant 38%, CAEN 37%: se remediază mai rar.

**Perechi.** Pentru 61 de respingeri, încheierea de amânare a aceleiași cereri este și ea în buletinele colectate. Pe ambele texte s-au aplicat aceleași reguli:
- cel puțin o cauză comună: 98% (din 53 de perechi cu cauze pe ambele părți);
- toate cauzele respingerii se regăsesc în amânare: 83%;
- categorie nouă la respingere: 17%.

## Evitabil la depunere

Marcajele de evitabilitate sunt cele de la amânări, motivate în `taxonomy.csv`. Pentru cele două categorii noi:
- **fără obiect**: da, o căutare în registru la depunere ar arăta că mențiunea este deja înregistrată;
- **impediment legal**: parțial, regula unei singure forme PFA/II se verifică în baza de date, opoziția și termenele legale nu.

Cauzele „neclasificate” contează ca neevitabile.

| variantă | manual n=150 (Wilson) | clasificator (IC buletin) | fără „neclasificat” | mențiuni / înmatriculări |
|---|---|---|---|---|
| **strictă**: toate cauzele „da” (cifra principală) | **28,0%** (21,4–35,7) | 16,6% (14,3–19,0) | 19,9% | 17,0% / 12,0% |
| **limita superioară**: ≥1 cauză „da” | **54,7%** (46,7–62,4) | 30,6% (27,7–33,4) | 36,6% | 30,5% / 31,3% |
| toate cauzele „da” sau „parțial” | 96% | 83,4% | – | – |

Valorile clasificatorului sunt **estimări inferioare**. Pe aceleași 150 de respingeri, clasificatorul dă 20,7% strict față de 28% manual (acord 86%)
și 38,7% față de 54,7% la limita superioară (acord 77%). Pe lotul nou de 50, valorile manuale sunt 28% strict și 60% la limita superioară.
Comparat cu amânările (22,9% strict, 45,1% limita superioară, clasificator), ponderea evitabilă este similară.
Respingerile nu sunt mai „juridice” decât amânările: sunt aceleași defecte formale, rămase nerezolvate la termen.

## Validare

- **Eșantioane.**
  - Lotul 1: 100 de respingeri, seed 20261122, etichetate din textul anonimizat **înainte** de a calcula embeddings, clustere sau reguli.
  - Lotul 2: 50 de respingeri, seed 20261123, disjuncte de lotul 1, etichetate după ce clasificatorul a fost fixat, dar înainte de a vedea predicțiile.
  - Regulile `FARA_OBIECT` și `IMPOSIBIL` și ștergerea frazelor procedurale au fost scrise după citirea lotului 1, deci pe lotul 1 sunt evaluate pe date pe care le-au văzut.
    Pe lotul 2, `FARA_OBIECT` are recall 0,25 (1 din 4): **regula este supra-ajustată**. Pentru cele două categorii noi, cifra de referință este cea manuală.

| clasificator | lot | set identic (Wilson) | ≥1 cauză corectă | precizie / recall |
|---|---|---|---|---|
| **final (hibrid)** | 1+2 (150) | **44%** (36–52) | 81% | **0,80 / 0,65** |
| final (hibrid) | 2 (50, nou) | 38% (26–52) | 74% | 0,79 / 0,59 |
| numai clustere | 1+2 | 29% | 66% | 0,72 / 0,47 |
| numai reguli | 1+2 | 28% | 93% | 0,62 / 0,91 |

- **Pe categorii (hibrid, 150).**
  - CAEN: precizie 0,90, recall 0,80;
  - sediu: 0,92 și 0,69;
  - solicitant: 0,82 și 0,82;
  - capital: 0,80 și 0,89;
  - avize: 1,00 și 0,62;
  - date de identificare: 0,80 și 0,46;
  - act constitutiv: 0,44 și 0,55;
  - cererea: 0,60 și 0,50;
  - semnătură: 0,83 și 0,50;
  - tarife: niciuna găsită.
- **Mecanismul (stratul A).** Este corect în 92,7% din cazuri (87,3–95,9). Distincția „după amânare / direct” este corectă în 95,3% din cazuri.
  18 din cele 20 de respingeri etichetate manual „directe” au, de fapt, o amânare în arhivă.
- **Concordanța clustere–reguli** (kappa Cohen, la nivel de respingere):
  - avize 0,81, CAEN 0,65, solicitant 0,59, capital 0,54, sediu 0,42, act constitutiv 0,42;
  - date de identificare 0,17, cererea 0,06.

  Categoriile cu kappa mic sunt și cele mai nesigure manual. Kappa este 0 la categoriile pe care niciun cluster nu le acoperă: semnătură, beneficiari reali, denumire, tarife și cele două noi.
- **Acoperire și reprezentativitate.**
  - Textele parsate sunt **11,1%** din respingerile din arhivă în fereastră (11,7% în zilele acoperite), din 275 de buletine și 21 din 23 de zile de decizie.
  - Acoperirea este aceeași pe tipuri: 11,2% la mențiuni și 10,6% la înmatriculări.
  - Pe săptămâni, acoperirea este între 7,1% și 16,0%.
  - Pe județe (42 de județe cu ≥20 de respingeri), acoperirea este între 2,6% și 20,4% (coeficient de variație 0,39), mai neuniformă decât la amânări.
  - Structura pe tip de profesionist este aceeași ca în arhivă: J 66,7% față de 67,3%, F 24,5% față de 23,3%.
  - Reponderarea pe județ × săptămână × tip schimbă ponderile cu cel mult 1,5 puncte procentuale.

## Seria săptămânală (figura c)

| săptămâna | n parsat / arhivă | CAEN | sediu | act | solicitant | avize | după amânare neîndeplinită (text) | arhivă: cu amânare anterioară |
|---|---|---|---|---|---|---|---|---|
| 19–25 oct. (4 zile) | 166 / 1.892 | 29,5% | 12,7% | 17,5% | 18,7% | 7,8% | 83,1% | 98,1% |
| 26 oct.–1 nov. (5) | 265 / 1.962 | 38,1% | 15,5% | 17,4% | 9,8% | 10,2% | 86,8% | 97,8% |
| 2–8 nov. (4) | 175 / 1.932 | 42,3% | 12,6% | 16,6% | 12,6% | 7,4% | 82,9% | 97,6% |
| 9–15 nov. (5) | 280 / 1.755 | 33,9% | 19,6% | 14,6% | 8,9% | 9,3% | 83,2% | 97,1% |
| 16–18 nov. (3) | 83 / 1.169 | 38,6% | 8,4% | 14,5% | 15,7% | 9,6% | 89,2% | 97,4% |

Intervalele se suprapun aproape peste tot. **Nu se poate afirma nicio tendință.**

## Limite

- **Eșantion de buletine, nu recensământ.** Textele acoperă 11% din respingeri, cu acoperire inegală pe județe. Intervalele reflectă doar eșantionarea între buletinele colectate.
  Constatarea principală (97,6% după o amânare) vine însă din arhivă și acoperă toate respingerile.
- **Clasificarea subestimează cauzele.** Recall-ul este 0,65, iar pe lotul nou 0,59. Ponderile clasificatorului sunt limite inferioare,
  „neclasificat” este supra-estimat de ~4 ori, iar regula „fără obiect” este supra-ajustată.
  Pentru afirmații publice, folosiți coloana „manual” sau cea ajustată.
- **Un singur evaluator**, un model AI, fără al doilea codificator.
- **Înmatriculări:** n=83, IC largi. Ponderea mare a cazierului fiscal este robustă ca direcție (IC 27–47%), nu ca valoare exactă.
- **Comparația cu amânările** compară cohorte diferite: respingerile reiau amânări cu ~16 zile mai vechi.
  Pentru amânări, ponderile și eșantionul manual vin din `delay_reasons` (n=100), cu precizia lui (de exemplu, „cererea” supra-atribuită acolo).
- **Evitabilitatea** este o judecată normativă a auditorului, neconfirmată de ONRC.
- **Legătura cu arhiva** (nr. cerere + zi de depunere) este o limită inferioară, pentru că arhiva pierde câteva amânări
  (vezi `../out/missing_postponements_sensitivity.json`).

## Confidențialitate

- Ieșirile conțin doar agregate. Exemplele din `taxonomy.csv` sunt fraze generice scrise de auditor.
- Etichetele manuale sunt indexate doar după poziția în eșantion.
- Toate fișierele intermediare la nivel de rând (`_tmp/`: texte, nr. cerere, embeddings, fișele de inspecție și de eșantion) și fișierele de probă din directorul temporar au fost **șterse** la final.
  Se refac rulând 01–03 și 05.
- Nu s-a folosit și nu s-a modificat nimic de pe `T:\`.

## Mediu Python

S-a folosit `venv`-ul existent fără nicio instalare, actualizare sau dezinstalare: `sentence-transformers 3.4.1`, `umap-learn 0.5.7`, `scikit-learn 1.4.1.post1`, `numpy 1.26.4`, `pandas 2.2.1`, `torch 2.3.1+cu121`.
Modelul `intfloat/multilingual-e5-small` era deja în cache-ul local. Scripturile rulează cu `python -X utf8`.

## Anexă: utilizarea AI

- **Model.** Analiza (scripturi, clasificare, text) a fost produsă de Claude Opus 5.5 (Anthropic). Modelul de embeddings `multilingual-e5-small` a rulat local.
  Niciun text din buletine nu a fost trimis în afara calculatorului.
- **Ce a făcut AI-ul:**
  - extragerea și anonimizarea;
  - clusterizarea și denumirea clusterelor;
  - regulile;
  - **etichetarea manuală a celor 150 de cazuri**: evaluatorul este modelul AI, nu un om;
  - judecata de evitabilitate;
  - figurile și acest README.
- **Ce rămâne la autor:** cerințele, verificarea, decizia de publicare și răspunderea.
- **Incertitudini:** acuratețea de mai sus; evitabilitatea este o judecată; acoperirea buletinelor este parțială.
- **Recomandat:** o a doua etichetare, umană, pe un eșantion nou, și validarea categoriilor „evitabile” cu ONRC.
