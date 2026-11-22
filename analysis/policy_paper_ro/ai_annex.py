"""Anexa comună tuturor documentelor: utilizarea AI, cerințele raportului, surse de date, limite și incertitudini.
Un singur text, inclus o singură dată la finalul fiecărui document și listat în cuprins."""

TITLE = "Utilizarea AI, cerințe, surse și limite"

DISCLAIMER = ("Raport realizat cu ajutorul inteligenței artificiale (Claude Opus 5.5 și Gemini 4 Neon), sub îndrumarea și verificarea autorului. "
              "Detalii despre cum a fost folosit AI-ul, despre surse și despre limite: anexa „" + TITLE + "”, la finalul documentului.")


def body(hl=lambda t: f"<mark class='hl'>{t}</mark>"):
    li = lambda xs: '<ul class="find body-list">' + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
    h = lambda t: f'<h3 class="sub3" style="margin-top:4mm">{t}</h3>'
    p = lambda t: f"<p>{t}</p>"
    b = p(hl("Acest raport a fost realizat cu ajutorul inteligenței artificiale. Analiza, textul, graficele și verificările automate au fost produse cu modele AI, sub îndrumarea, verificarea și răspunderea autorului.") +
          " Spunem aici, cât se poate de concret, ce a făcut AI-ul, ce a făcut omul, pe ce date ne-am bazat și ce nu se poate afla din ele.")
    b += h("1. Ce modele AI au fost folosite")
    b += li(["<b>Claude Opus 5.5</b> (Anthropic): colectarea datelor din portal cu scripturi, analiza statistică, rularea și verificarea modelului de prognoză, "
             "registrul afirmațiilor și verificatorul automat de cifre, demonstrațiile formale în Lean, redactarea textelor, graficele și construcția documentelor. "
             "Instanțe separate ale aceluiași model au făcut reimplementarea separată a cifrelor-cheie și revizuirea critică pe profiluri de cititori.",
             "<b>Gemini 4 Neon</b> (Google): folosit de autor, alături de Claude, la generarea raportului, la analiza datelor și la producerea rezultatelor. "
             "Contribuțiile celor două modele nu sunt separate componentă cu componentă în acest document."])
    b += h("2. Ce a făcut AI-ul, pas cu pas")
    b += li(["<b>Date.</b> Scripturi pentru descărcarea buletinului BERC și a unui eșantion din portalul myportal, cu acces autorizat de autor, cu ritm limitat și fără date personale în rezultate.",
             "<b>Analiză.</b> Calculul așteptărilor, al ritmurilor de lucru, al amânărilor și respingerilor; corectarea cenzurării (Kaplan–Meier); comparații între surse.",
             "<b>Motivele amânărilor și ale respingerilor.</b> Extragerea textului din buletinele PDF, anonimizarea, gruparea (embeddings rulate local) și clasificarea motivelor; " +
             hl("eșantioanele „manuale” (100 de amânări, 150 de respingeri) au fost etichetate de un model AI, nu de o persoană, iar judecata „evitabil la depunere” este tot a AI-ului, neconfirmată de ONRC.") +
             " Recomandăm o a doua etichetare, umană.",
             "<b>Model.</b> Rularea motorului de prognoză (2.000 de variante), a scenariilor OUG și a grilei de risc; testul pe date nevăzute.",
             "<b>Verificare.</b> O sursă unică de cifre blocată; un registru în care fiecare cifră are cod, sursă, script și amprenta datelor; un verificator care respinge orice cifră fără cod; o a doua implementare, separată, a cifrelor-cheie; demonstrații Lean pentru aritmetică și monotonie.",
             "<b>Revizuire pe profiluri.</b> Cititori simulați de AI (ministru, director, IT, statistician, sindicat, avocat) au criticat raportul; criticile și corecturile sunt în Volumul 6. " + hl("Acești cititori au fost simulați: nu sunt persoane reale și nu reprezintă instituțiile."),
             "<b>Redactare.</b> Textul, graficele, tabelele și cele opt documente au fost generate automat din aceleași fișiere de date."])
    b += h("3. Ce a făcut autorul")
    b += p(hl("Autorul, Ștefan-Lucian Deleanu, a stabilit cerințele, a ghidat analiza, a verificat rezultatele și a decis ce se publică; răspunderea pentru conținut îi aparține.") +
           " Autorul a cerut corecturi atunci când cifrele nu erau stabile sau nu se potriveau între surse, a ales publicul și formatul, a cerut verificări suplimentare (demonstrații Lean, revizuire pe profiluri) și a decis publicarea clasamentelor pe oficii.")
    b += h("4. Cerințele raportului")
    b += li(["Date corecte, verificate pe două surse independente, cu cifre stabile de la o versiune la alta.",
             "Un raport pentru instituții, ușor de citit și pentru nespecialiști: explicații pas cu pas, exemple, concluzii simple, propozițiile-cheie evidențiate cu galben ca note executive.",
             "Mai multe volume, pentru cititori diferiți: fișe pe profil, raport principal, ediție executivă, anexe statistice, raport statistic avansat, munca personalului, fișe pe județe, verificare și fișier de date.",
             "Analiza proiectului de OUG în modelul statistic, prognoză, grile de risc pe vitezele de intrare și ieșire, soluții.",
             "Onestitate: cifrele care nu avantajează pe nimeni se publică la fel ca celelalte; afirmațiile care nu rezistă la verificare se retrag public.",
             "Fără date personale; fără cifre despre registratori individuali; clasamente pe oficii acolo unde ajută la localizarea problemelor.",
             "Transparență privind utilizarea AI, sursele, limitele și incertitudinile."])
    b += h("5. Surse de date folosite și ierarhia lor")
    b += p(hl("Sursa de referință este buletinul BERC, folosit integral; cifrele publice care îl contrazic sunt menționate și explicate, dar nu îl înlocuiesc."))
    b += li(["<b>BERC</b>, Buletinul Electronic al Registrului Comerțului: 4.077.510 decizii, aprilie 2023 – noiembrie 2026.",
             "<b>Portalul myportal.onrc.ro</b>: 7.469 de numere de cerere sondate, recoltate pe 21–22 noiembrie 2026, fără nume, CNP sau date de contact.",
             "<b>Ministerul Justiției</b>: notele din 30 octombrie și 6 noiembrie 2026 (stocuri pe etape, intrări zilnice, buget).",
             "<b>Legea nr. 265/2022</b> (art. 105, art. 106 și art. 109), verificată în forma consolidată pe legislatie.just.ro la 22.11.2026 (o versiune anterioară a raportului folosise extrasul publicat de ONRC); <b>Directiva (UE) 2017/1132</b>, art. 13g alin. (7).",
             "<b>Proiectul de OUG din 18 noiembrie 2026</b>, după rezumatul pus în consultare.",
             "<b>Compilație de presă</b> din 21 noiembrie 2026 (surse secundare), folosită doar pentru comparație, în capitolul „Sursele noastre și sursele publice”."])
    b += h("6. Surse recomandate și date care ar trebui publicate")
    b += li(["Textul final al OUG și forma consolidată în vigoare a Legii 265/2022 (legislatie.just.ro).",
             "Statisticile lunare ONRC: înmatriculări, mențiuni, radieri, pe județe.",
             "De la ONRC, ca date deschise: stocul zilnic pe etape și tipuri de cereri; data și ora trecerii fiecărui dosar la registrator; cererile înregistrate zilnic, pe tipuri și oficii; codul tipului de cerere; un identificator pseudonimizat al firmei; personalul activ pe fiecare etapă; motivele amânărilor și ale respingerilor, codificate (azi sunt doar text liber în buletin); un jurnal al schimbărilor de procedură și al opririlor tehnice.",
             "Pentru comparații europene: rapoartele Comisiei Europene privind digitalizarea dreptului societăților și registrele altor state membre."])
    b += h("7. Limitele datelor")
    b += li(["BERC conține doar deciziile; stocul și intrările zilnice le-am estimat din numerele de înregistrare ale cererilor, combinate cu eșantionul din portal. Estimările sunt compatibile cu cifrele Ministerului, dar au o marjă de circa ±10%.",
             "Nu se cunoaște momentul trecerii dintre operare și soluționare: timpul pe fiecare etapă nu se poate măsura.",
             "Identificatorul firmei există doar în datele brute ale buletinului (îl folosim pentru redepuneri, fără să-l publicăm); tipul exact al cererii apare doar în textul buletinelor PDF, citit pe un eșantion.",
             "Oficiul din date este oficiul de depunere, nu neapărat cel care soluționează: clasamentele pe oficii arată unde apar diferențele, nu performanța personalului.",
             "Pentru lunile recente, timpii pe data depunerii sunt cenzurați: valorile sunt limite de jos.",
             "Eșantionul myportal e mic pe oficiu și pe lunile recente.",
             "Definițiile („soluționare”, „zi”, „decizie finală”) schimbă vizibil unele cifre; fiecare cifră are definiția ei în registru.",
             "Împărțirea stocului pe cele două etape la datele oficiale vine din notele Ministerului; datele noastre o pot verifica doar la data recoltării eșantionului."])
    b += h("8. Limitele modelului și ce rămâne incert")
    b += li(["Prognoza descrie un dosar obișnuit, tratat în ordinea sosirii; coada reală nu e strict cronologică.",
             "Intervalele de prognoză reflectă ipotezele despre valurile de cereri și ritmul de soluționare, nu probabilități măsurate.",
             "Efectul fiecărei măsuri (OUG, conversia CAEN, verificări la depunere) e o ipoteză, nu o măsurătoare.",
             "Evaluarea OUG folosește rezumatul din consultare; textul final poate schimba rezultatele.",
             "Aspectele contractuale ale platformei ONRC v2.0 și anchetele în curs nu sunt analizate în acest raport.",
             "Nu se poate spune din date: câți oameni lucrează efectiv la fiecare etapă, de ce unele dosare trec mai repede, ce a cauzat schimbarea din 27 aprilie 2026 și cât de mare va fi exact valul CAEN din 2027."])
    b += h("9. Limitele utilizării AI")
    b += li(["Modelele AI pot greși: pot calcula greșit, pot interpreta greșit o regulă sau pot formula mai sigur decât susțin datele. De aceea fiecare cifră trece prin registru, prin verificatorul automat și, pentru cifrele-cheie, printr-o a doua implementare.",
             "Verificările automate și formale (Lean) confirmă aritmetica și logica, nu corectitudinea datelor de intrare.",
             "Revizuirea pe profiluri a fost simulată de AI; nu înlocuiește consultarea reală a instituțiilor, a personalului și a profesioniștilor.",
             "Textele legale au fost verificate pe legislatie.just.ro la 22.11.2026."])
    b += p("<span class='note'>Declarație de interes: autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal. Credit: analiză big data pe datele din BERC.</span>")
    return b
