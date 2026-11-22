# Durata de înregistrare la ONRC, activitatea firmelor noi și veniturile bugetare la risc în 2027

Dosar de dovezi econometrice (22.11.2026). Conține doar agregate: nu apar CUI-uri, denumiri, nume de persoane sau rânduri individuale. Fișierele intermediare la nivel de dosar (`_work/`) sunt șterse de `99_cleanup.py` după rulare. Rezultatul final este `../out/econometrics.json`. Fiecare intrare are forma `{id, estimate, ci95, n, method, sample, window, caveat}`.

## Rulare (reproductibilă)

```
..\..\venv\Scripts\python.exe -X utf8 test_econ_lib.py    # testează OLS/2SLS/SE cluster pe date simulate
..\..\venv\Scripts\python.exe -X utf8 01_build_sample.py  # BERC JSON + bilanțuri MF -> _work/ (record-level)
..\..\venv\Scripts\python.exe -X utf8 02_part_a.py        # PARTEA A -> tables/*.csv, partA_results.json
..\..\venv\Scripts\python.exe -X utf8 03_part_b.py        # PARTEA B (motorul importat, nemodificat) -> tables/, partB_results.json
..\..\venv\Scripts\python.exe -X utf8 04_figures.py       # figures/*.png|svg
..\..\venv\Scripts\python.exe -X utf8 05_build_json.py    # ../out/econometrics.json
..\..\venv\Scripts\python.exe -X utf8 99_cleanup.py       # șterge _work/
```

Sămânța motorului este 20261121 (2.000 de variante), iar sămânța Monte Carlo este 20261122. Motorul `audit_forecast.py` este importat nemodificat. `prepare_workload()` rulează cu directorul de ieșire redirecționat către un director temporar. Scriptul verifică trei lucruri:
- fișierele din `audit_data/` rămân identice octet cu octet;
- intrările regenerate coincid cu cele publicate;
- scenariul „continuitate” reproduce 74/136/214,1 zile la 30.06.2028.

Biblioteca `econ_lib.py` implementează în numpy:
- OLS și 2SLS cu efecte fixe absorbite;
- SE cluster CR1 (una sau două dimensiuni);
- F cluster-robust de primă etapă;
- testul Anderson-Rubin.

Pe date simulate, acoperirea IC 95% iese 0,95, iar OLS coincide cu statsmodels.

## Date și eșantion

**Firme.** Înmatriculările de societăți (forma J) admise, din articolele BERC (`*_INMATRIC265.json`). Durata este numărul de zile calendaristice de la data depunerii la data încheierii. Ambele date au precizie de zi pe ambele platforme: înainte de 26.07.2024 ora depunerii este 00:00. Oficiul este județul cererii (42).

**Rezultate.** Firmele sunt legate prin CUI de bilanțurile MF (date deschise) pentru FY2024 și FY2025. O firmă fără rând de bilanț nu a depus bilanț și primește 0 la toate rezultatele monetare.

**Eșantionul principal.** Depuneri din 1.01–31.12.2024, decise în 2024: n = 90.004. Au fost excluse 451 de firme decise în 2025. Rezultatul este bilanțul FY2025, primul an complet după înregistrare.

**De ce nu cohorta 2025 pentru anul următor.** Pentru ea, primul an complet este FY2026, care nu există încă. Cohorta 2025 intră doar în analizele pe primul an parțial.

**Rezultate măsurate:**
- a depus bilanț;
- cifră de afaceri > 0 și log(1+cifră);
- salariați > 0 și numărul de salariați;
- impozit direct proxy în două variante:
  - I16−I18, cum s-a cerut;
  - (I16−I17)−(I18−I19), care captează și impozitul pe venitul microîntreprinderilor plătit de firmele cu pierdere.

Variabilele monetare sunt winsorizate la p99.

## PARTEA A — metode, credibilitate, limite

### (i) OLS cu efecte fixe

**Ce este.** O regresie a rezultatului pe durata proprie, cu efecte fixe pentru:
- săptămâna depunerii, care elimină sezonalitatea și șocul național de lansare a portalului;
- oficiu;
- forma juridică.

Erorile standard sunt grupate pe oficiu (42 de clustere). CAEN 2 cifre poate fi folosit doar pentru firmele care au depus bilanț, pentru că este observat numai în bilanț. De aceea apare doar într-un bloc de robustețe, condiționat pe depunere.

**Credibilitate.** Este o descriere corectă a corelației în interiorul aceleiași săptămâni și al aceluiași oficiu, dar nu este un efect cauzal. Durata proprie include amânările pentru dosare incomplete, iar acestea sunt mai frecvente la fondatorii mai slab pregătiți.

**Limite și rezultat.** OLS dă efecte negative mici și semnificative pe zi:
- −0,15 p.p. la cifra de afaceri > 0;
- −781 lei cifră de afaceri;
- −32 lei impozit.

Le interpretăm drept selecție. Treptele de durată pe OLS arată același tipar (figura 1, albastru).

### (ii) Variabilă instrumentală (2SLS)

**Ce este.** Durata proprie este instrumentată cu mediana leave-one-out a duratei celorlalte cereri de înmatriculare, de orice formă juridică, depuse la același oficiu în aceeași săptămână. Folosim săptămâna depunerii, nu a deciziei, pentru că aceasta din urmă depinde de propria durată. Celula trebuie să aibă cel puțin 5 alte cereri.

Prima etapă: coeficient 0,76, F cluster-robust 792 (two-way oficiu × săptămână 394). Instrumentul păstrează o variație reziduală de 2,6 zile după efectele fixe. Instrumentul nu este slab, iar intervalele Anderson-Rubin, robuste la instrument slab, sunt practic identice cu cele Wald.

Am rulat trei variante:
- media leave-one-out în loc de mediană;
- SE two-way pe oficiu × săptămână;
- un „IV național”: cohortele 2023 și 2024, cu mediana națională a săptămânii de depunere ca instrument și FE pe săptămâna din an, cohortă și oficiu × cohortă.

**Credibilitate.** Congestia oficiului într-o săptămână, mai ales în colapsul aug.–nov. 2024, este determinată de fluxul total și de capacitatea oficiului, nu de calitatea unei firme anume. Efectele fixe absorb diferențele permanente între oficii și șocurile naționale. Instrumentul elimină componenta endogenă a duratei proprii, adică amânările.

**Limite.**
- Riscul principal este un șoc local de cerere care aglomerează oficiul și, în același timp, schimbă tipul de fondatori. Testele placebo de mai jos îl verifică parțial.
- Efectul este local: este identificat pe durate observate de 0–93 zile (p99 = 35).
- Rezultatele vin din bilanțuri, nu din încasări ANAF.

**Rezultat (efect pe zi de așteptare, anul complet următor, IC 95%).** Nimic nu se distinge de zero:

| Rezultat | Efect pe zi | IC 95% |
|---|---|---|
| A depus bilanț | +0,09 p.p. | [−0,26; +0,44] |
| Cifră de afaceri | −422 lei | [−2.089; +1.245] |
| Cifră de afaceri peste plafonul TVA | −905 lei | [−2.195; +386] |
| Salariați | +0,003 | [−0,004; +0,009] |
| Impozit direct (I16−I17)−(I18−I19) | −16 lei | [−65; +32] |
| Impozit direct I16−I18 | −18 lei | [−67; +31] |

La 10 zile de așteptare, IC exclude:
- o scădere a probabilității de activitate mai mare de 2,6 p.p., față de o medie de 66,8%;
- o pierdere de impozit direct mai mare de 650 lei pe firmă, față de o medie de 4.822 lei.

Varianta condiționată, cu FE CAEN, și varianta cu media leave-one-out dau același rezultat nul. IV național dă efecte mici, pozitive la limită, de exemplu +18 lei impozit pe zi. Le atribuim compoziției cohortei și unui singur episod de șoc, nu unui efect benefic.

### (iii) Trepte de durată (event-study bins)

**Ce este.** Durata este împărțită în trepte: 0–2 (referință), 3–7, 8–14, 15–30, 31–60 și >60 zile. Se estimează în două feluri:
- OLS pe durata proprie;
- formă redusă pe treptele instrumentului.

Treapta >60 are 17 observații, iar instrumentul 31–60 are 12, așa că nu sunt estimate.

**Credibilitate și limite.** Treptele arată dacă efectul e neliniar, de exemplu un prag. Cele OLS coboară monoton, ceea ce reflectă selecția. Cele pe instrument au IC largi care includ zero (figura 1). Cu un singur episod de congestie mare, puterea pe treptele superioare este redusă.

### (iv) Testele placebo

**Ce este.** Atributele predeterminate sunt regresate pe instrument, cu aceleași efecte fixe. Pe tot eșantionul: forma SA, forme rare, depunere în weekend. Doar pentru firmele cu un bilanț: capitalul subscris (log și praguri) și secțiunea CAEN pentru 7 secțiuni.

**Rezultat.** Din 13 teste, două resping la 5%, față de circa 0,65 respingeri așteptate din întâmplare:
- **Depunerea în weekend** (+0,07 p.p. pe zi a instrumentului, la o bază de 0,6%). Este posibilă doar pe portalul nou, deci este un artefact de platformă.
- **Secțiunea H (transport)** (−0,15 p.p. pe zi, adică −15% din medie la 10 zile). Probabil reflectă valuri locale de firme de ride-sharing.

Capitalul subscris (p = 0,40–0,96) și celelalte secțiuni CAEN (p = 0,08–0,89) nu răspund semnificativ la instrument. La limită sunt forma SA (p = 0,07) și industria C (p = 0,08).

**Limite.** Testele pe capital și CAEN sunt condiționate pe depunerea unui bilanț. Recomandăm prudență: instrumentul este în mare parte, dar nu perfect, ortogonal la compoziție. Rezultatul nul rămâne valabil și cu FE CAEN în eșantionul condiționat.

### (v) Diferența-în-diferențe în jurul lansării portalului (2024)

**Ce este.** Compară depunerile din 1.08–30.11 („șoc”) cu cele din 1.06–25.07 („pre”). Contrastul se face față de aceleași ferestre din alt an, cu FE pe săptămâna din an și pe oficiu × cohortă. Wald-DiD împarte diferența de rezultat la diferența de durată (+10,2 zile; F = 105, two-way 61).

Ce este comparabil, exact:
- **Primul an complet după înregistrare:** cohorta 2024 (FY2025) față de cohorta 2023 (FY2024). Cohorta 2025 nu poate servi aici, pentru că FY2026 nu există.
- **Primul an parțial (anul înregistrării):** cohorta 2024 (FY2024) față de cohorta 2025 (FY2025).

**Credibilitate.** Sezonalitatea comună, adică faptul că o firmă înregistrată în august are un an parțial mai scurt, se anulează între ani. Volumul depunerilor nu a scăzut în timpul șocului: raportul șoc/pre a fost 2,81 în 2024, față de 2,61 în 2023 și 2,16 în 2025. Nu vedem deci selecție vizibilă la intrarea în sistem.

**Limite.**
- În 2024, grupul „pre” era pe platforma veche, iar în 2025 ambele grupuri sunt pe portal. Lansarea portalului aduce și alte schimbări, nu doar durata.
- Între ani regimul fiscal s-a schimbat (microîntreprinderi, TVA din august 2025).
- La anul parțial, rata de depunere a bilanțului crește în DiD (+5,7 p.p.), semn că ipoteza de tendințe paralele pentru depunerea pe anul parțial este discutabilă.

**Rezultat.**
- **Anul complet:** fără efect. Pe zi: +0,06 p.p. la activitate [−0,16; +0,28], −1.280 lei cifră de afaceri [−3.353; +792], −4 lei impozit [−47; +40]. Studiul pe luna depunerii (figura 3) arată un salt de durată de +14,8 zile în august–septembrie 2024 și nicio ruptură la activitatea din anul următor.
- **Anul parțial:** −1.327 lei cifră de afaceri [−1.821; −834] și −33 lei impozit direct [−48; −18] pe zi de așteptare.

### Primul an (parțial): cifra pe zi de la depunere vs. de la decizie

**Ce este.** IV pe aceeași celulă oficiu × săptămână, pe depunerile 1.01–31.10, cu rezultat în anul înregistrării.

**Rezultat, cohorta 2024 (F = 1.022).** Fiecare zi de așteptare reduce cifra de afaceri din primul an cu 1.434 lei [765; 2.102] și impozitul direct cu 43 lei [17; 69]. Cifra raportată la zilele de la depunere scade cu 5,8 lei/zi [1,7; 10,0], iar cea raportată la zilele de la decizie nu se mișcă semnificativ (−2,1 [−6,7; +2,4]).

**Interpretare.** Activitatea începe la decizie, deci zilele de așteptare se pierd din anul calendaristic al înregistrării. Pierderea pe zi este de circa 3 ori cifra zilnică medie din anul parțial și de 2,6 ori cifra zilnică matură din anul următor (553 lei), cu limita inferioară a IC tot peste 1,4. O amânare pură nu poate pierde mai mult de o zi matură per zi de așteptare. Rampa de creștere explică doar o parte; restul poate fi compoziție sau zgomot. De aceea, în PARTEA B estimarea servește doar ca limită superioară. DiD pe 2024 față de 2025 dă aceeași mărime (−1.327 lei/zi). Acest DiD pe anul parțial este însă un sprijin mai slab: rata de depunere a bilanțului se mișcă și ea (+5,7 p.p.), deci ipoteza de tendințe paralele e îndoielnică. Pentru cohorta 2025 (durate mici, F = 603), efectul nu e semnificativ: −602 lei [−1.736; +532].

### Concluzia PARTEA A

Așteptarea întârzie începutul activității și reduce cifra de afaceri și impozitul din primul an calendaristic. Aceasta este o pierdere de sincronizare, găsită în IV pe 2024 și susținută, mai slab, de DiD (vezi rezerva de mai sus). Nu găsim efect asupra activității, cifrei de afaceri, angajării sau impozitului în primul an complet, în niciun design. Pentru durate de până la ~35 zile, un efect persistent mare poate fi exclus; unul mic, nu.

## PARTEA B — venituri ale administrației publice la risc în 2027

### Componente

**(a) Durate.** Din cele 2.000 de variante ale motorului, pe scenariul „continuitate”, se ia pentru fiecare zi de depunere din 1.12.2026–31.12.2027 durata unui dosar standard. Variantele sunt extrase direct din motor, nu din cuantile. Durata la înmatriculare este durata cozii × κ:
- κ este triunghiular (0,65; 0,71; 1,0);
- valorile vin din raportul median înmatriculări/mențiuni pe săptămâna deciziei, ultimele 4 săptămâni;
- până la mijlocul lui octombrie 2026 raportul era ≈1, de atunci înmatriculările sunt prioritizate.

Zilele în exces se calculează peste o durată normală de 3 zile. Durata medie la înmatriculare pe trimestru (P50): T1 70, T2 112, T3 104, T4 110 zile. Aceste valori sunt de 2–4 ori peste suportul estimării din PARTEA A (p99 35 zile).

**(b) Volume.** Înmatriculările J pe lună vin din BERC: triunghiular între nivelurile 2025 și 2026. Pentru aug.–dec., unde datele 2026 sunt cenzurate, nivelul 2025 este scalat cu raportul 2026/2025 din ian.–iul. (0,86). Mențiunile folosesc nivelurile lunare 2024–2025.

**(c) Venitul public al unei firme.**

impozit direct (I16−I17)−(I18−I19) + salariați × 21.668 lei/an + 21% × pondere VA × cifra de afaceri a firmelor peste plafonul TVA

Termenii:
- 21.668 lei/an înseamnă CAS 25% + CASS 10% + impozit 10% după deducerea personală + CAM 2,25%, calculate la salariul minim de 4.325 lei;
- ponderea VA este triunghiulară 0,20–0,40 și este o presupunere, nu o estimare.

**(d) Parametri statutari.** Verificați pe texte oficiale; detaliile și URL-urile sunt în `statutory_parameters.json`:
- TVA 21% (din 1.08.2025);
- micro 1% (plafon 100.000 EUR, din 2026);
- profit și dividende 16%;
- CAS/CASS/impozit/CAM;
- salariul minim 4.325 lei (HG 146/2026).

Neverificat:
- salariul minim pentru 2027 (presupus neschimbat);
- actul care stabilește plafonul TVA de 395.000 lei.

Randamentul de actualizare: obligațiuni de stat la 10 ani, 6,77% (Eurostat, oct. 2026).

### Cele două canale, cerute separat

**Canalul 1 — amânat.** Venitul pe care firma l-ar fi generat în zilele de așteptare în exces.

*Calibrarea centrală* este mecanică: venitul public mediu al unei firme noi pe zi în primul an complet, pentru toate firmele (0 pentru cele fără bilanț): 77 lei/zi (IC 71–84). Se compune din:
- 13 lei impozit direct;
- 40 lei contribuții și impozit salarial;
- 24 lei TVA (presupus).

*Estimarea IV pe anul parțial* (−93 lei/zi, P2,5–P97,5 −220…+32) este doar o **limită superioară**:
- implică pierderea a mai mult de o zi matură de cifră de afaceri per zi de așteptare (1.434 față de 553 lei);
- este dominată de componenta TVA presupusă (−83 TVA, −43 impozit direct, +33 salarial, acesta din urmă zgomot).

Canalul 1 este raportat în patru măsuri:
- suma brută deplasată (1a);
- partea recuperată în aceeași perioadă (1b);
- efectul net de numerar (1c);
- **costul valorii în timp** (1d), la randamentul titlurilor de stat. Acesta este costul economic al venitului „doar amânat”.

Mențiunile intră doar aici, cu parametrii din `audit_costs.py`, care nu sunt estimați.

**Canalul 2 — pierdut persistent.** Efectul pe anul complet următor din PARTEA A × zilele în exces, aplicat ca flux anual de la data deciziei. Coeficientul IV comun este −6 lei pe firmă pe an per zi de așteptare (P2,5–P97,5 −252…+223), adică statistic zero. Se compune din:
- impozit direct −16;
- salarial +59;
- TVA −57.

### Rezultate 2027, continuitate (milioane lei)

| Componentă | Medie | P10 | P50 | P90 | P95 |
|---|---|---|---|---|---|
| **1d. Valoarea în timp a venitului amânat** | 13 | 8 | **13** | **20** | **22** |
| **2. Pierdut persistent (PARTEA A)** | 31 | −318 | **26** | **389** | **498** |
| Cost economic = 1d + 2 | 45 | −304 | 38 | 404 | 512 |
| 1a. Amânat brut (sincronizare de numerar) | 719 | 563 | 717 | 880 | 923 |
| 1c. Efect net de numerar al amânării în 2027 | 283 | 125 | 271 | 460 | 512 |
| Lectura A: impact de numerar 2027 (1c + 2) | 314 | −79 | 308 | 724 | 822 |
| Lectura B: limită superioară, venitul amânat nerecuperat (1a + 2) | 750 | 358 | 741 | 1.147 | 1.271 |

Pe trimestre (P50; valorile P10–P90 sunt în `tables/revenue_at_risk_2027.csv` și în figura 2):

| | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| Valoare în timp | 1,2 | 2,8 | 4,4 | 4,5 |
| Pierdut persistent | 0,7 (P90 10) | 3,6 (P90 54) | 7,3 (P90 111) | 14 (P90 215) |
| Lectura A | 74 | 61 | 130 | 45 |
| Lectura B | 108 | 156 | 230 | 249 |

Ca ordin de mărime, chiar lectura B (P50 741 mil. lei) reprezintă circa 0,09% din veniturile publice estimate pentru 2027 (35,6% × PIB CNSP de 2.227 mld. lei).

Pierderea persistentă deja „blocată” de cohorta 2026 deja decisă: P50 6 mil. lei (P95 116). Este raportată separat (memo).

Lectura A supraestimează golul de numerar din 2027, pentru că nu include recuperările din 2027 ale dosarelor depuse înainte de 1.12.2026 (stocul aflat deja în coadă).

### Scenarii evitate (an 2027)

**„Combinat”.** Pachetul motorului (+12% sprijin temporar, +4% câștig durabil, 60% automatizare CAEN, eșalonare). Evită P50 305 mil. lei în lectura B (P90 403) și 241 mil. lei în lectura A.

**„Coadă eliminată până la 30.06.2027”.** Necesită un spor de capacitate de +77% din 4.01.2027, valoare găsită prin bisecție pe motor. Evită P50 640 mil. lei în lectura B (P90 876) și 316 mil. lei în lectura A.

Valoarea în timp scade aproape la zero în ambele scenarii. Partea persistentă evitată rămâne centrată pe zero.

### Sensibilitate (an 2027, mil. lei)

| Variantă | Lectura B P50 / P95 | Lectura A P50 / P95 | Valoare în timp P50 | Pierdut P50 / P95 |
|---|---|---|---|---|
| Central (rată mecanică) | 741 / 1.271 | 308 / 822 | 12,9 | 26 / 498 |
| Randament 6,02% (12 luni) | = | = | 11,5 | = |
| κ = 1 | 874 / 1.407 | 455 / 1.013 | 18,5 | 27 / 515 |
| κ = 0,65 | 649 / 1.151 | 228 / 721 | 9,8 | 25 / 461 |
| Rată IV pe anul parțial (limită superioară) | 854 / 1.852 | 330 / 1.018 | 14,2 | 26 / 498 |
| Efect persistent plafonat la 35 zile (suport) | 740 / 1.013 | 301 / 592 | 12,9 | 12 / 231 |
| Efect persistent = OLS (endogen, limită de daună) | 1.076 / 1.360 | 634 / 939 | 12,9 | 355 / 530 |
| Fără TVA | 427 / 782 | 104 / 470 | 9,7 | −105 / 218 |
| Substituție 50% de către firmele existente | 370 / 635 | 154 / 411 | 6,4 | 13 / 249 |
| Fără mențiuni | 618 / 1.141 | 249 / 757 | 10,2 | 26 / 498 |

### Cum se citește (stil declarație de risc fiscal)

**Factorul de risc.** Coada ONRC fără măsuri noi duce la durate de înmatriculare de 70–110 zile (P50) în 2027.

**Ce este dovedit.** Așteptarea mută începutul activității firmelor noi. Costul economic al acestei amânări pentru buget, adică valoarea în timp, este mic: 13 mil. lei P50, 22 mil. lei P95.

**Ce nu este dovedit.** Nu există dovezi că întârzierea reduce activitatea sau impozitele în anul următor. Componenta „pierdut persistent” este centrată pe zero (P50 26 mil. lei). Coada ei (P90 389, P95 498 mil. lei) reflectă incertitudinea statistică extrapolată la durate de 2–4 ori mai mari decât cele observate, nu o pierdere demonstrată.

**Sincronizarea numerarului.** Dacă venitul din zilele de așteptare este doar amânat, golul de numerar în execuția 2027 este de circa 0,3 mld. lei P50 (P95 0,8). O parte din el trece în 2028.

**Limita superioară.** Dacă venitul din zilele de așteptare nu este recuperat niciodată, adică firma doar pornește mai târziu, impactul ajunge la 0,74 mld. lei P50 (P95 1,27). Această lectură nu are suport empiric direct.

**Orizontul.** Riscul crește în T3–T4 2027.

**Ce îl reduce.** Eliminarea cozii până la jumătatea anului reduce impactul cu circa 0,3–0,6 mld. lei P50, în funcție de lectură.

## Amenințări la validitate și cum le tratează fiecare design

**Selecția în depunere în timpul șocului.** Volumul depunerilor nu a scăzut, iar compoziția (SA, capital, CAEN) nu răspunde la instrument, cu excepția secțiunii H. La 100+ zile, renunțarea sau descurajarea pot deveni importante, iar acest lucru nu este măsurat: eșantionul conține doar dosarele admise.

**Sezonalitatea.** Este absorbită de FE pe săptămâna depunerii (IV, OLS) și de FE pe săptămâna din an cu an de control (DiD, IV național).

**Supraviețuirea.** Lipsa bilanțului este tratată ca rezultat (activitate sau supraviețuire), nu ca valoare lipsă. Rezultatele monetare sunt necondiționate.

**Anul parțial.** Este separat explicit de anul complet. Efectul pe anul parțial este mecanic în parte, și tocmai acesta este canalul de amânare.

**Extrapolarea.** Duratele prognozate pentru 2027 (55–150 zile) depășesc suportul estimării (p99 35, max 93). Canalul persistent este extrapolat liniar, iar sensibilitatea „plafonat la 35 zile” îl reduce la jumătate.

**Proxy fiscal.** Bilanțurile sunt pe regulile 2025. Regimul micro din 2026 (1%, 100.000 EUR, minimum 1 salariat) mută firme la impozitul pe profit. Dividendele (16%) nu sunt incluse. TVA folosește o pondere a valorii adăugate presupusă, iar contribuțiile sunt calculate la salariul minim (estimare prudentă).

**Puterea statistică.** Un singur episod mare de congestie: IC two-way și pe săptămână sunt raportate alături de cele pe oficiu.

## Fișiere

- `tables/coefficients.csv` — toate estimările OLS, IV, IV-variante, IV național, an parțial și condiționat-CAEN.
- `tables/did.csv` — DiD (forma redusă și Wald, SE pe oficiu și two-way), cu mediile celulelor.
- `tables/event_bins.csv` și `tables/event_month_2024_vs_2023.csv` — treptele de durată și studiul pe luna depunerii.
- `tables/placebo.csv`, `tables/instrument_diagnostics.csv`, `tables/partial_year_catchup.csv`.
- `tables/revenue_at_risk_2027.csv` — scenariu × componentă × trimestru, cu medie, P2,5, P5, P10, P50, P90, P95 și P97,5.
- `tables/revenue_at_risk_sensitivity.csv`, `tables/volumes_2027.csv`.
- `figures/fig1_trepte_durata`, `figures/fig2_evantai_venituri_la_risc_2027`, `figures/fig3_studiu_luna_depunerii` (PNG și SVG).
- `statutory_parameters.json` — parametrii fiscali, cu URL-uri și statutul de verificare.
- `partA_results.json`, `partB_results.json` — agregatele intermediare: coeficienți și vcov, medii pe firmă, diagnostice motor.
