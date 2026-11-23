# Pachet reel — Coada de la Registrul Comerțului (22.11.2026)

Generat din `claims_registry.csv`. Formularea pentru voce și ecran = `public_ro` din registru. Afirmațiile WARN se spun DOAR împreună cu rezerva. Afirmațiile FAIL sunt refuzate de generator.

Credit în reel: „analiză big data pe datele din BERC”. Declarație de interes: „activitate de înființare de societăți, închisă”.

## Reperul legal

### C23 · PASS · nivel C/S
- **Voce:** Legea cere ca registratorul să soluționeze cererea într-o zi lucrătoare de la înregistrare.
- **Ecran:** 1 zi lucrătoare
- **Grafic:** —  (text pe ecran)
- **Cum am calculat:** Am citit art. 105 alin. (1) și art. 109 din Legea 265/2022 în forma consolidată de pe legislatie.just.ro (22.11.2026).
- **Sursă / script:** Legea 265/2022 art. 105 alin. (1) și art. 109 — forma consolidată, legislatie.just.ro (citită la 22.11.2026) · `verificare manuală pe text`
- **Rezervă:** Textul a fost verificat pe legislatie.just.ro la 22.11.2026 (forma consolidată); o versiune anterioară a raportului folosise extrasul publicat de ONRC.

## Cum era înainte

### C17 · PASS · nivel A/E
- **Voce:** Pe vechea platformă, un dosar aștepta în mod obișnuit 1,6 zile.
- **Ecran:** 1,6 zile calendaristice
- **Grafic:** Fig. 3.1 istoric
- **Cum am calculat:** Mediana zilelor dintre depunere și decizie, pe toate deciziile finale din apr. 2023–iul. 2024.
- **Sursă / script:** BERC · `reconcile_sources.py:main`
- **Rezervă:** —

### C31 · PASS · nivel A/E
- **Voce:** Pe platforma veche, 74,9% din dosare erau soluționate într-o zi lucrătoare. În criză, sub 1%.
- **Ecran:** 74,9% → 0,66% % din decizii
- **Grafic:** —
- **Cum am calculat:** Ponderea deciziilor date în cel mult o zi lucrătoare, cu calendarul legal românesc.
- **Sursă / script:** BERC, calendar legal RO · `recompute_from_raw.py:windows`
- **Rezervă:** Platforma veche = apr. 2023–iul. 2024; criza = 1 aug.–20 nov. 2026.

## Cât se așteaptă acum

### C14 · PASS · nivel A/E
- **Voce:** Modificările soluționate în săptămâna 16–20 noiembrie au așteptat, în mod obișnuit, 57,1 zile.
- **Ecran:** 57,1 zile calendaristice
- **Grafic:** Fig. 2.1 săptămânal
- **Cum am calculat:** Mediana zilelor de așteptare a modificărilor soluționate în săptămâna 16–20 noiembrie.
- **Sursă / script:** BERC (CERERE265 finale, după data deciziei) · `reconcile_sources.py:main`
- **Rezervă:** —

### C16 · PASS · nivel A/E
- **Voce:** Așteptarea dosarelor soluționate a crescut în fiecare săptămână din octombrie și noiembrie.
- **Ecran:** 27,9 → 57,1 zile calendaristice
- **Grafic:** Fig. 2.1 săptămânal
- **Cum am calculat:** Aceeași mediană, calculată săptămână de săptămână din 28 septembrie.
- **Sursă / script:** BERC · `reconcile_sources.py:main`
- **Rezervă:** —

### C15 · PASS · nivel A/E
- **Voce:** Firmele noi aprobate în aceeași săptămână au așteptat 41,1 zile.
- **Ecran:** 41,1 zile calendaristice
- **Grafic:** Fig. 2.1 săptămânal
- **Cum am calculat:** Mediana pentru înmatriculările soluționate în aceeași săptămână.
- **Sursă / script:** BERC (INMATRIC265 finale) · `reconcile_sources.py:main`
- **Rezervă:** —

### C04 · WARN · nivel A/E
- **Voce:** Pentru dosarele depuse în septembrie, așteptarea a fost de cel puțin 39 de zile, față de 5 zile în mai. Septembrie e cenzurat: multe dosare din septembrie nu erau încă soluționate, deci valoarea reală e mai mare. Se spune «cel puțin».
- **Ecran:** 5 / 5 / 7 / 19 / ≥39 zile calendaristice
- **Grafic:** Fig. 2.2 pe luna depunerii
- **Cum am calculat:** Mediana pe luna depunerii, doar pentru dosarele deja soluționate; septembrie e o limită de jos.
- **Sursă / script:** BERC și portal, pe luna depunerii · `reconcile_sources.py:main`
- **Rezervă:** Septembrie e cenzurat: multe dosare din septembrie nu erau încă soluționate, deci valoarea reală e mai mare. Se spune «cel puțin».

### C11 · WARN · nivel A/E
- **Voce:** Pentru dosarele depuse în octombrie și noiembrie, timpul final nu se poate încă măsura. Se folosește în schimb așteptarea dosarelor decise pe săptămână (C14–C16).
- **Ecran:** cenzurat —
- **Grafic:** Fig. 2.3 cenzurare
- **Cum am calculat:** Am numărat câte dosare din fiecare lună au deja o decizie finală.
- **Sursă / script:** BERC (puține dosare decise) · `analyze_6month_trend.py`
- **Rezervă:** Se folosește în schimb așteptarea dosarelor decise pe săptămână (C14–C16).

## Producția față de intrări

### C30 · PASS · nivel A/E
- **Voce:** Pe aceeași perioadă a anului, Registrul dă mai multe decizii ca în anii trecuți. Producția nu s-a prăbușit; cererile au crescut mai repede.
- **Ecran:** 2.956 / 3.490 / 3.810 / 4.267 decizii finale / zi lucrătoare legală
- **Grafic:** Fig. 3.2 aceeași perioadă
- **Cum am calculat:** Decizii finale pe zi lucrătoare în fereastra 1 oct.–20 nov., an de an.
- **Sursă / script:** BERC, ferestre comparabile ale anului (20.11.2026, zi parțială, exclusă) · `stat_pack_ext.py (efort_aceeasi_perioada)`
- **Rezervă:** Se compară doar aceeași perioadă a anului; nu se compară cu alte luni.

### C01 · PASS · nivel A/E
- **Voce:** Registrul finalizează circa 4.300 de dosare pe zi lucrătoare în octombrie–noiembrie 2026.
- **Ecran:** ≈4.300 decizii finale / zi lucrătoare
- **Grafic:** Fig. 3.2
- **Cum am calculat:** Decizii finale pe zi lucrătoare, 1 oct.–20 nov. 2026, din BERC.
- **Sursă / script:** BERC (finale: admis, respins, renunțat, certificări) · `stat_pack_ext.py (efort_aceeasi_perioada)`
- **Rezervă:** Nu e un record absolut: vârful a fost în feb.–mar. 2025 (≈5.006/zi). E un număr de decizii, nu un volum de muncă.

### C47 · PASS · nivel C/S
- **Voce:** Ministerul raportează că cererile zilnice au crescut cu circa jumătate, de la 4.533 la 6.931 pe zi.
- **Ecran:** 4.533 → 6.931 (+53%) cereri / zi
- **Grafic:** —
- **Cum am calculat:** Cifra oficială de intrări din Nota MJ din 6 noiembrie, citată cu sursa.
- **Sursă / script:** Nota MJ, 6.11.2026 (citată în FAPTE_VERIFICATE §3) · `FAPTE_VERIFICATE_PENTRU_VIDEO_SI_RAPORT.md §3`
- **Rezervă:** Cifră oficială preluată; definiția «intrări» aparține MJ.

### C07 · PASS · nivel A/E
- **Voce:** În august s-au dat cu circa 10% mai puține decizii pe zi lucrătoare decât în iunie–iulie.
- **Ecran:** ≈90% % din nivelul iunie–iulie (finale stricte / zi lucrătoare legală)
- **Grafic:** —
- **Cum am calculat:** Decizii finale pe zi lucrătoare în august, raportate la iunie–iulie.
- **Sursă / script:** BERC; finale = admis, respins, renunțat; zile lucrătoare cu calendarul legal 2026 · `reconcile_sources.py:main (august_ratio_strict_finals_per_legal_wd)`
- **Rezervă:** Definiție corectată la poarta v2 (înainte: împărțire la zile cu decizii, 0,918). O explicație posibilă sunt concediile; datele nu o măsoară direct.

## Sincronizarea din 27 aprilie

### C32 · PASS · nivel A/E
- **Voce:** Din 27 aprilie 2026, aproape niciun dosar nu mai e rezolvat în două zile, în aproape toate județele, cu luni înainte de valul de cereri.
- **Ecran:** 20,8% → 1,2% % din decizii finale cu așteptare ≤2 zile calendaristice (după data deciziei)
- **Grafic:** —
- **Cum am calculat:** Ponderea deciziilor în cel mult două zile, pe județe, înainte și după 27 aprilie 2026.
- **Sursă / script:** BERC; ferestre 1.03–26.04 vs 27.04–31.07.2026 · `reconcile_sources.py:main (le2d_share_27apr_by_decision_date)`
- **Rezervă:** Definiție corectată la poarta v2 (înainte: mediana pe județe, 13,4% → 0,96%). Scăderea apare în aproape toate județele. Cauza nu e documentată în date.

## Cele două cozi

### C28 · PASS · nivel C/S
- **Voce:** La 6 noiembrie, Ministerul Justiției raporta 204.414 de cereri nesoluționate.
- **Ecran:** 204.414 cereri
- **Grafic:** Fig. 4.1 drumul dosarului
- **Cum am calculat:** Stocul oficial din Nota MJ din 6 noiembrie.
- **Sursă / script:** Nota Ministerului Justiției, 6.11.2026 · `tandem_bottleneck_analysis.py:mj_tandem_conservation`
- **Rezervă:** Cifră oficială preluată, nu recalculată.

### C29 · PASS · nivel C/S
- **Voce:** Dintre cele 204.414 de cereri nesoluționate, 106.060 (circa jumătate) erau încă în etapa de operare.
- **Ecran:** 106.060 (51,9%) cereri
- **Grafic:** Fig. 4.1
- **Cum am calculat:** Partea neprelucrată a stocului oficial, din aceeași notă.
- **Sursă / script:** Nota MJ, 6.11.2026 · `tandem_bottleneck_analysis.py:mj_tandem_conservation`
- **Rezervă:** Cifră oficială preluată.

## Cele două cozi (bilanț 30.10→6.11)

### C33 · PASS · nivel C/S
- **Voce:** În săptămâna 30 octombrie–6 noiembrie, coada de operare a scăzut cu 8.300, iar coada de la registrator a crescut cu 4.396.
- **Ecran:** -8.300 / +4.396 cereri în 5 zile lucrătoare
- **Grafic:** Fig. 4.2 bilanț
- **Cum am calculat:** Diferența dintre cele două fotografii oficiale ale MJ, pe fiecare etapă.
- **Sursă / script:** Nota MJ (30.10 și 6.11) + identitatea de conservare · `tandem_bottleneck_analysis.py:mj_tandem_conservation`
- **Rezervă:** Bilanț pe două fotografii oficiale; nu arată ce s-a întâmplat între ele.

## Cele două cozi

### C34 · PASS · nivel B/P
- **Voce:** În săptămâna 30 octombrie–6 noiembrie, operarea a lucrat cu circa 16–20% mai repede decât soluționarea, iar stocul de la registrator a crescut. E o singură săptămână; stocul acelei etape poate cuprinde și dosare care așteaptă completarea de către solicitant.
- **Ecran:** ≈20% % (16–20% după convenție)
- **Grafic:** Fig. 4.2
- **Cum am calculat:** Raportul dintre debitul operării și al soluționării în 2–6 noiembrie, pe trei convenții de numărare.
- **Sursă / script:** Nota MJ + BERC 2–6 nov. · `tandem_bottleneck_analysis.py:conventions`
- **Rezervă:** Diferența variază între 16% și 20% după cum se numără deciziile. O singură săptămână, între două fotografii oficiale; stocul «prelucrate, nesoluționate» poate cuprinde și dosare aflate în termenul de completare după o amânare (timpul solicitantului), iar datele publice nu arată câte.

## Online nu ocolește operarea

### C36 · WARN · nivel A/E
- **Voce:** Cererile depuse online în afara programului nu trec mai repede: așteaptă chiar puțin mai mult. Online-ul nu ocolește operarea. Sensibil la definiție: +1,1 … +1,9 în analiza noastră, +0,8 … +1,8 în recalculul independent. Semnul e același (online-ul nu e mai rapid); mărimea depinde de definiție.
- **Ecran:** +0,8 … +1,9 zile (după definiția «în afara programului»)
- **Grafic:** —
- **Cum am calculat:** Depuneri în afara programului (doar online) vs. în program, în aceeași zi și același județ.
- **Sursă / script:** BERC, depuneri în afara programului vs în program · `tandem_bottleneck_analysis.py:online_vs_office_hours`
- **Rezervă:** Sensibil la definiție: +1,1 … +1,9 în analiza noastră, +0,8 … +1,8 în recalculul independent. Semnul e același (online-ul nu e mai rapid); mărimea depinde de definiție.

## Coada e națională

### C49 · PASS · nivel A/E
- **Voce:** Așteptarea e aproape aceeași în toată țara: coada e practic națională, nu o problemă a unui județ anume.
- **Ecran:** 47,9–55,8 zile calendaristice (interval între cele 42 de județe)
- **Grafic:** Fig. 4.3 județe
- **Cum am calculat:** Mediana deciziilor din 1–18 noiembrie, pe oficiul de depunere.
- **Sursă / script:** BERC pe oficiul de depunere · `audit_atlas.py → county_indicators.csv`
- **Rezervă:** Județul = oficiul de depunere; cel mai mic are ~410 decizii în fereastră. Clasamentul pe oficii arată unde apar diferențele, nu performanța personalului.

## Dosare care trec mai repede

### C38 · PASS · nivel A/E
- **Voce:** Unele dosare trec mult mai repede: 8,7% din modificări au fost rezolvate în cel mult 14 zile, deși de obicei se așteaptă 53 de zile.
- **Ecran:** 8,7% modificări · 15,7% înmatriculări % din decizii finale
- **Grafic:** —
- **Cum am calculat:** Ponderea deciziilor finale date în cel mult 14 zile, 2–19 noiembrie.
- **Sursă / script:** BERC · `reconcile_sources.py:main (two_speed_2_19_nov)`
- **Rezervă:** Cauza nu se vede în BERC (cereri mai simple sau priorități legale sunt plauzibile). NU se spune «favoritism» sau «sărit coada».

## Amânările

### C03 · PASS · nivel A/E
- **Voce:** Pe lângă deciziile finale, se dau circa 1.000 de amânări pe zi: solicitantul primește un termen de cel mult 15 zile să completeze dosarul.
- **Ecran:** ≈1.000 amânări / zi lucrătoare
- **Grafic:** Fig. 4.1 / Fig. 6.1
- **Cum am calculat:** Număr de amânări pe zi lucrătoare în BERC; definiția din art. 106.
- **Sursă / script:** BERC (sol = Amânat) + art. 106 Legea 265/2022 · `reconcile_sources.py:main`
- **Rezervă:** Amânarea = termen de completare de cel mult 15 zile (art. 106); nu închide dosarul.

### C21 · PASS · nivel A/E
- **Voce:** Aproximativ una din cinci decizii e o amânare, la fel ca înainte de criză.
- **Ecran:** 20,3% → 19,4% % din toate actele
- **Grafic:** Fig. 6.1 structura deciziilor
- **Cum am calculat:** Ponderea amânărilor în toate actele, pe perioade.
- **Sursă / script:** BERC · `recompute_from_raw.py:windows`
- **Rezervă:** Ușor subestimat (~0,15 pp) din cauza unor pagini de amânări lipsă.

### C37 · PASS · nivel A/E
- **Voce:** Un dosar amânat așteaptă circa 42 de zile până la prima amânare. După completare, decizia vine în circa 14 zile: nu se reia coada de la capăt.
- **Ecran:** 41,9 / 14,0 zile (mediană)
- **Grafic:** —
- **Cum am calculat:** Mediana zilelor până la prima amânare și de la ultima amânare la decizie, noiembrie 2026.
- **Sursă / script:** BERC (AUTO_AMANARI) · `tandem_bottleneck_analysis.py:auto_amanari_timing`
- **Rezervă:** —

## Bucla respingere → redepunere

### C40 · WARN · nivel A/E
- **Voce:** Circa 8 din 10 firme respinse depun din nou în același an: o respingere înseamnă de obicei încă un dosar în coadă. WARN în ledger-ul verificat (RHO-78): «redepune» = orice cerere ulterioară de același tip a aceleiași firme; arhiva tabelară nu are ID-ul firmei, calculul cere JSON-ul brut.
- **Ecran:** 77,6–80,4% % din respingeri
- **Grafic:** —
- **Cum am calculat:** Firme respinse care depun din nou o cerere de același tip în cel mult un an.
- **Sursă / script:** BERC JSON brut (cu ID-ul firmei) · `check_refiling_rate.py · ledger RHO-78 (WARN)`
- **Rezervă:** WARN în ledger-ul verificat (RHO-78): «redepune» = orice cerere ulterioară de același tip a aceleiași firme; arhiva tabelară nu are ID-ul firmei, calculul cere JSON-ul brut.

## Directiva 13g

### C41 · PASS · nivel A/E
- **Voce:** 81,3% dintre firmele noi admise fără amânare în noiembrie au așteptat peste 10 zile lucrătoare de la înregistrare; pragul european de 5/10 zile se aplică doar constituirilor online.
- **Ecran:** 81,3% peste 10 zile lucrătoare % din înmatriculările J admise din prima, decise 1–20.11.2026 (n ≈ 3.500)
- **Grafic:** —
- **Cum am calculat:** Firme noi aprobate din prima în 1–20 noiembrie, peste 10 zile lucrătoare.
- **Sursă / script:** BERC + Directiva (UE) 2017/1132 art. 13g alin. (7) · `recompute_from_raw.py:eu_directive`
- **Rezervă:** Datele nu disting constituirile online cu model standard; NU se dă un «număr de încălcări».

## OUG-ul, pe articole

### C43 · PASS · nivel B/P
- **Voce:** Cu proiectul OUG, modelul arată o îmbunătățire, dar așteptarea rămâne de ordinul a trei luni: proiectul singur nu readuce termenul la câteva zile.
- **Ecran:** ≈102 (41–172) zile
- **Grafic:** Fig. 7.1 model auditat
- **Cum am calculat:** Modelul de coadă auditat, rulat pe datele curente; mediană și interval p10–p90.
- **Sursă / script:** model de coadă verificat · `rerun_oug_current.py / audit_forecast.py`
- **Rezervă:** Scenariu, interval larg. Câștig median pe aceleași simulări: ≈34 zile. NU se dă procentul de «șanse».

### C42 · PASS · nivel B/P
- **Voce:** Fără măsuri, modelul arată o așteptare de ordinul a patru luni în iunie 2028 (interval larg).
- **Ecran:** ≈136 (74–214) zile (mediană, interval p10–p90)
- **Grafic:** Fig. 7.1
- **Cum am calculat:** Același model, fără măsuri.
- **Sursă / script:** model de coadă verificat · `rerun_oug_current.py / audit_forecast.py`
- **Rezervă:** Scenariu: ±5% în capacitate mută rezultatul între ~102 și ~174 de zile. Se spune ca ordin de mărime.

### C44 · PASS · nivel B/P
- **Voce:** Doar transferul unor acte administrative (Art. III) schimbă foarte puțin. Efectul vine mai ales din capacitatea suplimentară de soluționare.
- **Ecran:** câștig ≈2 zile zile câștigate (mediana diferențelor pe aceleași simulări)
- **Grafic:** Fig. 7.1
- **Cum am calculat:** Același model, doar cu Art. III.
- **Sursă / script:** model de coadă verificat · `audit_data/oug_2026/scenarios.csv (median_saved)`
- **Rezervă:** Scenariu. NU se pun alăturat medianele 136 și 132 (s-ar citi «4 zile»); câștigul corect e pe aceleași simulări. Art. III se aplică după optimizarea IT (Art. IV).

## OUG-ul: limita mutării din operare

### C35 · PASS · nivel B/P
- **Voce:** Dacă juriștii delegați sunt luați din operare, câștigul are o limită. Peste un anumit prag, mutarea scade producția totală.
- **Ecran:** optim ≈440/zi; câștig zero la ≈879/zi dosare / zi lucrătoare mutate
- **Grafic:** Fig. 7.2 tandem
- **Cum am calculat:** Capacitatea sistemului când capacitate de operare e mutată 1:1 la soluționare.
- **Sursă / script:** model în tandem verificat (Lean T13c) · `tandem_bottleneck_analysis.py:conventions`
- **Rezervă:** Condiționat de ipoteza 1:1 și de ancora 2–6 nov.; nu e textul OUG, ci un mecanism.

## NU afirma (actualizat 22.11.2026)

- „Dosarele se rezolvă strict în ordinea depunerii” — nu e strict (C38).
- „Favoritism” / „sărit coada” — cauza dosarelor rapide e necunoscută.
- Productivitate sau plafon „per registrator”, comparații cu o „normă” — retras (C02).
- Clasamente de performanță ale județelor sau ale oamenilor.
- „Producție record” fără precizare — vârful absolut a fost în feb.–mar. 2025.
- Comparații între perioade diferite ale anului (ex. noiembrie 2026 vs media 2025) — retras (C20).
- „X firme așteaptă acum” — BERC nu arată cererile nerezolvate.
- Probabilități pentru scenarii („0,75% șanse”), „137 → 104 zile”, „P6 atinge 3 zile”, „P5 ≥100 zile”, „P1 0 zile”.
- Scenariile neauditate 710k–1,1 mil. și „50 de registratori luați din operare” — retrase (C24–C27).
- „Septembrie: 39 de zile” fără „cel puțin” — e cenzurat (C04, C05).
- Sfaturi despre ziua sau luna depunerii; cifre despre munca după program.
- „Tranziție supercritică”, „legea Kleinrock”, „DEFF 1,26”, „prognoza de 265 de zile”, „prognoza înghețată a nimerit”.
- „Stocul e 210.000” ca cifră oficială — cifra oficială este 204.414 (C28); 210k e sindicală (C08).
