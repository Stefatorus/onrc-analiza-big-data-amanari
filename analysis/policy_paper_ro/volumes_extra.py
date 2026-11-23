"""Volumele 0 (fișe pe profil), 4 (munca din spatele cozii), 5 (fișe pe județe) și 6 (verificare).
Folosește aceleași componente ca build_volume_stat.py (V, E, hl, table, fig, sec, sub, P, cover, toc)."""
import json, csv
import pandas as pd
import build_volume_stat as BV
from build_volume_stat import V, E, hl, sec, sub, P, cover, toc, ro, IA, REG
import re
import postponement_section as PSEC
import rejection_section as RSEC
ORI = re.search(r"de circa (\S+) ori", REG["C111"]["public_ro"]).group(1)      # Oct 2026 vs a normal month (C111)
HIRE_S = " În 2026, concursurile pentru posturi vacante sunt suspendate; Ministerul Justiției poate aproba doar excepții limitate."
NFOUND = V("C116").split(" · ")[1].split(" parametri")[0]                      # e.g. «10 din 18» (C116)
# the 40%-of-vacant-posts scenario (C52) assumes the 2026 hiring-freeze exceptions are approved (C153); text from the registry
HIRE_40 = " " + re.search(r"Scenariul presupune că Ministerul Justiției.*?\)\.", REG["C52"]["rezerva_obligatorie"]).group(0)
_KF = json.loads((IA / "out" / "cost_founded.json").read_text(encoding="utf-8"))["scenarios"]["fundamentat"]["central"]
_KCB = json.loads((IA / "out" / "cost_check.json").read_text(encoding="utf-8"))["oug_budget_mil_lei"]
_W = {1: "o zi", 2: "două zile", 3: "trei zile", 4: "patru zile", 5: "cinci zile", 6: "șase zile", 7: "șapte zile", 8: "opt zile", 9: "nouă zile", 10: "zece zile"}
OUG_D_ECON = _W.get(int(_KCB * 1e6 / _KF["daily_econ"] + .5), f"{int(_KCB * 1e6 / _KF['daily_econ'] + .5)} de zile")   # days of queue = OUG budget (C83, C108)

SPX = json.loads((IA / "out" / "stat_pack_ext.json").read_text(encoding="utf-8"))
LEAN3 = json.loads((IA / "out" / "lean_v3_results.json").read_text(encoding="utf-8"))
BV.SP.update({k: v for k, v in SPX.items()})          # tables of the extension become renderable by BV.table
BV.LABELS.update({"perioada": "Perioada", "decizii_total": "Decizii (total)", "finale": "Finale", "amanari": "Amânări",
                  "decizii_pe_zi_lucr": "Decizii / zi lucr.", "pondere_amanari_pct": "Amânări %", "finale_pe_zi_lucr": "Finale / zi lucr.",
                  "fata_de_2023_pct": "Față de 2023 %", "zile_nelucratoare_cu_decizii": "Zile nelucrătoare cu decizii",
                  "decizii_in_zile_nelucratoare": "Decizii în zile nelucrătoare", "pondere_zile_nelucratoare_pct": "% în zile nelucrătoare",
                  "pondere_dupa_16_sau_inainte_8_pct": "% după 16:00 / înainte de 8:00", "decizii": "Decizii", "in_zile_nelucratoare": "În zile nelucrătoare",
                  "dupa_program": "După program", "pondere_in_afara_pct": "% în afara programului", "decizii_pct": "Decizii %", "cod": "Cod",
                  "stage1_operare": "Eșantion: la operare", "stage2_registrator": "Eșantion: la registrator", "n_resolved": "Eșantion: rezolvate",
                  "pending_total": "Eșantion: în așteptare", "pondere_decizii_2026_pct": "% din deciziile 2026"})
BV.TEXT_COLS.update({"cod", "perioada", "tip_blocaj"})


def box(title, items):
    return f'<div class="issue"><h3>{title}</h3><ul class="find" style="margin:0 0 0 4mm">' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


def kv(rows):
    return ('<table class="dt kvt"><thead><tr><th style="width:62%">Ce</th><th style="width:22%">Cifra</th><th>Cod</th></tr></thead><tbody>' +
            "".join(f'<tr><td>{a}</td><td class="num">{b}</td><td>{E(*c)}</td></tr>' for a, b, c in rows) + "</tbody></table>")


# ================================================================== VOLUME 0 · one-page sheets by profile
def vol0(pg):
    BV.TN["n"] = 0; BV.FN["n"] = 0
    S = [("", "1", "Pentru ministru și decidenți politici", "1"), ("", "2", "Pentru conducerea ONRC", "2"), ("", "3", "Pentru echipa IT", "3"),
         ("", "4", "Pentru statisticieni și analiști", "4"), ("", "5", "Pentru juriști, avocați, notari și contabili", "5"),
         ("", "6", "Pentru personalul ONRC și sindicat", "6"), ("", "7", "Pentru antreprenori și public", "7"), ("", "8", "Pentru Ministerul Finanțelor și ANAF", "8"), ("", "9", "Harta volumelor", "9")]
    b = cover("Fișe pe profil", "O pagină pentru fiecare cititor: ce trebuie să știe, ce poate face și unde găsește detaliile. Fiecare fișă se poate tăia și distribui separat.",
              "Volumul 0", "<dt>Cum se folosește</dt><dd>Fiecare fișă începe pe o pagină nouă și se citește singură. Cifrele au coduri [Cxx], verificabile în registrul afirmațiilor.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    READ = ('<p class="note" style="border-top:.2mm solid #e4e1da;padding-top:1.5mm"><b>Cum citiți cifrele.</b> Toate duratele sunt în zile calendaristice, de la înregistrarea cererii la decizie. '
            '„Mediana” = valoarea din mijloc: jumătate din dosare așteaptă mai puțin, jumătate mai mult. „≈138 (105–175)” = cazul central și intervalul în care cad 8 din 10 variante simulate. '
            '„≤3” = coada e practic goală. Etapa 1 = <b>operare</b> (preluarea și verificarea formală a cererii); etapa 2 = <b>soluționare</b> (decizia registratorului). [Cxx] = codul cifrei în registrul de verificare (Volumul 6).</p>')
    it_tbl = ('<table class="dt kvt"><thead><tr><th style="width:5%">Nr.</th><th style="width:25%">Ce construim</th><th style="width:22%">De ce</th>'
              '<th style="width:18%">Depinde de</th><th style="width:30%">Cum verificăm că merge</th></tr></thead><tbody>'
              '<tr><td>1</td><td>Conversia automată a codurilor CAEN cu un singur corespondent nou, fără dosar și fără registrator</td><td>Valul CAEN e cea mai mare sursă de risc pentru vârful din 2027' + E("C68") + '</td><td>Temei legal (prevăzut în pachetele evaluate prin OUG) + tabelul oficial de corespondență</td><td>Numărul lunar de cereri doar-CAEN care mai intră în coadă scade; ținta o stabilește ONRC</td></tr>'
              '<tr><td>2</td><td>Verificări automate înainte de depunere pentru lipsurile formale frecvente</td><td>Circa unul din cinci dosare soluționate fusese amânat înainte' + E("C74") + '</td><td>Lista motivelor de amânare, pe frecvență (Volumul 1, secțiunea 6.4)' + E("C139") + '</td><td>Ponderea amânărilor din decizii scade față de nivelul de azi' + E("C82") + '; ca plafon, circa ' + V("C141").split(" (")[0].lstrip("≈") + ' de amânări pe zi mai puțin' + E("C141") + '</td></tr>'
              '<tr><td>3</td><td>Cereri online structurate preluate fără reintroducere manuală la operare</td><td>Azi, cererile online trec prin aceeași operare și nu sunt mai rapide' + E("C36") + '</td><td>Validarea semnăturii și a câmpurilor din formular</td><td>Timpul de la depunere la trecerea la registrator scade pentru cererile online</td></tr>'
              '<tr><td>4</td><td>Câmpuri noi în date: data și ora trecerii la registrator (<code>data_trecere_registrator</code>), codul tipului de cerere, identificator pseudonimizat al firmei</td><td>Fără ele nu se poate măsura cât stă un dosar în fiecare etapă</td><td>Aprobare GDPR pentru pseudonimizare</td><td>Câmpurile apar în exportul public lunar</td></tr>'
              '</tbody></table><p class="note">Efectul fiecărei măsuri IT, luată separat, nu se poate estima din datele publice. În model, un pachet care include conversia CAEN coboară mult așteptarea' + E("C53", "C54") + '; cifra exactă pentru conversie depinde de câte coduri sunt 1-la-1, pe care doar ONRC le poate număra.</p>')
    sheets = [
        ("1", "Pentru ministru și decidenți politici", "Ce se poate decide în următoarele 30 de zile: valul de cereri din ianuarie 2027 vine peste un sistem care lucrează deja aproape la capacitate.",
         [hl("Modificările soluționate în 16–20 noiembrie au așteptat " + V("C14") + " zile calendaristice; legea cere o zi lucrătoare de la înregistrare.") + E("C14", "C23"),
          hl("Fără măsuri noi, așteptarea ar urca la " + V("C59") + " zile la mijlocul lui 2027; cu proiectul de OUG, ar rămâne de ordinul a trei luni în 2028.") + E("C59", "C43"),
          hl("Un pachet minim realist (OUG prelungit, conversie CAEN 1-la-1, eșalonare, triaj) ar coborî așteptarea din iunie 2028, în model, la " + V("C54") + " zile.") + E("C54"),
          hl("Riscul cel mai mare: dacă se confirmă cifrele publice despre CAEN (902.243 de cereri rămase), așteptarea din iunie 2027 ar putea ajunge la " + V("C94").split(" · ")[1].split("→ ")[1] + "–" + V("C94").split(" · ")[2].split("→ ")[1].split(" (")[0] + " de zile; conversia automată CAEN o reduce la mai puțin de jumătate.") + E("C94", "C95")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "<b>Imediat (consultarea OUG):</b> includeți conversia automată a codurilor CAEN cu un singur corespondent și ocuparea posturilor finanțate neocupate." + E("C53", "C51") + HIRE_S + E("C153"),
             "<b>Până la valul din ianuarie 2027:</b> capacitate suplimentară la registrator <b>și</b> la operare; întărirea unei singure etape mută blocajul." + E("C56", "C72"),
             "<b>Permanent:</b> cereți ONRC să publice lunar stocul pe etape și personalul activ pe etape; fără ele, nicio măsură nu poate fi evaluată.",
             "Evaluarea OUG folosește textul integral pus în consultare (art. I–IV); modelul a fost rulat pe măsurile pe care le prevede textul, cu ipotezele de livrare declarate. Textul adoptat poate schimba rezultatul; detaliile, în analiza separată a proiectului de OUG."]) + "</ul>",
         [("Stoc oficial, 6.11.2026", V("C28"), ["C28"]), ("Iunie 2028, fără măsuri noi / cu OUG", V("C42") + " / " + V("C43"), ["C42", "C43"]),
          ("Capacitate +10% / −10% → iunie 2028", V("C63").split(" · ")[0].split("→ ")[1] + " / " + V("C63").split(" · ")[1].split("→ ")[1].split(" (")[0] + " zile", ["C63"]),
          ("Posturi finanțate neocupate", "134 din 1.384", ["C51"]), ("Bugetul proiectului OUG", V("C83"), ["C83"])],
         "Volumul 1, sinteza (p. 4), capitolele 8–10; ediția executivă."),
        ("2", "Pentru conducerea ONRC", "Cele două etape lucrează aproape la capacitate. Întărirea uneia singure mută blocajul în cealaltă.",
         [hl("La 6 noiembrie, peste jumătate din stoc (51,9%) era încă la operare.") + E("C29"),
          hl("Mutarea juriștilor din operare la registrator ajută doar până la un optim; peste el, câștigul dispare.") + E("C35"),
          hl("Producția din 2026 e puțin peste nivelul din 2025, iar scăderea din august–octombrie e sezonieră, nu o prăbușire.") + E("C87", "C86"),
          *PSEC.short_items(V, E, hl, "onrc")[:2], RSEC.short_item(V, E, hl, "onrc")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Delegați juriști din alte activități, nu din operare; ar fi utilă o cifră publică: câți dintre juriștii eligibili lucrează azi la operare." + E("C35"),
             "O explicație publică a schimbării din 27 aprilie 2026 ar lămuri dacă e un pas de procedură: de atunci aproape niciun dosar nu mai e soluționat în două zile." + E("C32"),
             "Semnalarea lipsurilor la depunere: circa unul din cinci dosare soluționate fusese amânat înainte; tabelul 6.1 din Volumul 1 arată, pe motive, ce se poate verifica automat." + E("C74", "C139"),
             "Volumul 5 arată unde au fost probleme locale înainte de valul național (" + ", ".join(x.split(" +")[0] for x in V("C88").split(" · ")) + ") și unde respingerile sunt cele mai mari; acolo merită verificat ce e diferit." + E("C88", "C90")]) + "</ul>",
         [("Decizii finale pe zi lucrătoare", V("C01"), ["C01"]), ("Amânări pe zi", V("C03"), ["C03"]),
          ("Operarea față de soluționare, în săptămâna 30.10–6.11", "circa 16–20% mai rapidă", ["C34"]), ("Dosare decise ≤14 zile (2–19.11)", V("C38"), ["C38"])],
         "Volumul 1, capitolele 4, 6, 9 și 10; Volumul 4 (munca); Volumul 5 (județe)."),
        ("3", "Pentru echipa IT", "Patru lucrări informatice scot muncă din ambele etape sau fac coada măsurabilă. Ordinea de mai jos e ordinea de prioritate.",
         [hl("Dacă valul CAEN ar dispărea complet, vârful din 2027 ar fi mai mic cu circa " + V("C68").split(" · ")[0].split(" (")[0].lstrip("≈") + " de zile; conversia 1-la-1 elimină doar o parte din el, deci câștigul real e mai mic.") + E("C68"),
          hl("Circa 1 din 4 decizii e doar o actualizare de cod CAEN; asta nu înseamnă 1 din 4 ore de muncă, pentru că aceste dosare sunt mai simple.") + E("C50"),
          hl("Cererile online nu sunt mai rapide: trec prin aceeași operare manuală.") + E("C36"),
          *PSEC.short_items(V, E, hl, "it")[:2], RSEC.short_item(V, E, hl, "it")],
         it_tbl,
         [("Decizii care sunt doar actualizări CAEN", "aproximativ 1 din 4", ["C50"]), ("Dosare soluționate cu o amânare anterioară", V("C74").split(" (")[0], ["C74"]),
          ("Întârzierea publicării în buletin", "de obicei sub o zi", ["C78"])],
         "Volumul 1, capitolele 8 (grila de risc) și 10 (soluții); Volumul 3, secțiunea 6 (datele lipsă)."),
        ("4", "Pentru statisticieni și analiști", "Cifrele despre prezent sunt solide; incertitudinea vine din definiții și din lipsa datelor interne, nu din eșantion.",
         [hl("Mediana de " + V("C14") + " zile vine din toate deciziile (recensământ), nu dintr-un eșantion; ce o poate schimba e definiția.") + E("C14", "C77"),
          hl("Pentru cohorta din septembrie, mediana Kaplan–Meier e de cel puțin circa 58 de zile (limită de jos: cenzurarea e informativă).") + E("C73"),
          hl("Aceeași mărime se schimbă vizibil cu definiția zilei sau a deciziei finale.") + E("C07", "C32")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Declarați mereu baza (decizie sau depunere), fereastra exactă și numitorul (zi lucrătoare legală sau zi cu decizii).",
             "Pentru lunile recente, nu calculați mediane pe dosarele rezolvate: sunt cenzurate." + E("C11"),
             "Reproduceți cu <code>stat_pack.py</code>, <code>forecast_grid.py</code> și <code>generate_claims_registry.py</code>; toate tabelele sunt în fișierul Excel.",
             "Verificările formale (Lean) acoperă aritmetica și monotonia modelului; nu validează datele de intrare."]) + "</ul>",
         [("Little: stoc implicat vs oficial", V("C76"), ["C76"]), ("Persistența pe oficii (ρ Spearman)", V("C75").split(" · ")[1], ["C75"]),
          ("Eroarea testului pe date nevăzute", V("C70").split(" · ")[0], ["C70"])],
         "Volumul 3 (metodă), Volumul 2 (tabele), Volumul 6 (verificare), Date_ONRC_Coada_2026-11.xlsx."),
        ("5", "Pentru juriști, avocați, notari și contabili", "Termenul legal este de o zi lucrătoare de la înregistrare; durata măsurată este de aproape două luni calendaristice, inclusiv completările.",
         [hl("Art. 105 alin. (1) din Legea 265/2022: soluționare în termen de o zi lucrătoare de la înregistrarea cererii; art. 106 alin. (1): termen de completare de cel mult 15 zile la amânare.") + E("C23", "C03"),
          hl("Un dosar amânat a așteptat circa 42 de zile până la prima amânare și circa 14 zile de la ultima amânare până la decizie.") + E("C37"),
          hl(V("C41").split()[0] + " dintre firmele noi admise fără amânare în noiembrie au așteptat peste 10 zile lucrătoare de la înregistrare.") + E("C41") +
          " Pragul din art. 13g alin. (7) al Directivei (UE) 2017/1132 (5 sau 10 zile lucrătoare) se aplică doar constituirilor online, pe care datele nu le identifică."],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Termen realist pentru clienți: dosarele soluționate acum fuseseră depuse cu aproape două luni în urmă." + E("C14"),
             "Dosare complete: o amânare adaugă săptămâni, iar circa unul din cinci dosare soluționate a avut una." + E("C74"),
             "După o respingere, majoritatea firmelor depun o nouă cerere de același tip (nu neapărat același dosar)." + E("C40"),
             "Raportul nu califică întârzierile drept nelegale și nu analizează consecințele depășirii termenului sau căile de atac.",
             "Textul legii a fost verificat pe legislatie.just.ro (forma consolidată) la 22.11.2026; pentru un memoriu, folosiți forma în vigoare la data depunerii."]) + "</ul>",
         [("Respinse din deciziile finale (din aug. 2026)", V("C39").split("→ ")[1], ["C39"]), ("Termen legal", V("C23") + " zi lucrătoare", ["C23"]),
          ("Mediana pe oficii, decizii 1–18 noiembrie", V("C49") + " zile", ["C49"]), ("Fără măsuri noi, iunie 2028", V("C42") + " zile (estimare)", ["C42"])],
         "Volumul 1, capitolele 1, 2, 6 și 9."),
        ("6", "Pentru personalul ONRC și sindicat", "Coada nu crește pentru că producția a scăzut: cererile au crescut cu circa 53%, iar producția e puțin peste nivelul din 2025.",
         [hl("În 1 octombrie–19 noiembrie, Registrul emite cu circa 40% mai multe decizii pe zi lucrătoare decât în 2023 și cu circa 9% mai multe decât în 2025.") + E("C79", "C87"),
          hl("Circa una din cinci decizii este o amânare: analiză făcută care nu apare în cifrele de soluționări finale.") + E("C82"),
          hl("Cererile au crescut cu circa 53% în august–octombrie, sezonul în care, atât în 2025, cât și în 2026, s-au emis cu circa 13% mai puține decizii pe zi.") + E("C47", "C86")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Folosiți cifre de volum ale sistemului; datele publice nu arată cine a lucrat la ce, deci nu există cifre individuale.",
             "Cereți ocuparea celor 134 de posturi finanțate neocupate (din 1.384 finanțate) și publicarea personalului activ pe etape." + E("C51") + HIRE_S + E("C153"),
             "Automatizarea CAEN: cereți să se stabilească unde merge capacitatea eliberată; datele nu spun nimic despre necesarul de personal." + E("C50"),
             "Mărcile temporale ale deciziilor nu dovedesc nici ore suplimentare, nici absența lor." + E("C81")]) + "</ul>",
         [("Decizii emise în 2025 / 2026 (până la 20.11)", V("C80"), ["C80"]), ("Amânări în 2026", V("C82"), ["C82"]),
          ("Aceeași perioadă: 2025 → 2026", V("C87"), ["C87"])],
         "Volumul 4 (munca din spatele cozii)."),
        ("7", "Pentru antreprenori și public", "Așteptarea e aproape aceeași peste tot; un dosar complet e cea mai bună protecție împotriva întârzierilor suplimentare.",
         [hl("Modificările soluționate în 16–20 noiembrie au așteptat aproape două luni.") + E("C14"),
          hl("Coada e națională: oficiul la care depuneți nu schimbă mult așteptarea.") + E("C49", "C75"),
          hl("Online-ul nu e mai rapid: cererile online trec tot prin operare.") + E("C36")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Planificați schimbările la firmă cu cel puțin două luni înainte.",
             "Verificați actele înainte de depunere: o amânare adaugă săptămâni." + E("C37"),
             "Pentru constituiri, contați pe mai mult decât termenul legal." + E("C41")]) + "</ul>",
         [("Așteptare modificări (16–20.11)", V("C14") + " zile", ["C14"]), ("Așteptare înmatriculări (16–20.11)", V("C15") + " zile", ["C15"])],
         "Volumul 1, sinteza și capitolul 2."),
        ("8", "Pentru Ministerul Finanțelor și ANAF", "Coada are un preț în bani: în economie și la buget. Zilele de întârziere sunt măsurate; transformarea lor în lei e dată ca interval de scenarii.",
         [hl("Într-o lună obișnuită, întârzierile costă economia câteva milioane de lei; în octombrie și noiembrie 2026, de circa " + ORI + " ori mai mult.") + E("C111"),
          hl("Încasările bugetare afectate în august–18 noiembrie: între circa " + V("C107").split(" / ")[0] + " și " + V("C107").split(" / ")[2] + " de milioane de lei, cu circa " + V("C107").split(" / ")[1] + " în scenariul central.") + E("C107"),
          hl("Fiecare zi în plus cu stocul actual costă, în scenariul central, circa " + V("C108").split(" / ")[1].split(" (")[0] + " milioane de lei la buget și circa " + V("C108").split(" (")[0] + " milioane în economie.") + E("C108"),
          hl(REG["C122"]["public_ro"]) + " Estimare extrapolată la așteptări mai lungi decât cele pe care a fost măsurat efectul. " + REG["C124"]["public_ro"] + E("C122", "C124", "C120"),
          "Parametri cu bază în date oficiale sau măsurate: " + NFOUND + "; cel mai important, costul unei modificări blocate, rămâne ipoteză. Cifrele sunt ordine de mărime, nu contabilitate." + E("C116", "C109")],
         '<ul class="find">' + "".join(f"<li>{k}</li>" for k in [
             "Cântăriți costul măsurilor față de expunerea zilnică: în scenariul central, economia pierde în circa " + OUG_D_ECON + " de coadă cât costă proiectul de OUG (ordin de mărime: cifra zilnică nu se înmulțește cu numărul de zile, iar proiectul singur scurtează coada, nu o elimină)." + E("C108", "C83"),
             "Includeți în evaluarea veniturilor pentru 2027 venitul care nu intră în bugetul anului din cauza cozii, cu ambele lecturi (recuperat ulterior sau pierdut); un pachet realist de măsuri ar evita cea mai mare parte din el." + E("C122", "C124", "C125"),
             "Permiteți o legare controlată, pseudonimizată, ONRC–ANAF pentru firmele cu dosare de sediu în așteptare: notificare, inactivare, reactivare.",
             "Folosiți declarațiile periodice ale firmelor noi pentru a măsura direct vânzările din primele luni.",
             "Posturile finanțate, dar neocupate, nu cer posturi noi; în model, ocuparea a 40% din ele, cu un OUG extins, coboară mult așteptarea din 2028. În 2026, concursurile sunt suspendate, cu excepții limitate." + HIRE_40 + E("C51", "C52", "C153")]) + "</ul>",
         [("Cost economic, oct. / nov. 2026 (central, pe lună)", V("C111").split(" · ")[2].replace("sept./oct./nov. 2026 ", "").split(" / ", 1)[1], ["C111"]),
          ("Cost economic aug.–18 nov. 2026 (mil. lei)", V("C106"), ["C106"]), ("Buget afectat aug.–18 nov. 2026 (mil. lei)", V("C107"), ["C107"]),
          ("O zi în plus cu stocul: economic / buget (mil. lei)", V("C108"), ["C108"]), ("Bugetul proiectului OUG", V("C83"), ["C83"])],
         "Volumul 7, „Impactul economic și bugetar al cozii”."),
    ]
    for n, title, lead, know, do, nums, where in sheets:
        b += sec(n, title) + f'<p class="abstract" style="font-size:10.4pt"><b>{lead}</b></p>'
        b += sub("", "Ce trebuie să știți") + '<ul class="find">' + "".join(f"<li>{k}</li>" for k in know) + "</ul>"
        b += sub("", "Ce puteți face") + do
        b += sub("", "Cifrele de care aveți nevoie") + kv(nums)
        b += P(f'<span class="note"><b>Detalii:</b> {where}</span>')
        b += "" if BV.BOOK else READ
    vols = [("0", "Fișe pe profil", "toți", "acest document"), ("1", "Raportul principal + ediția executivă", "decidenți, toți", "diagnostic, prognoză, OUG, soluții"),
            ("2", "Anexe statistice", "analiști", "toate tabelele, cu definiții și amprente"), ("3", "Raport statistic avansat", "statisticieni", "metodă, estimatori, problemele datelor"),
            ("4", "Munca din spatele cozii", "personal, sindicat", "volum de muncă la nivel de sistem"), ("5", "Fișe pe județe", "conducere, oficii", "42 de oficii, cu clasamente și serii lunare"),
            ("6", "Verificare și încredere", "oricine verifică", "registru, recalcul independent, Lean"), ("7", "Impactul economic și bugetar", "MF, ANAF, MJ, Guvern", "costul întârzierilor lunar, scenarii, buget, verificare"), ("X", "Date_ONRC_Coada_2026-11.xlsx", "analiști", "toate tabelele, gata de analiză")]
    if BV.BOOK:
        return b, S[:-1]
    b += sec("9", "Harta volumelor") + '<table class="dt"><thead><tr><th style="width:9mm">Vol.</th><th>Titlu</th><th>Pentru</th><th>Conține</th></tr></thead><tbody>' + \
        "".join(f"<tr><td>{a}</td><td><b>{t}</b></td><td>{w}</td><td>{c}</td></tr>" for a, t, w, c in vols) + "</tbody></table>"
    return b, S


# ================================================================== VOLUME 4 · work effort
def vol4(pg):
    BV.TN["n"] = 0; BV.FN["n"] = 0
    S = [("", "1", "Pe scurt", "1"), ("", "2", "Ce măsurăm și ce nu", "2"), ("", "3", "Volumul de muncă", "3"), ("", "4", "Amânările: analiză care nu se vede", "4"),
         ("", "5", "Programul", "5"), ("", "6", "Ce înseamnă pentru personal", "6"), ("", "7", "Ce se poate cere, pe baza datelor", "7"), ("", "8", "Tabele", "8")]
    b = cover("Munca din spatele cozii", "Cât lucrează Registrul Comerțului, măsurat din peste patru milioane de decizii. Pentru personalul ONRC, sindicat și oricine vrea să înțeleagă de ce coada crește deși producția nu a scăzut.",
              "Volumul 4", "<dt>Regula de onestitate</dt><dd>Doar cifre la nivel de sistem. Datele publice nu arată cine a lucrat la ce, deci nu calculăm productivitate individuală. Arătăm și cifrele care nu avantajează pe nimeni.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    b += sec("1", "Pe scurt") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        hl("În 1 octombrie–19 noiembrie, Registrul emite cu circa 40% mai multe decizii pe zi lucrătoare decât în 2023 și cu circa 9% mai multe decât în 2025.") + E("C79", "C87"),
        hl("Registrul a emis " + V("C80").split(" / ")[0] + " de decizii în 2025 și " + V("C80").split(" / ")[1] + " în 2026, până la 20 noiembrie.") + E("C80"),
        hl("Circa una din cinci decizii este o amânare: analiză făcută care nu închide dosarul și nu apare în cifrele de soluționări finale.") + E("C82"),
        hl("Cererile au crescut cu circa 53% în august–octombrie, sezonul în care, atât în 2025, cât și în 2026, s-au emis cu circa 13% mai puține decizii pe zi.") + E("C47", "C86"),
        hl("Din cele 1.384 de posturi finanțate, 134 nu sunt ocupate.") + E("C51")]) + "</ul>"
    b += P('<span class="note"><b>Termeni.</b> Etapa 1, <b>operarea</b>: preluarea și verificarea formală a cererii. Etapa 2, <b>soluționarea</b>: decizia registratorului. <b>Decizie finală</b>: admitere, respingere sau renunțare. <b>Amânare</b>: termen de completare dat când lipsește un act. Durate în zile calendaristice.</span>')
    b += sec("2", "Ce măsurăm și ce nu") + P(
        "Măsurăm munca prin decizii: fiecare admitere, respingere, renunțare sau amânare e o decizie pentru care cineva a analizat dosarul. Numărăm toate deciziile, nu doar pe cele finale, pentru că și o amânare cere analiza dosarului.") + P(
        hl("Nu calculăm productivitate pe om sau pe registrator.") + " Datele publice nu arată câți oameni lucrează la fiecare etapă și nici cine a emis o decizie. Versiunile anterioare ale raportului conțineau un calcul de decizii pe registrator, comparat cu o normă; o verificare separată l-a retras, pentru că numărul de registratori activi nu e cunoscut. Regula rămâne.") + P(
        "Nu toate dosarele cer același efort: circa un sfert din decizii sunt actualizări de cod CAEN, de regulă mai simple." + E("C50") + " O parte din creșterea din 2025 poate veni din aceste dosare; nu am separat-o. De aceea vorbim de volum de decizii, nu de efort exact.")
    b += sec("3", "Volumul de muncă") + P(hl("Pe aceeași perioadă a anului, 1 octombrie–19 noiembrie, numărul de decizii pe zi lucrătoare a crescut de la " + V("C79").split(" (")[0].replace("→", "la") + ".") + E("C79") +
        " Saltul mare s-a produs în 2025; față de 2025, creșterea e de circa 9%." + E("C87") + " Comparația pe aceeași perioadă elimină efectul anotimpului.")
    b += BV.fig("e01_aceeasi_perioada.svg", "Decizii pe zi lucrătoare legală, 1 octombrie–19 noiembrie, pe ani. Albastru: decizii finale; portocaliu: amânări.", ["C79", "C87"])
    b += P("În interiorul fiecărui an, producția variază cu sezonul. " + hl("Atât în 2025, cât și în 2026, august–octombrie a adus cu circa 13% mai puține decizii pe zi decât prima jumătate a anului (în 2024 scăderea a fost mai mare, din cauza lansării portalului).") + E("C86") +
        " Diferența din 2026 este că, exact în acest sezon, cererile au crescut cu circa 53%." + E("C47") + " Scăderile mai adânci din vara lui 2024 coincid cu lansarea noului portal." + E("C18"))
    b += BV.fig("e03_lunar.svg", "Toate deciziile pe zi lucrătoare legală, lunar, aprilie 2023–noiembrie 2026.", ["C86"])
    b += sec("4", "Amânările: analiză care nu se vede") + P(
        "O amânare înseamnă că registratorul a analizat dosarul, a găsit o lipsă și a dat un termen de completare. Analiza e făcută, dar dosarul nu se închide." +
        E("C03") + " " + hl("În 2026 s-au emis " + V("C82").split(" (")[0] + " de amânări, circa o cincime din toate deciziile.") + E("C82") +
        " Când dosarul revine, e analizat din nou. Cifrele de „soluționări” care numără doar deciziile finale nu văd această muncă. " + PSEC.short_items(V, E, hl, "onrc")[0] + " " + RSEC.short_item(V, E, hl, "onrc"))
    b += sec("5", "Programul") + P(
        "Marca temporală a deciziilor arată când au fost înregistrate în sistem. " + hl("Circa una din zece decizii poartă o oră de după 16:00 sau dinainte de 8:00.") + E("C81") +
        " Ponderea a variat în 2026 de la o lună la alta (tabelul lunar), fără o explicație în date. În weekend, buletinul nu conține practic decizii; datele nu arată dacă emiterea în weekend e prevăzută sau posibilă tehnic. " +
        hl("Marca temporală nu dovedește nici ore suplimentare, nici absența lor."))
    b += BV.fig("e02_ora.svg", "Ponderea deciziilor pe ora mărcii temporale, zile lucrătoare 2026.", ["C81"])
    b += sec("6", "Ce înseamnă pentru personal") + P(
        "Cererile au crescut mai repede decât orice creștere de producție, iar diferența s-a adunat în coadă." + E("C47", "C86") + " " +
        hl("Datele publice nu arată dacă numărul de oameni s-a schimbat din 2023; dacă a rămas același, fiecare om a emis în medie cu circa 40% mai multe decizii pe zi.") + E("C79") +
        " Este o afirmație condiționată. Cine cunoaște efectivele o poate completa:") + \
        '<div class="formula">creșterea pe om = 1,40 × (personal 2023 / personal 2026) − 1 &nbsp;&nbsp; (aceeași perioadă, 1 oct.–19 nov.)</div>' + \
        P("Exemplu: dacă personalul activ era același în ambii ani, creșterea pe om este de circa 40%; dacă personalul a crescut cu o zecime, creșterea pe om este de circa 27%.")
    b += sec("7", "Ce se poate cere, pe baza datelor") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "Ocuparea posturilor finanțate: în model, ocuparea a 40% din ele împreună cu un OUG extins ar coborî așteptarea din iunie 2028 la " + V("C52") + " zile." + E("C51", "C52") + HIRE_S + HIRE_40 + E("C153"),
        "Întărirea ambelor etape deodată: dacă se întărește doar soluționarea, capacitatea nouă rămâne nefolosită, pentru că operarea nu o poate alimenta, iar coada de operare crește." + E("C56"),
        "Automatizarea actualizărilor CAEN simple ar elibera capacitate pentru dosarele complexe din coadă; datele nu spun nimic despre necesarul de personal." + E("C50", "C68"),
        "Verificări automate la depunere: mai puține dosare incomplete înseamnă mai puține analize repetate ale aceluiași dosar." + E("C74"),
        "Publicarea personalului activ pe etape: singura cale de a arăta, cu date, încărcarea pe om."]) + "</ul>"
    b += sec("8", "Tabele") + BV.table("efort_anual", "Decizii pe an") + BV.table("efort_aceeasi_perioada", "Aceeași perioadă a anului, 2023–2026") + \
        BV.table("efort_sezon_MJ", "Aceleași ferestre ca intrările din nota MJ, pe ani") + \
        BV.table("efort_in_afara_programului", "Decizii în afara programului, pe ani") + BV.table("efort_in_afara_programului_lunar_2026", "Decizii în afara programului, lunar 2026")
    return b, S


# ================================================================== VOLUME 5 · county sheets
def vol5(pg):
    BV.TN["n"] = 0; BV.FN["n"] = 0
    S = [("", "1", "Cum se citesc fișele", "1"), ("", "2", "Clasamente: unde sunt problemele", "2"), ("", "3", "Toate oficiile, lună de lună", "3"),
         ("", "4", "Indicatori pe oficiu", "4"), ("", "5", "Mediana lunară pe oficiu", "5")]
    b = cover("Fișe pe județe", "Cele 42 de oficii ale Registrului Comerțului: clasamente care arată unde sunt problemele, așteptarea lună de lună, respingeri, amânări și înmatriculări, față de nivelul național.",
              "Volumul 5", "<dt>Atenție</dt><dd>Județul este oficiul de depunere, nu neapărat locul unde se soluționează dosarul. Fișele nu măsoară performanța unui oficiu.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    b += sec("1", "Cum se citesc fișele") + P(
        hl("Din august 2026, toate cele 42 de oficii urmează aproape exact aceeași curbă: coada a devenit comună, la nivel național.") + E("C49") +
        " Înainte, unele oficii aveau vârfuri locale scurte, care s-au rezolvat în câteva luni. Diferențele de azi sunt mici, iar ordinea oficiilor din 2025 nu prezice ordinea din 2026." + E("C75")) + P(
        hl("Clasamentele arată unde apar diferențele, ca să se știe unde să se intervină.") + " Nu sunt note pentru personal: nu cunoaștem personalul pe oficiu, oficiul din date e cel de depunere, iar respingerile și amânările depind și de ce depun solicitanții. Tabelele de după clasamente sunt în ordine alfabetică, ca un oficiu să fie găsit ușor. Toate datele lunare, cu numărul de decizii pe oficiu și lună, sunt în fișierul Excel.") + P(
        '<span class="note"><b>Ferestre.</b> „Mediană 1–18 nov.” = toate deciziile finale din 1–18 noiembrie 2026, ca în raportul principal. În tabelul lunar, coloana „26.11” = finale stricte din 1–20 noiembrie; diferențele de o zecime de zi vin din fereastra diferită. „Aug.–nov.” = 1 august – 19 noiembrie 2026. Durate în zile calendaristice.</span>')
    RK = json.loads((IA / "out" / "county_rankings.json").read_text(encoding="utf-8"))
    BV.SP.update(RK)
    BV.LABELS.update({"loc": "Loc", "exces_mediu_zile": "Peste național, medie (zile)", "exces_maxim_zile": "Peste național, maxim (zile)",
                      "luna_excesului_maxim": "Luna vârfului", "luni_peste_national_cu_5_zile": "Luni cu >5 zile peste național",
                      "schimbare_fata_de_2025_zile": "Creștere față de 2025 (zile)"})
    BV.TEXT_COLS.update({"luna_excesului_maxim", "code"})
    b += sec("2", "Clasamente: unde sunt problemele") + P(
        hl("Înainte de valul național, episoade locale de întârziere au avut " + ", ".join(x.split(" +")[0] for x in V("C88").split(" · ")) + ".") + E("C88") +
        " Acolo merită aflat ce s-a întâmplat (personal, volum local, proceduri), pentru că aceleași cauze pot reapărea. " +
        hl("Acum, cea mai lungă așteptare e la " + V("C89").split(" · ")[0] + " zile, urmată de " + V("C89").split(" · ")[1] + "; cea mai scurtă: " + V("C89").split(" · ")[2].replace("cea mai scurtă: ", "") + " zile.") + E("C89") +
        " Respingerile variază mai mult decât așteptarea: cele mai mari ponderi sunt la " + V("C90").split(" · ")[0].replace("cele mai mari: ", "") + "." + E("C90") +
        " Unde respingerile sunt mari, ghidurile pentru solicitanți și verificările la depunere au cel mai mare efect.")
    BV.LS.FIG_DIR = str(BV.HERE / "figures_institutii")
    b += BV.fig("fi08_judete.svg", "Clasamentul oficiilor după mediana așteptării deciziilor din 1–18 noiembrie 2026 (oficiul de depunere). Roșu: cele mai lungi 10%; verde: cele mai scurte 10%.", ["C49", "C89"], fdir="figures_institutii")
    b += BV.fig("c02_probleme_locale.svg", "Clasamentul episoadelor locale: cât a stat fiecare oficiu peste mediana națională, în medie pe lună, ianuarie 2025 – iulie 2026, înainte de valul național. Eticheta arată luna vârfului.", ["C88"])
    b += BV.table("rang_probleme_locale_2025_2026", "Clasament: probleme locale înainte de valul național", small=True) + \
        BV.table("rang_asteptare_nov", "Clasament: așteptarea acum (decizii 1–18 noiembrie 2026)", small=True) + \
        BV.table("rang_respingeri", "Clasament: ponderea respingerilor, august–noiembrie 2026", small=True) + \
        BV.table("rang_amanari", "Clasament: ponderea dosarelor amânate, august–noiembrie 2026", small=True) + \
        BV.table("rang_inmatriculari_peste_10_zile", "Clasament: înmatriculări peste 10 zile lucrătoare, august–noiembrie 2026", small=True) + \
        BV.table("rang_schimbare_fata_de_2025", "Clasament: cât a crescut așteptarea față de 2025", small=True) + \
        BV.table("rang_volum_2026", "Clasament: ponderea oficiului în deciziile din 2026", small=True)
    b += sec("3", "Toate oficiile, lună de lună") + BV.fig("c01_judete_lunar.svg", "Mediana așteptării pe luna deciziei, ianuarie 2025–noiembrie 2026, pentru fiecare oficiu (roșu) față de nivelul național (gri). Aceeași scară pe toate panourile.", ["C49", "C75"])
    base = {r["code"]: r for r in BV.SP["judete_alfabetic"]["rows"]}
    share = {r["cod"]: r["pondere_decizii_2026_pct"] for r in SPX["judete_pondere_2026"]["rows"]}
    rows = []
    for code, r in sorted(base.items(), key=lambda kv: kv[1]["name"]):
        rows.append(dict(cod=code, name=r["name"], pondere_decizii_2026_pct=share.get(code), median_y25=r["median_y25"], median_nov=r["median_nov"],
                         p90_nov=r["p90_nov"], rejection_pct_crisis=r["rejection_pct_crisis"], postponement_action_pct=r["postponement_action_pct"],
                         formation_gt10_pct=r["formation_gt10_pct"]))
    BV.SP["_v5_ind"] = dict(meta="Combinat din judete_alfabetic (atlas verificat) și judete_pondere_2026 (BERC).", columns=list(rows[0]), rows=rows)
    BV.TEXT_COLS.update({"name"})
    BV.LABELS.update({"median_nov": "Mediană 1–18 nov. (zile)", "p90_nov": "p90 1–18 nov. (zile)", "median_y25": "Mediană 2025 (zile)",
                      "rejection_pct_crisis": "Respinse % aug.–nov.", "postponement_action_pct": "Amânate % aug.–nov."})
    b += sec("4", "Indicatori pe oficiu") + BV.table("_v5_ind", "Indicatori pe oficiu de depunere, ordine alfabetică", small=True,
        note="Nu sunt indicatori de performanță. p90 = valoarea depășită de 1 din 10 decizii. Înmatric. >10 zile lucr. % = înmatriculări admise fără amânare care au depășit 10 zile lucrătoare, august–noiembrie 2026; cifra națională de 81,3% (C41) privește doar noiembrie, când așteptarea era mai mare.")
    cm = pd.DataFrame(SPX["judete_lunar"]["rows"]); months = [m for m in sorted(cm.luna.unique()) if m >= "2025-12"]
    piv = cm[cm.luna.isin(months)].pivot(index="cod", columns="luna", values="mediana")
    nat = {r["luna"]: r["mediana"] for r in SPX["national_lunar"]["rows"]}
    names = {k: v["name"] for k, v in base.items()}
    head = "<th style='width:26mm'>Oficiul</th>" + "".join(f"<th>{m[2:4]}.{m[5:]}</th>" for m in months)
    body = "".join(f"<tr><td>{names.get(c, c)}</td>" + "".join(f'<td class="num">{ro(piv.loc[c, m], 1) if m in piv.columns and pd.notna(piv.loc[c, m]) else "—"}</td>' for m in months) + "</tr>"
                   for c in sorted(piv.index, key=lambda c: names.get(c, c)))
    body += "<tr><td><b>Național</b></td>" + "".join(f'<td class="num"><b>{ro(nat.get(m), 1)}</b></td>' for m in months) + "</tr>"
    b += sec("5", "Mediana lunară pe oficiu") + f'<div class="tcap"><b>Tabelul {BV.TN["n"] + 1}</b>Mediana așteptării (zile calendaristice) pe oficiu și luna deciziei, decembrie 2025–noiembrie 2026</div>' + \
        f'<table class="dt small"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table><div class="tnote">Sursă: stat_pack_ext.json → judete_lunar (finale stricte, 0 ≤ W &lt; 400; noiembrie = 1–20 nov.). Seria completă din ianuarie 2025, cu numărul de decizii, e în fișierul Excel. Distribuția pe etape din eșantionul portal nu se publică pe oficii: eșantionul e prea mic pe oficiu.</div>'
    BV.TN["n"] += 1
    return b, S


# ================================================================== VOLUME 6 · verification
def vol6(pg):
    BV.TN["n"] = 0; BV.FN["n"] = 0
    S = [("", "1", "Pe scurt", "1"), ("", "2", "Lanțul de verificare", "2"), ("", "3", "Recalculul independent", "3"),
         ("", "4", "Demonstrații formale (Lean)", "4"), ("", "5", "Afirmații retrase", "5"), ("", "6", "Registrul complet", "6"),
         ("", "7", "Revizuirea pe profiluri", "7"), ("", "8", "Cum reproduceți", "8")]
    b = cover("Verificare și încredere", "Cum a fost verificată fiecare cifră: sursa unică, registrul afirmațiilor, verificatorul automat, recalculul independent, demonstrațiile formale în Lean și revizuirea pe profiluri de cititori.",
              "Volumul 6", "<dt>Pentru cine</dt><dd>Pentru oricine vrea să verifice o cifră înainte s-o folosească.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    reg = list(REG.values()); n_pass = sum(r["status"] == "PASS" for r in reg); n_warn = sum(r["status"] == "WARN" for r in reg); n_fail = sum(r["status"] == "FAIL" for r in reg)
    b += sec("1", "Pe scurt") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        hl("Fiecare cifră publicată are un cod, o sursă, scriptul care o produce, amprenta datelor și o stare.") + f" Registrul are {len(reg)} de afirmații: {n_pass} PASS, {n_warn} WARN, {n_fail} retrase.",
        hl("O sesiune separată a reimplementat, cu cod propriu și pe aceleași date, cifrele observate direct; cincisprezece s-au confirmat, iar diferențele de definiție au fost corectate public.") + E("C07", "C32"),
        hl(f"Aritmetica și monotonia din spatele a {len(LEAN3['theorems'])} afirmații sunt verificate formal în Lean; Lean nu verifică datele și nici ipotezele modelului."),
        hl("Un verificator automat respinge orice cifră din text fără cod și orice citare a unei afirmații retrase.")]) + "</ul>"
    b += sec("2", "Lanțul de verificare") + '<ol class="find">' + "".join(f"<li>{x}</li>" for x in [
        "<b>Date brute</b>: arhiva BERC (amprentă SHA-256 publicată), eșantionul myportal, nota MJ.",
        "<b>Sursa unică</b>: <code>LOCKED_CONSTANTS.json</code>. Fiecare cifră se calculează o singură dată; o nouă rulare nu are voie să schimbe cifrele existente.",
        "<b>Registrul afirmațiilor</b>: valorile sunt citite automat din ieșirile scripturilor, nu scrise de mână.",
        "<b>Rapoartele</b>: textul citește cifrele din registru, prin cod. O cifră retrasă oprește construcția raportului.",
        "<b>Verificatorul de cifre</b>: orice număr din text fără cod e o eroare.",
        "<b>Recalcul independent și Lean</b>: alte implementări și demonstrații formale verifică rezultatele cheie.",
        "<b>Revizuire pe profiluri</b>: cititori simulați cu profiluri diferite caută ce lipsește sau nu se înțelege."]) + "</ol>"
    b += sec("3", "Recalculul independent") + P(
        "O sesiune de lucru separată a scris propriul cod, fără să importe nimic din analiza noastră, a declarat dinainte toleranțele și a recalculat din aceeași arhivă cifrele de nivel A. Este o a doua implementare pe aceleași date, făcută tot cu un model AI într-o sesiune separată, nu o replicare pe date independente. " +
        "Cincisprezece cifre s-au confirmat. La patru, diferența venea din definiții; am adoptat definiția verificată și am publicat schimbarea:") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "Scăderea din august: împărțirea la zile lucrătoare legale, cu finale stricte, nu la zile cu decizii." + E("C07"),
        "Pasul din 27 aprilie: ponderea pe toate deciziile, nu mediana județelor." + E("C32"),
        "Cererile online după program: valoarea depinde de fereastra orară; trecută pe WARN." + E("C36"),
        "Proiectul OUG, doar Art. III: câștigul se măsoară pe aceleași simulări, nu ca diferență între două mediane." + E("C44")]) + "</ul>"
    b += sub("3.1", "Replicarea independentă din datele brute") + P(
        "La final, un analist separat a primit doar datele brute (arhiva BERC, eșantionul din portal, cifrele Ministerului, compilația de presă) și raportul. Nu a avut voie să citească nimic din codul sau fișierele noastre. A refăcut cifrele-cheie cu propriul cod și le-a marcat confirmate, diferite sau neverificabile. " +
        hl("Rezultatul: " + V("C114").split(" din ")[0].replace(" / ", " confirmate / ", 1).replace(" / ", " diferite / ", 1) + " neverificabile, din " + V("C114").split(" din ")[1] + " afirmații verificate.") + E("C114")) +         '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "<b>Ultima zi din arhivă (20 noiembrie) e incompletă.</b> Comparațiile pe aceeași perioadă se opresc acum la 19 noiembrie; creșterea față de 2025 e de circa 9%, nu de 6%." + E("C87", "C30"),
        "<b>Creșterea așteptării între mai și septembrie</b>: limita de jos susține „peste șapte ori”, nu „cel puțin opt”." + E("C05"),
        "<b>Intrările din octombrie</b> erau subestimate de eșantion (înmatriculările în curs nu apar); octombrie a fost aproape de ritmul de soluționare, doar noiembrie e clar sub el." + E("C99", "C100"),
        "<b>Pragul de trei zile lucrătoare</b> e valabil pentru aprilie–iunie 2026, nu după." + E("C101"),
        "<b>Testul prognozei</b> e un test în timp real; abaterea vine din întârzierea publicării, nu din model." + E("C70"),
        "<b>Respingerile</b> erau la un nivel similar și în 2025; creșterea față de vechea platformă nu e specifică crizei." + E("C39"),
        "<b>Sezonalitatea de vară</b> e mai plată în model decât în date; modelul e ușor pesimist pentru vara lui 2027." + E("C71"),
        "<b>Stocul din iunie 2028</b> e citat acum la aceeași dată ca în tabelele de prognoză." + E("C62")]) + "</ul>" + P(
        "Neverificabile pentru analist au fost cifrele care cer date pe care nu le-a avut: textul buletinelor PDF (ponderea CAEN), identificatorul firmei (redepunerile), cifrele interne ale Ministerului și textul legii. Raportul complet al replicării și scripturile analistului sunt păstrate împreună cu datele.")
    b += sec("4", "Demonstrații formale (Lean)") + P(
        "Lean este un asistent de demonstrații: un program care acceptă o afirmație matematică doar dacă fiecare pas al demonstrației e verificat mecanic. " +
        hl("Lean nu verifică dacă datele sunt corecte; verifică faptul că, din datele declarate, concluzia rezultă fără greșeală.") +
        " Am folosit Lean pentru două tipuri de afirmații: proprietăți generale ale modelului de coadă (de exemplu, mai multă capacitate nu poate lungi coada) și verificări aritmetice ale cifrelor publicate, generate automat din aceleași fișiere ca registrul.")
    def reg_status(cl):
        return " / ".join(f'{c.strip()}: {REG[c.strip()]["status"]}' for c in cl.split(",") if c.strip() in REG)
    rows = "".join(f'<tr><td><code>{t["theorem"].split(".")[-1]}</code></td><td>{t["meaning"]}</td><td>{"aritmetica verificată" if "VERIFICAT" in t["status"] else t["status"]}</td><td>{reg_status(t["claims"])}</td></tr>' for t in LEAN3["theorems"])
    b += f'<div class="tcap"><b>Tabelul 1</b>Verificări formale noi, legate de afirmațiile din registru</div><table class="dt"><thead><tr><th style="width:42mm">Teorema</th><th>Ce garantează, în cuvinte</th><th style="width:20mm">Lean</th><th style="width:26mm">Starea afirmației în registru</th></tr></thead><tbody>{rows}</tbody></table>'
    b += f'<div class="tnote">Generate de <code>gen_lean_v3_witnesses.py</code> din aceleași fișiere ca registrul; construite cu <code>lake build</code> ({LEAN3["lean_toolchain"]}). Dacă o actualizare a datelor ar schimba o cifră publicată astfel încât afirmația să nu mai fie adevărată, construcția ar eșua.</div>'
    TH = [t for t in csv.DictReader(open(BV.HERE / "audit_data" / "lean4_theorems_summary.csv", encoding="utf-8"))
          if t["id"] in ("T1a", "T1b", "T1c", "T1d", "T1e", "T7a", "T7b", "T11c")]
    _npdf = re.search(r"descărcate (\d+) de buletine PDF din 2026; eșantionul analizat cuprinde (\d+)", REG["C50"]["rezerva_obligatorie"])
    for t in TH:                                     # collected vs analysed PDF bulletins, stated explicitly (C50)
        if t["id"] == "T11c":
            t["claim_proved"] = re.sub(r"pentru cele \d+ de buletine PDF",
                                       f"pentru eșantionul de {_npdf.group(2)} de buletine PDF analizate (din {_npdf.group(1)} descărcate pentru 2026)", t["claim_proved"])
    TH.append(dict(id="T13a–e", theorem="OnrcProofs.TandemBottleneck", claim_proved="Mecanismul în tandem: capacitatea sistemului e minimul celor două etape; optimul mutării de personal și pragul de câștig zero (C35)."))
    note = {"T5c": "contrazice o afirmație retrasă («supercritic»)", "T2": "teoremă generală; nu e folosită ca afirmație publică"}
    rows2 = "".join(f'<tr><td>{t["id"]}</td><td><code>{t["theorem"].split(".")[-1]}</code></td><td>{t["claim_proved"]}{(" — " + note[t["id"]]) if t["id"] in note else ""}</td></tr>' for t in TH)
    b += f'<div class="tcap"><b>Tabelul 2</b>Teoremele generale folosite de raport (din suita analizei; 0 demonstrații deschise)</div><table class="dt small"><thead><tr><th style="width:9mm">ID</th><th style="width:52mm">Teorema</th><th>Ce demonstrează</th></tr></thead><tbody>{rows2}</tbody></table>'
    b += P(hl("Ce NU verifică Lean:") + " corectitudinea datelor, ipotezele modelului (ordinea strict cronologică a dosarelor, un sistem stabil, distribuțiile de intrare) și interpretarea. O teoremă verificată nu face o afirmație WARN să devină sigură: starea din registru rămâne cea care contează. Unele teoreme din suita veche presupun o coadă strict cronologică, pe care datele o contrazic parțial.")
    b += P("Cea mai importantă pentru cititor este monotonia cozii: dacă intrările cresc sau capacitatea scade, coada nu poate deveni mai scurtă. De aceea grila de risc are mereu aceeași direcție, iar Lean verifică acest lucru și pe toate cele 36 de celule calculate.")
    b += sec("5", "Afirmații retrase") + P("Afirmațiile retrase rămân în registru, fără valori, ca să se vadă ce s-a corectat:") + '<ul class="find">' + "".join(
        f"<li><b>{r['id']}</b>: {r['rezerva_obligatorie'].split(':')[0]}</li>" for r in reg if r["status"] == "FAIL") + "</ul>"
    rows3 = "".join(f'<tr><td>{r["id"]}</td><td>{r["level"]}</td><td>{r["status"]}</td><td>{r["source"]}</td><td><code>{r["script"]}</code></td><td><code>{r["data_sha256"][:12]}…</code></td></tr>'
                    for r in sorted(reg, key=lambda r: int(r["id"][1:])) if r["status"] != "FAIL")
    b += sec("6", "Registrul complet") + P("Valorile și rezervele fiecărei afirmații sunt în Volumul 1, Anexa B, și în <code>claims_registry.csv</code>. Aici: proveniența.") + \
        f'<table class="dt small"><thead><tr><th style="width:9mm">ID</th><th style="width:10mm">Nivel</th><th style="width:11mm">Stare</th><th>Sursă</th><th style="width:44mm">Script</th><th style="width:22mm">Amprentă</th></tr></thead><tbody>{rows3}</tbody></table>'
    rv = (IA / "out" / "persona_review.json")
    if rv.exists():
        R = json.loads(rv.read_text(encoding="utf-8"))
        b += sec("7", "Revizuirea pe profiluri") + P(R["intro"]) + P("După revizuire, autorul a decis să publice clasamente pe oficii (Volumul 5), cu rezervele de citire: oficiul din date e cel de depunere, iar clasamentul nu e o notă pentru personal.") + "".join(
            f'<div class="issue"><h3>{p["persona"]}</h3><dl><dt>Ce a criticat</dt><dd>{p["critique"]}</dd><dt>Ce a sărit</dt><dd>{p["skipped"]}</dd><dt>Ce am schimbat</dt><dd>{p["changed"]}</dd></dl></div>'
            for p in R["personas"])
    else:
        b += sec("7", "Revizuirea pe profiluri") + P("Revizuirea pe profiluri este în curs.")
    b += sec("8", "Cum reproduceți") + '<div class="formula">' + "<br>".join([
        r"venv\Scripts\python -X utf8 independent_audit\reconcile_sources.py", r"venv\Scripts\python -X utf8 independent_audit\stat_pack.py",
        r"venv\Scripts\python -X utf8 independent_audit\stat_pack_ext.py", r"venv\Scripts\python -X utf8 independent_audit\forecast_grid.py",
        r"venv\Scripts\python -X utf8 independent_audit\generate_claims_registry.py", r"venv\Scripts\python -X utf8 independent_audit\gen_lean_v3_witnesses.py",
        r"cd analysis\policy_paper_ro &amp;&amp; ..\..\venv\Scripts\python -X utf8 build_all_volumes.py"]) + "</div>"
    return b, S


VOLS = {"vol0": ("COADA DE LA REGISTRUL COMERȚULUI · FIȘE PE PROFIL", "Volumul 0", vol0, "Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil"),
        "vol4": ("COADA DE LA REGISTRUL COMERȚULUI · MUNCA DIN SPATELE COZII", "Volumul 4", vol4, "Raport_ONRC_Coada_2026-11_VOL4_Munca_din_spatele_cozii"),
        "vol5": ("COADA DE LA REGISTRUL COMERȚULUI · FIȘE PE JUDEȚE", "Volumul 5", vol5, "Raport_ONRC_Coada_2026-11_VOL5_Fise_pe_judete"),
        "vol6": ("COADA DE LA REGISTRUL COMERȚULUI · VERIFICARE ȘI ÎNCREDERE", "Volumul 6", vol6, "Raport_ONRC_Coada_2026-11_VOL6_Verificare")}
