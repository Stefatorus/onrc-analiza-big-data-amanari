"""Analiza proiectului de OUG privind registrul comerțului (consultare MJ, 18.11.2026) — ediția Lab.

Verifică fiecare afirmație factuală din preambulul proiectului și din Nota de fundamentare (NF) pe datele noastre și
evaluează efectul fiecărui articol cu modelele existente (fără a rerula conductele grele). Fiecare cifră din textul nostru
vine din claims_registry.csv prin V()/E(); cifrele citate din NF sunt înregistrate ca afirmații de nivel C (C154–C156)
și apar între ghilimele (<q class="src-nf">). Stil, componente și tipar: build_raport_institutii.py (Edge headless).

  ..\\..\\venv\\Scripts\\python.exe -X utf8 build_analiza_oug.py
"""
import re, sys, collections
from pathlib import Path

import build_raport_institutii as BR
import lab_styles as LS
from lab_styles import BASE_CSS, badge, hl, prose, pulls, counter_case, quote_box
import ai_annex

V, E, REG = BR.V, BR.E, BR.REG
HERE = BR.HERE
DELIV = BR.DELIV
HTML_OUT = HERE / "Analiza_proiectului_OUG_2026-11.html"
PDF_OUT = DELIV / "Analiza_proiectului_OUG_2026-11.pdf"

v0 = lambda c: V(c).split(" (")[0]
seg = lambda c, i: V(c).split(" · ")[i]
def W(c):   # WARN claims carry their reserve next to the number
    return REG[c]["rezerva_obligatorie"]
def q(t):   # quoted text from the draft / NF
    return f'<q class="src-nf">{t}</q>'
def B(c): return BR.B(c)

# ------------------------------------------------------------------ registry-derived fragments
C99 = V("C99")                                                 # 4.430 / 10.881 (…) / 4.129 / 3.039 · aug.–oct.: 6.840 (MJ: 6.931)
SEPT = C99.split(" / ")[1]                                     # 10.881 (10.123–11.588)
NOV = C99.split(" / ")[3].split(" ·")[0]                       # 3.039
AUGOCT = C99.split("aug.–oct.: ")[1].split(" (")[0]            # 6.840
H1 = V("C98").split("/zi")[0]                                  # 4.369
C161 = V("C161")
R_AO = C161.split(" · ")[0].split(": ")[1]                     # +57%
R_SEP = C161.split(" · ")[1].split(": ")[1]                    # ×2,5
R_J7 = C161.split("ian.–iul.: ")[1].split(" (")[0]             # +58% / ×2,5
C158 = V("C158").split(" · ")
EXP_DEC, EXP_JAN = C158[0].split(": ")[1], C158[1].split(": ")[1]   # «≈164 (112–216) vs ≈129 (80–182)»
EXP_SQ, EXP_OUG = EXP_JAN.split(" vs ")
STOCK28 = C158[3].split(": ")[1]                               # ≈395.000 vs ≈297.000
C159 = V("C159").split(" · ")
VAR_LO, VAR_MID, VAR_HI = (x.split(" ", 1)[1].replace(" unități/zi", "") for x in C159[:3])
U_LO, U_MID, U_HI = (x.split("= ")[1] for x in (VAR_LO, VAR_MID, VAR_HI))
C61 = V("C61")
WEAK_GAIN = C61.split("câștig ")[1].split(" ·")[0]             # ≈8
STRONG = C61.split("ridicat ")[1].split(",")[0]                # ≈56 (≤3–122)
STRONG_GAIN = C61.split("câștig ")[2]                          # ≈79
GAIN_OUG = re.search(r"aceleași simulări: (≈\d+) zile", REG["C43"]["rezerva_obligatorie"]).group(1)   # ≈34
C35 = V("C35"); OPT = C35.split("optim ")[1].split(";")[0]; ZERO = C35.split("zero la ")[1]
C63 = V("C63"); UP10 = C63.split(" · ")[0].split("→ ")[1]; DN10 = C63.split(" · ")[1].split("→ ")[1].split(" (")[0]
C56 = V("C56")
C55 = V("C55")
C160 = V("C160").split(" · ")
C157 = V("C157")
HJ_H1 = C157.split(" / ")[0]; HJ_AO = C157.split(" / ")[1]; HJ_NV = C157.split(" / ")[2].split(" ·")[0]
HJ_SH = C157.split(" · ")[1].split(" din")[0]                  # ≈0,3%
C94 = V("C94").split(" · "); C95 = V("C95").split(" · ")
CAEN80 = C94[1].split("→ ")[1]; CAEN100 = C94[2].split("→ ")[1].split(" (")[0]
CONV80 = C95[0].split("→ ")[1]; CONV100 = C95[1].split("→ ")[1].split(" (")[0]
C156 = V("C156").split(" · ")
C155 = V("C155")
NF_CAEN_DONE = C155.split("CAEN: ")[1].split(" cereri")[0]; NF_CAEN_LEFT = C155.split(" · ")[1].split(" entități")[0]
NF_CAP = C155.split("capital: ")[1].split(" · ")[0]; NF_ANAF = C155.split("ANAF: ")[1].split(" entități")[0]
C154 = V("C154").split(" / ")
C162 = V("C162")
C68 = V("C68").split(" · ")
C141 = V("C141"); AVOID = C141.split(" evitate")[0]
C139 = V("C139").split(" · ")
C108 = V("C108")
C163 = V("C163")

# ------------------------------------------------------------------ components
def chart(d, svg, title, ids, arata, proiect, impact, tag=""):
    LS.FIG_DIR = str(HERE / d)
    take = REG[ids[0]]["public_ro"]
    return (f'<div class="ec wide"><div class="ect">{title}</div>'
            f'<div class="eci"><p><b>Ce arată.</b> {arata}</p><p><b>Pentru proiect.</b> {proiect}</p><p><b>Impact.</b> {impact}</p></div>'
            f'{LS.load_inline_svg(svg, "ao_" + svg.split(".")[0])}'
            f'<div class="ecc">{hl(take)}{E(*ids)}</div></div>')

def sect(n, page, title, dek, meta, body, runon=True):
    return (f'<section class="chapter{" runon" if runon else ""}" style="page: ao-body;">'
            f'<div class="copen"><div class="cnum">{n}</div><h2>{title}</h2>'
            f'<p class="cdek">{dek}</p><div class="cmeta">{meta}</div></div>'
            f'<div class="cols">{body}</div></section>')

def h3(t): return f'<h3>{t}</h3>'
def P(body, mt="", mh="", key=False): return prose(body, mt, mh, key_flag=key)
def concl(t): return BR.concl(t)
def wide(html_): return f'<div class="wide-block">{html_}</div>'

VCLS = {"CONFIRMAT": "v-conf", "COMPATIBIL": "v-comp", "CONTRAZIS": "v-contr", "NEVERIFICABIL": "v-nev", "OBIECTIV": "v-obj"}
OBJ_PART, OBJ_NOT = "OBIECTIV — atins parțial", "OBIECTIV — neatins în model"
def pill(v):
    k, _, sub = v.partition(" — ")
    return f'<span class="vpill {VCLS[k]}">{k}</span>' + (f'<span class="vsub">{sub}</span>' if sub else "")
CNT = V("C165"); CNT26, CNT25 = CNT.split(" / ")[0], CNT.split(" / ")[1]; CNT25Y = CNT.split(" / ")[2].split(" pe")[0]; CNTCH = CNT.split("față de 2025: ")[1].split(" (")[0]
DEC_AO = V("C86").split("2026: ")[1].split(" → ")[1].split(" (")[0]


# ================================================================== 1. CLAIMS CHECK
ROWS = [
 ("NF §2.2", q("dacă în anul 2024 media zilnică a cererilor depuse era de " + C154[0] + ", iar în 2025, de " + C154[1] + " de cereri") + " — o creștere anuală constantă.",
  "Seria 2024–2025 nu se poate reproduce din datele noastre pe aceeași definiție. Indirect: deciziile finale pe aceeași perioadă a anului au crescut în fiecare an (" + V("C30") + ")" + E("C30") +
  "; intrările măsurate în S1 2026 (" + H1 + " pe zi lucrătoare) sunt peste nivelul dat pentru 2025." + E("C98", "C154"),
  "COMPATIBIL", "măsurat, indirect"),
 ("NF §2.2", q("în primele șapte luni ale anului 2026 aceasta a depășit " + C154[2].split(" pe zi")[0].lstrip(">") + " de cereri, reprezentând, așadar, o creștere de peste opt ori"),
  "Creșterea de opt ori nu se reproduce din datele BERC analizate de noi: cererile de înregistrare sunt " + H1 + " pe zi lucrătoare în S1 2026 (" + V("C47").split(" →")[0] + " în notă)." + E("C98", "C47", "C154") +
  " Ca ordin de mărime, cifra corespunde tuturor tipurilor de cereri de pe contorul național: " + CNT26 + " de numere pe zi lucrătoare legală în ianuarie–iulie 2026, " + CNT25 + " în aceeași perioadă din 2025 (" + CNTCH + ")." + E("C165") +
  " Explicație posibilă: unități diferite (toate cererile în 2026, cereri de înregistrare în 2024–2025).",
  "COMPATIBIL", "măsurat; ordin de mărime"),
 ("Preambul", q("media zilnică a acestora a depășit cu peste jumătate nivelul înregistrat în primele șapte luni ale anului"),
  "Din datele noastre, august–octombrie față de ianuarie–iulie: " + R_J7.split(" / ")[0] + "; față de S1: " + R_AO + "." + E("C161", "C99") +
  " Preambulul folosește ca reper primele șapte luni, nota folosește semestrul I; concluzia e aceeași. " + W("C161"),
  "CONFIRMAT", "măsurat, eșantion"),
 ("Preambul", q("ajungând, în luna septembrie, la mai mult decât dublul acesteia"),
  "Septembrie: " + SEPT + " cereri pe zi lucrătoare, adică " + R_SEP + " față de S1." + E("C99", "C161") + " Estimare din eșantionul portalului, cu interval.",
  "CONFIRMAT", "măsurat, eșantion"),
 ("NF §2.2", q("media zilnică a solicitărilor a crescut cu aproximativ 53%, comparativ cu primul semestru al anului, de la 4.533 la 6.931"),
  "Datele noastre: " + H1 + " → " + AUGOCT + " pe zi lucrătoare (" + R_AO + ")." + E("C98", "C99", "C161") + " Nivelurile se reproduc la câteva procente; BERC subnumără ușor cererile recente.",
  "CONFIRMAT", "măsurat"),
 ("NF §2.2", q("media zilnică a cererilor soluționate a fost de 4.912 în luna septembrie și 5.098 în luna octombrie"),
  "Se reproduc pe definiția notei, care numără și amânările ca soluționări: BERC dă " + V("C48").split(" vs ")[1] + " pe zi (finale + amânări)." + E("C48") + " Notă: deciziile finale stricte sunt mai puține.",
  "CONFIRMAT", "măsurat; definiția MJ"),
 ("Preambul", q("această creștere considerabilă a volumului de activitate nu a putut fi însoțită de o majorare proporțională a capacității de soluționare"),
  "Deciziile pe zi lucrătoare, 1 octombrie–19 noiembrie: " + V("C87") + " față de 2025, în timp ce intrările au crescut cu circa jumătate." + E("C87", "C47") +
  " Sezonul august–octombrie aduce în fiecare an circa 13% mai puține decizii decât prima jumătate a anului." + E("C86"),
  "CONFIRMAT", "măsurat"),
 ("NF §2.2", q("la data de 6 noiembrie 2026, însuma 204.414 cereri, dintre care 106.060 neprelucrate"),
  "Stocul estimat de noi la 6.11: " + V("C100").split(" / ")[1] + " cereri (fără înmatriculările în curs)." + E("C100") +
  " La recoltarea eșantionului (21–22.11): " + V("C164") + "." + E("C164"),
  "CONFIRMAT", "măsurat, ±10%"),
 ("NF §2.2", q("soldul total s-a diminuat cu 3.904 cereri, [...] reducerea numărului cererilor neprelucrate cu 8.300, concomitent cu creșterea cu 4.396 a cererilor prelucrate"),
  "Aritmetica se verifică." + E("C85", "C33") + " Estimarea noastră scade în aceeași săptămână de la " + V("C100").split(" / ")[0] + " la " + V("C100").split(" / ")[1].split(" (")[0] + ": aceeași direcție, în marja estimării." + E("C100"),
  "COMPATIBIL", "măsurat"),
 ("Preambul; NF §2.2", q("volumul solicitărilor depășește deja capacitatea de soluționare") + "; " + q("decalajul în creștere dintre volumul solicitărilor și capacitatea efectivă de soluționare"),
  "Adevărat pentru august–octombrie: " + AUGOCT + " cereri pe zi lucrătoare, față de circa " + DEC_AO + " decizii pe zi, inclusiv amânările." + E("C99", "C86") +
  " Stocul oficial și valurile anunțate (CAEN, capital, dizolvări) depășesc capacitatea și în prognoză: " + V("C59") + " zile la mijlocul lui 2027, vârf " + V("C60") + "." + E("C28", "C59", "C60") +
  " Notă: în noiembrie, intrările au coborât temporar sub ritmul deciziilor (" + NOV + " pe zi) și stocul a început să scadă încet, dar prognoza crește din nou cu valurile din 2027." + E("C99", "C100", "C67"),
  "CONFIRMAT", "măsurat; model"),
 ("Preambul; NF §2.2", q("apropierea termenelor limită pentru actualizarea obiectului de activitate potrivit CAEN Rev. 3") + "; termen " + q("prelungit ulterior până în martie 2027, prin Hotărârea Guvernului nr. 788/2026"),
  "HG nr. 656/1997, art. 5^1, stabilește o perioadă de tranziție, cu ambele versiuni valabile; nu am găsit un termen de decădere. Prelungirea: 6 luni de la 01.10.2026, până la ≈01.04.2027 (calculat de noi)." + E("C152"),
  "COMPATIBIL", "lege"),
 ("NF §2.2", q("pe lângă cele " + NF_CAEN_DONE + " de cereri depuse pentru actualizarea obiectului de activitate [...] alte " + NF_CAEN_LEFT + " de entități urmează să își îndeplinească această obligație"),
  "Tipul cererii nu e în datele BERC structurate. Măsurat: circa un sfert din decizii sunt doar actualizări CAEN." + E("C50", "C155") +
  " Prognoza noastră de bază presupune un val de " + C162 + "." + E("C162") + " Dacă vine o parte mai mare, vezi capitolul 3.",
  "NEVERIFICABIL", "—"),
 ("NF §2.2", q("au fost primite " + NF_CAP.split(" cereri din ")[0] + " cereri, dintr-un total de " + NF_CAP.split(" cereri din ")[1].split(" ")[0] + " de societăți potențial vizate"),
  "Majorările de capital nu se separă în BERC fără citirea fiecărui act. Modelul include valul: fără el, vârful așteptării ar fi mai mic cu " + C68[1] + " zile." + E("C68", "C155"),
  "NEVERIFICABIL", "—"),
 ("NF §2.2", q("ANAF a comunicat " + NF_ANAF + " de entități vizate de procedurile de dizolvare/radiere"),
  "Nu avem lista ANAF. Temeiul: Codul de procedură fiscală, art. 92 (inactivare pentru sediu expirat; dizolvare după un an). În model, valul fiscal adaugă la vârf " + C68[2] + " zile." + E("C68", "C155"),
  "NEVERIFICABIL", "—"),
 ("NF §2.2", q("Din cele 1.792 de posturi aprobate"),
  "Numărul maxim de posturi pentru ONRC și cele 42 de oficii, stabilit prin HG nr. 592/2024, anexa 2." + E("C51"),
  "CONFIRMAT", "lege"),
 ("NF §2.2", q("sunt ocupate 1.250, reprezentând 69,75%, în condițiile în care pentru anul 2026 sunt finanțate 1.384 de posturi"),
  "Aritmetica se verifică (" + C156[2] + ")." + E("C156") + " Rezultă " + V("C51").split("→ ")[1] + " din cele finanțate, dacă definițiile se aliniază." + E("C51") + " Nu avem o sursă proprie pentru ocupare și finanțare.",
  "NEVERIFICABIL", "aritmetică verificată"),
 ("NF §2.2", q("repartizarea aleatorie a cererilor la nivel național, în scopul echilibrării volumului de muncă"),
  "Efectul se vede: mediana pe oficiu, deciziile din 1–18 noiembrie, e între " + V("C49").replace("–", " și ") + " de zile; coada e practic națională." + E("C49", "C75") + " Mecanismul de repartizare nu e public.",
  "COMPATIBIL", "măsurat"),
 ("NF §2.2", q("a fost implementată măsura prevăzută prin Legea nr. 3/2026 [...] care permite personalului de conducere de specialitate juridică să fie desemnat"),
  "Aportul conducerii desemnate nu e publicat, iar raportul nu analizează persoane. În model l-am tratat ca ipoteză de test (capitolul 2, Art. II)." + E("C160"),
  "NEVERIFICABIL", "—"),
 ("Preambul", q("din motive obiective, independente de modul de organizare instituțională"),
  "Producția a crescut, iar vârful de cereri e concentrat în septembrie, înainte de finalul perioadei inițiale CAEN." + E("C87", "C99", "C152") +
  " O parte din muncă se naște însă în proces: circa o decizie din cinci e o amânare, " + C139[0].split(" (")[0] + " dintre ele aveau numai motive evitabile la depunere, iar aproape toate respingerile vin după o amânare." + E("C21", "C139", "C144") + " " + W("C139").split(". ")[0] + ".",
  "COMPATIBIL", "măsurat"),
 ("NF §2.2", q("evoluție care demonstrează necesitatea consolidării simultane a capacității de prelucrare și de soluționare"),
  "Modelul în tandem confirmă: întărind doar etapa a doua, registratorii rămân fără dosare, iar coada de operare crește; doar întărirea ambelor etape reduce stocul total." + E("C56") +
  " Articolele proiectului întăresc însă doar soluționarea (capitolul 2).",
  "CONFIRMAT", "model"),
 ("Preambul", q("măsurile [...] prevăzute de cadrul normativ în vigoare, inclusiv [...] personalul cu funcții de conducere [...] nu sunt suficiente"),
  "Prognoza fără măsuri noi, care include mecanismul existent: " + V("C59") + " zile în iunie 2027, la vârf " + V("C60") + " zile (scenarii)." + E("C59", "C60"),
  "COMPATIBIL", "model"),
 ("Preambul; NF §3.5", q("impactul semnificativ al dificultăților [...] asupra mediului de afaceri") + "; NF §3.5 nu cuantifică impactul.",
  "Costul economic al întârzierilor, august–18 noiembrie: " + V("C106") + " milioane de lei (prudent / central / tensionat), interval de scenarii, nu măsurătoare." + E("C106") +
  " În octombrie–noiembrie, de circa " + BR.ORI + " ori costul unei luni obișnuite." + E("C111"),
  "COMPATIBIL", "model, scenarii"),
 ("NF §3.5", q("Acestea vor contribui la diminuarea progresivă a soldului de cereri restante"),
  "Față de situația fără proiect, da: câștig " + GAIN_OUG + " zile în iunie 2028, pe aceleași simulări." + E("C43") +
  " Stocul din iunie 2028: " + STOCK28 + " (fără / cu proiect), deci tot peste punctul de pornire al modelului (≈200.000)." + E("C158"),
  OBJ_PART, "model"),
 ("Preambul; NF §2.3", q("astfel încât să fie asigurată soluționarea eficientă a cererilor, în termenele prevăzute de lege") + "; " + q("restabilirea unui ritm normal de efectuare a înregistrărilor"),
  "Termenul legal e de " + V("C23") + " zi lucrătoare." + E("C23") + " Cu proiectul, așteptarea ar rămâne " + V("C43") + " zile în iunie 2028 și " + EXP_OUG + " la expirarea măsurilor." + E("C43", "C158") +
  " Doar prin personal, revenirea la circa 3 zile ar cere " + C55 + "." + E("C55"),
  OBJ_NOT, "model"),
 ("NF §2.3; §4.8", q("se propune și prelungirea aplicării sale pentru încă 1 an [...] până la consolidarea resurselor umane ale instituției"),
  "Continuitatea e asigurată până la 8.01.2028. Consolidarea resurselor umane nu se poate evalua: nota nu are un plan de ocupare, iar în 2026 concursurile sunt suspendate, cu excepții limitate." + E("C153") +
  " În model, la 31.01.2028 coada nu e golită: " + EXP_JAN + " zile (fără / cu proiect)." + E("C158"),
  OBJ_PART, "lege; model"),
 ("NF §4.6–4.8", q("Pentru anul 2027 s-a avut în vedere un impact lunar de 480 mii lei/lună [...] x 12 luni = 5.760 mii lei/an") + "; fără impact în 2026.",
  "Aritmetica se verifică: " + C156[0] + "." + E("C156", "C83") + " Nota nu spune câte persoane; perioada din 2026 de după intrarea în vigoare și 1–8.01.2028 nu au linie bugetară proprie.",
  "CONFIRMAT", "aritmetică"),
 ("NF §2.3", q("Adaptările necesare ale sistemului informatic vor fi efectuate în termen de 15 de zile"),
  "Nu se poate măsura din date publice. Modelul a presupus aplicarea art. III de la " + C159[3].split("art. III de la ")[1] + "." + E("C159"),
  "NEVERIFICABIL", "—"),
 ("NF §5.3", q("contribuie la asigurarea aplicării directivelor europene recente ce vizează digitalizarea în domeniul societar"),
  "Dintre firmele noi admise fără amânare în noiembrie, " + V("C41").split(" ")[0] + " au așteptat peste 10 zile lucrătoare; pragul european de 5/10 zile se aplică doar constituirilor online." + E("C41") +
  " Proiectul ajută în direcția corectă, dar în model rămâne la luni." + E("C43"),
  OBJ_PART, "măsurat; model"),
]
COUNTS = collections.Counter(r[3].split(" — ")[0] for r in ROWS); COUNTS_OBJ = collections.Counter(r[3] for r in ROWS if r[3].startswith("OBIECTIV"))
KEYS = ("CONFIRMAT", "COMPATIBIL", "CONTRAZIS", "NEVERIFICABIL", "OBIECTIV")
NROWS = len(ROWS)


def claims_table():
    trs = "".join(f'<tr><td class="nr">{i}</td><td><span class="srcref">{s}</span> {c}</td><td>{o}</td><td>{pill(v)}<span class="basis">{b}</span></td></tr>'
                  for i, (s, c, o, v, b) in enumerate(ROWS, 1))
    return ('<div class="tbl-wrap allow-break ckwrap"><div class="tbl-head"><span class="tnum">Tabelul 1</span> Afirmațiile din preambul și din nota de fundamentare, verificate pe datele noastre</div>'
            '<table class="ck"><thead><tr><th>Nr.</th><th>Ce afirmă proiectul sau nota (citat)</th><th>Ce arată datele noastre și cum am calculat</th><th>Verdict · bază</th></tr></thead>'
            f'<tbody>{trs}</tbody></table>'
            '<p class="tcap">Verdicte: CONFIRMAT = aceeași valoare sau concluzie, în marja măsurării; COMPATIBIL = aceeași direcție, cu o diferență de definiție sau de nuanță; '
            'CONTRAZIS = datele noastre arată clar opusul, pentru aceeași perioadă și aceeași definiție; NEVERIFICABIL = nu se poate verifica din datele noastre; '
            'OBIECTIV = scop sau efect așteptat al proiectului, nu o afirmație de fapt: îl comparăm cu modelul (atins parțial sau neatins). O afirmație adevărată pentru perioada la care se referă e CONFIRMATĂ, chiar dacă situația s-a schimbat ulterior. „Bază” spune dacă verdictul vine din date măsurate, din model sau din textul legii: '
            'un verdict de model nu este o măsurătoare.</p></div>')


def ch1():
    b = BR.idea("Diagnosticul din proiect se confirmă în mare: cererile au crescut brusc în august–octombrie, mai ales în septembrie, iar capacitatea nu a ținut pasul. "
                "Nicio afirmație de fapt nu e contrazisă de datele noastre; creșterea de peste opt ori nu se reproduce din datele noastre (posibil, unități diferite), iar obiectivul revenirii la termenele legale nu e atins în model.")
    b += P(f"Am extras din preambul și din nota de fundamentare fiecare afirmație care poate fi verificată: cifre, cauze, efecte așteptate și termene. "
           f"Pentru fiecare am pus alături valoarea noastră, cum am calculat-o și un verdict. Cele {NROWS} de afirmații se împart astfel: "
           f"{hl(str(COUNTS['CONFIRMAT']) + ' confirmate, ' + str(COUNTS['COMPATIBIL']) + ' compatibile, ' + str(COUNTS['CONTRAZIS']) + ' contrazise și ' + str(COUNTS['NEVERIFICABIL']) + ' neverificabile din datele noastre')}; "
           f"alte {COUNTS['OBIECTIV']} sunt obiective ale proiectului, comparate cu modelul ({COUNTS_OBJ[OBJ_PART]} atinse parțial, {COUNTS_OBJ[OBJ_NOT]} neatins). "
           "Unde datele diferă, dăm explicația cea mai probabilă: de regulă, o definiție diferită sau o perioadă diferită.",
           "Cum se citește", "Textul dintre ghilimele e citat din proiect sau din notă. Codurile [Cxx] duc la registrul afirmațiilor: sursă, script, amprenta datelor.")
    b += wide(claims_table())
    b += h3("1.1 Ce reținem din verificare")
    b += P(hl("Povestea intrărilor se confirmă pe date independente.") + " Contorul național al numerelor de cerere, eșantionul din portal și buletinul BERC dau aceeași creștere ca nota: "
           f"august–octombrie cu {R_AO.lstrip('+')} peste primul semestru și septembrie de {R_SEP.lstrip('×')} ori nivelul obișnuit." + E("C161", "C99") +
           " Și stocul oficial se reproduce: estimarea noastră pentru 6 noiembrie e la circa 1% de cifra ministerului." + E("C100", "C28"))
    b += P(hl("Creșterea „de peste opt ori” nu se reproduce din datele BERC analizate de noi; cifra de peste " + C154[2].split(" pe zi")[0].lstrip(">") + " de cereri pe zi are însă ordinul de mărime al tuturor cererilor de pe contorul național.") +
           f" Pe contor, toate tipurile de cereri dau {CNT26} de numere pe zi lucrătoare în ianuarie–iulie 2026 și {CNT25} în aceeași perioadă din 2025: nivelul e aproape stabil." + E("C165") +
           f" Cifrele de {C154[0]} și {C154[1]} pentru 2024–2025 și cele {V('C47').split(' →')[0]} din primul semestru corespund cererilor de înregistrare; explicație posibilă: unități diferite." + E("C154", "C47") +
           " Recomandăm ca nota să precizeze unitatea fiecărei serii.",
           "De ce contează", "O creștere de opt ori ar justifica alte măsuri decât o creștere de circa jumătate. Unitatea corectă schimbă dimensionarea.")
    b += P(hl("Afirmația că volumul depășește capacitatea se confirmă pentru august–octombrie și pentru prognoza din 2027.") +
           f" În august–octombrie intrau {AUGOCT} cereri pe zi lucrătoare, față de circa {DEC_AO} decizii; în model, în 2027 intră mai multă muncă decât poate ieși." + E("C99", "C86", "C67") +
           f" În noiembrie, intrările au coborât temporar sub ritmul deciziilor ({NOV} pe zi) și stocul a început să scadă încet; valurile CAEN, de capital și fiscal îl vor împinge din nou în sus." + E("C99", "C100", "C68"))
    b += P(hl("Obiectivul declarat, soluționarea „în termenele prevăzute de lege”, nu e atins în model.") +
           f" Cu proiectul, așteptarea ar rămâne de ordinul lunilor, iar la expirarea măsurilor, în ianuarie 2028, de circa {EXP_OUG.split(' (')[0].lstrip('≈')} de zile, față de termenul de o zi lucrătoare." + E("C43", "C158", "C23") +
           " Proiectul ajută, dar singur nu închide distanța.")
    b += P("Observații de redactare, utile pentru consultare: nota (§2.3) trimite la „Ordonanța de urgență a Guvernului nr. 109/2014”, iar proiectul (art. II) la OUG nr. 109/2024, aprobată prin Legea nr. 3/2026: trimiterile pot fi armonizate; "
           "preambulul compară cu „primele șapte luni”, nota cu „primul semestru”; „funcții învestite” (art. III–IV) diferă de „persoane învestite” (nota).",
           "Notă", "Aceste observații nu schimbă cifrele; ele cer doar o formulare fără ambiguitate.")
    return sect("Capitolul 1", "ao-c1", "Ce afirmă proiectul și ce arată datele",
                "Fiecare afirmație factuală din preambul și din nota de fundamentare, cu valoarea noastră, metoda și verdictul.",
                "Surse: proiectul OUG și nota de fundamentare (consultare MJ, 18.11.2026) · BERC până la 20.11.2026 · contorul cererilor și eșantionul myportal · modelul verificat", b, runon=False)


# ================================================================== 2. ARTICLE BY ARTICLE
def ch2():
    b = BR.idea("Efectul proiectului vine aproape în întregime din art. I: câți consilieri ajung efectiv la soluționare și din ce activități vin. "
                "Art. III mută foarte puțină muncă, art. II prelungește ce există, iar art. IV e o condiție tehnică pentru art. III.")
    # ---- Art. I
    b += h3("2.1 Art. I · Consilierii juridici specialiști, desemnați registratori")
    b += quote_box("Proiectul, art. I alin. (1), (4) și (6)", [
        q("Personalul de specialitate juridică încadrat în funcția de execuție de consilier juridic specialist [...] poate fi desemnat, pe durata prevăzută la art. II alin. (1), pentru motive temeinic justificate și cu acordul prealabil, exprimat în scris, să realizeze serviciul public al controlului de legalitate"),
        q("Personalul desemnat [...] are calitatea de registrator în raport cu actele pe care le efectuează sau emite"),
        q("Pe perioada desemnării, [...] nu realizează și operațiuni din categoria celor prevăzute la art. 5^2")],
        "Proiect de OUG, consultare publică, 18.11.2026")
    b += P("<b>Ce schimbă.</b> Proiectul adaugă capacitate la etapa registratorului, cu personal propriu al ONRC, fără posturi noi și cu diferența salarială de registrator. "
           "Textul nu spune câte persoane, din ce activități vin și cât timp net vor avea pentru dosare; nota spune doar că desemnarea se face " + q("în raport cu necesitățile instituționale") + ". "
           + hl("Fără aceste trei date, efectul nu se poate estima dinainte; îl putem doar încadra între variante.") + E("C159"),
           "Ce nu spune nota", "Câți consilieri juridici specialiști are ONRC, câți ar accepta și ce fac astăzi: operare, mențiuni din oficiu sau alte sarcini juridice. Verdict: neverificabil.")
    b += P(f"<b>Cât contează numărul de oameni.</b> Modelul verificat a testat trei variante de livrare: {VAR_LO}, {VAR_MID} și {VAR_HI} unități pe zi (echivalente de normă întreagă × dosare-standard pe zi)." + E("C159") +
           f" Câștigul median în iunie 2028, pe aceleași simulări: {WEAK_GAIN} zile în varianta redusă, {GAIN_OUG} în cea centrală și {STRONG_GAIN} în cea ridicată (scenarii, intervale largi)." + E("C61", "C43") + " " +
           hl(f"Un efect vizibil, de ordinul unei luni, cere echivalentul a cel puțin 15 oameni cu normă întreagă la soluționare; revenirea la circa 3 zile doar prin personal ar cere {C55}.") + E("C55") +
           f" Sistemul e foarte sensibil: 10% capacitate în plus sau în minus mută așteptarea din iunie 2028 la {UP10}, respectiv {DN10} de zile." + E("C63"),
           "Rezervă", W("C159") + " " + W("C55").split(". ")[1] + ".", key=True)
    b += chart("figures_institutii", "fi24_doua_cozi_schema.svg", "Drumul unui dosar: două cozi, una după alta", ["C28", "C29", "C99", "C01", "C35"],
               "Cererea intră întâi la operare (preluare și verificare formală), apoi la registrator (decizie). Schema dă stocul din fiecare coadă la 6 noiembrie, intrările și deciziile finale pe zi." + E("C28", "C29", "C99", "C01"),
               "Art. I întărește doar a doua coadă. Dacă desemnații vin din operare, prima coadă pierde exact capacitatea câștigată de a doua.",
               "Orice desemnare trebuie judecată pe tot drumul dosarului; nota spune același lucru despre „consolidarea simultană”." + E("C56"))
    b += P(f"<b>De unde vin oamenii.</b> Dacă desemnații sunt luați din operare, câștigul are un plafon: în modelul în tandem, optimul e la {OPT} de dosare mutate pe zi, iar la {ZERO} câștigul dispare." + E("C35") +
           f" Varianta centrală ({U_MID} pe zi) e sub optim: ar ajuta și dacă oamenii vin din operare, dar mai puțin decât arată modelul cu o singură coadă. " +
           hl(f"Varianta ridicată ({U_HI} pe zi) depășește pragul de câștig zero: rezultatul ei, {STRONG} zile, e posibil doar dacă desemnații nu vin din operare.") + E("C61", "C35"),
           "Cum se citește", "Cele două modele folosesc unități apropiate (dosare pe zi lucrătoare); comparația dă ordinul de mărime, nu o cifră exactă. " + REG["C35"]["rezerva_obligatorie"])
    b += chart("figures_institutii", "fi06_tandem.svg", "Cele două etape au stocuri aproape egale", ["C56", "C29", "C34"],
               f"Stocul nesoluționat pe cele două etape: la 6 noiembrie, din {V('C28')} de cereri, {V('C29')} erau încă la operare. Operarea lucra cu circa {V('C34').lstrip('≈')} mai repede decât soluționarea." + E("C28", "C29", "C34"),
               "Cu stocuri aproape egale, a doua coadă nu poate crește mult mai repede decât prima fără să rămână fără dosare pregătite.",
               "Întărind doar etapa a doua, registratorii rămân fără dosare, iar coada de operare crește; doar întărirea ambelor etape scade stocul total." + E("C56"))
    b += chart("figures_institutii", "fi10_canibalizare.svg", "Mutarea oamenilor din operare are un optim și un prag de câștig zero", ["C35"],
               "Producția totală a sistemului în funcție de câte dosare pe zi preiau la soluționare oamenii mutați din operare.",
               f"Varianta centrală a proiectului ({U_MID}/zi) cade înaintea optimului ({OPT}/zi); varianta ridicată ({U_HI}/zi) cade după pragul de câștig zero ({ZERO}/zi)." + E("C159", "C35"),
               "Amendament util: desemnarea din alte activități decât operarea și publicarea activității de proveniență a fiecărui desemnat.")
    b += P("<b>Art. I și art. III folosesc același personal.</b> Art. III dă mențiunile din oficiu " + q("exclusiv") + " consilierilor juridici specialiști, iar art. I alin. (6) îi scoate din aceste sarcini pe cei desemnați registratori. "
           + hl("Fiecare consilier desemnat registrator lasă mai puțini oameni pentru noul flux din art. III.") +
           " La volumul vizibil azi în BERC, concurența e mică; dacă art. 5^1 aduce și actele altor autorități, ea poate deveni importantă (secțiunea 2.3)." + E("C157"),
           "Recomandare", "Proiectul ar trebui să spună câți consilieri rămân pentru art. III și ce se întâmplă dacă noul flux acumulează restanțe.")
    b += counter_case(["Un argument contrar: consilierii pot veni din sarcini juridice care nu țin de operare (contencios, avizare), iar atunci plafonul din modelul în tandem nu se aplică. E posibil, și de aceea textul final ar trebui să o spună explicit.",
                       "Datele publice nu arată însă ce fac azi consilierii eligibili. Fără această informație, o evaluare corectă după adoptare cere raportarea separată a orelor mutate și a activității de proveniență."])
    # ---- Art. II
    b += h3("2.2 Art. II · Durata, până la 8 ianuarie 2028, și prelungirea mecanismului existent")
    b += quote_box("Proiectul, art. II", [q("Măsura prevăzută la art. I [...] se aplică până la data de 8 ianuarie 2028."),
                                          q("Termenul prevăzut de art. 2 din Legea nr. 3/2026 [...] se prelungește până la data de 8 ianuarie 2028.")],
                   "Proiect de OUG, consultare publică, 18.11.2026")
    b += P("<b>Ce schimbă.</b> Fără art. II alin. (2), desemnarea conducerii de specialitate juridică pentru atribuțiile de registrator ar expira la 8 ianuarie 2027, potrivit notei, exact înaintea valului CAEN. "
           "Aportul acestui mecanism nu e publicat. " + hl(f"În model, dacă el valorează 75 sau 150 de dosare-standard pe zi, prelungirea câștigă în iunie 2028 circa {C160[0].split('câștig ')[1]}, respectiv {C160[1].split('câștig ')[1]} zile.") + E("C160") +
           " Prelungirea e deci utilă, dar efectul ei e mic față de cel al art. I.",
           "Rezervă", W("C160"))
    b += P(f"<b>Durata față de prognoză.</b> Măsurile expiră la 8 ianuarie 2028. Prognoza fără măsuri noi urcă la {V('C59')} zile la mijlocul lui 2027 și la un vârf de {V('C60')} zile." + E("C59", "C60") + " " +
           hl(f"La expirare, coada nu e golită în nicio variantă centrală: la 31 decembrie 2027, {EXP_DEC} zile, iar la 31 ianuarie 2028, {EXP_JAN} zile (fără / cu proiect).") + E("C158") +
           " După 8 ianuarie 2028, capacitatea adusă de desemnări dispare dintr-odată. Un criteriu de ieșire legat de indicatori ar evita această treaptă (propunerea 7).",
           "Rezervă", W("C158").split(". ")[0] + ". " + W("C158").split(". ")[-1], key=True)
    b += chart("figures_institutii", "fi12_prognoza.svg", "Prognoza fără măsuri noi: așteptarea crește puternic în 2027", ["C59", "C60", "C42"],
               "Câte zile ar aștepta un dosar depus în fiecare săptămână, până în iunie 2028, dacă nu se schimbă nimic. Linia e mijlocul simulărilor; banda arată 8 din 10 variante.",
               f"Măsurile proiectului acoperă tot anul 2027, dar expiră înainte ca prognoza să coboare: în iunie 2028, fără proiect, {V('C42')} zile; cu proiectul, {V('C43')}." + E("C42", "C43"),
               "Prelungirea cu încă un an e necesară; o prelungire condiționată de indicatori ar fi mai sigură decât o dată fixă.")
    # ---- Art. III
    b += h3("2.3 Art. III · Mențiunile din oficiu, fără control de legalitate")
    b += quote_box("Proiectul, art. III: noile art. 5^1 și 5^2 din Legea nr. 265/2022", [
        q("Mențiunile în baza unei hotărâri judecătorești sau a actelor prevăzute la art. 5^1 se înregistrează, din oficiu, de personalul de specialitate juridică încadrat în funcția de execuție de consilier juridic specialist"),
        q("personalul de specialitate juridică verifică proveniența actului, identificarea profesionistului, individualizarea măsurii și concordanța dintre act și mențiunea de înscris, fără a examina legalitatea măsurii dispuse de emitentul actului")],
        "Proiect de OUG, consultare publică, 18.11.2026")
    b += P("<b>Ce schimbă.</b> Înscrierile făcute în baza unei hotărâri judecătorești sau a actului altei autorități ies din coada registratorului și devin o operațiune administrativă. "
           "Soluția are logică juridică: controlul de legalitate al măsurii l-a făcut deja emitentul. " +
           hl(f"Volumul e însă mic: în BERC, mențiunile pe hotărâri judecătorești au fost {HJ_H1} în S1 2026, {HJ_AO} în august–octombrie și {HJ_NV} în 2–17 noiembrie, adică {HJ_SH} din toate deciziile.") + E("C157") +
           " Categoria e un reper parțial: poate include și articole de certificare, iar actele altor autorități pot apărea în alte categorii sau deloc în buletin.",
           "Rezervă", REG["C157"]["rezerva_obligatorie"])
    b += P(f"<b>Ce arată modelul.</b> Doar art. III câștigă, pe aceleași simulări, {V('C44')} în iunie 2028." + E("C44") +
           " Ipoteza modelului e mai generoasă decât volumul vizibil în BERC, deci câștigul real ar putea fi și mai mic. "
           f"Singura cale prin care art. III ar conta mai mult este ca art. 5^1 să cuprindă și procedurile inițiate de ANAF, pentru care nota dă {NF_ANAF} de entități." + E("C155") +
           " Dacă aceste proceduri sunt „acte” care se înscriu fără analiza registratorului depinde de Legea nr. 239/2025, pe care nu am reverificat-o aici; o listă ANAF nu este, în sine, un act care se înscrie.",
           "De reținut", "Art. IV alin. (3): procedurile începute înainte de intrarea în vigoare rămân sub legea veche. Art. III nu atinge deci stocul actual.")
    b += P("<b>Riscuri de aplicare.</b> Art. 5^2 alin. (3) trimite neconcordanțele înapoi la emitent; fără un termen pentru răspuns, cererile de clarificare pot crea o coadă nouă, nevăzută în indicatorii actuali. "
           "Pentru că se renunță la controlul registratorului, merită publicate numărul de acte primite, clarificările cerute și erorile constatate după înscriere (propunerea 6).")
    b += chart("figures_institutii", "fi09_oug.svg", "Proiectul complet ajută; art. III singur aproape deloc", ["C44", "C42", "C43"],
               "Așteptarea estimată în iunie 2028 fără măsuri noi, doar cu art. III și cu proiectul complet. Punctul e mijlocul simulărilor; bara e intervalul p10–p90.",
               f"Câștigul se măsoară pe aceleași simulări: {V('C44')} pentru art. III, {GAIN_OUG} zile pentru proiectul complet." + E("C44", "C43"),
               "Art. III e o simplificare utilă și ieftină, nu o măsură împotriva cozii. Efectul proiectului depinde de art. I.")
    # ---- Art. IV
    b += h3("2.4 Art. IV · Fluxul informatic, în 15 zile")
    b += P("<b>Ce schimbă.</b> ONRC are 15 zile pentru a adapta sistemul informatic la noul flux, iar art. III se aplică " + q("de la data optimizării fluxului în sistemul informatic") + ". "
           "Fezabilitatea nu se poate măsura din date publice, iar data optimizării nu are o formă de publicare: proiectul ar trebui să ceară publicarea ei, pentru că de ea depinde regimul juridic al înscrierilor. "
           "La secțiunea 3.7 (inovare și digitalizare), nota menționează " + q("Nu este cazul") + "; o evaluare a adaptării informatice din art. IV ar fi utilă.",
           "Ce lipsește", "Costul adaptării, cine o face și cum se testează nu apar în notă.")
    b += P(hl("Același articol ar putea purta o măsură cu efect mult mai mare: verificările automate la depunere.") +
           f" Pentru {V('C143').split(' · ')[0].split(' / ')[0]} din cele 12 motive de amânare, soluția principală e o verificare standard, fără AI." + E("C143") +
           f" Cel mult {AVOID.lstrip('≈')} de amânări pe zi lucrătoare ar dispărea, iar analiza registratorilor s-ar muta spre dosarele noi." + E("C141") +
           " Decizia rămâne la registrator; programul doar pregătește și semnalează." + E("C142"),
           "Rezervă", W("C141").split(". ")[0] + ". " + W("C139").split(". ")[0] + ".")
    b += chart("figures_impact", "i08_motive_amanare.svg", "De ce se amână dosarele și ce se poate verifica automat la depunere", ["C139", "C143", "C141"],
               "Motivele amânărilor din 19 octombrie–18 noiembrie 2026, după nivelul de automatizare al soluției: verificare standard, AI, AI avansat sau judecata registratorului.",
               "Art. IV se ocupă doar de fluxul pentru art. III. O completare cu verificări la depunere ar lucra pe o parte mult mai mare a muncii.",
               f"Circa o amânare din cinci avea numai motive evitabile la depunere, iar aproape jumătate cel puțin unul ({C139[0].split(' (')[0]} / {C139[1].split(' (')[0]})." + E("C139"))
    b += concl("Proiectul e util, dar efectul lui depinde de un singur lucru pe care textul nu-l fixează: câți consilieri ajung efectiv la soluționare și din ce activități vin. "
               "Art. II e necesar, art. III e o simplificare corectă, dar mică, iar art. IV poate deveni mult mai valoros dacă se extinde la verificările de la depunere.")
    return sect("Capitolul 2", "ao-c2", "Articol cu articol: ce schimbă și ce efect are",
                "Ce prevede fiecare articol, ce arată datele și modelele noastre despre efectul lui și unde are limite.",
                "Surse: textul proiectului · model verificat (scenariile OUG, 2.000 de variante) · model în tandem · BERC · motivele amânărilor (buletine PDF)", b)


# ================================================================== 3. WHAT IS MISSING
def ch3():
    b = BR.idea("Cele mai mari pârghii nu sunt în proiect: valul CAEN din 2027, verificările la depunere, ocuparea posturilor finanțate și etapa de operare. "
                "Prima se poate trata cu o conversie automată, iar perioada de tranziție se stabilește prin hotărâre de Guvern.")
    b += h3("3.1 Valul CAEN din 2027")
    b += P(f"Nota dă {NF_CAEN_LEFT} de entități care nu și-au actualizat încă codurile CAEN." + E("C155") +
           f" Prognoza noastră de bază presupune un val de {C162}: deja acest val face din CAEN cea mai mare sursă de risc, cu circa {C68[0].split(' (')[0].lstrip('≈')} de zile la vârf." + E("C162", "C68") + " " +
           hl(f"Dacă 80% sau toate entitățile rămase ar depune înainte de sfârșitul perioadei de tranziție, așteptarea din iunie 2027 ar urca la {CAEN80}, respectiv {CAEN100} de zile; cu o conversie automată a codurilor simple, la {CONV80}, respectiv {CONV100}.") + E("C94", "C95"),
           "Rezervă", W("C94").split(". ")[0] + ". " + W("C95").split(". ")[1].rstrip(".") + ".", key=True)
    b += P("Perioada de tranziție este stabilită prin HG nr. 656/1997, art. 5^1, nu prin lege, iar ambele versiuni ale codurilor sunt valabile în această perioadă." + E("C152") +
           " Guvernul o poate corela cu capacitatea ONRC fără o lege nouă. Conversia automată „1-la-1”, fără modificarea actului constitutiv, cere însă o normă de rang legal: proiectul de OUG este vehiculul potrivit (propunerea 1)." + E("C53"))
    b += chart("figures_institutii", "fi22_caen.svg", "Riscul valului CAEN și efectul conversiei automate", ["C94", "C95", "C152"],
               "Așteptarea din iunie 2027 dacă firmele depun în masă actualizările CAEN înainte de sfârșitul perioadei de tranziție (roșu) și dacă codurile simple sunt convertite automat (verde).",
               "Proiectul nu tratează valul. O conversie automată în OUG și o perioadă de tranziție corelată cu capacitatea, prin HG, ar trata direct cea mai mare sursă de risc.",
               "E măsura cu cel mai mare efect și cel mai mic cost din toate cele testate.")
    b += h3("3.2 Verificările la depunere")
    b += P(f"Circa o decizie din cinci e o amânare, iar {C139[0].split(' (')[0]} dintre amânări aveau numai motive evitabile la depunere." + E("C21", "C139") +
           f" Aproape toate respingerile ({V('C144').split(' (')[0]}) vin după o amânare a aceleiași cereri, iar după o respingere aproape jumătate din firme depun din nou în 30 de zile: aceeași muncă se face de două ori." + E("C144", "C103") + " " +
           hl("Verificările la depunere țin de ONRC și ADR, nu cer o lege nouă și pot începe imediat; proiectul le-ar putea da un termen și un temei explicit în art. IV.") + E("C143"),
           "Rezervă", W("C139").split(". ")[0] + ".")
    b += h3("3.3 Ocuparea posturilor finanțate")
    b += P(f"Nota dă {V('C51').split(' → ')[0].replace(' / ', ', ')} posturi (aprobate, finanțate, ocupate): rezultă {V('C51').split('→ ')[1]}." + E("C51") +
           " În 2026, concursurile sunt suspendate, iar Ministerul Justiției poate aproba excepții limitate." + E("C153") + " " +
           hl(f"Un pachet cu OUG extins și ocuparea a 40% din posturile vacante finanțate ar coborî așteptarea din iunie 2028, în model, la {V('C52')} zile.") + E("C52") +
           " " + BR.HIRE_40 + " Proiectul de OUG poate conține direct o derogare pentru ONRC (propunerea 4).",
           "Rezervă", W("C52").split(". ")[0] + ".")
    b += h3("3.4 Etapa de operare")
    b += P(f"Jumătate din stocul oficial era la operare la 6 noiembrie ({V('C29')})." + E("C29") +
           " Nota observă corect că trebuie întărite simultan prelucrarea și soluționarea, dar niciun articol nu adaugă capacitate la operare. "
           + hl(f"În modelul în tandem, extinderea echilibrată a ambelor etape lasă după 120 de zile lucrătoare un stoc de circa {C56.split('total ')[1].split(' vs')[0].lstrip('≈')}, față de {C56.split('vs ')[1].split(' fără')[0].lstrip('≈')} fără măsuri.") + E("C56"),
           "Rezervă", REG["C56"]["rezerva_obligatorie"])
    b += h3("3.5 Datele și evaluarea")
    b += P("În textul notei analizat de noi nu am găsit conținut la secțiunile 3.1, 6.2 și 8.1 (beneficii și costuri, consultări, monitorizare) și nici indicatori de rezultat sau o dată de evaluare. "
           "Datele care ar permite verificarea efectului există la ONRC: stocul zilnic pe etape și tipuri de cereri, intrările, deciziile, amânările și respingerile pe oficii, "
           "persoanele desemnate și orele lor nete. Legea nr. 544/2001, art. 5, și ROF-ul ONRC, art. 16, permit publicarea lor fără o normă nouă (propunerea 6).")
    b += concl("Proiectul tratează capacitatea la registrator. Ce lipsește tratează volumul de muncă: CAEN, amânările evitabile și ocuparea posturilor. "
               "Fără aceste completări, câștigul rămâne parțial, iar riscul cel mai mare, valul CAEN, rămâne neacoperit.")
    return sect("Capitolul 3", "ao-c3", "Ce nu tratează proiectul",
                "Pârghiile care lipsesc din text, cât cântărește fiecare în model și cine le poate aplica.",
                "Surse: nota de fundamentare · HG nr. 656/1997 · Legea nr. 141/2025 · motivele amânărilor și respingerilor · model verificat · model în tandem", b)


# ================================================================== 4. AMENDMENTS
AMEND = [
 ("Conversia automată a actualizărilor CAEN „1-la-1”", "Articol nou: codurile CAEN Rev. 2 cu un singur corespondent în Rev. 3 se actualizează din oficiu, fără modificarea actului constitutiv și fără cerere; Guvernul corelează perioada de tranziție cu capacitatea ONRC.",
  "HG nr. 656/1997, art. 5^1 alin. (1)–(3) (perioada, prin HG); competența MJ de a iniția un regim simplificat (HG nr. 592/2024, art. 6 pct. II.3)",
  f"Iunie 2027, val CAEN de 80% / 100%: {CAEN80} / {CAEN100} → {CONV80} / {CONV100} zile." + E("C94", "C95") + f" Pachetul P4: {V('C53')}." + E("C53")),
 ("Verificări automate la depunere", "Art. IV completat: ONRC (cu ADR) introduce, într-un termen fixat, verificările automate pentru motivele standard de amânare; decizia rămâne la registrator.",
  "Legea nr. 265/2022, art. 24 alin. (1) lit. g), n) și art. 106; Legea nr. 242/2022, art. 11",
  f"Cel mult {AVOID.lstrip('≈')} de amânări pe zi lucrătoare evitate." + E("C141") + " Respingerile scad odată cu amânările." + E("C146")),
 ("Întărirea ambelor etape", "Art. I completat: desemnarea sau redistribuirea poate privi și etapa de operare, iar decizia de desemnare indică activitatea de proveniență.",
  "Legea nr. 265/2022, art. 22 alin. (1)–(2), (5); ROF ONRC, art. 6 alin. (7)",
  f"Stoc după 120 de zile lucrătoare: echilibrat ≈{C56.split('total ')[1].split(' vs')[0].lstrip('≈')} față de ≈{C56.split('vs ')[1].split(' fără')[0].lstrip('≈')}." + E("C56")),
 ("Derogare de la suspendarea concursurilor pentru ONRC", "Articol nou: ONRC poate ocupa prin concurs posturile vacante finanțate, peste limita excepțiilor din 2026.",
  "Legea nr. 141/2025, art. XXII alin. (1), (2), (4), (6)",
  f"Pachetul P3 (OUG extins + 40% din posturile vacante): {V('C52')} zile în iunie 2028." + E("C52", "C153")),
 ("Desemnați din afara operării", "Art. I alin. (1): desemnarea se face, cu prioritate, din personal care nu lucrează la operare; numărul și activitatea de proveniență se publică.",
  "Legea nr. 265/2022, art. 21 alin. (2), art. 22 alin. (5)",
  f"Fără plafon tandem: varianta ridicată {STRONG} zile e posibilă doar așa (optim {OPT}/zi; zero la {ZERO}/zi)." + E("C61", "C35")),
 ("Indicatori publicați lunar și evaluare la 6 luni", "Articol nou: ONRC publică lunar stocul pe etape și tipuri, intrările, deciziile, amânările, respingerile, persoanele desemnate și orele nete; MJ evaluează efectul la 6 luni.",
  "Legea nr. 544/2001, art. 5; ROF ONRC, art. 16 alin. (3) lit. d); Legea nr. 265/2022, art. 22",
  "Nemodelat: permite verificarea efectului." + E("C42", "C43")),
 ("Criteriu de ieșire în loc de dată fixă", "Art. II: măsurile se aplică până la 8.01.2028 și se prelungesc automat, cel mult o dată, dacă așteptarea mediană publicată depășește un prag stabilit.",
  "Constituția, art. 115 alin. (4); Legea nr. 265/2022, art. 105 alin. (1)",
  f"La 31.01.2028: {EXP_JAN} zile (fără / cu proiect): coada nu e golită." + E("C158")),
 ("Sfera și personalul pentru art. III", "Art. III: lista actelor (act–temei–operator), un termen pentru răspunsul emitentului la clarificări și un număr minim de consilieri rezervați fluxului.",
  "Legea nr. 265/2022, art. 5^1–5^2 propuse; art. I alin. (6) din proiect",
  f"Mic: câștig {V('C44')}; volum vizibil {HJ_SH} din decizii." + E("C44", "C157")),
 ("Fișa financiară completă", "Nota: numărul de persoane, diferențele salariale pe categorie, costul adaptării IT și costul de a nu acționa.",
  "Legea nr. 500/2002, art. 15; Legea nr. 69/2010, art. 15",
  f"O zi în plus cu stocul actual: {C108.split(' / ')[0]} mil. lei în economie." + E("C108")),
 ("Precizări de redactare", "Nota: aceeași trimitere ca în art. II (OUG nr. 109/2024); unitatea seriei de peste opt ori (toate cererile de pe contor sau doar cele de înregistrare); același reper (semestrul I) în preambul și în notă; „persoane învestite” în art. III–IV.",
  "Legea nr. 24/2000 (tehnica legislativă)",
  "Fără efect asupra cozii; elimină ambiguitățile." + E("C154", "C165")),
]


def ch4():
    b = BR.idea("Zece propuneri pentru consultare, fiecare cu temeiul legal și, unde îl avem, cu efectul din model. Primele cinci au cel mai mare efect.")
    trs = "".join(f'<tr><td class="nr">{i}</td><td><b>{t}</b><br>{d}</td><td>{l}</td><td>{e}</td></tr>' for i, (t, d, l, e) in enumerate(AMEND, 1))
    b += wide('<div class="tbl-wrap allow-break"><div class="tbl-head"><span class="tnum">Tabelul 2</span> Propuneri de amendamente, cu temei și efect modelat</div>'
              '<table class="am"><thead><tr><th>Nr.</th><th>Propunerea</th><th>Temei legal</th><th>Efect (model)</th></tr></thead>'
              f'<tbody>{trs}</tbody></table>'
              '<p class="tcap">Temeiurile legale sunt cele verificate pe legislatie.just.ro la 22.11.2026 (LEGAL_BASIS.md). Efectele sunt scenarii, cu ipotezele în registru; nu sunt promisiuni. '
              'Pachetele P3–P5 combină mai multe măsuri și presupun livrarea fiecăreia.</p></div>')
    b += P(hl(f"Un pachet minim realist, cu OUG prelungit, conversia CAEN, eșalonarea depunerilor și triajul la intrare, ar coborî așteptarea din iunie 2028, în model, la {V('C54')} zile.") + E("C54") +
           " Rezultatul e fragil: la o singură schimbare plauzibilă a ipotezelor, câștigul scade mult.",
           "Rezervă", W("C54").split(". ")[0] + ".", key=True)
    b += chart("figures_institutii", "fi21_pachete.svg", "Ce schimbă fiecare pachet de măsuri: așteptarea în iunie 2028", ["C54", "C52", "C53", "C43", "C42"],
               "Cinci variante pentru iunie 2028: fără măsuri, proiectul de OUG și trei pachete mai largi. Punctul e mijlocul simulărilor; bara e intervalul în care cad 8 din 10 variante.",
               f"Proiectul singur: {V('C43')} zile. Conversia CAEN și eșalonarea, fără personal nou: {V('C53')}. OUG extins și 40% din posturile vacante: {V('C52')}. Pachetul minim realist: {V('C54')}." + E("C43", "C53", "C52", "C54"),
               "Propunerile 1–5 transformă un câștig de ordinul unei luni într-unul de ordinul lunilor; fiecare are însă condiția ei de livrare.")
    return sect("Capitolul 4", "ao-c4", "Propuneri pentru consultare",
                "Amendamente concrete, fiecare cu temei legal și efectul estimat în model.",
                "Surse: LEGAL_BASIS.md (legislatie.just.ro, 22.11.2026) · model verificat (pachete P3–P5) · model în tandem · motivele amânărilor", b)


# ================================================================== 5. BUDGET
def ch5():
    b = BR.idea("Bugetul proiectului e mic și calculat corect, dar nu spune câți oameni cumpără. Comparat cu costul întârzierilor, e de ordinul a două zile de coadă; comparația e însă fragilă.")
    b += P(f"<b>Ce spune nota.</b> {C156[0]}, din diferențe salariale pentru art. I și II; fără impact în 2026 și fără posturi noi." + E("C156", "C83") +
           " Art. III nu are cost declarat, iar adaptarea informatică din art. IV nu are o linie proprie. Nota nu spune câte persoane, ce diferență pe persoană și cât revine fiecărui articol, deci numărul de oameni nu se poate deduce din buget.",
           "Rezervă", W("C156"))
    b += P(f"<b>Cât cumpără bugetul, ilustrativ.</b> Împărțit la capacitatea suplimentară din cele trei variante, bugetul înseamnă {C163.split(' (')[0]}, după cât personal ajunge efectiv la soluționare." + E("C163") +
           " " + hl("Raportul nu e un cost marginal: arată doar că, dacă desemnările livrează capacitate, suma e mică pe dosar.") + E("C163"),
           "Rezervă", W("C163"))
    b += P(f"<b>Costul de a nu acționa.</b> Fiecare zi în plus cu stocul actual costă, în scenariul central, circa {C108.split(' (')[0]} milioane de lei în economie și {C108.split(' / ')[1].split(' (')[0]} la buget." + E("C108") +
           " Cifra nu se înmulțește cu numărul de zile, pentru că stocul și compoziția lui se schimbă. "
           f"Pentru 2027, fără măsuri noi, circa {V('C122').split(' (')[0]} de milioane de lei din veniturile bugetare s-ar încasa abia după 2027: un risc de calendar, nu o pierdere; costul de finanțare al amânării e de circa {v0('C123')} de milioane." + E("C122", "C123") +
           f" Un pachet realist ar evita mutarea a circa {v0('C125')} de milioane." + E("C125"),
           "Rezervă", W("C108") + " " + W("C122").split(";")[0] + ".")
    b += P("<b>Cum se citește comparația.</b> " + hl("Chiar dacă aproape toată activitatea pierdută ar fi preluată de alte firme, costul net al întârzierilor rămâne de ordinul milioanelor sau zecilor de milioane de lei.") + E("C110") +
           " " + W("C110"),
           "Onest", "Comparația dintre bugetul OUG și costul întârzierilor sprijină direcția (măsura merită), nu o cifră de randament.")
    b += chart("figures_impact", "i07_risc_venituri_2027.svg", "Veniturile bugetare mutate în 2027", ["C122", "C125", "C83"],
               "Pe trimestre ale anului 2027, veniturile care ar intra mai târziu din cauza cozii, fără măsuri (portocaliu) și cu un pachet realist (verde).",
               f"Proiectul costă {V('C83')}; un pachet realist ar evita mutarea a circa {v0('C125')} de milioane de lei din veniturile anului." + E("C83", "C125"),
               f"Fără măsuri, circa {V('C122').split(' (')[0]} de milioane de lei s-ar încasa în anul următor; veniturile nu se pierd, dar întârzie." + E("C122"))
    b += chart("figures_impact", "i01_cost_lunar.svg", "Costul lunar al întârzierilor, din 2024", ["C111", "C106"],
               "Costul economic (sus) și încasările bugetare afectate (jos), lună de lună, în scenariul central; liniile verticale dau intervalul scenariilor.",
               f"În octombrie–noiembrie 2026, întârzierile au costat de circa {BR.ORI} ori mai mult decât într-o lună obișnuită." + E("C111"),
               f"Pentru august–18 noiembrie 2026: {V('C106')} milioane de lei (prudent / central / tensionat), interval de scenarii." + E("C106"))
    return sect("Capitolul 5", "ao-c5", "Bugetul: ce costă proiectul și ce costă coada",
                "Bugetul din nota de fundamentare, pus lângă costul estimat al întârzierilor, cu limitele comparației.",
                "Surse: nota de fundamentare, secțiunea 4 · scenariul fundamentat de cost · modelul econometric al veniturilor 2027", b)


# ================================================================== 6. LIMITS + SOURCES
def ch6():
    b = h3("6.1 Limitele acestei analize")
    b += '<ul class="body-list lim">' + "".join(f"<li>{x}</li>" for x in [
        "Scenariile de model au intervale largi; câștigurile sunt mediane pe aceleași simulări.",
        "Cifrele notei sunt citate; CAEN, capitalul și lista ANAF nu se pot verifica din datele noastre.",
        "Intrările și stocul sunt estimate din contor și din eșantionul portalului (±10%).",
        "CERERE_HJ265 e un reper parțial pentru volumul art. III.",
        "Analizăm textul pus în consultare; nu e consultanță juridică."]) + "</ul>"
    b += h3("6.2 Surse")
    src = [
        "<b>Proiectul de OUG</b> pentru instituirea unor măsuri privind activitatea de înregistrare în registrul comerțului și <b>Nota de fundamentare</b>, puse în consultare de Ministerul Justiției la 18.11.2026 (text extras: <code>independent_audit/oug_text/</code>).",
        "<b>BERC</b>, Buletinul Electronic al Registrului Comerțului: arhiva deciziilor până la " + REG["C14"]["data_date"].replace("BERC până la ", "") + "; categoriile CERERE265, INMATRIC265, AUTO_AMANARI și CERERE_HJ265; buletinele PDF pentru motivele amânărilor și ale respingerilor.",
        "<b>Contorul național al numerelor de cerere</b> și <b>eșantionul myportal</b> (21–22.11.2026), pentru intrări și stoc.",
        "<b>Modelul verificat de prognoză</b> și scenariile OUG (<code>audit_oug.py</code>, <code>audit_data/oug_2026/</code>), <b>modelul în tandem</b> (<code>tandem_bottleneck.json</code>), scenariul CAEN (<code>forecast_caen_compliance.json</code>).",
        "<b>Costuri</b>: scenariul fundamentat (<code>cost_founded.json</code>), costul lunar (<code>cost_monthly.json</code>), veniturile 2027 (<code>econometrics.json</code>).",
        "<b>Temeiuri legale</b>: <code>independent_audit/stakeholders/LEGAL_BASIS.md</code>, forme consolidate citite pe legislatie.just.ro la 22.11.2026.",
        "<b>Analize însoțitoare</b>: „Coada de la Registrul Comerțului”, raportul complet și ediția executivă (noiembrie 2026); „Evaluarea proiectului OUG” (21.11.2026).",
        "<b>Registrul afirmațiilor</b>: <code>claims_registry.csv</code>; fiecare cod [Cxx] are sursa, scriptul, amprenta SHA-256 a datelor și starea. Afirmațiile noi ale acestei analize: C154–C165."]
    b += '<ol class="body-list srcs">' + "".join(f"<li>{x}</li>" for x in src) + "</ol>"
    b += P("Toate cifrele din acest document trec prin verificatorul automat (<code>lint_numbers.py</code>): orice cifră fără cod din registru oprește publicarea.")
    return sect("Capitolul 6", "ao-c6", "Limite și surse", "Ce nu poate spune această analiză și de unde vine fiecare cifră.", "Surse: registrul afirmațiilor · LEGAL_BASIS.md", b)


def annex():
    body = ai_annex.body(hl)
    body = body.replace("<b>Proiectul de OUG din 18 noiembrie 2026</b>, după rezumatul pus în consultare.",
                        "<b>Proiectul de OUG din 18 noiembrie 2026</b> și nota de fundamentare, textul integral pus în consultare.")
    body = body.replace("Evaluarea OUG folosește rezumatul din consultare; textul final poate schimba rezultatele.",
                        "Evaluarea OUG folosește textul pus în consultare; textul adoptat poate schimba rezultatele.")
    return (f'<section class="chapter runon" style="page: ao-body;"><div class="copen"><div class="cnum">Anexă</div><h2>{ai_annex.TITLE}</h2>'
            '<p class="cdek">Transparență: ce a făcut inteligența artificială, ce a făcut autorul, ce cerințe a avut analiza, pe ce surse se bazează și ce nu se poate afla din ele.</p></div>'
            f'<div class="ai-annex">{body}</div></section>')


# ================================================================== FRONT
TITLE_H1 = "Proiectul de OUG privind registrul comerțului: ce spune, ce arată datele, ce lipsește"

def cover():
    return f"""
<section class="cover">
  <div class="eyebrow">Analiză independentă din date deschise · Consultare publică · Ministerul Justiției</div>
  <h1>{TITLE_H1}</h1>
  <p class="sub">Fiecare afirmație din preambulul proiectului și din nota de fundamentare, verificată pe datele BERC, ale portalului myportal și ale contorului cererilor; efectul fiecărui articol în modelele noastre verificate; ce ar trebui adăugat în consultare</p>
  <div class="threads" aria-hidden="true"><i class="t-e"></i><i class="t-s"></i><i class="t-m"></i><i class="t-p"></i></div>
  <p class="verdict">Diagnosticul proiectului se confirmă în mare. Măsurile ajută, dar singure nu readuc termenele legale: efectul depinde de câți consilieri ajung efectiv la soluționare, iar cel mai mare risc, valul CAEN din 2027, nu e tratat.</p>
  <p class="verdict-sub">Fiecare cifră are un cod (de exemplu [C43]) care duce la registrul afirmațiilor: sursă, script, amprenta datelor și stare. Cifrele citate din nota de fundamentare apar între ghilimele.</p>
  <dl class="meta">
    <dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
    <dt>Documente analizate</dt><dd>Proiectul de OUG și nota de fundamentare, puse în consultare la 18 noiembrie 2026</dd>
    <dt>Date</dt><dd>BERC până la {REG['C14']['data_date'].replace('BERC până la ', '')} · eșantion myportal 21–22.11.2026 · modelul verificat de prognoză</dd>
    <dt>Ediție și dată</dt><dd>Analiză pentru consultare · 23.11.2026</dd>
    <dt>Declarație de interes</dt><dd>Autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal.</dd>
    <dt>Utilizarea AI</dt><dd>{ai_annex.DISCLAIMER}</dd>
  </dl>
</section>"""


def summary():
    tiles = pulls([
        (v0("C43") + " zile", f"așteptarea în iunie 2028 cu proiectul, față de {v0('C42')} fără el (câștig {GAIN_OUG}, pe aceleași simulări)", f"{B('C43')} scenariu, interval larg{E('C43', 'C42')}", True),
        (EXP_OUG.split(" (")[0] + " zile", "așteptarea la 31.01.2028, după expirarea măsurilor, cu proiectul", f"{B('C158')} scenariu: coada nu e golită{E('C158')}", False),
        (HJ_SH, "din decizii sunt mențiuni pe hotărâri judecătorești: volumul vizibil al art. III", f"{B('C157')} BERC, S1 2026{E('C157')}", False),
        (V("C83"), "bugetul proiectului, numai diferențe salariale, pentru 2027", f"{B('C156')} nota de fundamentare{E('C156', 'C83')}", False),
    ])
    concls = [
        f"Diagnosticul se confirmă pe date independente: cererile au crescut cu {R_AO.lstrip('+')} în august–octombrie, iar în septembrie au fost de {R_SEP.lstrip('×')} ori nivelul din S1." + E("C161") +
        " Creșterea „de peste opt ori” din notă nu se reproduce din datele noastre; pe aceeași definiție (toate cererile de pe contor), nivelul e aproape stabil față de 2025." + E("C154", "C165"),
        f"Volumul a depășit capacitatea în august–octombrie și, în model, o va depăși din nou în 2027; în noiembrie, intrările au coborât temporar sub ritmul deciziilor." + E("C99", "C86", "C67"),
        f"Efectul proiectului vine din art. I și depinde de câți oameni ajung la soluționare: echivalentul a 5, 15 sau 30 de oameni câștigă {WEAK_GAIN}, {GAIN_OUG} sau {STRONG_GAIN} zile; luați din operare, câștigul are un plafon." + E("C61", "C43", "C35"),
        f"Art. III e o simplificare corectă, dar mică ({V('C44')}); art. II e necesar, dar măsurile expiră când coada e încă de ordinul lunilor." + E("C44", "C158"),
        f"Cel mai mare risc, valul CAEN, nu e tratat: cu 80% din entitățile rămase, așteptarea din iunie 2027 ar urca la {CAEN80} de zile; conversia automată o coboară la {CONV80}." + E("C94", "C95"),
    ]
    top = [
        "<b>Conversia automată CAEN „1-la-1”</b> în OUG, cu perioada de tranziție corelată prin HG (HG nr. 656/1997, art. 5^1)." + E("C95", "C152"),
        "<b>Verificări automate la depunere</b>, cu termen, în art. IV (Legea nr. 265/2022, art. 24 și 106)." + E("C141"),
        "<b>Întărirea ambelor etape</b>: desemnare și la operare, iar la registrator din afara operării (Legea nr. 265/2022, art. 22)." + E("C56", "C35"),
        "<b>Derogare pentru ocuparea posturilor finanțate</b> de la suspendarea concursurilor (Legea nr. 141/2025, art. XXII)." + E("C52", "C153"),
        "<b>Indicatori lunari publici și criteriu de ieșire</b> în loc de dată fixă (Legea nr. 544/2001, art. 5)." + E("C158"),
    ]
    contr = [
        ("Termenele legale · neatins", f"{V('C43')} zile în iunie 2028, față de {V('C23')} zi lucrătoare." + E("C23", "C43")),
        ("Diminuarea soldului · atins parțial", f"câștig {GAIN_OUG} zile; stocul rămâne peste punctul de pornire." + E("C43", "C158")),
        ("Directivele UE · atins parțial", "direcție corectă, așteptarea rămâne de luni." + E("C41", "C43")),
        ("Prelungirea până la consolidarea personalului · atins parțial", "fără plan de ocupare; coada nu e golită la expirare." + E("C153", "C158")),
    ]
    vc = (f'<div class="vstrip"><span class="vl">Tabelul 1 · {NROWS} afirmații verificate</span>'
          + "".join(f'{pill(k)}<b class="vn">{COUNTS[k]}</b>' for k in KEYS) + '</div>')
    return f"""
<section class="front front-synth" style="page: ao-sum;">
  <div class="eyebrow">Sinteză · O pagină</div>
  <h2>Un pas util, dar insuficient: efectul depinde de câți oameni ajung la soluționare și de unde vin</h2>
  {tiles}
  {vc}
  <div class="sumgrid">
    <div><div class="lab">Cinci concluzii</div><ol class="sum">{''.join(f'<li>{c}</li>' for c in concls)}</ol></div>
    <div><div class="lab">Primele cinci propuneri pentru consultare</div><ol class="sum">{''.join(f'<li>{t}</li>' for t in top)}</ol>
    <p class="note" style="margin-top:1mm">Toate cele zece propuneri: capitolul 4. Câștigurile sunt mediane pe aceleași simulări.</p>
    <div class="contr"><div class="lab">Obiectivele proiectului, în model</div><ul>{''.join(f'<li><b>{s}.</b> {c}</li>' for s, c in contr)}</ul></div></div>
  </div>
</section>"""


def toc_page(pg):
    items = [("Sinteză", "O pagină: cifre, concluzii, propuneri", "sum"),
             ("Cap. 1", "Ce afirmă proiectul și ce arată datele", "c1"),
             ("Cap. 2", "Articol cu articol: ce schimbă și ce efect are", "c2"),
             ("Cap. 3", "Ce nu tratează proiectul", "c3"),
             ("Cap. 4", "Propuneri pentru consultare", "c4"),
             ("Cap. 5", "Bugetul: ce costă proiectul și ce costă coada", "c5"),
             ("Cap. 6", "Limite și surse", "c6"),
             ("Anexă", ai_annex.TITLE, "ai")]
    li = "".join(f'<li><span class="tn">{a}</span><span><b>{b}</b></span><span class="tpg">{pg.get(k, "")}</span></li>' for a, b, k in items)
    arts = [("Art. I", "Consilierii juridici specialiști pot fi desemnați, cu acord scris, să facă controlul de legalitate, cu drepturile salariale ale registratorului, până la 8.01.2028; pe durata desemnării nu fac mențiunile din oficiu de la noul art. 5^2."),
            ("Art. II", "Durata art. I, până la 8.01.2028, și prelungirea până la aceeași dată a desemnării conducerii de specialitate juridică (Legea nr. 3/2026, care aprobă OUG nr. 109/2024)."),
            ("Art. III", "Noile art. 5^1–5^2 din Legea nr. 265/2022: mențiunile pe hotărâri judecătorești și pe actele altor autorități se înscriu din oficiu de consilieri juridici, fără controlul legalității măsurii."),
            ("Art. IV", "ONRC optimizează fluxul informatic în 15 zile; art. III se aplică de la data optimizării; procedurile începute rămân sub legea veche.")]
    at = "".join(f'<tr><td class="nw"><b>{a}</b></td><td>{t}</td></tr>' for a, t in arts)
    return f"""
<section class="front" style="page: ao-toc;">
  <div class="eyebrow">Structura analizei</div><h2>Cuprins</h2>
  <ul class="toc-plain">{li}</ul>
  <h3>Ce prevede proiectul, pe scurt</h3>
  <div class="tbl-wrap"><table class="arts"><tbody>{at}</tbody></table></div>
  <h3>Cum se citește</h3>
  <ul class="key">
    <li class="kitem">{badge("E")}<div><strong>Măsurat.</strong> Din datele publice (BERC, portal, contorul cererilor), fără ipoteze de model.</div></li>
    <li class="kitem">{badge("S")}<div><strong>Preluat.</strong> Cifră din nota de fundamentare sau din textul legii, citată cu sursa.</div></li>
    <li class="kitem">{badge("P")}<div><strong>Scenariu.</strong> Rezultat de model, dat ca interval; cifrele WARN apar cu rezerva lor alături.</div></li>
    <li class="kitem"><span class="vpill v-conf">CONFIRMAT</span><div><strong>Verdictele</strong> din tabelul 1: confirmat, compatibil, contrazis, neverificabil, iar pentru scopurile proiectului „obiectiv” (atins parțial sau neatins în model); coloana „bază” spune dacă verdictul vine din date, din model sau din lege.</div></li>
  </ul>
  <p class="note"><strong>Unități.</strong> Așteptările sunt în zile calendaristice, de la înregistrarea cererii la decizia finală; termenul legal e în zile lucrătoare. Intervalele de forma „≈102 (41–172)” dau mijlocul simulărilor și intervalul în care cad 8 din 10 variante. Proiectul este în consultare publică; formularea finală se poate schimba.</p>
</section>"""


# ================================================================== CSS + BUILD
TITLE = "PROIECTUL DE OUG PRIVIND REGISTRUL COMERȚULUI · ANALIZĂ · 23.11.2026"
FOOT = BR.FOOT
PAGES = [("ao-sum", "Sinteză"), ("ao-toc", "Cuprins"), ("ao-c1", "Cap. 1 · Afirmațiile verificate"), ("ao-c2", "Cap. 2 · Articol cu articol"),
         ("ao-c3", "Cap. 3 · Ce lipsește"), ("ao-c4", "Cap. 4 · Propuneri"), ("ao-c5", "Cap. 5 · Bugetul"), ("ao-c6", "Cap. 6 · Limite și surse"),
         ("ao-ai", "Anexă · Utilizarea AI"), ("ao-body", "Verificare · articole · propuneri")]

CSS = r"""
.ec{break-inside:auto;margin:5mm 0 4mm}.ec .ect{font:600 12pt/1.25 var(--sans);margin:0 0 1.5mm;border-top:.6mm solid var(--ink);padding-top:1.5mm;break-after:avoid}
.eci{font:400 10pt/1.45 var(--serif);margin:0 0 2mm;break-after:avoid}.eci p{margin:0 0 1.1mm}.eci b{font-family:var(--sans);font-weight:600}
.ec svg{width:100%;height:auto;max-height:78mm;display:block;margin:0 auto;break-inside:avoid}
.ecc{font:400 9.6pt/1.42 var(--serif);margin-top:1mm}
.wide-block{margin:0}
q.src-nf{font-style:italic;quotes:"„" "”" "‚" "’"}
.ckwrap table.ck{table-layout:fixed;width:100%;font:400 7.7pt/1.36 var(--sans)}
table.ck td, table.ck th, table.am td, table.am th{overflow-wrap:normal;word-break:normal;hyphens:auto}
table.ck th:nth-child(1){width:7mm} table.ck th:nth-child(2){width:52mm} table.ck th:nth-child(4){width:25mm}
table.ck td{padding:1.2mm 1.4mm} table.ck td.nr, table.am td.nr{font:600 7.4pt var(--mono);color:var(--ink-3)}
table.ck q.src-nf{font-family:var(--serif);font-size:8pt}
.srcref{display:block;font:600 6.3pt var(--mono);text-transform:uppercase;letter-spacing:.04em;color:var(--ink-3);margin-bottom:.4mm}
.vpill{display:inline-block;font:600 6.3pt/1.5 var(--mono);letter-spacing:.03em;padding:.2mm 1.2mm;border-radius:.6mm;color:#fff;white-space:nowrap}
.v-obj{background:#7a6200}.vsub{display:block;font:600 6.6pt/1.3 var(--sans);color:#7a6200;margin-top:.6mm}.v-conf{background:#1d5e5a}.v-comp{background:#2f6f95}.v-contr{background:#a63228}.v-nev{background:#6b7178}
.basis{display:block;font:400 6.8pt/1.3 var(--sans);color:var(--ink-3);margin-top:.8mm}
table.am{table-layout:fixed;width:100%;font:400 7.9pt/1.38 var(--sans)}
table.am th:nth-child(1){width:7mm} table.am th:nth-child(3){width:38mm} table.am th:nth-child(4){width:40mm}
table.arts{table-layout:fixed;width:100%;font:400 8.8pt/1.42 var(--sans)} table.arts td:first-child{width:16mm}
.vstrip{display:flex;flex-wrap:wrap;align-items:center;gap:1.6mm 2.2mm;border-top:.2mm solid var(--rule);border-bottom:.2mm solid var(--rule);padding:1.8mm 0;margin:0 0 4mm;font:400 8.4pt var(--sans)}
.vstrip .vl{font:500 7.4pt var(--mono);text-transform:uppercase;letter-spacing:.04em;color:var(--ink-3);margin-right:2mm}
.vstrip .vn{font:600 11pt var(--sans);margin-right:3mm}
.sumgrid{display:grid;grid-template-columns:1fr 1fr;gap:6mm}
.sumgrid .lab{font:600 7.6pt var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--accent);border-top:.6mm solid var(--ink);padding-top:1.5mm;margin-bottom:1.5mm}
ol.sum{margin:0;padding-left:4.5mm;font:400 9.6pt/1.42 var(--serif)} ol.sum li{margin-bottom:1.6mm}
.front-synth h2{font-size:17pt;margin-bottom:2mm}
.front-synth .pulls{margin:3mm 0 3mm}.front-synth .pn{font-size:16pt;white-space:normal}
ul.lim li, ol.srcs li{margin-bottom:1mm}
.cols > ul.body-list.lim, .cols > ol.body-list.srcs{font:400 9.8pt/1.45 var(--serif)}
.contr{margin-top:2.5mm;background:var(--tint);border-top:.5mm solid #a63228;padding:2.5mm 3mm}
.contr .lab{font:600 7.6pt var(--mono);text-transform:uppercase;letter-spacing:.05em;color:#a63228;margin-bottom:1.2mm}
.contr ul{margin:0;padding-left:4mm;font:400 9pt/1.38 var(--serif)} .contr li{margin-bottom:1mm}
.ai-annex{max-width:none;columns:2;column-gap:7mm;font:400 9pt/1.4 var(--serif)} .ai-annex h3{break-after:avoid} .ai-annex li{break-inside:avoid}
section.chapter.runon{break-before:auto;margin-top:12mm} section.chapter.runon .copen{break-inside:avoid;padding-top:3mm}
.vstrip{flex-wrap:nowrap;gap:1.4mm 1.6mm} .vstrip .vn{margin-right:2mm}
"""


def running_css():
    esc = lambda s: s.replace('"', '\\"')
    out = [f'@page {{ @top-left {{ content: "{esc(TITLE)}"; }} @bottom-left {{ content: "{esc(FOOT)}"; }} }}']
    out += [f'@page {n} {{ @top-right {{ content: "{esc(h)}"; }} }}' for n, h in PAGES]
    return "\n".join(out)


def sups(html_):   # «5^1» -> 5<sup>1</sup> (article numbers of the draft)
    return re.sub(r"(\d)\^(\d)", r"\1<sup>\2</sup>", html_)


def build_html(pg):
    body = "\n".join([cover(), summary(), toc_page(pg), ch1(), ch2(), ch3(), ch4(), ch5(), ch6(), annex()])
    return f"""<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8">
<title>Proiectul de OUG privind registrul comerțului · analiză · Ștefan-Lucian Deleanu</title>
<link rel="stylesheet" href="fonts/fonts.css">
<style>{BASE_CSS}
{running_css()}
{BR.EXTRA_CSS}
{CSS}</style></head><body>{sups(body)}</body></html>"""


MARKERS = {"sum": r"SINTEZĂ\s*·\s*O PAGINĂ", "c1": r"^CAPITOLUL 1\s*$", "c2": r"^CAPITOLUL 2\s*$", "c3": r"^CAPITOLUL 3\s*$",
           "c4": r"^CAPITOLUL 4\s*$", "c5": r"^CAPITOLUL 5\s*$", "c6": r"^CAPITOLUL 6\s*$", "ai": r"^ANEXĂ\s*$"}

def toc_pages(pdf):
    import fitz
    d = fitz.open(str(pdf)); found = {}
    for p in range(1, len(d)):
        t = d[p].get_text("text").upper()
        for k, pat in MARKERS.items():
            if k not in found and re.search(pat, t, re.M) and not re.search(r"^CUPRINS\s*$", t, re.M):
                found[k] = str(p + 1)
    n = len(d); d.close(); return found, n


def checks(pdf):
    import fitz
    d = fitz.open(str(pdf)); sizes = collections.Counter(); low = []
    for i, p in enumerate(d):
        chars = 0
        for blk in p.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:
                    chars += len(sp["text"])
                    if i > 0: sizes[round(sp["size"], 1)] += len(sp["text"])
        ys = [b[3] for b in p.get_text("blocks") if b[4].strip()] + [r["rect"].y1 for r in p.get_drawings()]
        body_ys = [y for y in ys if y < p.rect.height - 60]          # ignore the running footer
        fill = (max(body_ys) if body_ys else 0) / p.rect.height
        if i > 0 and fill < 0.45:
            low.append((i + 1, round(fill, 2)))
    n = len(d); d.close()
    body = sizes.most_common(1)[0][0]
    print(f"dominant text size (all pages after the cover): {body} pt · near-empty pages: {low or 'none'}")
    assert body >= 9.5, f"Document was shrunk to fit (body {body} pt)"
    return n


def main():
    HTML_OUT.write_text(build_html({}), encoding="utf-8"); BR.compile_pdf(HTML_OUT, PDF_OUT)
    pg, n = toc_pages(PDF_OUT)
    HTML_OUT.write_text(build_html(pg), encoding="utf-8"); BR.compile_pdf(HTML_OUT, PDF_OUT)
    pg2, n2 = toc_pages(PDF_OUT)
    missing = set(MARKERS) - set(pg2)
    print(f"PDF: {PDF_OUT} · {n2} pages · TOC: {pg2}" + (f" · MISSING {missing}" if missing else ""))
    print(f"claims check: {NROWS} rows · " + " · ".join(f"{k} {COUNTS[k]}" for k in KEYS) + " · " + " · ".join(f"{k} {v}" for k, v in COUNTS_OBJ.items()))
    checks(PDF_OUT)


if __name__ == "__main__":
    main()
