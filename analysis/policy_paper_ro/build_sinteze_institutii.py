"""Șase sinteze executive (≈8–10 pagini A4) ale raportului «Coada de la Registrul Comerțului», câte una pe instituție,
fiecare încadrată de competențele legale ale instituției (independent_audit/out/stakeholders_legal.json, doar citări verificate).

Aceleași reguli ca raportul complet: fiecare cifră vine din claims_registry.csv prin V('Cxx') și se citează cu E('Cxx');
cifrele WARN poartă rezerva lor scurtă (cite()); cifrele FAIL nu apar. Stil Lab (BASE_CSS), tipărit cu Edge headless.

    ..\\..\\venv\\Scripts\\python.exe -X utf8 build_sinteze_institutii.py

Ieșire: analysis/raport_executiv_2026-11/sinteze_institutii/Sinteza_{MJ,MF_ANAF,MEDAT_ADR,Guvern,Parlament,ONRC}.pdf
        analysis/policy_paper_ro/sinteze_institutii/*.html (verificate cu lint_numbers.py înainte de tipărire)
"""
import re, subprocess, sys, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_raport_institutii as BRI          # V, E, hl, BASE_CSS, EXTRA_CSS, FOOT, compile_pdf, REG, HIRE_40, OCTNOV
import lab_styles as LS
import ai_annex
import book_style as BSV
from lab_styles import pulls

V, E, hl, REG = BRI.V, BRI.E, BRI.hl, BRI.REG
ROOT = HERE.parent.parent
DELIV = ROOT / "analysis" / "raport_executiv_2026-11"
OUT_HTML = HERE / "sinteze_institutii"
OUT_PDF = DELIV / "sinteze_institutii"
COMPLET = DELIV / "Raport_ONRC_Coada_2026-11_COMPLET.pdf"
PY = sys.executable
GITHUB = "https://github.com/Stefatorus/onrc-analiza-big-data-amanari"
DATE = "23.11.2026"

# ------------------------------------------------------------------ registry helpers
PR = lambda c: REG[c]["public_ro"]
v0 = lambda c: V(c).split(" (")[0]
G34 = re.search(r"aceleași simulări: (≈\d+) zile", REG["C43"]["rezerva_obligatorie"]).group(1)   # paired OUG gain (C43)
HIRE = BRI.HIRE_40[0].lower() + BRI.HIRE_40[1:]

# short caveat for every WARN claim used (nothing is published without its reserve)
CAV = {
    "C04": "valoare cenzurată: «cel puțin»", "C11": "se folosesc dosarele decise pe săptămână",
    "C36": "mărimea depinde de definiție; sensul e același", "C40": "«redepune» = orice cerere ulterioară de același tip",
    "C52": "scenariu fragil; cere excepții de la suspendarea angajărilor peste plafonul de 15%, deci probabil o derogare prin lege", "C53": "scenariu; efectele măsurilor sunt ipoteze",
    "C54": "scenariu foarte sensibil la ipoteze", "C55": "conversia în posturi e o ipoteză de model, nu o normă",
    "C58": "prognoză de model, nu măsurătoare", "C59": "prognoză condiționată de valurile de cereri anunțate",
    "C60": "prognoză; momentul vârfului variază între simulări", "C61": "ipoteze de livrare, nu măsurători",
    "C62": "unități de muncă, nu număr de cereri", "C63": "scenariu de model", "C65": "«≤3» = coada e practic goală",
    "C66": "scenariu de model", "C67": "unități de muncă, mediană pe simulări", "C68": "contrafactual: arată pârghia, nu ce e realizabil",
    "C72": "scenariu de model", "C94": "scenariu: dacă se confirmă cifrele publice despre CAEN", "C95": "efectul conversiei e o ipoteză de intrare",
    "C99": "estimare din eșantion, fără înmatriculările în curs", "C100": "estimare compatibilă cu cifrele MJ la circa ±10%",
    "C106": "interval de scenarii, nu măsurătoare", "C107": "interval de scenarii; presupune, fără sursă, că o parte din vânzările amânate se pierd definitiv",
    "C108": "indicator de sensibilitate; nu se înmulțește cu numărul de zile", "C109": "ipoteză fără sursă publică",
    "C110": "comparația cu bugetul nu e robustă", "C111": "scenariu cu parametri declarați; nu e contabilitate",
    "C112": "partea din stoc e o expunere, nu un cost produs", "C113": "scenariul central; 2026 e parțial",
    "C116": "parametrii fără bază rămân ipoteze declarate",
    "C122": "interval de simulare de 95%, condiționat de ipoteze; față de o coadă normală, de 3 zile; extrapolat dincolo de așteptările pe care s-a estimat efectul",
    "C123": "valabil doar dacă veniturile se recuperează", "C124": "limită de sus, nu prognoză; componenta persistentă are un interval foarte larg și semn nedeterminat", "C125": "depinde de scenariul de măsuri",
    "C127": "clasificare automată verificată pe un eșantion; ponderile nu se adună", "C128": "clasificare automată; ponderile nu se adună",
    "C129": "clasificare automată; ponderile nu se adună",
    "C139": "«evitabil» e evaluarea autorului, asistată de AI, neconfirmată de ONRC",
    "C140": "un singur evaluator, un model AI", "C141": "plafon: presupune că verificarea prinde tot ce e evitabil; o parte din verificări poate exista deja în sistemul ONRC",
    "C145": "din textul unui eșantion de încheieri", "C147": "eșantion etichetat de un model AI; contează direcția, nu valoarea exactă",
    "C148": "clasificare automată; la înmatriculări eșantion mic", "C149": "eșantion mic",
    "C150": "«evitabil» e evaluarea autorului, asistată de AI, neconfirmată de ONRC",
}


def cite(*ids):
    """E() plus the short reserve of every WARN claim among ids (raises if a WARN claim has no reserve defined)."""
    cav = []
    for i in ids:
        if REG[i]["status"] == "WARN":
            assert i in CAV, f"{i} is WARN and has no caveat defined"
            if CAV[i] not in cav:
                cav.append(CAV[i])
    return E(*ids) + (f' <span class="cav">({"; ".join(cav)})</span>' if cav else "")


def tiles(items):
    """items: (number, label, ids, accent)"""
    return pulls([(n, l, cite(*ids), a) for n, l, ids, a in items])


def W(a, b, c):
    return (f'<p><b>Ce arată.</b> {a}</p><p><b>Pentru proiectul de OUG.</b> {b}</p><p><b>Impact.</b> {c}</p>')


def card(d, svg, title, intro, take):
    """Full-width chart card: title, three-line reading above, the chart, a highlighted takeaway with codes."""
    LS.FIG_DIR = str(HERE / d)
    try:
        code = LS.load_inline_svg(svg, svg.split(".")[0] + "_sz")
    finally:
        LS.FIG_DIR = str(HERE / "figures_institutii")
    return (f'<div class="ec"><div class="ect">{title}</div><div class="eci">{intro}</div>{code}'
            f'<div class="ecc">{take}</div></div>')


def H(text, ids, extra=""):
    """highlighted registry sentence + codes (with reserves)"""
    return hl(text) + extra + cite(*ids)


# ------------------------------------------------------------------ shared cards
def card_prognoza():
    return card("figures_institutii", "fi12_prognoza.svg", "Ce prognozăm: fără măsuri noi, așteptarea crește puternic în 2027",
                W("Câte zile ar aștepta un dosar depus în fiecare săptămână, până în iunie 2028, dacă nu se schimbă nimic. Linia e mijlocul simulărilor; banda cuprinde 8 din 10 variante. "
                  "Vârful, în cazul central: " + V("C60") + " zile." + cite("C60"),
                  "Cu proiectul, așteptarea din iunie 2028 rămâne de ordinul a trei luni; câștigul median, pe aceleași simulări, e de circa " + G34.lstrip("≈") + " de zile." + E("C43") +
                  " Valul de actualizări CAEN de la începutul lui 2027, cea mai mare sursă de risc, nu e tratat direct în textul proiectului." + cite("C68"),
                  PR("C108") + cite("C108")),
                H(PR("C59"), ["C59", "C60"]))


def card_pachete():
    return card("figures_institutii", "fi21_pachete.svg", "Ce schimbă fiecare măsură: așteptarea în iunie 2028, pe pachete",
                W("Cinci variante pentru iunie 2028: fără măsuri noi, proiectul de OUG și trei pachete mai largi. Punctul e mijlocul simulărilor, bara e intervalul; «≤3» înseamnă coadă practic goală.",
                  "Transferul unor acte administrative (Art. III) aduce doar " + V("C44").replace("câștig ", "un câștig de ") + "; efectul vine din capacitatea suplimentară." + E("C44") +
                  " Conversia automată CAEN 1-la-1 și eșalonarea, fără personal nou: " + V("C53") + " zile." + cite("C53") +
                  " OUG extins plus ocuparea a 40% din posturile vacante finanțate: " + V("C52") + " zile; " + HIRE + cite("C52", "C153"),
                  "Pachetul minim realist (OUG prelungit, conversie CAEN, eșalonare, triaj): " + V("C54") + " zile, cu un interval larg." + cite("C54")),
                H(PR("C54"), ["C54", "C52", "C153"]))


def card_schema():
    return card("figures_institutii", "fi24_doua_cozi_schema.svg", "Cum circulă un dosar: două cozi, una după alta",
                W("Drumul unei cereri: coada de operare (preluare și verificare formală), apoi coada registratorului (decizia). Cifrele: stocul oficial la 6 noiembrie, cererile noi pe zi și deciziile finale pe zi." +
                  E("C28", "C29") + cite("C99") + E("C01"),
                  "Proiectul aduce consilieri juridici desemnați la soluționare. Dacă vin din operare, mutarea ajută doar până la un prag: " + V("C35") + "." + E("C35"),
                  "Cu cele două cozi aproape egale, o decizie de personal se judecă pe tot drumul dosarului, nu pe o singură etapă." + E("C56")),
                H(PR("C29"), ["C28", "C29"]))


def card_tandem():
    return card("figures_institutii", "fi06_tandem.svg", "Cele două cozi la două date oficiale, la o săptămână distanță",
                W(PR("C33") + E("C33"), PR("C56") + E("C56"), PR("C34") + E("C34")),
                H("Când intrările sunt la nivelul din august–octombrie, doar întărirea ambelor etape deodată reduce stocul total; o singură etapă întărită mută blocajul. În noiembrie, cu intrări mai mici, stocul a scăzut încet.", ["C56", "C29", "C100"]))


def card_canib():
    return card("figures_institutii", "fi10_canibalizare.svg", "Cât ajută mutarea oamenilor de la o coadă la alta",
                W("Producția totală, după câte dosare pe zi preiau la soluționare oamenii mutați din operare.",
                  "Mutarea ajută până la un optim, iar la un prag câștigul dispare: " + V("C35") + "." + E("C35") +
                  " Dacă consilierii juridici desemnați vin din alte activități ale ONRC sau din posturi ocupate prin concurs, plafonul dispare.",
                  "De publicat: câți dintre consilierii juridici eligibili lucrează azi la operare. Fără această cifră nu se poate ști dacă desemnarea ajută sau doar mută coada."),
                H(PR("C35"), ["C35"], ' <span class="cav">(mecanism de model, condiționat de ipoteza 1:1; nu e textul OUG)</span>'))


def card_grila():
    return card("figures_institutii", "fi15_grila.svg", "Cât contează viteza: cererile față de capacitate",
                W("Așteptarea din iunie 2028 dacă cererile (rânduri) și capacitatea de soluționare (coloane) se abat de la scenariul central; stânga: cazul central, dreapta: varianta nefavorabilă.",
                  "Capacitatea adăugată contează doar dacă cresc ambele etape: luată din operare, are o limită." + E("C35", "C56"),
                  PR("C65") + cite("C65")),
                H(PR("C63"), ["C63"]))


def card_caen():
    return card("figures_institutii", "fi22_caen.svg", "Riscul valului CAEN și efectul conversiei automate",
                W("Așteptarea din iunie 2027 dacă firmele depun în masă actualizările CAEN înainte de sfârșitul perioadei de tranziție (roșu) și dacă codurile simple sunt convertite automat (verde).",
                  "Textul proiectului nu tratează direct valul CAEN. Perioada de tranziție se stabilește prin hotărâre a Guvernului (HG nr. 656/1997, art. 5^1); după calculul nostru, se încheie la 1 aprilie 2027. Conversia automată, fără modificarea actului constitutiv, cere însă o normă de rang legal, pe care o poate cuprinde chiar OUG." + E("C152"),
                  PR("C95") + cite("C95")),
                H(PR("C94"), ["C94"]))


def card_oug():
    return card("figures_institutii", "fi09_oug.svg", "Proiectul de OUG în modelul verificat: iunie 2028",
                W("Așteptarea estimată în iunie 2028 în trei variante: fără măsuri noi, doar Art. III și proiectul complet. Punctul e mijlocul simulărilor, bara e intervalul p10–p90.",
                  "Câștigul se măsoară pe aceleași simulări: circa " + G34.lstrip("≈") + " de zile pentru proiectul complet; Art. III: " + V("C44") + ". Punctele din grafic sunt medianele fiecărei variante, calculate separat: diferența dintre ele nu e câștigul." + E("C43", "C44"),
                  PR("C61") + cite("C61")),
                H(PR("C43"), ["C42", "C43"]))


def card_cost():
    return card("figures_impact", "i01_cost_lunar.svg", "Costul lunar al întârzierilor, pentru economie și buget",
                W("Costul economic (sus) și încasările bugetare afectate (jos), lună de lună, în scenariul fundamentat; liniile verticale dau intervalul prudent–tensionat.",
                  "Proiectul de OUG costă " + V("C83") + "." + E("C83") + " " + PR("C110") + cite("C110"),
                  "August–18 noiembrie 2026: " + V("C106") + " milioane de lei (prudent / central / tensionat)." + cite("C106")),
                H(PR("C111"), ["C111"]))


def card_venituri():
    return card("figures_impact", "i07_risc_venituri_2027.svg", "Venituri care nu intră în bugetul anului 2027 din cauza cozii",
                W("Pe trimestre ale anului 2027, veniturile bugetare care nu intră în bugetul anului din cauza cozii, fără măsuri noi și cu un pachet realist de măsuri; liniile: intervalul de simulare de 95% (percentilele 2,5–97,5 ale variantelor simulate)." + E("C122"),
                  "Proiectul de OUG costă " + V("C83") + "." + E("C83") + " " + PR("C125") + cite("C125"),
                  PR("C123") + cite("C123") + " " + PR("C124") + cite("C124")),
                H(PR("C122"), ["C122"]))


def card_cauzal():
    return card("figures_impact", "i06_efect_cauzal.svg", "Efectul unei zile de așteptare asupra firmelor noi",
                W(PR("C119") + E("C119"),
                  "Fiecare zi câștigată adaugă la primul an al firmelor noi o parte din vânzările și taxele lor." + E("C121"),
                  PR("C121") + E("C121")),
                H(PR("C120"), ["C120"]))


def card_amanari():
    return card("figures_impact", "i08_motive_amanare.svg", "De ce se amână dosarele și ce se poate automatiza",
                W("Motivele amânărilor din 19 octombrie–18 noiembrie 2026 și nivelul de automatizare al soluției: reguli fixe, AI, AI avansat, judecata registratorului. " + PR("C82") + E("C82"),
                  "Textul proiectului nu tratează amânările. Verificările la depunere țin de ONRC, cu sprijinul ADR; cele care interoghează alte registre cer protocoale, Platforma națională de interoperabilitate și o evaluare de impact privind protecția datelor.",
                  PR("C141") + cite("C141")),
                H(PR("C143"), ["C143"]))


def card_respingeri():
    return card("figures_impact", "i10_motive_respingere.svg", "Respingerile vin aproape toate din amânări nerezolvate",
                W("Ce a precedat respingerile din 19 octombrie–18 noiembrie 2026 și cauzele lor, pe eșantionul verificat.",
                  PR("C146") + E("C146"),
                  PR("C103") + E("C103")),
                H(PR("C144"), ["C144"], " " + PR("C150") + cite("C150")))


# ------------------------------------------------------------------ institutions
def para(*xs):
    return "".join(f"<p>{x}</p>" for x in xs)


def MJ():
    asks = [
        ("Amendați proiectul de OUG: capacitate pe ambele etape",
         "Art. I desemnează consilierii juridici specialiști ai ONRC ca registratori, cu acordul lor scris, până la 8 ianuarie 2028: ca această capacitate să ajungă atât la operare, cât și la soluționare, cu o derogare pentru ocuparea posturilor vacante finanțate ale ONRC și un termen de evaluare a efectelor; nota de fundamentare completată cu fișa financiară detaliată.",
         "Legea nr. 52/2003, art. 7 alin. (2), (9); HG nr. 592/2024, art. 6 pct. II.3; Legea nr. 141/2025, art. XXII",
         PR("C56") + E("C56", "C43")),
        ("Introduceți în proiectul de OUG conversia automată CAEN „1-la-1”",
         "Actualizarea din oficiu a codurilor CAEN cu un singur corespondent în Rev. 3, fără modificarea actului constitutiv și fără cerere: cere o normă de rang legal, iar OUG e vehiculul potrivit; perioada de tranziție se corelează separat, prin HG.",
         "HG nr. 592/2024, art. 6 pct. II.3 și I.1; HG nr. 656/1997, art. 5^1; HP nr. 4/2026, anexa 2 (Programul de guvernare)", PR("C95") + cite("C94", "C95")),
        ("Aprobați excepțiile de la suspendarea concursurilor",
         "Ca ordonator principal de credite, aprobați pentru ONRC excepțiile de la suspendarea ocupării posturilor vacante din 2026, pentru etapele în care se formează coada; concursurile le organizează directorul general.",
         "Legea nr. 141/2025, art. XXII alin. (2), (4), (6); Legea nr. 265/2022, art. 22 alin. (5)",
         PR("C153") + E("C153")),
        ("Alocați posturile existente etapelor-gâtuire",
         "Modificați prin ordin statul de funcții al ONRC, în limita numărului maxim de posturi, astfel încât posturile să ajungă la operare și la soluționare.",
         "Legea nr. 265/2022, art. 22 alin. (1)–(2); ROF ONRC, art. 6 alin. (7)–(8)",
         PR("C51") + E("C51")),
        ("Fundamentați creditele pentru personal și IT",
         "Cereți Ministerului Finanțelor creditele necesare pentru personal și IT, la rectificare sau în bugetul pe 2027.",
         "HG nr. 592/2024, art. 6 pct. VI.5", PR("C122") + cite("C122")),
        ("Introduceți în ROF publicarea lunară a indicatorilor",
         "Stocul pe etape, intrările, deciziile finale, amânările, așteptarea mediană pe tipuri de cereri și personalul activ pe etape.",
         "Legea nr. 265/2022, art. 22 alin. (1); HG nr. 592/2024, art. 6 pct. V.6; Legea nr. 544/2001, art. 5", ""),
    ]
    an = []
    an.append('<h2>Cât se așteaptă și ce cere legea</h2>' + tiles([
        (V("C15") + " zile", "firmele noi aprobate în 16–20 noiembrie", ["C15"], False),
        (V("C17") + " zile", "așteptarea obișnuită pe vechea platformă", ["C17"], False),
        (V("C31").split("→ ")[1], "dosare soluționate într-o zi lucrătoare în criză, față de " + V("C31").split(" →")[0], ["C31"], True),
        (V("C41").split(" ")[0], "firme noi admise fără amânare care au așteptat peste 10 zile lucrătoare", ["C41"], False)]) +
        para("Legea cere o decizie într-o zi lucrătoare de la înregistrare (Legea nr. 265/2022, art. 105 alin. (1) și art. 109)." + E("C23") + " " + hl(PR("C31")) + E("C31"),
             PR("C41") + E("C41") + " Raportul nu califică întârzierile drept nelegale și nu numără „încălcări”: datele nu disting constituirile online cu model standard.",
             "Producția nu s-a prăbușit: " + PR("C87") + E("C87") + " " + hl("Coada vine din cereri: " + PR("C47")) + E("C47")))
    an.append('<h2>Cele două cozi: unde trebuie să ajungă oamenii</h2>' +
              para(hl("Fiecare dosar trece întâi prin operare, apoi la registrator, iar cele două stocuri sunt aproape egale.") + E("C29") +
                   " De aceea, fiecare decizie de personal a ministerului (excepții, stat de funcții, desemnări prin OUG) se judecă pe ambele etape.") +
              card_schema() + card_tandem() + card_canib())
    an.append('<h2>Personalul: ce poate și ce nu poate face ministerul</h2>' + tiles([
        (V("C51").split("→ ")[1].split(" ")[0], "posturi finanțate, dar neocupate", ["C51"], True),
        (v0("C52") + " zile", "iunie 2028, OUG extins + 40% din posturile vacante (circa " + re.search(r"circa (\d+) de posturi", PR("C52")).group(1) + ")", ["C52", "C51"], False),
        (v0("C54") + " zile", "iunie 2028, pachetul minim realist", ["C54"], False),
        (V("C55").split("(")[1].rstrip(")"), "doar prin personal, pentru a reveni la circa trei zile (estimare de model)", ["C55"], False)]) +
        para(PR("C51") + E("C51") + " " + PR("C52") + cite("C52"),
             hl(PR("C153")) + E("C153") + " " + REG["C153"]["rezerva_obligatorie"].split("Regimul pentru 2027 nu a fost verificat. ")[1] + " Regimul pentru 2027 nu a fost verificat." + E("C153", "C52"),
             PR("C55") + cite("C55")) + card_grila())
    return dict(
        key="MJ", name="Ministerul Justiției", head="MINISTERUL JUSTIȚIEI", forl="Ministerul Justiției",
        decide=("<b>Două decizii pentru această săptămână, înainte de încheierea consultării publice.</b> "
                "<b>1.</b> Amendarea art. I, astfel încât desemnările să întărească ambele etape, operarea și soluționarea, cu o derogare pentru posturile vacante finanțate (cererea 1): "
                "proiectul singur câștigă circa " + G34.lstrip("≈") + " de zile în iunie 2028, iar întărirea unei singure etape mută blocajul." + E("C43", "C56") +
                " <b>2.</b> Conversia automată CAEN „1-la-1” în textul OUG (cererea 2): în scenariile cu val CAEN mare, reduce așteptarea din iunie 2027 la mai puțin de jumătate." + cite("C95") +
                " Celelalte cereri pot urma după adoptare."),
        verdict="Ministerul aprobă organizarea și statul de funcții ale Registrului, îi fundamentează bugetul și inițiază proiectul de OUG. Datele arată că măsurile au efect doar dacă ajung la ambele etape ale dosarului.",
        why="ONRC funcționează în subordinea Ministerului Justiției, care îi aprobă organizarea și statul de funcții, îi asigură finanțarea și inițiază actele normative din domeniul registrului comerțului, inclusiv proiectul de OUG aflat în consultare (Legea nr. 265/2022, art. 19 alin. (1); HG nr. 592/2024, art. 6 pct. V.6 și art. 40).",
        asks=asks,
        codec="Bugetul: Ministerul Finanțelor, Guvernul și Parlamentul. Numărul maxim de posturi: Guvernul, prin HG. OUG: Guvernul, apoi Parlamentul, prin lege de aprobare. ROF-ul și statele de funcții se aprobă doar prin ordinul ministrului.",
        analysis="".join(an),
        limit="Regimul concursurilor pentru 2027 nu a fost verificat; câte posturi acoperă excepția din 2026 depinde de o cifră pe care o are Ministerul Justiției." + E("C153"),
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("1 · Pentru ministru", "Fișa pentru ministru și decidenți"),
                 ("Cap. 2", "Cât se așteaptă acum"), ("Cap. 4", "Cele două cozi"), ("Cap. 7", "Prognoza până în 2028"),
                 ("Cap. 9", "Proiectul de OUG, pe articole"), ("Cap. 10", "Ce se poate face: pachete de măsuri"),
                 ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


def MF():
    asks = [
        ("MF · Includeți în previziunea pentru 2027 veniturile ținute în afara anului de coadă",
         "În previziunea veniturilor și în analiza riscurilor fiscale din strategia fiscal-bugetară.",
         "Legea nr. 69/2010, art. 29 alin. (2) lit. d); Legea nr. 500/2002, art. 19 lit. b^1)", PR("C122") + cite("C122")),
        ("MF · Verificați fișa financiară a proiectului de OUG",
         "La avizare, confirmați sursa de finanțare și luați în calcul costul de a nu acționa, pe baza scenariilor din raport.",
         "Legea nr. 500/2002, art. 15; Legea nr. 69/2010, art. 15 alin. (2); Constituția, art. 138 alin. (5)", PR("C83") + E("C83")),
        ("MF · Analizați creditele pentru posturile ONRC și pentru IT",
         "La cererea fundamentată a Ministerului Justiției, în bugetul pe 2027 sau la rectificare; cereți rapoarte periodice despre stoc și capacitate.",
         "HG nr. 34/2009, art. 3 alin. (1) pct. 6; Legea nr. 500/2002, art. 19 lit. a) și e)", PR("C125") + cite("C125")),
        ("MF · Inițiați modificarea art. 92 din Codul de procedură fiscală",
         "O firmă cu o cerere privind sediul social aflată în curs la ONRC să nu fie inactivată pe temeiul art. 92 alin. (1) lit. g), iar termenul până la dizolvare să nu curgă cât timp cererea așteaptă.",
         "HG nr. 34/2009, art. 3 alin. (1) pct. 3; Codul de procedură fiscală, art. 92", ""),
        ("ANAF · Verificați cererile în curs înainte de inactivare",
         "Completați procedura aprobată prin ordin: înainte de inactivarea pe lit. g), organul fiscal verifică dacă la registrul comerțului există o cerere în curs privind sediul; un protocol de date cu ONRC.",
         "Codul de procedură fiscală, art. 92 alin. (4), (14) și art. 91 alin. (2); HG nr. 520/2013, art. 7 lit. A pct. 9 și 41; Legea nr. 265/2022, art. 27 alin. (4)", PR("C37") + E("C37")),
        ("ANAF · Publicați lunar inactivările pe lit. g) și reactivările",
         "Agregat și pe județe; dacă soluția cere o lege, transmiteți propunerea Ministerului Finanțelor.",
         "Codul de procedură fiscală, art. 92 alin. (10)–(11); Legea nr. 544/2001, art. 5; HG nr. 520/2013, art. 7 lit. A pct. 21", ""),
    ]
    an = []
    an.append('<h2>Cât costă coada: economia și bugetul</h2>' + tiles([
        (BRI.OCTNOV, "mil. lei pe lună, cost economic în oct.–nov. 2026 (central)", ["C111"], True),
        (V("C106").split(" / ")[1], "mil. lei, cost economic aug.–18 nov. 2026 (central; interval " + V("C106").split(" / ")[0] + "–" + V("C106").split(" / ")[2] + ")", ["C106"], False),
        (V("C107").split(" / ")[1], "mil. lei, încasări bugetare afectate, aceeași perioadă (central; depinde de ipoteze fără sursă)", ["C107"], False),
        (v0("C108").split(" ")[0], "mil. lei în economie pentru fiecare zi în plus cu stocul actual", ["C108"], False)]) +
        para(hl("Zilele de întârziere sunt măsurate; transformarea lor în lei e un interval de scenarii.") + " " + PR("C105") + E("C105") + " " + PR("C116") + cite("C116"),
             PR("C109") + cite("C109") + " " + PR("C112") + cite("C112"),
             PR("C113") + cite("C113") + " " + PR("C115") + E("C115"),
             hl(PR("C108")) + cite("C108") + " Proiectul de OUG costă " + V("C83") + "." + E("C83")) + card_cost())
    an.append('<h2>Riscul pentru veniturile din 2027</h2>' + tiles([
        (v0("C122"), "mil. lei care nu intră în bugetul anului 2027 din cauza cozii (interval de simulare de 95%: " + V("C122").split("(")[1].split(")")[0] + ")", ["C122"], True),
        (V("C124").split(" (")[0], "mil. lei dacă nimic nu se recuperează (limită de sus; interval de simulare de 95%: " + V("C124").split(" / ")[0].split("(")[1].rstrip(")") + "); componenta persistentă: " + V("C124").split(" / ")[1].split(" (")[0] + " (interval de simulare de 95%: " + V("C124").split(" / ")[1].split("(")[1].rstrip(")").replace("-", "−") + "; pozitiv = pierdere)", ["C124"], False),
        (v0("C123"), "mil. lei, costul de finanțare, doar dacă veniturile se recuperează", ["C123"], False),
        (v0("C125"), "mil. lei evitate de un pachet realist (interval de simulare de 95%: " + V("C125").split("(")[1].rstrip(")") + ")", ["C125"], False)]) +
        para(hl(PR("C122")) + cite("C122") + " " + PR("C124") + cite("C124"),
             "Veniturile amânate din cererile depuse înainte de decembrie 2026 nu sunt scăzute. "
             "Din bilanțurile firmelor noi vin impozitul direct și angajații; TVA și toată partea modificărilor sunt ipoteze." + cite("C122"),
             PR("C119") + E("C119") + " " + PR("C121") + E("C121") + " " + hl(PR("C120")) + E("C120")) + card_venituri() + card_cauzal())
    an.append('<h2>Inactivarea fiscală: legătura cu ANAF</h2>' +
              para("Codul de procedură fiscală declară inactivă firma al cărei drept de folosință asupra sediului a expirat (art. 92 alin. (1) lit. g) și alin. (3)); fără reactivare într-un an, urmează dizolvarea (alin. (4^1)–(4^2)). " +
                   hl("Când prelungirea sau schimbarea sediului așteaptă la Registru, firma poate ajunge inactivă pentru o întârziere care nu îi aparține."),
                   PR("C14") + E("C14") + " " + PR("C37") + E("C37"),
                   "Raportul nu cuantifică firmele afectate și nici inactivările rezultate; în costul economic, canalul inactivării se sprijină pe ipoteze declarate." + cite("C116") +
                   " Ce le-ar măsura: o legare controlată, pseudonimizată, ONRC–ANAF, cu data notificării, a inactivării și a reactivării pentru firmele cu cereri de sediu în așteptare."))
    return dict(
        key="MF_ANAF", name="Ministerul Finanțelor și ANAF", head="MINISTERUL FINANȚELOR ȘI ANAF", forl="Ministerul Finanțelor și ANAF",
        verdict="Coada are un preț în bani: în economie și la buget. Pentru 2027, coada ține în afara bugetului anului venituri de ordinul sutelor de milioane de lei; o parte se poate recupera ulterior, dar datele nu exclud o pierdere durabilă. Pentru ANAF, riscul e ca o firmă să devină inactivă pentru o cerere de sediu care încă așteaptă.",
        why="Ministerul Finanțelor elaborează previziunile de venituri, legile bugetare și de rectificare, verifică fișele financiare și analizează riscurile fiscale (Legea nr. 500/2002, art. 15 și art. 19; Legea nr. 69/2010, art. 29). ANAF aplică procedura de inactivare fiscală, inclusiv pentru sediul expirat (Codul de procedură fiscală, art. 92).",
        asks=asks,
        codec="Bugetul și rectificarea: Guvernul (adoptă proiectul) și Parlamentul (lege). Ordinul de aplicare a art. 92: ANAF singură. Modificarea art. 92: MF (inițiator), Guvernul și Parlamentul. Protocolul de date: ANAF și ONRC (și ADR, pentru platforma de interoperabilitate).",
        analysis="".join(an),
        limit="Circa trei sferturi din costul central depind de o ipoteză nemăsurată (costul unei modificări blocate); numărul inactivărilor legate de coadă nu e cunoscut." + cite("C109"),
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("8 · Pentru Ministerul Finanțelor", "Fișa pentru MF și ANAF"),
                 ("Partea 3", "Impactul economic și bugetar, lună de lună"), ("8 · Estimarea econometrică", "Experimentul natural și riscul pentru veniturile din 2027"),
                 ("6 · Pe ce se sprijină", "Fiecare parametru: sursă oficială, măsurat sau ipoteză"), ("Cap. 7", "Prognoza până în 2028"),
                 ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


def MEDAT():
    asks = [
        ("MEDAT · Includeți costul pentru IMM-uri în evaluarea de impact",
         "Costul întârzierilor pentru antreprenori, în evaluarea măsurilor privind ONRC, și consultarea asociațiilor mediului de afaceri asupra proiectului de OUG.",
         "HG nr. 189/2025, art. 4 lit. F lit. a); Legea nr. 52/2003, art. 7 alin. (3)", PR("C111") + cite("C111")),
        ("MEDAT · Regimul CAEN de după perioada de tranziție",
         "Împreună cu INS, un regim corelat cu capacitatea reală a ONRC (perioada de tranziție se încheie, după calculul nostru, la 1 aprilie 2027).",
         "HG nr. 656/1997, art. 5^1 alin. (2^1), (3); HG nr. 189/2025, art. 1", PR("C94") + cite("C94")),
        ("MEDAT · Eliminarea codurilor CAEN din actele constitutive",
         "Împreună cu Ministerul Justiției, măsura din Programul de guvernare, ca actualizarea codului să nu mai ceară modificarea actului constitutiv.",
         "HP nr. 4/2026, anexa 2; HG nr. 189/2025, art. 4 lit. F", PR("C50") + E("C50")),
        ("Ministrul delegat și ADR · Conectarea registrului la PNI",
         "Prioritizarea conectării registrului comerțului la Platforma națională de interoperabilitate și un calendar public pentru preluarea datelor de către ANAF și alte instituții.",
         "HG nr. 189/2025, art. 4 lit. I lit. b), d); OUG nr. 40/2026, art. 2 alin. (5); Legea nr. 242/2022, art. 7 alin. (1) lit. e), art. 9, art. 11", ""),
        ("ADR · Sprijin tehnic pentru ONRC, dacă ONRC îl consideră util",
         "Verificări automate la depunere pentru motivele frecvente de amânare, prelucrarea automată a actualizărilor CAEN simple, componente reutilizabile.",
         "HG nr. 89/2020, art. 3 lit. b); Legea nr. 242/2022, art. 5 alin. (1) lit. a)", PR("C143") + E("C143")),
        ("ADR · Fluxul ONRC–ANAF în raportarea despre interoperabilitate",
         "Includerea cererilor în curs privind sediul social în raportarea anuală despre eficacitatea interoperabilității.",
         "Legea nr. 242/2022, art. 5 alin. (1) lit. b) pct. (ii); HG nr. 89/2020, art. 2 lit. m)", ""),
    ]
    an = []
    an.append('<h2>Ce înseamnă coada pentru antreprenori</h2>' + tiles([
        (V("C15") + " zile", "așteptarea firmelor noi aprobate în 16–20 noiembrie", ["C15"], True),
        (V("C41").split(" ")[0], "firme noi admise fără amânare care au așteptat peste 10 zile lucrătoare", ["C41"], False),
        (V("C121").split(" (")[0].lstrip("-"), "lei vânzări mai puțin în primul an, pe fiecare zi de așteptare", ["C121"], False),
        (V("C118").split(": ")[1].split(" ")[0], "din modificări sunt doar actualizări CAEN", ["C118"], False)]) +
        para(PR("C15") + E("C15") + " " + PR("C104") + E("C104") + " " + hl(PR("C121")) + E("C121"),
             PR("C120") + E("C120") + " " + PR("C118") + E("C118"),
             hl(PR("C111")) + cite("C111") + " " + PR("C106") + cite("C106"),
             "Online-ul nu ocolește coada: " + PR("C36") + cite("C36")))
    an.append('<h2>De ce se amână și se resping dosarele</h2>' + tiles([
        (V("C139").split(" (")[0], "din amânări aveau numai motive prinse de o verificare la depunere", ["C139"], True),
        (V("C141").split(" (")[0], "amânări pe zi lucrătoare care ar putea dispărea (plafon)", ["C141"], False),
        (V("C144").split(" (")[0], "din respingeri au fost precedate de o amânare", ["C144"], False),
        (V("C143").split(" / ")[0] + " din 12", "motive cu soluție principală fără AI", ["C143"], False)]) +
        para(PR("C126") + E("C126") + " Cele mai dese motive: obiectul de activitate și codurile CAEN (" + v0("C127") + "), sediul (" + v0("C128") + "), cererea și anexa fiscală (" + v0("C129") + ")." + cite("C127", "C128", "C129"),
             hl(PR("C139")) + cite("C139") + " " + PR("C141") + cite("C141"),
             PR("C144") + E("C144") + " " + PR("C147") + cite("C147")) + card_amanari() + card_respingeri())
    an.append('<h2>Cât se poate automatiza și în ce cadru legal</h2>' +
              para(hl(PR("C143")) + E("C143") + " Reguli fixe la depunere: câmpuri obligatorii, calcule, nomenclatoare și interogarea altor registre. AI obișnuit doar ca ajutor (citirea actelor scanate, sugestia de cod CAEN). AI avansat doar pentru concordanța actului constitutiv cu hotărârea, care semnalează, fără să decidă.",
                   hl("Decizia rămâne la registrator") + " (Legea nr. 265/2022, art. 28 alin. (2)); o decizie luată numai de un program ar cere o autorizare expresă în lege (GDPR, art. 22). " + PR("C142") + E("C142") +
                   " După evaluarea noastră, înregistrarea firmelor nu e printre utilizările cu risc ridicat din Regulamentul european privind IA; oricum, acele obligații s-ar aplica de la 2.12.2027 (Regulamentul (UE) 2026/1744). Se aplică deja instruirea personalului (art. 4) și informarea celor care vorbesc cu un asistent AI (art. 50). Citirea automată a actelor de identitate cere o evaluare de impact privind protecția datelor (GDPR, art. 35). Încadrarea e interpretarea autorului, nu un aviz." + E("C142"),
                   "Interoperabilitatea e condiția: registrul comerțului e registru de bază, iar instituțiile nu pot cere documente cu date pe care statul le are deja (Legea nr. 242/2022, art. 7 alin. (1) lit. e) și art. 11). Interogarea la depunere a evidenței persoanelor, a cazierului fiscal sau a nomenclatorului stradal depinde de platforma administrată de ADR (art. 9). Ce ar ajuta imediat: un cod pentru fiecare motiv de amânare, în fiecare încheiere."))
    an.append('<h2>Valul CAEN: riscul cel mai mare</h2>' +
              para(PR("C50") + E("C50") + " " + PR("C152") + E("C152"), hl(PR("C95")) + cite("C95")) + card_caen())
    return dict(
        key="MEDAT_ADR", name="Ministerul Economiei, Digitalizării, Antreprenoriatului și Turismului și ADR", head="MEDAT ȘI ADR",
        forl="Ministerul Economiei, Digitalizării, Antreprenoriatului și Turismului și Autoritatea pentru Digitalizarea României",
        verdict="Firmele noi și schimbările la firmele existente așteaptă săptămâni. O parte mare din amânări și respingeri ar putea fi prinsă la depunere, cu reguli fixe și date luate din alte registre, fără ca decizia să plece de la registrator.",
        why="Ministerul are în domeniu IMM-urile, antreprenoriatul, mediul de afaceri și digitalizarea (HG nr. 189/2025, art. 1 și art. 4 lit. F și I), iar ADR, în coordonarea ministrului delegat pentru digitalizare (OUG nr. 40/2026, art. 2 alin. (5)), este unicul administrator al Platformei naționale de interoperabilitate (Legea nr. 242/2022, art. 9).",
        asks=asks,
        codec="Regimul CAEN: Guvernul, prin HG, cu INS și MEDAT. Modificarea legilor: Guvernul, cu MJ, și Parlamentul. Investițiile IT: buget (MF). Sprijinul ADR se dă dacă ONRC îl consideră util; ONRC și ANAF rămân administratorii datelor.",
        analysis="".join(an),
        limit="Motivele vin dintr-o clasificare automată verificată de un model AI, iar «evitabil» e evaluarea autorului, neconfirmată de ONRC." + cite("C140", "C139"),
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("6.4", "Analiza amânărilor și tabelul cu soluții și cadrul legal"),
                 ("6.5", "De ce se resping dosarele"), ("3 · Pentru echipa IT", "Fișa pentru echipa tehnică"),
                 ("7 · Pentru antreprenori", "Fișa pentru antreprenori și public"), ("12.4", "Dacă se confirmă cifrele publice despre CAEN"),
                 ("Partea 3", "Impactul economic și bugetar"), ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


def GUV():
    asks = [
        ("Adoptați OUG numai cu fundamentare completă",
         "Stoc, timpi de așteptare, scenarii pentru 2027 și fișă financiară, după consultarea publică și avizul CES, cu indicatori de rezultat publicați lunar.",
         "Constituția, art. 115 alin. (4); Legea nr. 52/2003, art. 7; Legea nr. 248/2013, art. 2 alin. (1)", PR("C43") + E("C43")),
        ("Constituiți un comitet interministerial",
         "Ministerul Justiției, Ministerul Finanțelor, ANAF, MEDAT, ADR și INS, cu un plan cu termene pentru stocul ONRC, CAEN și inactivarea fiscală.",
         "Codul administrativ, art. 34 alin. (1)", ""),
        ("Corelați prin HG regimul CAEN cu capacitatea ONRC",
         "Regimul de după încheierea perioadei de tranziție la CAEN Rev. 3 (după calculul nostru, 1 aprilie 2027).",
         "HG nr. 656/1997, art. 5^1; Constituția, art. 108 alin. (2)", PR("C94") + cite("C94")),
        ("Analizați o alocare din Fondul de rezervă",
         "Pentru capacitatea urgentă a ONRC (personal temporar, IT), dacă rectificarea nu e disponibilă.",
         "Legea nr. 500/2002, art. 30 alin. (2)", PR("C125") + cite("C125")),
        ("Dacă e nevoie de mai mult personal: o derogare de la suspendarea concursurilor",
         "Peste limita excepțiilor pe care le poate aproba Ministerul Justiției, ocuparea posturilor vacante finanțate cere o derogare prin lege sau OUG.",
         "Legea nr. 141/2025, art. XXII; Constituția, art. 115 alin. (4)", PR("C153") + E("C153")),
        ("Un calendar pentru măsurile privind ONRC din Programul de guvernare",
         "Registru-platformă online și debirocratizare.",
         "HP nr. 4/2026, anexa 2; Codul administrativ, art. 25 lit. e)", ""),
    ]
    rows = [
        ("Capacitate suplimentară (proiectul de OUG)", "Guvernul, prin OUG, la inițiativa MJ; aprobare prin lege", "Câștig median pe aceleași simulări: circa " + G34.lstrip("≈") + " de zile în iunie 2028." + E("C43")),
        ("Conversia automată CAEN 1-la-1, regim simplificat", "Lege sau OUG (MJ, cu MEDAT); procedura internă: ONRC", PR("C95") + cite("C95")),
        ("Perioada de tranziție CAEN", "Guvernul, prin HG (MEDAT, cu INS)", PR("C68") + cite("C68")),
        ("Ocuparea posturilor vacante", "MJ (excepții); peste limită: derogare prin lege sau OUG", PR("C52") + cite("C52", "C153")),
        ("Bani pentru personal și IT", "MF și Guvernul (rectificare, Fondul de rezervă prin HG); Parlamentul (buget)", PR("C125") + cite("C125")),
        ("Verificări la depunere, triaj", "ONRC (act al conducătorului); sprijin ADR", PR("C141") + cite("C141")),
        ("Inactivarea fiscală pentru sediu", "ANAF (ordin); MF (Codul de procedură fiscală)", "Riscul nu e cuantificat în raport."),
        ("Date deschise lunare", "ONRC; MJ, prin ROF", "Condiția pentru a măsura efectul oricărei măsuri."),
    ]
    tbl = ('<table class="map-tbl"><thead><tr><th>Măsura</th><th>Cine decide și prin ce act</th><th>Ce arată datele sau modelul</th></tr></thead><tbody>' +
           "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows) + "</tbody></table>")
    an = []
    an.append('<h2>Harta deciziilor: cine ține fiecare pârghie</h2>' +
              para(hl("Nicio instituție nu are singură toate pârghiile: capacitatea ține de MJ și ONRC, banii de MF și Parlament, valul CAEN de o HG, datele de ADR și ANAF.") +
                   " " + PR("C67") + cite("C67")) + tbl)
    an.append('<h2>Cele două cozi și limita mutărilor de personal</h2>' + card_schema() + card_tandem() + card_canib())
    an.append('<h2>OUG și tranziția CAEN</h2>' + tiles([
        (G34 + " zile", "câștigul median al proiectului de OUG, pe aceleași simulări", ["C43"], True),
        (V("C44").replace("câștig ", ""), "câștigul transferului de acte administrative (Art. III)", ["C44"], False),
        (V("C83"), "costul proiectului; nu creează posturi noi", ["C83"], False),
        (v0("C54") + " zile", "iunie 2028, pachetul minim realist", ["C54"], False)]) +
        para(PR("C61") + cite("C61") + " " + PR("C152") + E("C152"), hl(PR("C95")) + cite("C95")) + card_caen())
    return dict(
        key="Guvern", name="Guvernul României și Secretariatul General al Guvernului", head="GUVERN ȘI SGG",
        forl="Guvernul României și Secretariatul General al Guvernului",
        verdict="Coada traversează competențele a cel puțin șase instituții. Proiectul de OUG ajută, dar singur nu ajunge; cel mai mare risc, valul CAEN din 2027, depinde de o hotărâre a Guvernului.",
        why="Guvernul adoptă ordonanța aflată în consultare și hotărârile privind clasificarea CAEN, iar prim-ministrul poate constitui comitete interministeriale (Constituția, art. 108 și 115; Codul administrativ, art. 34); SGG asigură operațiunile tehnice ale actelor de guvernare (Codul administrativ, art. 20).",
        asks=asks,
        codec="OUG: aprobare sau respingere prin lege de către Parlament. HG: inițiator ministerul de resort (MJ, MEDAT, INS), avize MF și MJ. Bugetul: Parlamentul. Proiectele din domeniul economic și fiscal: avizul CES.",
        analysis="".join(an),
        limit="Data de 1 aprilie 2027 e calculată de noi; evaluarea privește textul OUG pus în consultare, nu pe cel adoptat." + E("C152"),
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("1 · Pentru ministru", "Fișa pentru decidenți politici"),
                 ("Cap. 8", "Grila de risc: vitezele de intrare și ieșire"), ("Cap. 9", "Proiectul de OUG, pe articole"),
                 ("Cap. 10", "Ce se poate face: pachete de măsuri"), ("12.4", "Dacă se confirmă cifrele publice despre CAEN"),
                 ("Partea 3", "Impactul economic și bugetar"), ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


def PARL():
    asks = [
        ("Cereți date la examinarea legii de aprobare a OUG",
         "De la Ministerul Justiției și ONRC: stocul, timpii de așteptare și capacitatea pe fiecare etapă.",
         "Constituția, art. 111 alin. (1), art. 115 alin. (5), (7)", PR("C28") + E("C28")),
        ("Audiați conducerea MJ, a ONRC și, la comisiile de buget, a MF",
         "În comisiile de specialitate ale ambelor Camere.",
         "Constituția, art. 111 alin. (2), art. 64 alin. (4)", ""),
        ("Analizați amendamente la legea de aprobare",
         "Un raport public lunar privind stocul și timpii, un termen de evaluare a efectelor și un regim simplificat pentru actualizarea CAEN.",
         "Constituția, art. 115 alin. (7)", PR("C43") + E("C43")),
        ("Finanțați capacitatea ONRC în bugetul pe 2027",
         "Personal și IT, cu indicarea sursei de finanțare.",
         "Constituția, art. 138 alin. (2), (5)", PR("C125") + cite("C125")),
        ("Cereți Curții de Conturi un audit al performanței ONRC",
         "Resursa umană pe etape, investițiile IT, platforma myportal.",
         "Constituția, art. 140 alin. (3); Legea nr. 94/1992, art. 4 alin. (2), art. 21 alin. (2)", ""),
        ("Propuneri legislative: Legea nr. 265/2022 și art. 92 din Codul de procedură fiscală",
         "Regim CAEN simplificat; fără inactivare fiscală cât timp o cerere privind sediul așteaptă la ONRC; fișa financiară se cere Guvernului.",
         "Constituția, art. 74 alin. (1); Legea nr. 500/2002, art. 15 alin. (2)", ""),
    ]
    an = []
    an.append('<h2>La aprobarea OUG: ce poate și ce nu poate face proiectul</h2>' + tiles([
        (G34 + " zile", "câștigul median al proiectului, pe aceleași simulări, iunie 2028", ["C43"], True),
        (V("C83"), "costul proiectului; nu creează posturi noi", ["C83"], False),
        (V("C51").split("→ ")[1].split(" ")[0], "posturi finanțate, dar neocupate", ["C51"], False),
        (v0("C54") + " zile", "iunie 2028, pachetul minim realist", ["C54"], False)]) +
        para("Evaluat pe textul integral pus în consultare (art. I–IV), cu ipotezele de livrare declarate. " + hl(PR("C43")) + E("C43") + " " + PR("C44") + E("C44"),
             PR("C35") + E("C35") + " " + PR("C56") + E("C56")) + card_oug())
    an.append('<h2>Ce se poate corecta prin lege</h2>' +
              para("<b>Actualizarea CAEN.</b> " + PR("C50") + E("C50") + " " + hl(PR("C95")) + cite("C95") +
                   " Termenul de tranziție se stabilește prin HG (HG nr. 656/1997, art. 5^1), nu prin lege: Parlamentul îl poate influența doar legiferând în materie sau cerând informații Guvernului." + E("C152"),
                   "<b>Inactivarea fiscală.</b> Codul de procedură fiscală (art. 92 alin. (1) lit. g)) declară inactivă firma cu sediul expirat, chiar dacă cererea de prelungire așteaptă la Registru. Raportul nu cuantifică firmele afectate; semnalează riscul.",
                   "<b>Automatizarea.</b> " + PR("C142") + E("C142") + " O decizie luată numai de un program ar cere o autorizare expresă în lege.",
                   "<b>Termenul.</b> Legea cere o zi lucrătoare (Legea nr. 265/2022, art. 105 alin. (1)); " + PR("C41") + E("C41", "C23") +
                   " Raportul nu califică întârzierile drept nelegale și nu numără „încălcări”.") + card_caen())
    an.append('<h2>Bugetul pe 2027</h2>' +
              para(hl(PR("C122")) + cite("C122") + " " + PR("C123") + cite("C123"),
                   PR("C111") + cite("C111") + " " + PR("C110") + cite("C110"),
                   PR("C52") + cite("C52") + " " + PR("C153") + E("C153")) + card_venituri())
    an.append('<h2>Controlul parlamentar: ce să cereți lunar</h2>' +
              para(hl("Stocul pe etape, intrările, deciziile finale, amânările și respingerile, așteptarea mediană pe tipuri de cereri și personalul activ pe etape, pe oficii.") +
                   " Cifrele se pot verifica din surse publice: " + PR("C92") + E("C92"),
                   PR("C96") + E("C96") + " " + PR("C91") + E("C91")))
    return dict(
        key="Parlament", name="Parlamentul României — comisiile juridice și de buget", head="PARLAMENT · COMISIILE JURIDICE ȘI DE BUGET",
        forl="Parlamentul României: comisiile juridice și comisiile de buget ale Camerei Deputaților și Senatului",
        verdict="Parlamentul aprobă sau respinge ordonanța și votează bugetul. Datele arată ce poate face proiectul, ce rămâne nerezolvat și ce trebuie cerut lunar pentru control.",
        why="Comisiile juridice examinează legea de aprobare a ordonanței privind registrul comerțului, iar comisiile de buget examinează bugetul și impactul bugetar al actelor normative. Guvernul și administrația sunt obligate să prezinte informațiile cerute de Camere și de comisii (Constituția, art. 111); ordonanțele se aprobă sau se resping prin lege (art. 115 alin. (5), (7)); bugetul se aprobă fără cheltuieli fără sursă (art. 138).",
        asks=asks,
        codec="Legile: ambele Camere și promulgarea. Perioada de tranziție CAEN se stabilește prin HG: Parlamentul nu o modifică direct. Denumirile și competențele exacte ale comisiilor, din regulamentele Camerelor, nu au fost verificate.",
        analysis="".join(an),
        limit="Competențele exacte ale comisiilor (regulamentele Camerelor) nu au fost verificate; textul adoptat al OUG poate diferi de cel pus în consultare.",
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("Cap. 1", "De ce contează o zi: ce cere legea"),
                 ("Cap. 9", "Proiectul de OUG, pe articole"), ("Cap. 10", "Ce se poate face: pachete de măsuri"),
                 ("Partea 3", "Impactul economic și bugetar"), ("Cap. 11", "Cât de sigure sunt cifrele"),
                 ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


def ONRC():
    asks = [
        ("Triaj la intrare și procedură simplificată pentru actualizarea CAEN",
         "Un flux separat pentru cererile simple și o procedură simplificată pentru actualizarea CAEN, aprobate prin act al conducătorului. Conversia automată a codurilor cu corespondență unică, fără modificarea actului constitutiv, cere o normă de rang legal; ONRC o poate propune Ministerului Justiției pentru proiectul de OUG.",
         "HG nr. 656/1997, art. 5^1 alin. (1); Legea nr. 265/2022, art. 24 alin. (1) lit. g), i)", PR("C50") + E("C50")),
        ("Verificări automate la depunere, în myportal",
         "Pentru motivele frecvente de amânare, acolo unde verificarea nu există deja, cu un cod de motiv în fiecare încheiere; cele care interoghează alte registre cer protocoale, conectarea la Platforma națională de interoperabilitate și o evaluare de impact privind protecția datelor.",
         "Legea nr. 265/2022, art. 24 alin. (1) lit. g), n); Legea nr. 242/2022, art. 11", PR("C139") + cite("C139")),
        ("Personal pe ambele etape",
         "Concursuri pentru posturile deblocate prin excepția aprobată de MJ, în limita ei, și continuarea redistribuirii interne, pe ambele etape.",
         "Legea nr. 265/2022, art. 22 alin. (5); ROF, art. 6 alin. (7), art. 7 alin. (2) lit. b)", PR("C56") + E("C56")),
        ("Publicarea regulii de repartizare națională a dosarelor",
         "Repartizarea aleatorie la nivel național e deja aplicată (oficiul de depunere nu e neapărat cel care soluționează); publicarea regulii și a efectului ei pe oficii.",
         "Legea nr. 265/2022, art. 21 alin. (2), art. 24 alin. (1) lit. h)–i), art. 32 alin. (3)–(4)", PR("C49") + E("C49")),
        ("Date deschise lunare și un termen estimat realist pentru solicitanți",
         "Stocul pe etape, intrările, deciziile, amânările și respingerile, pe oficii și tipuri de cereri, și personalul activ pe etape, agregat la nivel național, fără date personale.",
         "Legea nr. 544/2001, art. 5; ROF, art. 16 alin. (3) lit. d)", ""),
        ("Extinderea schimbului de date cu ANAF și propuneri legislative către MJ",
         "Extinderea sau verificarea protocolului existent, astfel încât cererile în curs privind sediul social să fie cunoscute organului fiscal înainte de o inactivare; propuneri de modificare a Legii nr. 265/2022.",
         "Legea nr. 265/2022, art. 24 alin. (1) lit. n) și o), art. 27 alin. (4); Legea nr. 242/2022, art. 11", ""),
    ]
    an = []
    an.append('<h2>Operarea și soluționarea</h2>' + tiles([
        (V("C29").split(" (")[0], "cereri încă neprelucrate la 6 noiembrie (din " + V("C28") + ")", ["C29", "C28"], True),
        (REG["C34"]["unit"].split("(")[1].split(" ")[0], "cât de repede a lucrat operarea față de soluționare, într-o singură săptămână (30.10–6.11)", ["C34"], False),
        (V("C32").split("→ ")[1], "dosare rezolvate în două zile după 27 aprilie 2026, față de " + V("C32").split(" →")[0], ["C32"], False),
        (V("C21").split("→ ")[1], "din decizii sunt amânări", ["C21"], False)]) +
        para(hl(PR("C34")) + E("C34") + " " + PR("C36") + cite("C36"),
             PR("C101") + E("C101") + " Cauza nu e documentată în date.",
             PR("C38") + E("C38") + " Cauza nu se vede în BERC: cereri mai simple sau priorități legale sunt plauzibile.") +
        card_schema() + card_tandem() + card_canib())
    an.append('<h2>Amânări și respingeri: verificările la depunere</h2>' + tiles([
        (V("C139").split(" (")[0], "din amânări aveau numai motive prinse de o verificare la depunere", ["C139"], True),
        (V("C141").split(" (")[0], "amânări pe zi lucrătoare care ar putea dispărea (plafon)", ["C141"], False),
        (V("C144").split(" (")[0], "din respingeri au fost precedate de o amânare", ["C144"], False),
        (V("C146").split(" ")[0], "din cererile amânate au ajuns respinse", ["C146"], False)]) +
        para(PR("C126") + E("C126") + " Cele mai dese motive: obiectul de activitate și codurile CAEN (" + v0("C127") + "), sediul (" + v0("C128") + "), cererea și anexa fiscală (" + v0("C129") + ")." + cite("C127", "C128", "C129"),
             hl(PR("C141")) + cite("C141") + " " + PR("C37") + E("C37"),
             hl("Ce ar ajuta imediat: un cod pentru fiecare motiv de amânare, publicat în încheiere.") + " În buletinul public, motivul apare ca text liber; nu știm dacă sistemul intern al ONRC are deja o clasificare. Cu un cod publicat, ONRC ar putea raporta lunar ce lipsește la depunere și ar ști ce verificare să construiască întâi, dintre cele care nu există deja.",
             "<b>IT: ce trebuie construit.</b> (1) momentul trecerii fiecărui dosar de la operare la registrator, înregistrat și exportabil; (2) coduri pentru motivele de amânare și de respingere; (3) tabelul de corespondență CAEN Rev. 2 → Rev. 3, cu marcarea codurilor cu un singur corespondent; (4) o etichetă de rutare pentru actele din art. III, cu starea „clarificare cerută” și termenul de răspuns.") +
        card_amanari() + card_respingeri())
    an.append('<h2>Diferențele între oficii</h2>' +
              para(hl(PR("C49")) + E("C49") + " " + PR("C89") + " (" + V("C89") + ")." + E("C89"),
                   PR("C90") + " (" + V("C90") + ")." + E("C90") + " " + PR("C88") + " (" + V("C88") + ")." + E("C88"),
                   PR("C75") + E("C75") + " " + hl("Oficiul din date e oficiul de depunere: clasamentele arată unde merită verificat ce e diferit, nu performanța personalului.")))
    return dict(
        key="ONRC", name="Oficiul Național al Registrului Comerțului (conducerea)", head="CONDUCEREA ONRC",
        forl="Conducerea Oficiului Național al Registrului Comerțului",
        verdict="Registrul emite mai multe decizii decât în anii trecuți, dar cererile au crescut mai repede. Mai multe soluții (triaj, verificări la depunere, procedura CAEN, date deschise) țin de atribuțiile proprii ale ONRC; conversia automată CAEN cere însă o normă de rang legal, iar verificările care interoghează alte registre cer protocoale și interoperabilitate.",
        why="Directorul general conduce, coordonează și controlează activitatea ONRC și a oficiilor (Legea nr. 265/2022, art. 21 alin. (2)); atribuțiile ONRC includ sistemul informatic, organizarea registratorilor, îndrumarea oficiilor, colaborarea cu alte autorități și propunerile de acte normative (art. 24 alin. (1) lit. g), h), i), n), o)). Procedurile pentru CAEN se pot stabili prin act al conducătorului (HG nr. 656/1997, art. 5^1 alin. (1)).",
        asks=asks,
        codec="ROF-ul și statele de funcții: ordin al ministrului justiției. Posturi noi: HG și buget (MF, Guvern, Parlament). Protocoale de date: cu ANAF (și ADR, pentru platforma de interoperabilitate). Procedurile interne și desemnările: decizia directorului general.",
        analysis="".join(an),
        limit="Nu vedem sistemele interne ONRC: o parte din verificări poate exista deja; oficiul din date e cel de depunere." + E("C143", "C49"),
        details=[("Sinteză executivă", "Toată imaginea, pentru decizie"), ("2 · Pentru conducerea ONRC", "Fișa pentru conducerea Registrului"),
                 ("Cap. 4", "Cele două cozi"), ("6.4", "Analiza amânărilor și tabelul cu soluții"), ("6.5", "De ce se resping dosarele"),
                 ("2 · Clasamente", "Clasamentele pe oficii, cu rezervele lor"), ("Partea 6", "Munca din spatele cozii"),
                 ("11.4", "Ce ar trebui publicat"), ("6 · Registrul complet", "Registrul afirmațiilor: sursa fiecărui cod")])


INSTITUTIONS = [MJ, MF, MEDAT, GUV, PARL, ONRC]

# ------------------------------------------------------------------ complete-report page map
def page_map():
    import fitz
    d = fitz.open(str(COMPLET)); toc = d.get_toc(); n = len(d)
    out = {}
    for i, (lvl, title, p) in enumerate(toc):
        nxt = next((q for l2, _, q in toc[i + 1:] if l2 <= lvl), n + 1)
        out[title] = (p, max(p, nxt - 1) if nxt > p else p)
    secs = {}
    for pno in range(n):                       # numbered sections (6.4, 6.5, 11.4, 12.4) are not in the outline
        for line in d[pno].get_text().splitlines():
            m = re.match(r"^(\d{1,2}\.\d) [A-ZĂÎÂȘȚ]", line)
            if m and m.group(1) not in secs and pno >= 16:
                secs[m.group(1)] = pno + 1
    d.close()
    starts = sorted(set([q for _, _, q in toc] + list(secs.values())))
    for k, p in secs.items():
        later = [q for q in starts if q > p]
        out[k] = (p, (later[0] if later else p))
    return out, n


def find_pages(pm, key):
    for t, v in pm.items():
        if t == key or t.startswith(key + " ") or t.startswith(key):
            return v
    raise KeyError(key)


# ------------------------------------------------------------------ page assembly
CSS = r"""
.cover .for { font: 500 16pt/1.3 var(--sans); color: var(--accent); max-width: 140mm; margin: -2mm 0 6mm; }
.cover h1 { font-size: 32pt; }
.cover .threads { margin: 9mm 0 7mm; }
section.sz { break-before: page; }
section.sz .eyebrow { break-after: avoid; }
section.sz.flow { break-before: auto; margin-top: 9mm; border-top: .6mm solid var(--ink); padding-top: 3mm; }
section.sz h2 { font: 600 17pt/1.18 var(--sans); margin: 0 0 3mm; letter-spacing: -.01em; }
section.sz h2 + .pulls { margin-top: 3mm; }
section.sz .dek { font: 400 10.6pt/1.48 var(--serif); color: var(--ink-2); margin: 0 0 4mm; }
section.sz p { margin: 0 0 2.2mm; }
section.sz .an h2 { margin-top: 7mm; break-after: avoid; border-top: .35mm solid var(--ink); padding-top: 2.5mm; }
.pl { font-size: 8.6pt; } .ps { font-size: 7pt; }
.pn { font-size: 18pt; }
.an > h2:first-child { border-top: none; padding-top: 0; margin-top: 2mm; }
.cav { font: 400 8pt/1.4 var(--sans); color: var(--ink-3); }
ol.asks { list-style: none; counter-reset: a; padding: 0; margin: 0 0 3mm; }
ol.asks > li { counter-increment: a; display: grid; grid-template-columns: 8mm 1fr; column-gap: 2mm; padding: 1.6mm 0 1.6mm; border-top: .2mm solid var(--rule-2); break-inside: avoid; }
ol.asks > li::before { content: counter(a); font: 600 13pt/1 var(--sans); color: var(--accent); padding-top: .6mm; }
.at { font: 600 10.6pt/1.3 var(--sans); margin: 0 0 .8mm; }
.ab { font: 400 10.3pt/1.45 var(--serif); margin: 0 0 .9mm; }
.acit { font: 400 8.6pt/1.4 var(--sans); color: var(--ink-2); margin: 0; }
.acit b, .adata b { font-weight: 600; color: var(--ink); }
.adata { font: 400 8.6pt/1.4 var(--sans); color: var(--ink-2); margin: .6mm 0 0; }
.box { background: var(--tint); border-left: 1mm solid var(--accent); padding: 2.2mm 3.5mm; font: 400 9pt/1.45 var(--sans); margin: 2mm 0 0; break-inside: avoid; }
.box p { margin: 0 0 1mm; }
.box.decide { margin: 0 0 3mm; font: 400 10pt/1.45 var(--sans); }
ul.five { list-style: none; padding: 0; margin: 2mm 0 0; }
ul.five li { padding: 2.2mm 0; border-top: .2mm solid var(--rule-2); font: 400 10.3pt/1.5 var(--serif); }
ul.five li b { font-family: var(--sans); font-weight: 600; }
.ec { margin: 4mm 0 6mm; break-inside: avoid; }
.ect { font: 600 12.5pt/1.25 var(--sans); margin: 0 0 1.5mm; border-top: .6mm solid var(--ink); padding-top: 1.5mm; break-after: avoid; }
.eci { font: 400 10.3pt/1.45 var(--serif); margin: 0 0 1.5mm; break-after: avoid; }
.eci p { margin: 0 0 1mm; }
.eci b { font-family: var(--sans); font-weight: 600; }
.ec svg { width: 100%; height: auto; max-height: 70mm; display: block; margin: 0 auto; break-inside: avoid; }
.ecc { font: 400 10.3pt/1.45 var(--serif); margin-top: 1.2mm; break-before: avoid; }
table.map-tbl { width: 100%; border-collapse: collapse; table-layout: fixed; font: 400 8.8pt/1.4 var(--sans); margin: 3mm 0 2mm; }
table.map-tbl th { text-align: left; font: 600 7.4pt var(--mono); text-transform: uppercase; color: var(--ink-2); border-bottom: .35mm solid var(--ink); padding: 1.2mm; }
table.map-tbl td { border-bottom: .2mm solid var(--rule-2); padding: 1.4mm 1.2mm; vertical-align: top; overflow-wrap: break-word; }
table.map-tbl th:nth-child(1) { width: 40mm; } table.map-tbl th:nth-child(2) { width: 50mm; }
table.where { width: 100%; border-collapse: collapse; table-layout: fixed; font: 400 9.6pt/1.4 var(--sans); margin: 2mm 0 3mm; }
table.where td { border-bottom: .2mm solid var(--rule-2); padding: 1.3mm 1.2mm; vertical-align: top; }
table.where td:first-child { width: 46mm; font-weight: 600; } table.where td:last-child { width: 22mm; text-align: right; font: 500 9pt var(--mono); }
.url { overflow-wrap: anywhere; word-break: break-all; font: 500 9pt var(--mono); }
ul.lim { margin: 1mm 0 5mm 4mm; padding: 0; } ul.lim li { margin-bottom: 1.2mm; font: 400 10.3pt/1.45 var(--serif); }
"""


def page_css(head):
    esc = lambda s: s.replace('"', '\\"')
    title = f"COADA DE LA REGISTRUL COMERȚULUI · SINTEZĂ PENTRU {head}"
    pages = [("s-body", "Sinteză executivă · " + DATE)]
    return "\n".join([f'@page {{ @top-left {{ content: "{esc(title)}"; }} @bottom-left {{ content: "{esc(BRI.FOOT)}"; }} }}'] +
                     [f'@page {n} {{ @top-right {{ content: "{esc(h)}"; }} }}' for n, h in pages])


def build(inst, pm, npages):
    I = inst()
    cover = f"""
<section class="cover">
  <div class="eyebrow">Sinteză executivă · Analiză independentă din date deschise · BERC / ONRC / myportal</div>
  <h1>Coada de la Registrul Comerțului</h1>
  <p class="for">— sinteză pentru {I['forl']}</p>
  <p class="sub">Ce vă cerem, în limitele competențelor dumneavoastră, și pe ce date se sprijină fiecare cerere</p>
  <div class="threads" aria-hidden="true"><i class="t-e"></i><i class="t-s"></i><i class="t-m"></i><i class="t-p"></i></div>
  <p class="verdict">{I['verdict']}</p>
  <dl class="meta">
    <dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
    <dt>Ediție și dată</dt><dd>{BSV.VERSION_HTML} · {DATE}</dd>
    <dt>Bază empirică</dt><dd>4.077.510 decizii BERC (aprilie 2023 – noiembrie 2026) · 7.469 de numere de cerere sondate în myportal · notele Ministerului Justiției</dd>
    <dt>Raport complet</dt><dd>Raport_ONRC_Coada_2026-11_COMPLET.pdf · {GITHUB}</dd>
    <dt>Declarație de interes</dt><dd>Autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal.</dd>
    <dt>Utilizarea AI</dt><dd>{ai_annex.DISCLAIMER}</dd>
  </dl>
</section>"""
    li = ""
    for t, txt, citation, data in I["asks"]:
        codes = "".join(re.findall(r'<span class="eid">\[C\d+\]</span>', data))     # supporting claims, by code only
        li += (f'<li><div><div class="at">{t}</div><p class="ab">{hl(txt)}</p><p class="acit"><b>Temei.</b> {citation}' +
               (f' · <b>Datele:</b>{codes}' if codes else "") + "</p></div></li>")
    asks = f"""
<section class="sz" style="page: s-body;">
  <div class="eyebrow">Cererile</div>
  <h2>Ce vă cerem și de ce e în competența dumneavoastră</h2>
  <p class="dek"><b>De ce vă privește.</b> {I['why']}</p>
  {('<div class="box decide"><p>' + I['decide'] + '</p></div>') if I.get('decide') else ''}
  <ol class="asks">{li}</ol>
  <div class="box"><p><b>Cine mai decide.</b> {I['codec']}</p>
  <p><b>Independența registratorului.</b> Cererile privesc organizarea, resursele, datele și regulile, niciodată soluția unui dosar: registratorul decide independent (Legea nr. 265/2022, art. 28 alin. (4)). Triajul și verificările la depunere privesc pregătirea și ordinea dosarelor, nu soluția.</p></div>
</section>"""
    key = f"""
<section class="sz flow" style="page: s-body;">
  <div class="eyebrow">Ce urmează și ce schimbă fiecare măsură</div>
  <h2>Fără măsuri noi, coada crește în 2027; proiectul de OUG ajută, dar singur nu ajunge</h2>
  {card_prognoza()}{card_pachete()}
</section>"""
    five = [
        ("Ce se întâmplă.", "Fiecare dosar trece prin două etape: operarea și decizia registratorului. " + hl(PR("C14")) + E("C14") + " " + PR("C16") + E("C16") +
         " Durata se măsoară în zile calendaristice, include timpul în care solicitantul completează dosarul după o amânare și privește doar dosarele deja decise; termenul din lege, de o zi lucrătoare, privește cererea completă." + E("C23") +
         " Pe lângă deciziile finale, registratorii emit circa " + V("C03").lstrip("≈").split(" ")[0] + " de amânări pe zi, tot muncă de analiză; cu ele, Registrul a dat " + V("C48").split(" vs ")[1].split(" pe zi")[0] + " decizii pe zi în septembrie / octombrie." + E("C03", "C48")),
        ("De ce.", hl("Cererile au crescut mult mai repede decât producția.") + " " + PR("C47") + E("C47") + " " + PR("C87") + E("C87")),
        ("Unde se blochează.", PR("C29") + E("C29") + " " + PR("C34") + E("C34")),
        ("Ce urmează.", PR("C59") + cite("C59") + " " + hl(PR("C43")) + E("C43") + " Câștigul median al proiectului, pe aceleași simulări: circa " + G34.lstrip("≈") + " de zile." + E("C43")),
        ("Ce costă.", PR("C111") + cite("C111") + " " + hl(PR("C122")) + cite("C122")),
    ]
    prob = f"""
<section class="sz flow" style="page: s-body;">
  <div class="eyebrow">Problema într-o pagină</div>
  <h2>Registrul emite cel puțin cât în anii trecuți, dar cererile au crescut mult mai repede</h2>
  {tiles([(V("C14") + " zile", "așteptarea obișnuită a modificărilor soluționate în 16–20 noiembrie", ["C14"], True),
          (V("C28"), "cereri nesoluționate raportate de Ministerul Justiției la 6 noiembrie", ["C28"], False),
          (V("C01"), "decizii finale pe zi lucrătoare în octombrie–noiembrie 2026", ["C01"], False),
          (V("C23") + " zi lucr.", "termenul legal de soluționare (Legea nr. 265/2022, art. 105 alin. (1))", ["C23"], False)])}
  <ul class="five">{"".join(f"<li><b>{a}</b> {b}</li>" for a, b in five)}</ul>
</section>"""
    analysis = f'<section class="sz flow" style="page: s-body;"><div class="eyebrow">Analiza pentru {I["name"]}</div><div class="an">{I["analysis"]}</div></section>'
    lim = [PR("C11") + cite("C11"),
           "Prognozele și pachetele sunt scenarii de model, cu intervale largi; efectele măsurilor sunt ipoteze, nu măsurători." + E("C42") + cite("C54"),
           I["limit"]]
    rows = ""
    for k, desc in I["details"]:
        a, b = find_pages(pm, k)
        label = {"6.4": "§6.4", "6.5": "§6.5", "11.4": "§11.4", "12.4": "§12.4"}.get(k, k)
        rows += f'<tr><td>{label}</td><td>{desc}</td><td><span class="tpg">p. {a}{"–" + str(b) if b > a else ""}</span></td></tr>'
    end = f"""
<section class="sz flow" style="page: s-body;">
  <div class="eyebrow">Limite</div><h2>Ce nu știm</h2>
  <ul class="lim">{"".join(f"<li>{x}</li>" for x in lim)}</ul>
  <div class="eyebrow">Detalii</div><h2>Unde găsiți detaliile</h2>
  <p>În raportul complet, <b>Raport_ONRC_Coada_2026-11_COMPLET.pdf</b> (ediția de <span class="tpg">{npages}</span> de pagini, cu care au fost verificate trimiterile de mai jos):</p>
  <table class="where"><tbody>{rows}</tbody></table>
  <p>Codurile dintre paranteze drepte duc, în registrul afirmațiilor, la sursă, la scriptul care calculează cifra, la amprenta datelor și la starea verificării. Datele, codul și registrul: <span class="url">{GITHUB}</span></p>
  <p class="note">{ai_annex.DISCLAIMER}</p>
</section>"""
    html_ = f"""<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8">
<title>Coada de la Registrul Comerțului · sinteză pentru {I['name']} · Ștefan-Lucian Deleanu</title>
<link rel="stylesheet" href="../fonts/fonts.css">
<style>{BRI.BASE_CSS}
{page_css(I['head'])}
{BRI.EXTRA_CSS}
{CSS}</style></head><body>{cover}{asks}{prob}{key}{analysis}{end}</body></html>"""
    return I, html_


def shrink_check(pdf):
    import fitz
    d = fitz.open(str(pdf)); sizes = collections.Counter()
    for p in d[1:]:
        for blk in p.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:
                    sizes[round(sp["size"], 1)] += len(sp["text"])
    n = len(d); d.close()
    return n, sizes.most_common(1)[0][0], sizes


def main():
    OUT_HTML.mkdir(exist_ok=True); OUT_PDF.mkdir(exist_ok=True)
    pm, npages = page_map()
    built = []
    for inst in INSTITUTIONS:
        I, h = build(inst, pm, npages)
        p = OUT_HTML / f"Sinteza_{I['key']}.html"
        p.write_text(h, encoding="utf-8")
        built.append((I, p))
    bad = False
    for I, p in built:                     # lint all before the (slow) printing
        r = subprocess.run([PY, "-X", "utf8", str(DELIV / "lint_numbers.py"), str(p)], capture_output=True, text=True, encoding="utf-8")
        print(r.stdout.strip()[:3000])
        bad |= r.returncode != 0
    if bad:
        sys.exit("LINT FAILED — no PDF printed")
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    for I, p in built:
        if only and I["key"] not in only:
            continue
        pdf = OUT_PDF / f"Sinteza_{I['key']}.pdf"
        BRI.compile_pdf(p, pdf)
        n, body, sizes = shrink_check(pdf)
        print(f"PDF {pdf.name}: {n} pages · dominant text {body} pt · 10.3pt chars {sizes.get(10.3, 0)}")
        assert body >= 9.5, f"{pdf.name} shrunk (dominant {body} pt)"


if __name__ == "__main__":
    main()
