# De ce se amână dosarele la ONRC și ce se poate automatiza

> **Notă AI:** document realizat cu ajutorul inteligenței artificiale (Claude Opus 5.5 și Gemini 4 Neon), sub îndrumarea și verificarea autorului (vezi anexa de la final). Cifrele sunt agregate și nu conțin date personale.

**Data verificării juridice:** 22.11.2026. **Versiunea pentru mașină:** `../out/postponement_solutions.json`, generat de `08_solutions.py` din `../out/delay_reasons.json`.
**În raport:** secțiunea 6.4 (`analysis/policy_paper_ro/postponement_section.py`), afirmațiile C126–C143 (după integrare, vezi `INTEGRARE.md`), figurile `i08_motive_amanare` și `i09_evitabil_la_depunere`.

## Pe scurt

- **Ce am măsurat.** 2.914 amânări cu motiv publicat, 19.10–18.11.2026, adică 12,5% din amânările din arhivă în aceeași fereastră. Județele și tipurile de firme sunt reprezentate ca în arhivă (`README.md`).
- **Motivele cele mai dese.** CAEN și declarația de autorizare 31,7%; sediul 21,9%; cererea și anexa fiscală 20,7% (supra-atribuită, ajustat ≈13%); actul constitutiv, hotărârile și mandatul 17,7%. O amânare poate avea mai multe motive.
- **Cât se poate preveni la depunere.** **22,9%** (IC 21,5–24,3) dintre amânări au numai motive evitabile: n-ar mai avea loc. În **45,1%** (43,3–46,8), cel puțin un motiv era evitabil: amânarea devine mai simplă, dar poate rămâne.
- **Capacitate.** La circa 1.012 amânări pe zi lucrătoare (1.10–19.11.2026), înseamnă cel mult circa **230** de amânări mai puțin pe zi (220–250) și circa **460** de amânări pe zi cu cel puțin un motiv mai puțin. O amânare evitată scoate o decizie de amânare și a doua analiză a dosarului, **nu** adaugă o decizie finală. E un plafon: presupune că verificarea prinde tot ce e evitabil.
- **Automatizare.** Pentru **11 din 12** motive, soluția principală e **Standard** (reguli fixe, fără AI). Doar concordanța actului constitutiv cu hotărârea cere **AI avansat**, ca asistent. În **4** motive, o parte rămâne la judecata registratorului.
- **Legea.** Decizia rămâne la registrator (Legea 265/2022, art. 28 alin. (2)). O decizie luată numai de un program ar cere o autorizare expresă în lege (GDPR art. 22; Legea 242/2022, art. 13 alin. (9)). După evaluarea noastră, niciun caz nu intră în anexa III a AI Act; oricum, obligațiile pentru risc ridicat din anexa III se aplică abia din **2.12.2027** (Regulamentul (UE) 2026/1744).

**Dacă nu există deja.** Nu vedem sistemele interne ale ONRC. Fiecare soluție de mai jos e o recomandare de verificat: o parte poate exista deja în portal.

## Nivelurile de automatizare

| nivel | ce înseamnă |
|---|---|
| **Standard** | reguli deterministe, validări de formular, calcule, interogări prin interoperabilitate; fără AI |
| **Doar cu AI** | ML/NLP/OCR: citirea documentelor scanate, sugerarea codului CAEN din descrierea activității |
| **Doar cu AI avansat** | modele avansate/generative care raționează pe acte juridice (concordanța actului constitutiv actualizat cu hotărârea) |
| **Nu se poate automatiza** | judecata juridică a registratorului (controlul de legalitate) |

## Matricea de soluții

Pondere = procentul de amânări care invocă motivul (IC 95%). „Evitabil” = marcajul din `taxonomy.csv`; doar categoriile „da” intră în intervalul 22,9–45,1%.

| motiv | pondere | evitabil | ce cauzează amânarea (exemple generice) | soluții (nivel) | nivel principal | complexitate | unde acționează | depinde de |
|---|---|---|---|---|---|---|---|---|
| Obiect de activitate / CAEN, declarația de autorizare | 31,7% (30,0–33,4) | parțial | cod care nu mai există în CAEN Rev.3; text adăugat codului; declarația-tip lipsă sau incompletă; limita PFA/II depășită; cod condiționat de o lege specială; descriere care nu corespunde codului | coduri numai din nomenclatorul Rev.3 + tabel de corespondență (S); declarația generată din coduri, limita PFA verificată (S); sugestie de cod din descrierea activității (AI); activitatea condiționată (J) | Standard | medie | la depunere | nomenclatorul CAEN Rev.3 și corespondența (INS); HG 656/1997, art. 5^1; OUG 44/2008; lista activităților condiționate |
| Sediu: dovada folosinței, acorduri, adresă | 21,9% (20,4–23,4) | parțial | dovadă expirată; lipsa acordului vecinilor/asociației pentru locuință; adresă diferită între acte; sediu secundar fără dovadă | data de expirare verificată la depunere (S); adresa din nomenclatorul stradal, acordul cerut automat (S); citirea contractului încărcat (AI); valabilitatea titlului (J) | Standard | medie | la depunere | nomenclatorul de adrese și cartea funciară (ANCPI); CPF art. 92 |
| Cererea de înregistrare și anexa fiscală | 20,7% (19,2–22,3); ajustat ≈13% | da | anexa fiscală greșită; câmpuri lipsă; formular vechi; altă cerere în curs | formular structurat cu reguli (S); avertisment pentru cereri paralele (S) | Standard | scăzută | la depunere | regulile ANAF pentru anexa fiscală |
| Act constitutiv, hotărâri, mandat | 17,7% (16,3–19,1) | parțial | actul actualizat nu corespunde actului modificator; durata mandatului lipsă/nedeterminată; act nelizibil sau neatașat; firmă în dizolvare | listă de acte pe tipul cererii, starea firmei verificată, câmp pentru durata mandatului în actele-tip (S); asistent care compară actele și semnalează neconcordanțe (AI avansat); legalitatea clauzelor (J) | **Doar cu AI avansat** | ridicată | la operare, la soluționare | acte-tip; model găzduit în UE/infrastructura statului; set de test etichetat de registratori |
| Solicitant: identitate, împuternicire | 11,3% (10,2–12,5) | da | lipsește împuternicirea; semnatar fără calitate; lipsește copia actului de identitate sau a cardului de avocat | semnatarul comparat cu rolurile din registru, împuternicire cerută automat (S); calitatea de avocat/notar verificată în registrul profesiei (S) | Standard | medie | la depunere | eIDAS; evidența persoanelor prin PNI; registrele profesiilor |
| Date de identificare ale asociaților | 10,9% (9,8–12,1) | da | alt act de identitate decât în registru; datele noi nepreluate în decizie | date precompletate din registru și evidența persoanelor, diferențe arătate la depunere (S) | Standard | medie | la depunere | evidența persoanelor prin PNI (Legea 242/2022, art. 7 alin. (1) lit. a)) |
| Avize ale altor instituții | 9,5% (8,5–10,6) | parțial | cesiune fără atestare fiscală; fapte în cazierul fiscal; activități care cer autorizație profesională | cazier fiscal / atestare interogate la ANAF înainte de depunere (S) — *nu înlătură impedimentul, îl arată mai devreme*; autorizații verificate în registrul emitentului (S); efectul faptelor (J) | Standard | ridicată | la depunere | ANAF; PNI (ADR); registrele profesiilor |
| Capital social | 8,5% (7,5–9,5) | parțial | lipsește dovada vărsării; structura după majorare neprezentată | dovadă obligatorie + calcule automate (S); citirea extrasului bancar (AI) | Standard | scăzută | la depunere | — (opțional: confirmarea băncii) |
| Semnătura și forma actelor | 4,8% (4,0–5,6) | da | semnătură olografă reprodusă ca imagine; fără semnătură electronică calificată | validarea automată a semnăturii calificate la încărcare (S) | Standard | scăzută | la depunere | serviciu de validare eIDAS; Legea 265/2022, art. 83 |
| Beneficiari reali | 3,6% (2,9–4,3) | da | declarația lipsă; beneficiar care nu e persoană fizică | declarația cerută automat când se schimbă asociații; beneficiarul = persoană fizică (S) | Standard | scăzută | la depunere | registrul beneficiarilor reali (ONRC); Legea 129/2019 |
| Denumire | 2,5% (1,9–3,0) | da | denumirea PFA fără numele titularului | validator de denumire la rezervare (S) | Standard | scăzută | la depunere | — |
| Tarif de publicare | 1,7% (1,2–2,2) | da | lipsește contorul de caractere | tarif calculat automat din text (S) | Standard | scăzută | la depunere | regulile de tarifare ale Monitorului Oficial |

S = Standard · AI = Doar cu AI · AI avansat = Doar cu AI avansat · J = Nu se poate automatiza (judecata registratorului). Neclasificat: 4,5% (manual: toate aveau un motiv concret).

### Efectul așteptat, pe scurt

- **Intervalul de efect** e 22,9% (strict) – 45,1% (limita de sus) din amânări. El se sprijină numai pe motivele marcate „da”, toate cu soluție Standard. Soluțiile pentru motivele „parțial” (CAEN, sediu, act constitutiv, capital, alte instituții) ar adăuga la efect, dar efectul lor nu se poate măsura din date. Ponderile nu se pot aduna pe categorii, pentru că o amânare are în medie 1,45 categorii; nu mai avem date la nivel de amânare ca să recalculăm intervalul pe nivel de automatizare.
- **Capacitate eliberată:** circa 230 (220–250) de decizii de amânare pe zi lucrătoare evitate; circa 460 de amânări pe zi mai simple. Pentru firmă, o amânare evitată înseamnă un termen de completare mai puțin (după completare, decizia vine în circa 14 zile, C37).
- **Ponderile vin din 19.10–18.11.2026** și nu se extind la ianuarie–septembrie. Ritmul de 1.012 amânări pe zi vine din aceeași sursă ca C79/C30 (1.10–19.11.2026).

## Cadrul legal

### Ce am citit (surse oficiale, 22.11.2026)

| prevedere | ce spune, pe scurt | stare |
|---|---|---|
| Legea 265/2022, art. 28 alin. (1)-(2); art. 30 lit. a)-b); art. 105 alin. (1); art. 106 alin. (1)-(2) | registratorul face controlul de legalitate și soluționează cererile prin încheiere; verifică actele și datele de identitate; la dosar incomplet, termen de cel mult 15 zile calendaristice; termenul și motivele se afișează pe portal | verificat, legislatie.just.ro |
| Legea 242/2022, art. 7 alin. (1) lit. a), e); art. 11 alin. (1)-(3); art. 13 alin. (9); art. 17 alin. (2) | registrul comerțului și evidența persoanelor sunt registre de bază; instituțiile folosesc PNI și nu mai cer acte cu date disponibile prin platformă; „Nicio persoană vizată nu va fi afectată de o decizie … bazată exclusiv pe prelucrarea automată a datelor sale … cu excepția cazului în care o astfel de decizie este autorizată” de lege; cazierul judiciar nu e în lista registrelor de bază | verificat (forma afișată) |
| Directiva 2017/1132, art. 13b alin. (4), art. 13g alin. (3) lit. a), f), alin. (7), (8), art. 13h, art. 13i (introduse prin Directiva (UE) 2019/1151) | se verifică capacitatea și puterea de reprezentare, numirea administratorilor; prezența fizică doar caz cu caz, la suspiciune; formulare-tip; administratori decăzuți; constituire online în 5/10 zile lucrătoare | verificat, EUR-Lex |
| GDPR (Reg. 2016/679), art. 22 alin. (1), (2) lit. b), (3); art. 25; art. 35 alin. (1), (3) lit. a) | fără decizii exclusiv automate cu efecte juridice, decât dacă legea le autorizează cu garanții (alin. (3) nu se aplică lit. b)); protecția datelor din proiectare; DPIA pentru tehnologii noi cu risc ridicat | verificat, EUR-Lex |
| AI Act (Reg. 2024/1689), art. 3 pct. 4; art. 6 alin. (3)-(4); art. 14; art. 26; art. 27 alin. (1); art. 50 alin. (1), (4); art. 86 | ONRC ar fi implementator; derogările de la riscul ridicat (sarcină procedurală restrânsă, pregătitoare etc.; niciodată la profilarea persoanelor); supraveghere umană; obligațiile implementatorului (jurnale ≥ 6 luni, informarea lucrătorilor și a persoanelor); FRIA pentru organismele de drept public; transparența chatbot-urilor | verificat, EUR-Lex |
| Reg. (UE) 2026/1744 („Digital Omnibus on AI”), 8.07.2026, JO L 24.07.2026, în vigoare 27.07.2026 | anexa III (risc ridicat): cap. III secț. 1-3 de la **2.12.2027**; anexa I de la 2.08.2028; art. 4 înlocuit (măsuri de sprijin pentru alfabetizarea AI, fără nivel garantat); art. 27 alin. (4)-(5) modificate (FRIA poate trimite la DPIA); art. 111 alin. (2): sistemele cu risc ridicat folosite de autorități, introduse înainte, se conformează până la 2.08.2030; art. 50 nu e amânat | verificat, EUR-Lex |
| AI Act, art. 113 original | cap. I-II (inclusiv interdicțiile și art. 4) de la 2.02.2025; GPAI de la 2.08.2025; aplicare generală 2.08.2026; art. 6 alin. (1) de la 2.08.2027 | **sursă secundară** (artificialintelligenceact.eu); EUR-Lex nu s-a putut citi până la art. 113 |
| AI Act, anexa III pct. 5 lit. a) și pct. 8 lit. a) | 5 a): eligibilitatea **persoanelor fizice** pentru prestații și servicii publice de asistență; 8 a): sisteme folosite de o **autoritate judiciară** sau în numele ei | **sursă secundară**; nemodificate de 2026/1744 (verificat EUR-Lex) |

### Încadrarea cazurilor ONRC în AI Act (evaluarea noastră)

Niciun caz din matrice nu intră în anexa III. Pct. 5 lit. a) privește prestațiile de asistență pentru persoane fizice, nu înregistrarea firmelor. Pct. 8 lit. a) cere o autoritate judiciară; registratorul este specialistul în drept al ONRC, instituție în subordinea MJ, nu o instanță. Chiar dacă s-ar susține contrariul, asistența la verificare ar fi o sarcină pregătitoare (art. 6 alin. (3) lit. d)), cu condiția să nu facă profilarea persoanelor fizice. **Rezervă:** interpretare a auditorului, nu aviz juridic.

Regulile deterministe (nivelul Standard) nu sunt „sisteme AI” în sensul art. 3 pct. 1: nu deduc singure cum să genereze rezultate. *[interpretare; ghidul Comisiei privind definiția nu a fost recitit în această sesiune]*

### Ce se cere, pe nivel de automatizare

| nivel | obligatoriu | recomandat |
|---|---|---|
| **Standard** | GDPR: temei legal (art. 6 alin. (1) lit. c)/e)), minimizare și protecție din proiectare (art. 25); Legea 242/2022: interogări prin PNI, fără a cere din nou acte (art. 11, art. 17 alin. (2)). AI Act nu se aplică. | verificările semnalează, nu decid: solicitantul poate depune și cu avertisment; DPIA pentru interogările la scară mare |
| **Doar cu AI** (asistă, omul decide) | AI Act art. 4 (alfabetizare AI, în vigoare); art. 50 alin. (1) dacă e un asistent conversațional pe portal: proiectat să spună că e AI (obligația furnizorului; ONRC e furnizor dacă îl pune în funcțiune sub numele său; din 2.08.2026); GDPR art. 35 (DPIA pentru citirea actelor de identitate la scară mare), art. 25; decizia rămâne umană (GDPR art. 22; Legea 242/2022, art. 13 alin. (9); Legea 265/2022, art. 28) | supraveghere, jurnale și monitorizare după modelul art. 14 și 26; evaluarea „nu e risc ridicat” documentată (art. 6 alin. (4)); rezultatul arătat ca sugestie, cu sursa din document |
| **Doar cu AI avansat** | tot ce se cere mai sus; contract de prelucrare și găzduire în UE sau în infrastructura statului *[GDPR art. 28 neverificat în această sesiune]* | din prudență, ca pentru risc ridicat: supraveghere conform art. 14, jurnale ≥ 6 luni (art. 26 alin. (6)), informarea personalului (art. 26 alin. (7)), evaluare de tip FRIA (art. 27), explicații (art. 86); test pe un set etichetat înainte de utilizare; dacă ar fi încadrat ca risc ridicat: obligații din 2.12.2027 |
| **Nu se poate automatiza** (decizia însăși) | decizia o dă registratorul prin încheiere (Legea 265/2022, art. 28 alin. (2), art. 105 alin. (1)); o decizie exclusiv automată ar cere autorizare în lege, cu garanții (GDPR art. 22 alin. (2) lit. b); Legea 242/2022, art. 13 alin. (9)) | orice regim fără registrator (de ex. conversia automată CAEN 1-la-1) cere mai întâi temei legal |

### Ce nu am putut verifica

- art. 113 original din AI Act și formularea exactă a anexei III (citite pe o sursă secundară);
- eIDAS art. 32-33; Legea 129/2019 (articolul despre declarația de beneficiar real); GDPR art. 28; ghidul Comisiei privind definiția sistemului AI;
- forma consolidată a Legii 242/2022 (am citit forma afișată pe legislatie.just.ro);
- **ce verificări are deja ONRC** (nu vedem sistemele interne).

## O recomandare care face restul măsurabil

Motivul amânării e azi text liber; programul registrului tipărește doar patru formule generale. Un **cod de motiv** în fiecare încheiere (de exemplu, aceleași 12 categorii) ar permite ONRC să publice lunar ce lipsește la depunere și să aleagă ce verificare construiește întâi.

## Legătura cu modelul de cost

Modelul de cost (`cost_founded.py`, canalul D „amânări evitabile”) folosește pentru `preventable_post_share` o ipoteză fără bază în date: 8% / 15% / 25%. Măsurarea de aici dă 22,9% (21,5–24,3) strict. Actualizarea parametrului ar schimba afirmațiile de cost (C106–C113); e o decizie separată a autorului, nu face parte din această integrare.

## Anexă: utilizarea AI

- **Modele.** Claude Opus 5.5 (Anthropic) și Gemini 4 Neon (Google), conform textului comun din `analysis/policy_paper_ro/ai_annex.py`. Matricea, încadrarea juridică, figura, textul și scripturile din acest document au fost produse de Claude Opus 5.5.
- **Ce a făcut AI-ul:** a propus soluțiile și nivelurile de automatizare pe baza exemplelor din `taxonomy.csv`; a citit textele legale pe EUR-Lex și legislatie.just.ro (un subagent a extras citatele din EUR-Lex); a calculat efectele din ponderile măsurate; a scris secțiunea 6.4 și scriptul de integrare.
- **Ce rămâne la autor:** validarea matricei (ideal împreună cu ONRC), decizia de publicare și răspunderea.
- **Incertitudini:** nivelurile de automatizare și complexitatea sunt judecăți, nu măsurători; încadrarea juridică nu e aviz juridic; ponderile au erorile de clasificare din `README.md` (setul exact de motive corect în 55% din cazuri).
