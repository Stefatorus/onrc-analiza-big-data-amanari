# Replicare independentă: raportul despre coada de la Registrul Comerțului (noiembrie 2026)

Am lucrat doar cu fișierele din `replicare_independenta/`: arhiva BERC (pickle), recoltarea myportal, nota MJ, compilația de presă și textul PDF-ului. Fiecare cifră de mai jos e recalculată cu cod propriu, din `lucru/`.

Anexa `claims_registry.csv` am deschis-o abia după ce valorile mele erau salvate (`valori_proprii_first_pass.csv`). Am afișat din ea cinci rânduri (C05, C13, C41, C99, C101) și am folosit doar definițiile lor:
- **C41**: numai înmatriculări J;
- **C99**: ferestrele lunare, de exemplu „mai–iul.”;
- **C101**: fereastra 27.04–28.06 și cele trei categorii.

Confirmările pentru C41 și C101 depind de aceste definiții, care nu apar în textul raportului.

Rezultatul conține doar agregate, fără firme, CUI sau persoane.

## 1. Rezumat

| Verdict | Rânduri |
|---|---|
| CONFIRMAT | 54 |
| DIFERIT | 5 |
| NEVERIFICABIL | 9 |
| **Total** | **68** (acoperă ~95 de coduri [Cxx]/[Pxx]) |

**Ce se confirmă.** Cifrele observate direct în BERC se reproduc aproape toate la zecimală, sub definițiile raportului:
- timpii de așteptare;
- volumele și ritmurile;
- amânările și respingerile;
- valorile pe oficii;
- comparațiile cu presa.

Se reproduc și intrările reconstituite din contorul numerelor de cerere (C93, C98, C99), cu o estimare ponderată pe straturi ale contorului. Arhiva are aceleași dimensiuni ca auditul din raport: 4.077.510 rânduri; 13.811 cu W<0; 42 cu W≥400; 3.241.580 finale stricte. Calendarul legal reconstituit dă exact zilele lucrătoare din Tabelul 3, lună de lună.

**Cele cinci diferențe sunt mici:**
- C05: „cel puțin de 8 ori” dă de fapt 7,6–7,8×;
- C100: stocul estimat la 6.11 iese cu 3,4% peste raport, dar în interiorul IC;
- C71: scăderea de vară e mai adâncă în date decât în profilul modelului;
- C62: o nepotrivire internă, 398.000 față de 395.446;
- P05: „vârful” zilnic al contorului.

**Problemele importante țin de interpretare (secțiunea 3):**
- Abaterea din backtestul C70 vine din întârzierea de publicare, nu din regula de prognoză.
- „Așteptarea a crescut în fiecare săptămână” e adevărat doar pentru modificări.
- „Termenul minim de fapt de 3 zile lucrătoare” e valabil doar aprilie–iunie.
- Clasamentul oficiilor se sprijină pe diferențe de minute.
- Nivelul de 8% respingeri exista deja în 2025.
- Ultima zi din arhivă (20.11) e incompletă.

## 2. Tabelul complet

Convenții:
- W = `res − app`, în zile calendaristice.
- Finale stricte = Admis, Respins, Renunțat. Finale largi = cele stricte plus certificările.
- Pentru timpi: 0 ≤ W < 400.
- Zi lucrătoare legală = luni–vineri, fără sărbătorile legale (Paștele ortodox calculat algoritmic).
- Legătura dosar ↔ amânare se face prin cheia (`app_nr`, marca exactă `app`), după 08.2024. Cheia are 413 dubluri la 2,2 milioane de finale.
- În portal, „în așteptare” = fazele „Cerere în procesare” (operare) și „Cerere în soluționare” (registrator). Aceeași definiție e folosită pentru C06, C13 și C100.

Notă despre coloane: brief-ul inversa `res` și `sol`. În date, `res` e momentul deciziei, iar `sol` e soluția.

| # | Cod | Afirmația (pe scurt) | Pag. | Valoarea din raport | Valoarea mea | Verdict | Notă |
|---|---|---|---|---|---|---|---|
| 1 | C14 | Mediana modificărilor (CERERE265), decizii 16–20.11 | 5, 15, 19 | 57,1 z | 57,09 (16–19.11: 57,10) | CONFIRMAT | |
| 2 | C15 | Mediana înmatriculărilor, 16–20.11 | 11, 19 | 41,1 z | 41,06 | CONFIRMAT | |
| 3 | C16 | Mediana săptămânală crește în fiecare săptămână: 27,9 → 57,1 | 16, 19 | 27,9 → 57,1 | 27,91 → 57,09, monoton (modificări) | CONFIRMAT | Doar pentru modificări; vezi observația 3 |
| 4 | C84 | Toate finalele 1–20.11 | 15 | ≈50,0 | 50,02 | CONFIRMAT | |
| 5 | P02 | Mediana în octombrie | 55 | 35 | 35,01 | CONFIRMAT | |
| 6 | C17 | Platforma veche, mediana | 18 | 1,6 | 1,64 | CONFIRMAT | Vezi observația 9 |
| 7 | C18 | Lansarea din 2024: mediană; finale pe zi | 23 | 12,1; 2.570 | 12,11; 236.467 / 92 zile cu decizii = 2.570 | CONFIRMAT | |
| 8 | C19 | 2025: mediană; finale pe zi | 23 | 3,0; 4.011 | 2,97; 1.010.770 / 252 = 4.011 | CONFIRMAT | |
| 9 | C04/C09 | Mediane pe luna depunerii, mai–sept. (doar dosare decise) | 20–21 | 5/5/7/19/≥39 | BERC 5,12/5,15/7,07/19,04/39,04; portal 5/5/7/18–19/39 | CONFIRMAT | |
| 10 | C05 | Creștere „de cel puțin 8 ori” mai → sept. | 20 | ≥ ~8× | 39,04 / 5,12 = 7,6× (39/5 = 7,8×); doar cu KM ≈11× | **DIFERIT** | Limita de jos declarată nu susține „≥8×” |
| 11 | C73 | Mediana Kaplan–Meier, cohorta din septembrie (portal) | 8, 79 | ≥≈58 (56–62) | 57; pe săptămâni: 28/35/50 | CONFIRMAT | n = 597 (raport: 605) |
| 12 | C11 | Octombrie–noiembrie sunt cenzurate | 21 | – | doar 18.761 / 4.585 dosare decise | CONFIRMAT | |
| 13 | C31 | Rezolvate într-o zi lucrătoare: platforma veche → criză | 16, 22 | 74,9% → 0,66% | 74,53% → 0,66% | CONFIRMAT | |
| 14 | C32 | W ≤ 2 zile: 1.03–26.04 vs 27.04–31.07.2026 | 24 | 20,8% → 1,2% | 20,80% → 1,18%; toate cele 42 de oficii < 3% | CONFIRMAT | |
| 15 | C101 | Exact a 3-a zi lucrătoare: modificări / înmatriculări / amânări | 24 | 56,7 / 49,8 / 72,5%; p5 23,9 → 70,0 h | 56,9 / 49,9 / 72,9% (27.04–28.06); p5 23,3 → 69,6 h | CONFIRMAT | Fereastra luată din registru. În iulie: 2,3%; vezi observația 4 |
| 16 | C01 | Finale pe zi lucrătoare, 1.10–20.11.2026; vârful feb.–mar. 2025 | 6, 15, 24 | ≈4.200; 5.006 | 4.176 (largi); 5.006 (stricte) | CONFIRMAT | Fără ziua parțială 20.11: 4.267 |
| 17 | C30 | Finale stricte pe zi lucrătoare, 1.10–20.11, anii 2023–2026 | 24 | 2.936 / 3.475 / 3.816 / 4.171 | 2.937 / 3.475 / 3.816 / 4.171 | CONFIRMAT | |
| 18 | C79 | Toate deciziile pe zi lucrătoare, 2023 → 2026 | 10 | 3.707 → 5.190 (+40%) | 3.707 → 5.190 (+40,0%) | CONFIRMAT | Include amânările |
| 19 | C87 | 2025 → 2026, aceeași fereastră | 10, 15 | 4.881 → 5.190 (+6%) | +6,3% | CONFIRMAT | Pe 1.10–19.11: 4.861 → 5.279 (+8,6%); pe finale stricte: +9,3% |
| 20 | C80 | Decizii în 2025 / 2026 | 10 | 1.268.621 / 1.159.219 | 1.268.622 / 1.159.219 | CONFIRMAT | Diferență de 1, ca în Tabelul 13 al raportului |
| 21 | C86 | Decizii pe zi lucrătoare, H1 → aug.–oct. | 10, 15 | 2025: −14%; 2026: −13% | −13,5%; −12,7% | CONFIRMAT | Pe finale stricte: −16,9% / −9,8%; vezi observația 8 |
| 22 | C07 | August față de iunie–iulie (finale stricte pe zi lucrătoare) | 24 | ≈0,90 | 0,900 | CONFIRMAT | |
| 23 | C03 | Amânări pe zi lucrătoare | 6, 31 | ≈1.000 | 1.015 (1.10–20.11); 1.058 (2026) | CONFIRMAT | |
| 24 | C21 | Ponderea amânărilor: platforma veche → val | 31 | 20,3 → 19,4% | 20,38 → 19,36% | CONFIRMAT | |
| 25 | C82 | Amânări în 2026 | 10 | 237.025 (20,4%) | 237.025 (20,45%) | CONFIRMAT | |
| 26 | C74 | Finale din noiembrie cu amânare anterioară | 7, 9 | ≈21%; 54,7 vs 49,8 | 21,37% (0 / 1 / 2 amânări: 78,63 / 21,12 / 0,24%); 54,7 vs 49,8 | CONFIRMAT | |
| 27 | C37 | Până la prima amânare / de la ultima amânare la decizie | 9, 32 | 41,9 / 14,0 | 41,9 / 14,0 | CONFIRMAT | |
| 28 | C39 | Ponderea respingerilor: platforma veche → din aug. 2026 | 9, 32 | 5,7 → 8,2% | 5,68 → 8,11% | CONFIRMAT | Vezi observația 6 |
| 29 | C57 | Respingeri: S2 2025 / 2025 / acum | 64 | 8,1% (1,6 z) / 7,51% / 8,6% | 8,05% (1,63 z) / 7,51% / 8,56% | CONFIRMAT | |
| 30 | C40 | Circa 8 din 10 firme respinse depun din nou | 9, 15, 31 | 77,6–80,4% | – | NEVERIFICABIL | Pickle-ul nu are identificatorul firmei |
| 31 | C103 | Redepunere după respingere vs după admitere | 32 | 43,8 / 69,1 / 84,4 vs 14,4 / 23,5 / 48,9 | – | NEVERIFICABIL | Idem |
| 32 | C41 | Înmatriculări admise fără amânare, > 10 zile lucrătoare | 9, 22 | 81,3% | 81,3% (doar J, n = 3.548); J + F: 82,0% | CONFIRMAT | Definiția (doar J) luată din registru |
| 33 | C38 | Rezolvate în ≤ 14 zile, 2–19.11; mediane | 6, 30 | 8,7% / 15,7%; 53 / 42 | 8,7% / 15,7%; 52,9 / 42,0 | CONFIRMAT | |
| 34 | C102 | Profilul dosarelor rapide | 30 | respinse 0,9% vs 9,0%; PFA 12,9% vs 20,6%; τ 0,43 | doar CERERE265: 0,8% vs ≈9,0%; 13,0% vs 20,7%; τ 0,427 | CONFIRMAT | Calculat doar pe modificări; pe ambele categorii: PFA 20,7% vs 24,4%, τ 0,38 |
| 35 | C36 | Depuse în afara programului vs în program (aceeași zi, același județ) | 27 | +0,8…+1,9 z | +0,6 (mediana diferențelor) / +1,6 (ponderat) / +2,5 (medie) | CONFIRMAT | Semnul se confirmă; mărimea depinde de definiție, cum spune și raportul |
| 36 | C49 | Medianele pe oficii, decizii 1–18.11 | 9, 16, 28 | 47,9–55,8; mediana oficiilor 50,2 | 47,92–55,81; 50,19; N minim 420 | CONFIRMAT | N-urile mele sunt cu ~1% mai mari |
| 37 | C89 | BN 55,8; 4 oficii la ≈53,1; B 47,9 | 28, 128 | – | BN 55,81; HR 53,09, VN 53,06, VS 53,05, TR 53,05 (BH 53,04); B 47,92 | CONFIRMAT | Vezi observația 5 |
| 38 | C75 | CV între oficii; Spearman 2025 vs noiembrie | 8 | 3,3%; −0,07 (−0,37…0,24) | 3,33%; −0,076 (bootstrap −0,39…0,25) | CONFIRMAT | |
| 39 | C88 | Abaterea medie lunară față de mediana națională, ian. 2025–iul. 2026 | 28, 129 | CT 3,88 / BV 2,71 / TR 2,46 / GL 2,28 | 3,87 / 2,71 / 2,46 / 2,29; aceleași vârfuri | CONFIRMAT | |
| 40 | C90 | Respingeri pe oficiu, aug.–nov. 2026 | 131 | BC 11,9 / BV 11,1 / IL 10,4 / GJ 3,2 | 11,78 / 10,99 / 10,38 / 3,25 | CONFIRMAT | Ordinea respingerilor e stabilă: ρ(2025, criză) = 0,46 |
| 41 | C78 | Întârzierea publicării în 2026: p50 / p99 | 7 | 0,67 / 5,01 z | 0,674 / 5,01 | CONFIRMAT | |
| 42 | C81 | Decizii în afara orelor 8–16: 2023 → 2026; în zile nelucrătoare | 64 | 14,4 → 10,6%; 5 | 14,4 → 10,6%; 5 | CONFIRMAT | Perechea de ani (2023 → 2026) nu e spusă în text |
| 43 | C93 | Numere de contor pe zi lucrătoare (ian.–iul.); cereri de înregistrare | 53, 65 | ≈21.000; ≈4.400 | 21.057; 4.369 | CONFIRMAT | |
| 44 | C98 | Intrări H1 2026 (BERC, dosare distincte) | 29 | 4.369 | 4.369 (cu HJ) / 4.355 (fără) | CONFIRMAT | |
| 45 | C99a | Vârful din septembrie, intrări pe zi lucrătoare | 15, 29 | 10.881 (10.123–11.588) | 10.953 (10.239–11.667), ponderat pe straturi săptămânale | CONFIRMAT | Calibrare: ponderea ponderată a numerelor din BERC e 0,250, față de 0,247 din BERC/contor. Neponderat: 11.193 |
| 46 | C99b | Mai–iulie / octombrie / 1–19.11 / aug.–oct. | 29 | 4.430 / 4.129 / 3.039 / 6.840 | 4.492 / 4.130 / 3.036 / 6.866 | CONFIRMAT | Iunie–august estimat vs BERC: 4.151 vs 4.075 și 5.450 vs 5.611. Mai e supraestimat (5.043 vs 4.191), pentru că eșantionul începe abia la 11.05 |
| 47 | C100 | Stoc estimat la 30.10 / 6.11 / 20.11 | 29 | ≈214k / ≈203k (192–216k) / ≈193k | 218,1k / 210,0k (IC la 7.11: 192–219k) / 194,7k | **DIFERIT** | Diferențe +1,9 / +3,4 / +0,9%; cea de la 6.11 e peste pragul de 2%, dar în interiorul IC. Vezi observația 10 |
| 48 | C22 | Săptămâna de vârf din septembrie vs vară | 29 | ≈1,7× | 1,68× (contor, toate tipurile) | CONFIRMAT | Pentru cererile supuse soluționării vârful e mult mai mare |
| 49 | C06 | Dintre dosarele în așteptare (portal), cât e la operare | 27 | 48,5% | 48,6% neponderat; 46,2% ponderat după densitatea contorului | CONFIRMAT | Vezi observația 12 |
| 50 | C13 | Cel mai vechi dosar nerezolvat din eșantion | 19 | 16.09.2026 | 16.09 (15.09 dacă faza „în înscriere” se socotește nerezolvată) | CONFIRMAT | |
| 51 | C28/C29/C33/C85/C47/C51/C83 | Cifrele MJ și aritmetica pe ele | 5, 15, 26–27 | 204.414; 51,9%; −8.300 / +4.396; −3.904; +53%; 134; 5,76 mil. | aceleași (transcriere și aritmetică) | CONFIRMAT | Cifrele de bază ale MJ nu se pot verifica din date |
| 52 | C34 | Operarea față de soluționare, 31.10–6.11 | 6, 27 | 16–20% | 16,1% (toate deciziile) – 20,8% (finale stricte) | CONFIRMAT | |
| 53 | C48 | „Soluționările” MJ vs BERC | 30 | 4.912 / 5.098 vs 4.825 / 5.041 | cifrele MJ lipsesc din folder; fereastra BERC nu e spusă | NEVERIFICABIL | |
| 54 | C50 | ≈25% din decizii sunt actualizări CAEN | 7, 50 | 24,0–26,1% | – | NEVERIFICABIL | Cere textul PDF al buletinelor |
| 55 | C76 | Stoc prin legea lui Little | 8 | ≈136.000 | 118.000–154.000, după alegerea lui W | NEVERIFICABIL | Definiția nu e precizată |
| 56 | C70 | Backtest pe ritmul de soluționare: MAE; real ≥ prognoză | 35–36, 88 | ≈5,5%; 7 din 9 | 5,57%; 7 din 9, dacă prognoza folosește doar deciziile publicate până la origine | CONFIRMAT | Pe date revizuite (complete): MAE 4,8%, real ≥ prognoză doar în 2 din 9; vezi observația 2 |
| 57 | C71a | Profil sezonier: ian.–mar. față de noiembrie | 37–38 | +11 / +13 / +11% | 2024: +15 / +9 / +7%; 2026: +15 / +21 / +14% (2025: +61…+81%, după un noiembrie 2024 slab) | CONFIRMAT | Ordinul de mărime se potrivește cu anii fără perturbări |
| 58 | C71b | Profil sezonier: iulie–august față de noiembrie | 37–38 | −5 / −6% | 2023: −21 / −22%; 2025: −10 / −11% | **DIFERIT** | Scăderea de vară e mai adâncă în date decât în profilul atenuat al modelului |
| 59 | Tab. 17 | Intrări ale modelului: capacitate (moda) 4.425; stoc inițial (moda) 200k | 85 | 4.425; 200k | 4.504 (media ultimelor 12 zile lucrătoare până la 19.11, finale stricte); stocul MJ 204k | CONFIRMAT | Abatere 1,8% / 2% |
| 60 | Tab. 17 | Flux recurent zilnic, moda 3.350 | 85 | 3.350 | intrări măsurate 4.369 / zi lucrătoare (H1, cu CAEN) | NEVERIFICABIL | Se potrivește doar dacă cererile CAEN (~27%) sunt scoase separat; unitatea nu e spusă |
| 61 | C42–C44, C59–C61, C63–C66, C68, C69, C72 | Rezultatele modelului și ale grilei | 33–44 | ex. 136 (74–214); 73 / 222; 206; 69 (47–96) | Textul se potrivește cu Tabelele 18–22, celulă cu celulă | NEVERIFICABIL | Doar consistența internă e verificată, nu simularea |
| 62 | C62 | Stocul de muncă în iunie 2028 | 34, 63 | ≈398.000 | Tabelele 18 și 20 ale aceluiași raport: 395.446 | **DIFERIT** | Nepotrivire internă mică (altă sursă de traiectorie) |
| 63 | C58, C67, C96, C97, C35, C56, C52–C55 | Prognoze, model în tandem, backtest de mecanism | 33–50 | – | – | NEVERIFICABIL | Ar cere reconstruirea simulării |
| 64 | C91 | Bilanțul față de presă | 16, 53 | 9 / 5 / 2 / 3 | Tabelul 12.1 dă exact 9 / 5 / 2 / 3 (19 rânduri din 23) | CONFIRMAT | Vezi observația 13 |
| 65 | C92/P12 | Înmatriculări admise ian.–sept. 2026; variația anuală | 53, 56 | 100.802; −8,0% | 100.802; −8,0% | CONFIRMAT | |
| 66 | P13–P17, P04, P19 | Aug.–oct. −48,8%; sept. −52,2% / +21,9%; oct. −58,4%; 2.784 → 1.448; −17,8%; Cluj 52,8; Mehedinți 53,0 | 55–56 | idem | identice | CONFIRMAT | |
| 67 | P05 | Vârful contorului pe zi | 55 | ≈34.520 | anvelopă robustă (cuantila 1%): 50.142 (13.01.2026); în septembrie 36.547 (15.09) | **DIFERIT** | Definiția „vârfului” nu e spusă; 13.01 pare o zi reală de vârf (12–14.01: 23k / 50k / 27k) |
| 68 | C23 | Art. 105 alin. (1): o zi lucrătoare | 5, 17 | 1 zi lucrătoare | transcrierea se potrivește cu `cifre_oficiale_MJ.md` | NEVERIFICABIL | Textul legii nu e în folder |

## 3. Observații critice

1. **Ultima zi din arhivă e incompletă** (p. 6, 10, 15, 24 și Tabelul 3, p. 75).
   - Pe 20.11 arhiva are doar 892 de finale stricte, față de ~4.500 într-o zi obișnuită. Pentru modificări: 801, față de ~3.800.
   - Ziua e totuși numărată ca zi lucrătoare întreagă. Pe fereastra 1.10–19.11, C01 devine 4.267 (în loc de 4.176), iar C87 devine 4.861 → 5.279 (+8,6%, în loc de +6%).
   - Efectul e conservator pentru afirmațiile despre producție. Medianele nu se schimbă: 57,10 pe 16–19.11.

2. **Backtestul C70: abaterea vine din întârzierea de publicare** (p. 35–36, 64, 88–89).
   - Tabelul 24 se reproduce exact dacă prognoza „media ultimelor 12 zile” folosește doar deciziile publicate până la data de origine. E un test „în timp real”, legitim pentru un motor alimentat cu arhiva așa cum e publicată.
   - Subestimarea în 7 din 9 ferestre nu vine însă din regulă. Vine din ultimele zile, încă incomplete din cauza întârzierii de publicare (p50 ≈ 0,7 zile, p90 ≈ 2,9 zile).
   - Pe date revizuite (complete), aceeași regulă supraestimează ușor ritmul: real ≥ prognoză doar în 2 din 9 ferestre, MAE 4,8%.
   - Textul ar trebui să spună că testul e în timp real și că abaterea ține de vechimea datelor, nu de regulă.
   - Intrarea modelului (moda 4.425) e apropiată de valoarea pe date complete (4.504), deci concluzia practică („poate puțin pesimistă”) nu se schimbă mult.

3. **„Așteptarea a crescut în fiecare săptămână”** (p. 15, 16, 19; C16). E adevărat doar pentru modificări. La înmatriculări, mediana săptămânală scade de două ori: 34,8 → 30,9 în săptămâna 26.10 și 43,6 → 41,1 în săptămâna 16.11.

4. **Termenul minim de fapt de 3 zile lucrătoare** (p. 24; C101).
   - Cifrele sunt corecte pentru 27.04–28.06, fereastră care apare doar în registrul atașat.
   - Textul spune „de atunci, majoritatea deciziilor sunt emise exact în a treia zi lucrătoare”. În iulie, ponderea finalelor emise exact în a treia zi lucrătoare e 2,3%, iar pe 27.04–31.07 e 37%.

5. **Clasamentul oficiilor nu are rezoluție** (p. 6, 28, 128–131; C89).
   - Medianele se adună pe câteva valori: 8 oficii la 53,0, 4 la 53,1, 7 la 50,1, 6 la 50,0. Locurile 2–13 diferă cu cel mult 0,1 zile (~2 ore).
   - Grupul „4 oficii la ≈53,1” lasă pe dinafară Bihorul (53,04) față de Teleorman (53,05). Diferența e de 0,01 zile, adică ~15 minute.
   - Raportul spune singur că diferențele sunt mici (C75). Totuși numește oficii în fișele executive.

6. **Respingerile nu cresc din cauza crizei** (p. 9, 31–32; C39 vs C57).
   - Fișele compară platforma veche (5,7%) cu criza (8,2%).
   - Ponderea era deja 7,4–7,9% în 2025, 8,05% în S2 2025 și 8,0% în H1 2026, deci saltul e din 2024–2025.
   - Raportul spune asta doar în C57, care nu apare în fișe.

7. **Redepunerea după respingere e prezentată fără termen de comparație** (p. 9, 15, 31; C40 vs C103).
   - „Circa 8 din 10 firme respinse depun din nou” apare fără bază de comparație. Propriul C103 arată că 48,9% dintre firmele admise depun și ele o nouă cerere în același orizont.
   - Definiția „redepunerii” variază: același tip sau orice cerere; în același an sau în 30 de zile.
   - Nu se poate verifica aici: datele nu au identificatorul firmei.

8. **Sezonalitatea e sprijinită pe puține date** (p. 10, 15, 37; C86, C71).
   - „Scăderea din aug.–oct. e sezonieră” se bazează practic doar pe 2025: 2024 e perturbat, iar 2023 nu are H1 în arhivă.
   - Rezultatul depinde și de includerea amânărilor. Pe finale stricte, scăderea e −16,9% în 2025 și −9,8% în 2026.
   - Vârful din ianuarie–martie al profilului din model (+11…+13%) se potrivește cu 2024 și 2026. Scăderea de vară din date (−10…−22%) e însă mai adâncă decât în profil (−5…−6%).

9. **Mărcile de timp de pe platforma veche** (p. 18, 22 și Tabelul 6, p. 78).
   - Înainte de 26.07.2024, 100% din datele de depunere sunt la ora 00:00. Pe platforma nouă, depunerea are loc în medie la 0,53 dintr-o zi (≈12:45).
   - W de pe platforma veche include deci, în medie, ~0,5 zile dinaintea depunerii: mediana de 1,6 zile e umflată.
   - Coloana „≤24 h” din Tabelul 6 (0,30% pe platforma veche vs 15,8% în 2025) e un artefact.
   - Indicatorul în zile lucrătoare (C31) nu e afectat.

10. **Intrările și stocul estimate din portal** (p. 15, 29; C99, C100).
    - Înmatriculările în curs nu se văd în portal: nu au încă firmă, deci nici detalii.
    - Cu cele 400–600 pe zi adăugate (corecție recunoscută de raport), intrările din octombrie (~4.500–4.700 pe zi lucrătoare) sunt cel puțin la nivelul finalelor din octombrie (4.139). „Din octombrie, intrările sub ritmul de soluționare” e sigur doar pentru noiembrie.
    - Seria mea de stoc urcă până la ~224k pe 13.10, stă pe loc în octombrie și scade de la sfârșitul lui octombrie.
    - Circa 6k din scăderea de ~23k dintre 30.10 și 20.11 e un artefact: înmatriculările decise înainte de recoltare se văd doar la datele mai vechi. Fără înmatriculări, stocul scade de la 211,9k la 194,7k.

11. **C05.** Limita de jos declarată (39 / 5) dă 7,6–7,8×, nu „de cel puțin 8 ori”.

12. **C06.** Eșantionul din portal e neuniform: fișierele de recoltare acoperă intervale diferite ale contorului. Ponderat după densitatea contorului, procentul la operare e 46,2%, nu 48,6%, și exclude înmatriculările în curs. Acordul cu cifra oficială de 51,9% e deci mai slab decât pare.

13. **Comparația cu presa** (p. 53–56).
    - P14 (+27,8% în presă vs +21,9% în date) e marcat CONFIRMAT, deși regula raportului cere aceeași definiție și o diferență mică. Ar trebui COMPATIBIL.
    - Bilanțul 9 / 5 / 2 / 3 acoperă 19 din cele 23 de afirmații din compilație. P11 și P21–P23 lipsesc fără mențiune.

14. **„Decizii” înseamnă lucruri diferite în afirmații alăturate** (p. 10, 15, 24).
    - C30 folosește finale stricte: +9,3% față de 2025.
    - C79 și C87 includ amânările, deci un dosar amânat e numărat de două ori: +6%.
    - C01 folosește finale largi, dar vârful de 5.006 e pe finale stricte.
    - Nu e greșit, dar „cât a crescut producția” depinde de numitor.

15. **Ferestre care se schimbă de la o afirmație la alta.** Apar 16–20, 1–20, 1–18 și 2–19 noiembrie, iar unele ferestre nu sunt spuse deloc în text (C101, C99, C81). Valorile pe care le-am testat sunt robuste, dar replicarea e mai grea.

16. **Modelul de prognoză.**
    - Modelul FIFO descrie dosarul tipic, deși datele arată o bandă rapidă (τ = 0,43; 8,7% din modificări în ≤ 14 zile).
    - Backtestul mecanismului (C96) acoperă doar cohortele decise până la 13.09, adică înaintea vârfului.
    - Fluxul recurent (3.350) nu are unitatea declarată.
    - C62 (398k) diferă de Tabelele 18 și 20 (395.446).
    - În Tabelul 20, patru celule p90 ale rândului „−10% intrări” sunt identice cu mediana rândului „0%” (222 / 136 / 73 / 18). Merită verificat dacă e o coincidență.

17. **Subpopulații alese fără să fie spuse.**
    - C41 folosește doar înmatriculările J, deși textul spune „firmele noi”. Cu J + F: 82,0%.
    - Profilul dosarelor rapide (C102) e calculat doar pe modificări.
    - Diferențele de valoare sunt mici.

## 4. Scripturile și comenzile rulate (în `lucru/`)

| Script | Ce face |
|---|---|
| `common.py` | Încărcare slabă a datelor (fără `office` și `code4`), calendarul legal RO (Paștele ortodox calculat), zile lucrătoare |
| `s00_inspect.py`, `s01_portal_inspect.py` | Inspecția structurii datelor |
| `s02_calendar_check.py` | Reproduce Tabelul 1; validează calendarul pe Tabelul 3; ponderea depunerilor la ora 00:00, pe ani |
| `s03_link_check.py` | Unicitatea cheii dosarului; completitudinea ultimelor zile; întârzierea de publicare |
| `s04_berc_core.py` → `res_berc_core.txt` | C01, C03, C07, C14–C19, C21, C30–C32, C79–C87, C101 |
| `s05_berc_more.py` → `res_berc_more.txt` | C36–C41, C49, C57, C74, C75, C78, C81, C88–C90, C102, C04, presa |
| `s06_berc_misc.py` → `res_berc_misc.txt` | Variante de definiție: C101, C102, C88, C18; C34; C70; C71; C76; trunchierea |
| `s07_backtest_variants.py`, `s08_backtest_realtime.py` | Definițiile backtestului C70 |
| `s09_portal_explore.py` | Deduplicarea portalului (păstrează înregistrarea cea mai completă); legătura cu BERC; contorul. Scrie fișierele cache `portal_*_dedup.pkl` |
| `s10_inflow.py` → `res_inflow.txt` | C93, C98, C99 (neponderat), C22 |
| `s11_portal_stock.py` → `res_portal_stock.txt` | C06, C13, C73/C09, C100 (stoc ponderat pe straturi ale contorului, IC bootstrap) |
| `s12_stock_series.py` → `res_stock_series.txt` | Seria săptămânală a stocului estimat |
| `s13_remaining.py` → `res_remaining.txt` | C88 (abaterea medie), intrările modelului, C48, P05, C05 |
| `s14_registry_defs.py` → `res_registry_defs.txt` | C41 și C101 pe definițiile din registru (rulat după prima trecere) |
| `s15_fixes.py` → `res_fixes.txt` | C99 ponderat pe straturi și calibrare; C71 pe mai mulți ani; P05 robust; C87 fără 20.11; ora medie a depunerii |
| `valori_proprii_first_pass.csv` | Valorile mele, salvate înainte de a deschide orice anexă atașată |

**Comenzi rulate direct (fără fișier de script):**
- Extragerea textului PDF cu PyMuPDF (`page.get_text()`), folosită ca material de lucru și apoi ștearsă, pentru că conținea numele autorului.
- Afișarea a cinci rânduri din `claims_registry.csv` (C05, C13, C41, C99, C101), după prima trecere.
- O singură citire în afara folderului: o copie a ieșirii propriei mele comenzi (partea a 3-a a textului PDF), salvată automat de mediul de lucru în directorul lui de sesiune, pentru că ieșirea era prea lungă. Nu am deschis alte fișiere din afara folderului.

**Fișierele cache** `berc_slim.pkl` și `portal_*_dedup.pkl` sunt la nivel de înregistrare și au fost șterse la final. Se regenerează automat: `common.load()` pentru primul, `s09_portal_explore.py` pentru celelalte.
