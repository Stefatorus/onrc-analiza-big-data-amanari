"""Metodologia, în proză, pe înțelesul tuturor. Un singur text, inclus la finalul raportului principal (înaintea anexei AI)
și o singură dată în dosarul unic. Secțiunea despre numerele de înregistrare se completează din rezultatele verificării
(independent_audit/reserves_check/serials_summary.json), dacă există."""
import json
from pathlib import Path

TITLE = "Metodologia"
_SER = Path(__file__).resolve().parents[2] / "independent_audit" / "reserves_check" / "serials_summary.json"
_REGF = Path(__file__).resolve().parents[2] / "analysis" / "raport_executiv_2026-11" / "claims_registry.csv"


def _pdf_counts():
    """(collected, analysed) PDF bulletins, from the C50 caveat in the claims registry."""
    import csv, re
    r = next(x for x in csv.DictReader(open(_REGF, encoding="utf-8")) if x["id"] == "C50")
    m = re.search(r"descărcate (\d+) de buletine PDF din 2026; eșantionul analizat cuprinde (\d+)", r["rezerva_obligatorie"])
    return m.group(1), m.group(2)


def _serials_text():
    if _SER.exists():
        s = json.loads(_SER.read_text(encoding="utf-8"))
        return s.get("text_ro", "")
    return ("Fiecare cerere primește la depunere un număr de înregistrare. Dacă aceste numere sunt date în ordine, dintr-un singur contor, "
            "atunci diferența dintre primul și ultimul număr dintr-o zi arată câte cereri s-au înregistrat în acea zi, inclusiv cererile "
            "care nu au primit încă o decizie. Am verificat dacă numerele cresc în ordinea timpului de depunere și ce anume numără contorul. "
            "Rezultatele acestei verificări sunt descrise în Volumul 6; până la confirmarea lor, raportul nu folosește numerele de înregistrare "
            "ca măsură a intrărilor, ci cifrele Ministerului Justiției.")


def body(hl=lambda t: f"<mark class='hl'>{t}</mark>"):
    h = lambda t: f'<h3 class="sub3" style="margin-top:4.5mm">{t}</h3>'
    p = lambda t: f"<p>{t}</p>"
    b = p(hl("Această anexă explică, fără prescurtări tehnice, de unde vin datele, cum le-am prelucrat, ce înseamnă fiecare măsură, ce am făcut ca să verificăm rezultatele și ce riscuri rămân.") +
          " Volumul 3 conține aceeași metodă în limbaj statistic, cu formule; aici o povestim de la un capăt la altul, ca un cititor fără pregătire de specialitate să poată judeca singur cât de mult se poate baza pe concluzii.")

    b += h("De unde vin datele")
    b += p("Sursa principală este Buletinul Electronic al Registrului Comerțului (BERC). Registrul publică acolo fiecare decizie a registratorilor: admiterea, respingerea sau amânarea unei cereri, renunțarea solicitantului. "
           "Buletinul este public și poate fi consultat de oricine. Noi l-am descărcat automat, zi de zi și pe fiecare categorie de publicare, prin interfața publică a buletinului, cu pauze între cereri, cu reluarea automată a paginilor care răspundeau greu și cu eliminarea dublurilor după identificatorul unic al fiecărei publicări. "
           "Am păstrat patru categorii, cele care conțin decizii asupra cererilor de înregistrare: modificările la firmele existente (mențiuni), înmatriculările de firme noi, amânările și cererile soluționate în urma unei hotărâri judecătorești. "
           "Rezultatul este o arhivă de 4.077.510 decizii, din aprilie 2023 până la 20 noiembrie 2026.")
    b += p("Pentru fiecare decizie, buletinul arată numărul și data înregistrării cererii, data deciziei, data publicării, județul în care a fost depusă cererea, oficiul, soluția și forma juridică a firmei. "
           "Datele brute conțin și identificatorul firmei, pe care l-am folosit doar acolo unde era necesar (de exemplu, ca să aflăm dacă o firmă respinsă a depus o nouă cerere) și pe care nu îl publicăm. "
           "Am descărcat și buletinele în format PDF, care conțin textul complet al deciziilor: " + _pdf_counts()[0] + " de buletine din 2026. Pe un eșantion de " + _pdf_counts()[1] + " dintre ele am citit acest text ca să aflăm ce parte din decizii sunt simple actualizări ale codului CAEN; analizele motivelor de amânare și de respingere folosesc buletinele din 19 octombrie–18 noiembrie 2026.")
    b += p("A doua sursă proprie este un eșantion din portalul myportal al Registrului: 7.469 de numere de cerere sondate, recoltate pe 21–22 noiembrie 2026 prin contul autorului, cu un ritm limitat de cereri și fără a păstra nume, CNP sau date de contact. "
           "Portalul arată ce buletinul nu arată: în ce etapă se află un dosar care nu a primit încă decizia, la operare sau la registrator. Dintre aceste dosare, 1.819 au avut toate datele necesare pentru calculul timpilor.")
    b += p("A treia sursă sunt cifrele oficiale ale Ministerului Justiției, din notele din 30 octombrie și 6 noiembrie 2026: stocul de cereri nesoluționate pe cele două etape, intrările zilnice medii, posturile și bugetul proiectului de ordonanță. "
           "Le citez cu sursa și nu le recalculez, pentru că nu am datele din care au fost obținute. "
           "În sfârșit, am comparat rezultatele cu o compilație de articole de presă din 21 noiembrie 2026, ca să vedem ce confirmă și ce contrazice datele noastre.")
    b += p(hl("Ierarhia este fixă: buletinul BERC este sursa de referință pentru decizii și timpi; ce nu se află în BERC luăm din sursele oficiale; presa servește doar la comparație.") +
           " Când o cifră publică contrazice buletinul, rămâne cifra din buletin, iar diferența este menționată și explicată.")

    b += h("Ce înseamnă fiecare măsură")
    b += p("Măsura centrală a raportului este așteptarea: numărul de zile calendaristice dintre momentul în care cererea a fost înregistrată și momentul în care registratorul a luat decizia finală. "
           "Ea include și timpul în care solicitantul completează actele după o amânare, pentru că acesta este timpul pe care îl trăiește firma. "
           "Termenul legal se exprimă în zile lucrătoare; o zi lucrătoare peste un weekend înseamnă trei zile calendaristice, de aceea comparația cu legea este făcută cu atenție la unitate.")
    b += p("Folosim mediana, nu media: valoarea din mijloc, față de care jumătate din dosare au așteptat mai puțin și jumătate mai mult. Mediana nu este trasă în sus de câteva dosare foarte întârziate și descrie mai bine experiența obișnuită. "
           "Unde contează și cazurile grele, dăm și percentila 90: valoarea depășită doar de unul din zece dosare.")
    b += p("Așteptarea se poate măsura în două feluri, care răspund la întrebări diferite. Dacă luăm dosarele decise într-o săptămână, aflăm cât de vechi sunt dosarele pe care Registrul le termină acum; măsura este completă imediat. "
           "Dacă luăm dosarele depuse într-o lună, aflăm cât va aștepta cine depune acum, dar numai după ce toate acele dosare au primit decizia. "
           "Pentru lunile recente, multe dosare nu sunt încă decise, iar o mediană calculată doar pe cele decise ar ieși fals de mică; acest fenomen se numește cenzurare. "
           "De aceea, pentru lunile recente dăm limite de jos („cel puțin”) și folosim o metodă statistică, estimatorul Kaplan–Meier, care ține cont și de dosarele încă nerezolvate.")
    b += p("O decizie finală este admiterea, respingerea sau renunțarea solicitantului. Amânarea nu este o decizie finală, dar este muncă de analiză și o numărăm separat. "
           "Ritmul de lucru îl exprimăm în decizii pe zi lucrătoare legală, adică luni–vineri, fără sărbători; acest numitor schimbă vizibil unele cifre, de aceea îl precizăm de fiecare dată.")

    b += h("Ce am calculat și cum")
    b += p("Pentru prezent am calculat, din buletin, așteptarea pe săptămâna deciziei și pe luna depunerii, ritmul deciziilor, ponderea amânărilor și a respingerilor, pe tipuri de cereri și pe oficii. "
           "Pe oficii, am comparat fiecare oficiu cu nivelul național lună de lună și am construit clasamente care arată unde au existat probleme locale; oficiul din date este cel de depunere, deci un clasament nu este o notă pentru personalul de acolo.")
    b += p("Pentru cele două etape ale unui dosar, operarea și soluționarea, am folosit stocurile oficiale ale Ministerului la două date și ritmul deciziilor din buletin. Din ele am estimat cât de încărcată este fiecare etapă și ce se întâmplă dacă personalul este mutat dintr-o etapă în alta.")
    b += p("Pentru viitor am folosit un model de coadă. Ideea lui e simplă: stocul de mâine este stocul de azi plus cererile care intră, minus dosarele care ies, și nu poate coborî sub zero. "
           "Ritmul de ieșire l-am măsurat din buletin; nu l-am ajustat ca modelul să dea un rezultat dorit. Mărimea cererilor viitoare, mai ales a valurilor anunțate pentru 2027, nu se cunoaște; de aceea modelul rulează 2.000 de variante plauzibile și raportează un interval, nu o singură cifră. "
           "Pe același model am rulat proiectul de ordonanță, pachete de măsuri, o grilă cu 36 de combinații de viteze de intrare și ieșire și un scenariu în care valul de actualizări CAEN este atât de mare cât sugerează sursele publice.")

    b += h("Numerele de înregistrare ale cererilor")
    b += p(_serials_text())

    b += h("Cum am verificat")
    b += p("Fiecare cifră publicată are un cod între paranteze drepte și o fișă în registrul afirmațiilor: valoarea, unitatea, sursa, programul care o calculează, amprenta digitală a datelor de intrare și o rezervă obligatorie. "
           "Valorile din registru sunt citite automat din rezultatele programelor, nu scrise de mână, iar textul rapoartelor citește cifrele din registru. "
           "Un verificator automat respinge orice cifră din text care nu are cod și orice citare a unei afirmații retrase.")
    b += p("Cifrele de bază sunt calculate o singură dată și blocate într-un fișier unic; o nouă rulare nu are voie să le schimbe. "
           "Cifrele observate direct au fost recalculate separat, cu un cod scris de la zero, într-o sesiune de lucru distinctă; acolo unde rezultatul depindea de definiție, am adoptat definiția verificată și am publicat schimbarea. "
           "Calculele aritmetice și proprietățile logice ale modelului (de exemplu, că mai multă capacitate nu poate lungi coada) sunt demonstrate formal în Lean, un program care acceptă o afirmație doar dacă fiecare pas al demonstrației este corect.")
    b += p(hl("Modelul de coadă a fost testat pe trecut, pe datele din buletin: pornit din martie, iunie și august 2026, cu intrările și capacitatea reale, a reprodus așteptarea observată cu o eroare medie de 1–3 zile.") +
           " Același test arată și limita: fără să știe de valul de cereri din toamnă, o prognoză făcută la începutul verii ar fi subestimat așteptarea. "
           "Înainte de publicare, raportul a fost citit și criticat de cititori simulați cu profiluri diferite (ministru, director, specialist IT, statistician, sindicat, avocat); criticile și corecturile sunt în Volumul 6. "
           "La final, o analiză separată, cu acces doar la datele brute, refăcute de la zero, verifică cifrele-cheie.")

    b += h("Riscuri și limite")
    b += p("Datele publice nu conțin momentul în care un dosar trece de la operare la registrator și personalul activ pe fiecare etapă; acestea rămân necunoscute sau preluate din sursele oficiale. "
           "Intrările zilnice și stocul le-am estimat din numerele de înregistrare și din eșantion; estimările se potrivesc cu cifrele Ministerului, dar au o marjă de circa ±10%. "
           "Tipul exact al fiecărei cereri nu apare în datele tabelare, ci doar în textul buletinelor, pe care l-am citit pe un eșantion.")
    b += p("Prognoza descrie un dosar obișnuit, tratat în ordinea sosirii; în realitate, unele dosare trec mai repede, iar cele amânate stau mai mult. "
           "Intervalele de prognoză reflectă ipotezele despre cererile viitoare; cel mai mare risc este valul de actualizări CAEN, pe care îl tratăm într-un scenariu separat. "
           "Evaluarea proiectului de ordonanță folosește rezumatul pus în consultare, pentru că nu am avut acces la textul integral la data analizei. Textele legale au fost verificate pe legislatie.just.ro (forma consolidată) la 22.11.2026; o versiune anterioară a raportului folosise extrasul publicat de ONRC. "
           "Analiza a fost realizată cu ajutorul inteligenței artificiale, sub îndrumarea și verificarea autorului; modelele pot greși, de aceea fiecare cifră trece prin verificările descrise mai sus.")
    b += p(hl("Ce putem spune cu încredere mare: cât au așteptat dosarele decise, cât de repede lucrează Registrul și cum s-a schimbat situația din 2023 până azi. Ce spunem cu prudență: cât vor aștepta dosarele depuse recent și ce se va întâmpla în 2027–2028."))
    return b
