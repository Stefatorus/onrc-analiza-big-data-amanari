"""Raport pentru instituții: «Coada de la Registrul Comerțului» — în stilul Lab
(T:\\Annulment-report: Source Serif 4 + IBM Plex, paleta monocromă + accent #1d5e5a,
marker galben). Fiecare cifră vine din claims_registry.csv (doar PASS/WARN) prin ID.
Se tipărește cu Microsoft Edge headless, ca rapoartele Lab.

  ..\\..\\venv\\Scripts\\python -X utf8 build_raport_institutii.py
"""
import csv, re, os, shutil, subprocess, tempfile, json, sys as _sys
from pathlib import Path

import lab_styles as LS
from lab_styles import BASE_CSS, badge, hl, prose, in_brief, pulls, counter_case, open_question
import ai_annex
import methodology
import postponement_section as PSEC
import rejection_section as RSEC

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DELIV = ROOT / "analysis" / "raport_executiv_2026-11"
LS.FIG_DIR = str(HERE / "figures_institutii")
HTML_OUT = HERE / "Raport_ONRC_Coada_2026-11.html"
PDF_OUT = DELIV / "Raport_ONRC_Coada_2026-11.pdf"
BOOK = "--book" in _sys.argv                  # complete report as one document
NOANNEX = "--no-annex" in _sys.argv or BOOK          # edition for the combined dossier: the AI annex is added once, at the end of the dossier
if NOANNEX:
    (DELIV / "_dosar").mkdir(exist_ok=True)
    HTML_OUT = HERE / "Raport_ONRC_Coada_2026-11_dosar.html"; PDF_OUT = DELIV / "_dosar" / "Raport_ONRC_Coada_2026-11.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

# ------------------------------------------------------------------ registry
REG = {r["id"]: r for r in csv.DictReader(open(DELIV / "claims_registry.csv", encoding="utf-8"))}
def V(cid):
    r = REG[cid]; assert r["status"] in ("PASS", "WARN"), f"{cid} is {r['status']} — must not be published"
    return r["value"]
def E(*ids):
    for i in ids:
        assert REG[i]["status"] in ("PASS", "WARN"), f"{i} is {REG[i]['status']}"
    return " " + " ".join(f'<span class="eid">[{i}]</span>' for i in ids)
ORI = re.search(r"de circa (\S+) ori", REG["C111"]["public_ro"]).group(1)      # Oct–Nov 2026 vs a normal month, as a word (C111)
_on = [x.strip() for x in V("C111").split(" · ")[2].replace("sept./oct./nov. 2026 ", "").split(" / ")[1:3]]   # Oct, Nov (C111)
OCTNOV = "–".join(sorted(_on, key=lambda x: float(x.replace(".", "").replace(",", "."))))                      # e.g. «36,3–37,5»
# the 40%-of-vacant-posts scenario (C52) assumes the 2026 hiring-freeze exceptions are approved (C153); text from the registry
HIRE_40 = re.search(r"Scenariul presupune că Ministerul Justiției.*?\)\.", REG["C52"]["rezerva_obligatorie"]).group(0)
def B(cid):   # evidence badge from the registry level (A/E, B/P, C/S)
    return badge(REG[cid]["level"].split("/")[1], inline=True)

# ------------------------------------------------------------------ components
def concl(text):
    return ('<div class="takeaway concl"><div class="lab">Pe scurt, pe înțelesul tuturor</div>'
            f'<p>{text}</p></div>')
def idea(text):
    return ('<div class="takeaway"><div class="lab">Ideea principală<br><span class="p5">1 min</span></div>'
            f'<p>{text}</p></div>')
def h3(t): return f'<h3>{t}</h3>'
def P(body, mt="", mh="", key=False): return prose(body, mt, mh, key_flag=key)

def fig(fnum, tag, title, svg, arata, citeste, inseamna, nu, ids):
    svg_code = LS.load_inline_svg(svg, svg.split(".")[0])
    return ('<figure class="chart">'
            f'<div class="fnum"><span>{fnum}</span><span>{tag}</span></div>'
            f'<div class="ftitle">{title}</div>{svg_code}'
            '<dl class="decode">'
            f'<dt>Ce arată</dt><dd>{arata}</dd><dt>Cum se citește</dt><dd>{citeste}</dd>'
            f'<dt>Ce înseamnă</dt><dd>{inseamna}</dd><dt>Ce NU înseamnă</dt><dd>{nu}</dd></dl>'
            f'<p class="fsrc"><b>Sursă și verificare.</b>{E(*ids)}</p>'
            '</figure>')

def chapter(n, page, title, dek, meta, body):
    return (f'<section class="chapter" style="page: {page};">'
            f'<div class="copen"><div class="cnum">Capitolul {n}</div><h2>{title}</h2>'
            f'<p class="cdek">{dek}</p><div class="cmeta">{meta}</div></div>'
            f'<div class="cols">{body}</div></section>')

EXTRA_CSS = r"""
.gloss-box { border: .25mm solid var(--rule); border-left: 1mm solid var(--accent); padding: 2mm 3.5mm; margin: 3mm 0 0; break-inside: avoid; }
.gloss-box h3 { margin: 0 0 1.2mm; font: 600 9.6pt var(--sans); color: var(--accent); }
.gloss-box dl { display: grid; grid-template-columns: 24mm 1fr 24mm 1fr; gap: .8mm 3mm; margin: 0; font: 400 8.8pt/1.4 var(--sans); }
.gloss-box dt { font-weight: 600; } .gloss-box dd { margin: 0; }
.ver code { font: inherit; color: inherit; background: none; padding: 0; border: 0; }
.concl { background: var(--tint); border-top: .5mm solid var(--accent); margin-top: 4mm; padding: 2.5mm 3mm 3mm; }
.concl .lab { color: var(--accent); }
.concl p { font: 500 10.2pt/1.5 var(--sans); }
dl.decode { display: grid; grid-template-columns: 30mm 1fr; gap: 1.2mm 4mm; margin: 2.5mm 0 1.5mm;
  font: 400 8.4pt/1.45 var(--sans); border-top: .2mm solid var(--rule); padding-top: 2mm; }
dl.decode dt { font: 600 7.4pt/1.45 var(--mono); text-transform: uppercase; letter-spacing: .04em; color: var(--ink-2); }
dl.decode dd { margin: 0; color: var(--ink); }
dl.decode dt:nth-last-of-type(1), dl.decode dd:nth-last-of-type(1) { color: var(--ink); }
dl.decode dd:last-of-type { background: var(--tint); padding: .4mm 1.5mm; }
.eid { font: 500 6.4pt var(--mono); color: var(--ink-3); white-space: nowrap; }
.toc-plain { list-style: none; padding: 0; margin: 4mm 0; font: 400 10pt/1.5 var(--sans); max-width: 152mm; }
.toc-plain li { display: grid; grid-template-columns: 20mm 1fr 12mm; border-bottom: .2mm solid var(--rule-2); padding: 1.6mm 0; }
.toc-plain .tn { font: 500 7.6pt var(--mono); color: var(--ink-3); text-transform: uppercase; padding-top: .7mm; }
.toc-plain .tpg { font: 500 8.6pt var(--mono); text-align: right; }
.toc-plain .tsub { display: block; font: 400 8.2pt/1.35 var(--serif); color: var(--ink-2); }
.toc-plain li { padding: 1.1mm 0; }
.toc-plain li.part { display: block; border-bottom: .35mm solid var(--ink); padding: 3.2mm 0 .8mm; margin-top: 1mm;
  font: 600 7.8pt var(--mono); text-transform: uppercase; letter-spacing: .05em; color: var(--accent); }
.toc-plain li.part .psub { font: 400 7.6pt var(--sans); text-transform: none; letter-spacing: 0; color: var(--ink-2); margin-left: 3mm; }
.reg-tbl { width: 100%; border-collapse: collapse; font: 400 7.3pt/1.35 var(--sans); }
.reg-tbl th { text-align: left; font: 600 6.8pt var(--mono); text-transform: uppercase; color: var(--ink-2);
  border-bottom: .35mm solid var(--ink); padding: 1mm 1.2mm; }
.reg-tbl td { border-bottom: .2mm solid var(--rule-2); padding: 1.1mm 1.2mm; vertical-align: top; }
.reg-tbl .st-PASS { color: var(--accent); font-weight: 600; } .reg-tbl .st-WARN { color: #7a6200; font-weight: 600; }
.reg-tbl .st-FAIL { color: #a63228; font-weight: 600; }
.notlist li { margin-bottom: 1.4mm; }
.gl-tbl { width: 100%; border-collapse: collapse; font: 400 8.6pt/1.45 var(--sans); }
.gl-tbl td { border-bottom: .2mm solid var(--rule-2); padding: 1mm 1.2mm; vertical-align: top; }
.gl-tbl td:first-child { width: 44mm; }
.osint table.dt { width: 100%; border-collapse: collapse; font: 400 7pt/1.35 var(--sans); table-layout: fixed; }
.osint table.dt th { font: 600 6.4pt var(--mono); text-transform: uppercase; text-align: left; border-bottom: .35mm solid var(--ink); padding: .8mm; overflow-wrap: anywhere; }
.osint table.dt td { border-bottom: .2mm solid var(--rule-2); padding: .8mm; vertical-align: top; overflow-wrap: anywhere; }
.osint table.dt th:nth-child(1) { width: 8mm; } .osint table.dt th:nth-child(5) { width: 20mm; }
.ai-annex { max-width: 160mm; font: 400 9.6pt/1.5 var(--serif); }
.ai-annex ul { margin: 1mm 0 2.5mm 4mm; padding: 0; } .ai-annex li { margin-bottom: 1.2mm; }
.ai-annex h3 { font: 600 10pt var(--sans); color: var(--accent); margin: 4mm 0 1mm; }
/* short columns must not break mid-word (the Lab .chapter sets overflow-wrap:anywhere).
   Widths are scoped per table: an unscoped nowrap overflowed Annex C and made Edge shrink every page. */
.claims-tbl, .src-tbl, .oug-tbl { table-layout: fixed; width: 100%; }
.claims-tbl td, .claims-tbl th, .src-tbl td, .src-tbl th, .oug-tbl td, .oug-tbl th { overflow-wrap: normal; word-break: normal; hyphens: manual; }
.claims-tbl th:nth-child(1) { width: 9mm; } .claims-tbl th:nth-child(3) { width: 26mm; }
.claims-tbl th:nth-child(4) { width: 10mm; } .claims-tbl th:nth-child(5) { width: 12mm; }
.claims-tbl td:nth-child(1), .claims-tbl td:nth-child(4), .claims-tbl td:nth-child(5) { white-space: nowrap; }
.src-tbl th:nth-child(1) { width: 9mm; } .src-tbl th:nth-child(3) { width: 46mm; } .src-tbl th:nth-child(4) { width: 42mm; }
.src-tbl td:nth-child(1) { white-space: nowrap; } .src-tbl code { overflow-wrap: anywhere; }
.oug-tbl th:nth-child(1) { width: 15mm; } .oug-tbl th:nth-child(3) { width: 24mm; }
.oug-tbl td:nth-child(1), .oug-tbl td:nth-child(3) { white-space: nowrap; }
"""

TITLE = "COADA DE LA REGISTRUL COMERȚULUI · RAPORT COMPLET" if BOOK else "COADA DE LA REGISTRUL COMERȚULUI · NOIEMBRIE 2026"
import book_style as _BSV
FOOT = "Analiză independentă din date deschise · Ștefan-Lucian Deleanu · stefandeleanu.ro · " + _BSV.VERSION_FOOT
PAGES = [("rf-front", "Cuprins"), ("rf-guide", "Cum se citește raportul"), ("rf-synth", "Sinteză executivă"),
         ("rc-01", "Cap. 1 · De ce contează o zi"), ("rc-02", "Cap. 2 · Cât se așteaptă acum"),
         ("rc-03", "Cap. 3 · Cum s-a ajuns aici"), ("rc-04", "Cap. 4 · Cele două cozi"),
         ("rc-05", "Cap. 5 · Cererile și ritmul lor"), ("rc-06", "Cap. 6 · Amânări și respingeri"),
         ("rc-07", "Cap. 7 · Prognoza până în 2028"), ("rc-08", "Cap. 8 · Grila de risc"),
         ("rc-09", "Cap. 9 · Proiectul de OUG, pe articole"), ("rc-10", "Cap. 10 · Ce se poate face"),
         ("rc-11", "Cap. 11 · Cât de sigure sunt cifrele"), ("rc-12", "Cap. 12 · Sursele noastre și sursele publice"), ("ra-a", "Anexa A · Glosar"),
         ("ra-b", "Anexa B · Registrul afirmațiilor"), ("ra-c", "Anexa C · Metodă și reproducere"), ("ra-d", "Anexa D · Metodologia"), ("ra-e", "Anexa E · Utilizarea AI și limite")]
def running_css():
    esc = lambda s: s.replace('"', '\\"')
    out = [f'@page {{ @top-left {{ content: "{esc(TITLE)}"; }} @bottom-left {{ content: "{esc(FOOT)}"; }} }}']
    out += [f'@page {n} {{ @top-right {{ content: "{esc(h)}"; }} }}' for n, h in PAGES]
    if BOOK:
        import book_style
        out.append(book_style.margins_css())
        # complete report: chapters run on (no near-empty page at each chapter end); one running head for the part
        out.append('.chapter { break-before: auto !important; page: auto !important; margin-top: 10mm; } .chapter .copen { break-inside: avoid; break-after: avoid; display: inline-block; width: 100%; box-sizing: border-box; vertical-align: top; } .chapter .copen .cnum { break-after: avoid; } '
                   '@page { @top-right { content: "Partea 2 · Raportul principal"; } }')
    return "\n".join(out)

def book_refs(html_):
    import book_style
    return book_style.book_refs(html_)



# ================================================================== FRONT
GLOSS = '''<div class="gloss-box"><h3>Termeni, pe scurt</h3><dl>
    <dt>BERC</dt><dd>Buletinul electronic al registrului comerțului: deciziile publicate zilnic; sursa principală a raportului.</dd>
    <dt>myportal</dt><dd>Portalul online al ONRC, prin care se depun cererile; din el am sondat un eșantion de cereri în așteptare.</dd>
    <dt>OUG</dt><dd>Ordonanță de urgență a Guvernului; aici, proiectul pus în consultare la 18 noiembrie 2026.</dd>
    <dt>CAEN</dt><dd>Codul activității unei firme; trecerea la versiunea Rev. 3 cere actualizarea codurilor.</dd>
    <dt>Operare</dt><dd>Prima etapă: preluarea cererii și verificarea ei formală, de către un operator.</dd>
    <dt>Registrator · soluționare</dt><dd>A doua etapă: registratorul verifică legalitatea și decide (admite, respinge sau amână).</dd>
    <dt>p10–p90</dt><dd>Intervalul în care cad 8 din 10 variante simulate ale prognozei.</dd>
    <dt>Interval</dt><dd>Spunem mereu ce fel de interval e: de simulare, de încredere sau distanța dintre scenarii (ghidul de lectură).</dd>
  </dl></div>'''   # executive edition: key terms (IT/lawyer review)
def front(pg):
    cover = f"""
<section class="cover">
  <div class="eyebrow">Analiză independentă din date deschise · BERC / ONRC / myportal</div>
  <h1>Coada de la Registrul Comerțului</h1>
  <p class="sub">Ce arată datele publice despre cele două etape ale unui dosar, de ce crește așteptarea, ce poate schimba proiectul de OUG din 18 noiembrie 2026 și ce rămâne de măsurat</p>
  <div class="threads" aria-hidden="true"><i class="t-e"></i><i class="t-s"></i><i class="t-m"></i><i class="t-p"></i></div>
  <p class="verdict">Registrul Comerțului dă azi mai multe decizii pe zi decât în aceeași perioadă a anilor trecuți. Totuși, un dosar soluționat la jumătatea lui noiembrie a așteptat aproape două luni, iar legea cere o zi lucrătoare.</p>
  <p class="verdict-sub">Raportul folosește două surse independente — buletinul oficial BERC și portalul myportal — și le verifică una pe alta. Fiecare cifră are un cod (de exemplu [C14]) care duce, în Anexa B, la sursă, la scriptul care o calculează și la amprenta datelor.</p>
  <dl class="meta">
    <dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
    <dt>Bază empirică</dt><dd>4.077.510 decizii BERC, până la {REG['C14']['data_date'].replace('BERC până la ', '')} · eșantion myportal de 7.469 de numere de cerere sondate · Nota Ministerului Justiției din 6 noiembrie 2026</dd>
    <dt>Ediție și dată</dt><dd>Raport pentru instituții · {_BSV.VERSION_HTML} · {_BSV.VERSION_DATE_LONG}</dd>
    <dt>Declarație de interes</dt><dd>Autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal.</dd>
    <dt>Utilizarea AI</dt><dd>{ai_annex.DISCLAIMER}</dd>
  </dl>
</section>"""

    items = [("Front", "Sinteză executivă", "Totul în câteva pagini, pentru decizie", "synth"),
             ("PART", "Partea I · Diagnosticul", "Ce se întâmplă acum și de ce", ""),
             ("Cap. 1", "De ce contează o zi", "Ce face Registrul și ce cere legea", "c1"),
             ("Cap. 2", "Cât se așteaptă acum", "Așteptarea măsurată pe două căi și de ce octombrie nu se poate încă măsura", "c2"),
             ("Cap. 3", "Cum s-a ajuns aici", "Patru perioade, din 2023 până azi; producția nu a scăzut", "c3"),
             ("Cap. 4", "Cele două cozi", "Operarea și soluționarea: unde se adună dosarele", "c4"),
             ("Cap. 5", "Cererile și ritmul lor", "Cât a crescut cererea și de ce unele dosare trec mai repede", "c5"),
             ("Cap. 6", "Amânări și respingeri", "De ce se amână și se resping dosarele și ce se poate verifica la depunere", "c6"),
             ("PART", "Partea a II-a · Prognoză și risc", "Ce urmează și cât de sensibil e sistemul", ""),
             ("Cap. 7", "Prognoza până în 2028", "Așteptarea și stocul fără măsuri noi, sezonul cererilor, testul modelului", "c7"),
             ("Cap. 8", "Grila de risc", "Vitezele de intrare și ieșire: 36 de combinații, cazul central și cel nefavorabil", "c8"),
             ("PART", "Partea a III-a · Politici și soluții", "Ce poate schimba OUG și ce altceva ajută", ""),
             ("Cap. 9", "Proiectul de OUG, pe articole", "Ce poate schimba fiecare articol și unde are limite", "c9"),
             ("Cap. 10", "Ce se poate face", "Pârghiile, pachetele de măsuri și capcanele lor", "c10"),
             ("PART", "Partea a IV-a · Încrederea în cifre", "Verificări, termeni și proveniența fiecărei cifre", ""),
             ("Cap. 11", "Cât de sigure sunt cifrele", "Verificări, limite și ce nu afirmăm", "c11"),
             ("Cap. 12", "Sursele noastre și sursele publice", "Ce confirmă presa, ce nu se reproduce din datele noastre și riscul CAEN", "c12"),
             ("Anexa A", "Glosar", "Termenii, explicați o singură dată", "aa"),
             ("Anexa B", "Registrul afirmațiilor", "Fiecare cifră, cu sursă și stare", "ab"),
             ("Anexa C", "Metodă și reproducere", "Scripturi, date, amprente", "ac"),
             ] + ([] if NOANNEX else [("Anexa D", methodology.TITLE, "Metoda întreagă, în proză: date, măsuri, model, verificări, riscuri", "ad"),
                                       ("Anexa E", ai_annex.TITLE, "Cum a fost folosit AI-ul, ce a verificat autorul, surse, limite și incertitudini", "ae")])
    li = "".join((f'<li class="part"><span>{b}</span><span class="psub">{c}</span></li>' if a == "PART" else
                  f'<li><span class="tn">{a}</span><span><b>{b}</b><span class="tsub">{c}</span></span>'
                  f'<span class="tpg">{pg.get(k, "")}</span></li>') for a, b, c, k in items)
    toc = f"""
<section class="front" style="page: rf-front;">
  <div class="eyebrow">Structura raportului</div><h2>Cuprins</h2>
  <ul class="toc-plain">{li}</ul>
  <p class="note"><strong>Volumul 2, document separat:</strong> „Anexe statistice” — toate seriile și tabelele de date folosite, pentru verificare și analiză proprie. Un raport statistic avansat, cu metoda completă, însoțește ambele volume.</p>
</section>"""

    guide = f"""
<section class="front front-guide" style="page: rf-guide;">
  <div class="eyebrow">Ghid de lectură</div><h2>Cum se citește raportul</h2>
  <div class="paths">
    <div class="path"><div class="lab">În cinci minute</div><p>Citiți sinteza executivă și casetele „Pe scurt, pe înțelesul tuturor” de la finalul fiecărui capitol.</p></div>
    <div class="path"><div class="lab">Pentru verificare</div><p>Fiecare cifră are un cod între paranteze drepte. Codul duce în Anexa B la sursă, script, amprenta datelor și stare.</p></div>
  </div>
  <h3>Ce înseamnă marcajele</h3>
  <ul class="key">
    <li class="kitem">{badge("E")}<div><strong>Observat direct.</strong> Măsurat în datele publice (BERC, portal), fără ipoteze. Exemplu: cât au așteptat dosarele soluționate într-o săptămână.</div></li>
    <li class="kitem">{badge("S")}<div><strong>Cifră preluată dintr-o sursă.</strong> De exemplu, stocul comunicat de Ministerul Justiției sau textul legii. O citez cu sursa; nu o recalculez.</div></li>
    <li class="kitem">{badge("M")}<div><strong>Estimare.</strong> Depinde de o ipoteză spusă explicit. Se citește ca ordin de mărime.</div></li>
    <li class="kitem">{badge("P")}<div><strong>Scenariu.</strong> Ce s-ar putea întâmpla în anumite condiții. Se dă mereu ca interval, nu ca predicție.</div></li>
    <li class="kitem"><mark class="hl">Evidențiat cu galben</mark><div><strong>Notele executive.</strong> Propozițiile de reținut, mereu sprijinite pe date. Citite în ordine, formează un rezumat al raportului.</div></li>
    <li class="kitem"><span class="lab">Notă de margine</span><div><strong>Explicații laterale:</strong> o definiție, un exemplu concret sau o rezervă despre limitele datelor.</div></li>
  </ul>
  <h3>Patru cuvinte pe care le veți întâlni des</h3>
  <p><strong>Dosar</strong> înseamnă o cerere depusă la Registru. <strong>Decizie finală</strong> înseamnă că dosarul a fost admis, respins sau renunțat (solicitantul renunță la cerere). <strong>Amânare</strong> înseamnă că registratorul a cerut acte în plus și a dat un termen. <strong>Mediana</strong> este valoarea din mijloc: jumătate din dosare stau mai puțin, jumătate mai mult. Folosim mediana pentru că puținele cazuri extreme nu o trag în sus.</p>
  <p class="note"><strong>Unități.</strong> Toate duratele sunt în zile calendaristice, de la înregistrarea cererii la decizia finală, inclusiv timpul de completare după o amânare. Termenul legal se exprimă în zile lucrătoare: o zi lucrătoare peste un weekend înseamnă trei zile calendaristice. <strong>Model verificat</strong> înseamnă motorul de prognoză al analizei, rerulat pe datele curente; rezultatele-cheie ale scenariilor au fost verificate într-o etapă separată (tot cu AI), iar celula de bază a grilei trebuie să reproducă exact prognoza. Nu este un audit al unei instituții.</p>
  <p class="note"><strong>Patru feluri de intervale.</strong> „≈138 (105–175)” înseamnă cazul central al unei prognoze și intervalul p10–p90, în care cad 8 din 10 variante simulate. „Interval de simulare de 95%” (la veniturile din 2027) cuprinde 95 din 100 de variante simulate, între percentilele 2,5 și 97,5 ale distribuției; e condiționat de ipotezele fixe și nu e un interval de încredere.{E("C122")} „IC 95%” este intervalul de încredere al unei estimări dintr-un eșantion: arată doar eroarea de eșantionare. „Prudent / central / tensionat” este distanța dintre scenarii construite din ipoteze diferite și nu are o probabilitate atașată.</p>
  <p class="note">Toate cifrele sunt verificate printr-un registru de afirmații. Doar cifrele cu starea PASS apar fără rezervă. Cifrele cu starea WARN apar numai cu rezerva lipită de ele. Cifrele retrase nu apar deloc.</p>
</section>"""

    synth = f"""
<section class="front front-synth" style="page: rf-synth;">
  <div class="eyebrow">Sinteză executivă · Pentru decidenți</div>
  <h2>Registrul emite cel puțin cât în anii trecuți, dar cererile au crescut mult mai repede</h2>
  <p class="lead">Un dosar care pe vechea platformă se rezolva în mod obișnuit în mai puțin de două zile așteaptă azi aproape două luni. Producția e puțin peste nivelul din 2025 și mult peste cea din 2023, dar cererile au crescut cu circa jumătate, iar cele două etape ale unui dosar au ritmuri apropiate.</p>
  {pulls([
      (V("C14") + " zile", "mediana pentru modificările soluționate în 16–20 noiembrie (toate deciziile din 1–20 nov.: " + V("C84") + ")", f"{B('C14')} zile calendaristice{E('C14', 'C84')}", False),
      (V("C28"), "cereri nesoluționate raportate de Ministerul Justiției la 6 noiembrie", f"{B('C28')} cifră oficială{E('C28')}", False),
      (V("C01"), "decizii finale pe zi lucrătoare în octombrie–noiembrie", f"{B('C01')} peste aceeași perioadă din 2025; în plus, circa {V('C03').lstrip('≈').split(' ')[0]} de amânări pe zi, tot muncă a registratorilor{E('C01', 'C30', 'C03')}", False),
      (V("C23") + " zi lucr.", "termenul din lege pentru soluționare, de la înregistrarea cererii", f"{B('C23')} art. 105 alin. (1), Legea 265/2022{E('C23')}", True),
  ])}
  <p><strong>Ce se întâmplă.</strong> Fiecare dosar trece prin două etape: <em>operarea</em>, în care un operator introduce și verifică cererea, și <em>soluționarea</em>, în care un registrator decide. La 6 noiembrie, cele două stocuri erau aproape egale; în săptămâna anterioară, stocul total scăzuse ușor.{E('C29', 'C85')} {hl("Modificările soluționate în 16–20 noiembrie au așteptat, în mod obișnuit, " + V("C14") + " zile calendaristice de la înregistrare, iar așteptarea a crescut în fiecare săptămână din octombrie.")}{E('C14', 'C16')} Durata include și timpul în care solicitantul completează dosarul după o amânare și privește doar dosarele deja decise; termenul legal de o zi lucrătoare privește cererea completă. Raportul nu califică întârzierile drept nelegale.</p>
  <p><strong>De ce.</strong> {hl("Cererile au crescut mult mai repede decât producția.")} Registrul emite mai multe decizii pe zi decât în aceeași perioadă a anilor trecuți (circa 9% peste 2025).{E('C30', 'C87', 'C79')} Cererile zilnice au crescut însă cu circa jumătate în august–octombrie (Ministerul Justiției), exact în sezonul în care, în fiecare an, se emit mai puține decizii.{E('C47', 'C86')} {hl('Coada s-a format în câteva săptămâni din septembrie, când au intrat de peste două ori mai multe cereri decât de obicei; din noiembrie, intrările sunt sub ritmul de soluționare și stocul scade încet.')}{E('C99', 'C100')} Așteptarea dosarelor decise crește totuși, pentru că acum se soluționează cererile din vârf. O parte din dosare trec de două ori prin sistem: circa una din cinci decizii e o amânare, iar aproape toate respingerile vin după o amânare neîndeplinită, din aceleași cauze (capitolul 6).{E('C21', 'C144')}</p>
  <p><strong>Ce urmează.</strong> Prognoza fără măsuri noi are trei repere, pe orizonturi diferite: {hl("la mijlocul lui 2027 (30 iunie), o așteptare de " + V('C59') + " zile; la vârf, " + V('C60') + " zile; în iunie 2028, " + V('C42') + " zile.")}{E('C59', 'C60', 'C42')} Comparațiile cu proiectul de OUG și cu pachetele de măsuri de mai jos privesc toate iunie 2028. În model, sistemul e foarte aproape de limită: cu aceleași cereri, {hl("10% mai multă capacitate ar coborî așteptarea din iunie 2028 la " + V('C63').split(' · ')[0].split('→ ')[1] + " de zile, iar 10% mai puțină ar urca-o la " + V('C63').split(' · ')[1].split('→ ')[1].split(' (')[0] + " de zile")}.{E('C63')} Valul CAEN de la începutul lui 2027 e cea mai mare sursă de risc.{E('C68')}</p>
  <p><strong>Ce poate face proiectul de OUG.</strong> Textul integral pus în consultare prevede desemnarea temporară, cu acordul lor scris, a consilierilor juridici specialiști ai ONRC ca registratori, până la 8 ianuarie 2028 (art. I–II), înscrierea din oficiu a mențiunilor din hotărâri judecătorești și din actele altor autorități (art. III) și adaptarea fluxului informatic în 15 zile (art. IV). Rulat pe aceste măsuri, cu ipotezele de livrare declarate (analiza separată a proiectului de OUG), modelul verificat arată o îmbunătățire reală, dar parțială: în iunie 2028, așteptarea ar rămâne de ordinul a trei luni, față de circa patru luni fără măsuri noi, cu intervale largi.{E('C42', 'C43')} Efectul vine mai ales din capacitatea suplimentară de soluționare. Dacă consilierii juridici delegați sunt luați din operare, câștigul are o limită clară, pentru că operarea e aproape la fel de încărcată.{E('C34', 'C35')}</p>
  <p><strong>Ce ajută.</strong> {hl("Un pachet minim realist ar coborî așteptarea din iunie 2028, în model, la " + V('C54') + " zile.")}{E('C54')} Pachetul: OUG prelungit, conversia automată a codurilor CAEN cu un singur corespondent nou („1-la-1”), eșalonarea depunerilor și triajul (cererile simple separate la intrare). Cu OUG extins și ocuparea a 40% din posturile vacante finanțate, așteptarea ar coborî la {V('C52')} zile{E('C52')}; în 2026 însă concursurile sunt suspendate. {HIRE_40}{E('C153')} Detalii în capitolul 10.</p>
  <p><strong>Ce costă.</strong> {hl("În octombrie și noiembrie 2026, întârzierile au costat economia, în scenariul central, circa " + OCTNOV + " milioane de lei pe lună, de circa " + ORI + " ori mai mult decât într-o lună obișnuită; la buget, circa " + V('C111').split('buget nov. 2026 ')[1] + " milioane în noiembrie.")}{E('C111')} Pentru august–18 noiembrie, scenariile dau între circa {V('C106').split(' / ')[0]} și {V('C106').split(' / ')[2]} de milioane de lei, iar fiecare zi în plus cu stocul actual costă circa {V('C108').split(' (')[0]} milioane în economie și {V('C108').split(' / ')[1].split(' (')[0]} milioane la buget (indicator de sensibilitate: nu se înmulțește cu numărul de zile).{E('C106', 'C108')} Zilele sunt măsurate; {V('C116').split(' · ')[1].split(' parametri')[0].replace(' din ', ' din cei ')} parametri care le transformă în lei au bază în date oficiale sau măsurate, restul sunt ipoteze declarate (Volumul 7).{E('C116')} {hl('Pentru 2027, fără măsuri noi, circa ' + V('C122').split(' (')[0] + ' de milioane de lei din veniturile bugetare nu ar intra în bugetul anului din cauza cozii; o parte se poate recupera ulterior, dar datele nu exclud o pierdere durabilă.')} Reperul e o coadă normală, de 3 zile; intervalul de simulare de 95% (percentilele 2,5–97,5 ale variantelor simulate) e de {V('C122').split('(')[1].split(')')[0]} de milioane. Dacă nimic nu s-ar recupera, minusul ar fi de circa {V('C124').split(' (')[0]} de milioane.{E('C122', 'C124', 'C120')}</p>
  <p><strong>Ce spun sursele publice.</strong> {hl("Majoritatea cifrelor publicate în presă despre coadă se confirmă sau sunt compatibile cu datele noastre; cifra de peste 26.000 de cereri pe zi nu se reproduce din datele BERC analizate de noi pentru cererile de înregistrare, iar capitolul 12 arată valorile noastre și definițiile folosite.")}{E('C91', 'C93')} {hl("Dacă se confirmă cifrele publice despre valul CAEN, așteptarea din iunie 2027 ar putea ajunge la " + V('C94').split(' · ')[1].split('→ ')[1] + "–" + V('C94').split(' · ')[2].split('→ ')[1].split(' (')[0] + " de zile (circa 9–11 luni); conversia automată CAEN ar reduce-o la mai puțin de jumătate.")}{E('C94', 'C95')}</p>
  <p><strong>Ce nu putem spune.</strong> Pentru dosarele depuse în octombrie și noiembrie, timpul final nu se poate încă măsura; ce nu afirmăm e în capitolul 11.</p>
  <div class="strip3">
    <div class="s3 s3-est"><div class="s3h">Măsurat direct</div><div class="s3d">Din peste patru milioane de decizii BERC și din eșantionul myportal.</div>
      <ul><li>Așteptarea dosarelor soluționate crește săptămânal: {V('C16')} zile.{E('C16')}</li>
          <li>Sub 1% din dosare mai sunt rezolvate într-o zi lucrătoare, față de {V('C31').split('→')[0].strip()} pe vechea platformă.{E('C31')}</li>
          <li>Coada e practic națională: pentru deciziile din 1–18 noiembrie, mediana pe oficiu e între {V('C49').split('–')[0]} și {V('C49').split('–')[1]} zile.{E('C49')}</li></ul></div>
    <div class="s3 s3-mod"><div class="s3h">Preluat sau modelat</div><div class="s3d">Cifre oficiale citate și scenarii date ca intervale.</div>
      <ul><li>Stoc oficial: {V('C28')} cereri, dintre care {V('C29')} neprelucrate.{E('C28', 'C29')}</li>
          <li>Iunie 2028, fără măsuri noi: {V('C42')} zile; cu OUG: {V('C43')}.{E('C42', 'C43')}</li>
          <li>Grila de risc: capacitate {V('C63')} zile.{E('C63')}</li></ul></div>
    <div class="s3 s3-opn"><div class="s3h">Încă deschis</div><div class="s3d">Ce ar trebui publicat pentru o imagine completă.</div>
      <ul><li>Stocul pe tipuri și vârste, din baza internă.</li><li>Personalul activ pe fiecare etapă.</li><li>De ce unele tipuri de dosare sunt soluționate mai repede (priorități legale, cereri simple).</li></ul></div>
  </div>
</section>"""
    return "" if BOOK else (cover + toc + guide + synth)      # complete report: synthesis and guide open the whole document


# ================================================================== CHAPTERS
def ch1():
    b = idea("Fără înregistrarea la Registru, o firmă nouă nu există ca persoană juridică, iar multe schimbări la firmele existente nu sunt opozabile terților. De aceea, câteva săptămâni de așteptare blochează contracte, conturi și salarii.")
    b += h3("1.1 Ce face Registrul Comerțului")
    b += P("Oficiul Național al Registrului Comerțului (ONRC) ține evidența tuturor firmelor din România. " + hl("Funcționează ca o stare civilă a economiei: o firmă dobândește personalitate juridică prin înmatriculare, iar multe schimbări devin opozabile terților abia după înregistrare.") + " O firmă nouă nu poate factura până nu e înmatriculată. Pentru o firmă existentă, schimbarea sediului, a administratorului sau a asociaților produce efecte față de bănci, parteneri și autorități abia după înregistrare.",
           "Definiție", "<strong>ONRC</strong> are un oficiu în fiecare județ. Dosarele se depun la oficiul județean, online sau la ghișeu.")
    b += P("Pentru o firmă, întârzierea are efecte concrete. Banca nu recunoaște noul administrator. Un contract de închiriere nu poate fi trecut ca sediu. Un asociat care a vândut părțile sociale rămâne în acte. Fiecare dintre aceste situații înseamnă bani blocați și decizii amânate.",
           "Exemplu", "O firmă își mută sediul la 1 octombrie. Până când Registrul nu admite mutarea, facturile și corespondența oficială rămân legate de vechea adresă.")
    b += h3("1.2 Ce cere legea")
    b += P(hl("Legea cere ca registratorul să soluționeze cererea de înmatriculare într-o zi lucrătoare de la înregistrarea ei (art. 105 alin. (1)); aceeași regulă se aplică, în mod corespunzător, și celorlalte cereri de înregistrare.") + E('C23') +
           " Dacă dosarul e incomplet, registratorul poate amâna soluționarea și da un termen de completare de cel mult 15 zile (art. 106 alin. (1)). Pentru comparație corectă: termenul legal e în zile lucrătoare, iar așteptarea măsurată în raport e în zile calendaristice și include timpul de completare.",
           "Sursa textului", "Legea 265/2022: art. 105 alin. (1) și (6)–(7), art. 106 alin. (1) și art. 109. Textele legale au fost verificate pe legislatie.just.ro (forma consolidată) la 22.11.2026; o versiune anterioară a raportului folosise extrasul publicat de ONRC.", key=True)
    b += f'''<div class="issue" style="border:.25mm solid var(--rule);border-left:1mm solid var(--accent);padding:2.5mm 3.5mm;margin:2mm 0 4mm"><b>Ce nu afirmă raportul în plan juridic.</b> Raportul nu califică întârzierile drept nelegale, nu analizează consecințele depășirii termenului și nu tratează căile de atac. Cifrele descriu durate statistice, nu situația unui dosar anume.</div>'''
    b += P("Pe vechea platformă, un dosar aștepta în mod obișnuit " + V('C17') + " zile." + E('C17') +
           " Asta arată că termenul scurt nu era doar teoretic. Sistemul l-a respectat ani la rând pentru majoritatea dosarelor.")
    b += h3("1.3 De ce o mediană de săptămâni e o problemă de sistem")
    b += P("O întârziere de o zi se poate explica printr-un dosar complicat. " + hl("O mediană de câteva săptămâni înseamnă altceva: jumătate din toate dosarele așteaptă cel puțin atât.") + " Asta nu mai ține de un dosar anume, ci de felul în care circulă toate dosarele prin sistem.")
    b += concl("Registrul e o etapă obligatorie pentru orice schimbare la o firmă. Legea îi dă o zi. Când așteptarea obișnuită ajunge la săptămâni, problema e a întregului sistem, nu a unor dosare izolate.")
    return chapter(1, "rc-01", "De ce contează o zi",
                   "Registrul Comerțului e o etapă obligatorie pentru orice firmă. Legea cere o decizie într-o zi lucrătoare; pe vechea platformă, termenul se respecta în majoritatea cazurilor.",
                   "Surse: Legea 265/2022 (legislatie.just.ro, 22.11.2026) · BERC 2023–2026", b)


def ch2():
    b = idea("Așteptarea crește de la o săptămână la alta. Dosarele soluționate la jumătatea lui noiembrie fuseseră depuse, în mod obișnuit, în jurul datei de 20 septembrie.")
    b += h3("2.1 Două moduri de a măsura așteptarea")
    b += P("Putem măsura așteptarea în două feluri. Primul: luăm dosarele depuse într-o lună și vedem cât au durat. Al doilea: luăm dosarele soluționate într-o săptămână și vedem cât au stat. Ambele sunt corecte, dar răspund la întrebări diferite.",
           "De ce două", "Prima metodă spune cât va aștepta cine depune azi, dar abia peste câteva luni. A doua spune cât de vechi sunt dosarele pe care Registrul le termină acum.")
    b += h3("2.2 Ce arată dosarele soluționate acum")
    b += P(hl("Modificările soluționate în săptămâna 16–20 noiembrie au așteptat, în mod obișnuit, " + V('C14') + " zile.") + E('C14') +
           " La sfârșitul lui septembrie, aceeași măsură era sub 28 de zile. Ea a crescut în fiecare săptămână fără excepție." + E('C16') +
           " Pentru firmele noi, așteptarea a fost de " + V('C15') + " zile în aceeași săptămână." + E('C15'),
           "Exemplu", "Un dosar decis pe 18 noiembrie, după 57 de zile, fusese depus în jurul datei de 22 septembrie. Cel mai vechi dosar încă nerezolvat din eșantionul nostru fusese depus pe " + V('C13') + "." + E('C13'), key=True)
    b += fig("FIGURA 2.1", "DECIZII FINALE · SĂPTĂMÂNAL · 28 SEP.–20 NOV. 2026",
             "Modificările soluționate acum sunt tot mai vechi: așteptarea crește în fiecare săptămână",
             "fi03_acum.svg",
             "Câte zile au așteptat, la mijlocul distribuției, dosarele soluționate în fiecare săptămână.",
             "Fiecare punct e o săptămână de decizii. Linia roșie sunt modificările, linia albastră înmatriculările. Linia verde punctată e termenul din lege.",
             "Registrul termină acum dosare depuse cu aproape două luni în urmă, iar distanța crește.",
             "Nu arată cât va aștepta un dosar depus azi. Acela va fi soluționat abia peste câteva săptămâni.",
             ["C14", "C15", "C16"])
    b += h3("2.3 Ce arată dosarele după luna depunerii")
    b += P("A doua metodă confirmă direcția. Pentru dosarele depuse în mai, așteptarea obișnuită a fost de 5 zile. " + hl("Pentru cele depuse în septembrie, de cel puțin 39 de zile.") + E('C04') +
           " Spunem „cel puțin” pentru că multe dosare din septembrie nu erau încă rezolvate când am descărcat datele. Ele vor trage cifra în sus.",
           "Rezervă", "Valoarea pentru septembrie e o limită de jos, nu valoarea finală. La fel și raportul de „peste șapte ori” dintre mai și septembrie." + E('C05'))
    b += fig("FIGURA 2.2", "PE LUNA DEPUNERII · IAN.–SEP. 2026 · DOUĂ SURSE",
             "Pentru dosarele depuse în septembrie, așteptarea a fost de cel puțin 39 de zile",
             "fi02_colaps_doua_surse.svg",
             "Timpul obișnuit până la decizie, pentru dosarele depuse în fiecare lună, din două surse.",
             "Linia albastră vine din buletinul oficial BERC. Linia portocalie vine din portalul myportal. Unde se suprapun, sursele spun același lucru.",
             "Așteptarea a crescut puternic din august. Două surse independente dau aceleași valori lunare.",
             "Nu dă valoarea finală pentru septembrie, care va fi mai mare. Octombrie și noiembrie lipsesc intenționat: nu se pot încă măsura.",
             ["C04", "C09"])
    b += h3("2.4 De ce octombrie și noiembrie nu se pot încă măsura")
    b += P("Imaginați-vă că măsurați cât au stat la coadă doar oamenii care au ieșit deja din magazin. Îi vedeți doar pe cei rapizi. Cei care încă așteaptă nu apar în calcul. Exact asta se întâmplă cu dosarele depuse recent: " + hl("dacă le-am măsura acum, am vedea doar dosarele rapide și am obține o cifră fals mică.") + E('C11'),
           "Termen tehnic", "Fenomenul se numește cenzurare la dreapta. Din acest motiv, pentru lunile recente folosim așteptarea dosarelor soluționate pe săptămână (secțiunea 2.2).")
    b += fig("FIGURA 2.3", "DOSARE DEJA SOLUȚIONATE · PE LUNA DEPUNERII · 2026",
             "Pentru octombrie și noiembrie, prea puține dosare sunt încă rezolvate ca să măsurăm timpul",
             "fi11_cenzurare.svg",
             "Câte dosare depuse în fiecare lună au primit deja o decizie finală.",
             "Barele gri, pentru octombrie și noiembrie, sunt mult mai scurte decât celelalte.",
             "Pentru aceste luni avem doar dosarele rapide. Un timp calculat pe ele ar arăta, greșit, o îmbunătățire.",
             "Nu înseamnă că s-au depus mai puține dosare în octombrie și noiembrie. Înseamnă că nu au fost încă soluționate.",
             ["C11"])
    b += h3("2.5 Față de reperele legale")
    b += P("Pe vechea platformă, " + V('C31').split('→')[0].strip() + " din dosare erau rezolvate într-o zi lucrătoare. În criză, sub 1%." + E('C31') +
           " " + hl(V('C41').split()[0] + " dintre firmele noi aprobate fără amânare în noiembrie au așteptat peste 10 zile lucrătoare de la înregistrare.") + E('C41') +
           " Pentru comparație, art. 13g alin. (7) din Directiva (UE) 2017/1132 cere ca o constituire online să fie finalizată în 5 zile lucrătoare (persoane fizice care folosesc modelele standard) sau în 10 zile lucrătoare în celelalte cazuri, de la primirea tuturor documentelor sau de la plata taxei.",
           "Rezervă", "Pragul european se aplică doar constituirilor online, iar datele publice nu le identifică. De aceea cifra nu stabilește încălcări individuale, ci arată ordinul de mărime al depășirii reperului.")
    b += concl("Dosarele terminate acum sunt cele depuse cu aproape două luni în urmă, iar distanța crește în fiecare săptămână. Pentru dosarele depuse recent, încă nu putem spune cât vor aștepta; știm doar că nu va fi mai puțin.")
    return chapter(2, "rc-02", "Cât se așteaptă acum",
                   "Așteptarea măsurată pe două căi independente arată același lucru: crește. Capitolul explică și de ce lunile recente nu se pot încă măsura corect.",
                   "Surse: BERC până la 20 nov. 2026 · eșantion myportal · Directiva (UE) 2017/1132 art. 13g alin. (7)", b)


def ch3():
    b = idea("Criza din 2024 și cea din 2026 arată la fel din afară, dar au cauze diferite. În 2024 a scăzut producția. În 2026 producția e mare, dar cererile au crescut și mai mult.")
    b += h3("3.1 Patru perioade într-o singură imagine")
    b += P("Am urmărit așteptarea săptămână cu săptămână din aprilie 2023 până în noiembrie 2026. Se văd clar patru perioade. Pe vechea platformă, așteptarea era sub două zile." + E('C17') +
           " " + hl("După lansarea noului portal în iulie 2024, așteptarea a urcat la circa 12 zile, dar în decembrie 2024 a revenit la normal.") + E('C18') +
           " În 2025, sistemul a fost stabil, cu o așteptare de circa trei zile." + E('C19'),
           "Precizare", "În săptămâna migrării din iulie 2024, Registrul a fost oprit tehnic. Săptămânile cu foarte puține decizii sunt scoase din linie, ca să nu creeze vârfuri false.")
    b += fig("FIGURA 3.1", "DECIZII FINALE · SĂPTĂMÂNAL · APR. 2023–NOV. 2026",
             "Lansarea portalului din 2024 a fost o criză scurtă; valul din 2026 urcă mult mai sus",
             "fi01_istoric.svg",
             "Așteptarea obișnuită a dosarelor soluționate în fiecare săptămână, din aprilie 2023 până azi.",
             "Benzile colorate marchează perioadele. Linia arată câte zile au stat dosarele terminate în săptămâna respectivă.",
             "Episodul din 2024 s-a rezolvat în câteva luni. Creșterea din 2026 e mult mai mare și încă nu s-a oprit.",
             "Nu compară volumul de muncă dintre perioade. Arată doar cât au așteptat dosarele.",
             ["C17", "C18", "C19", "C14"])
    b += h3("3.2 Producția nu s-a prăbușit")
    b += P(hl("Pe aceeași perioadă a anului, Registrul a dat în 2026 mai multe decizii finale pe zi decât în oricare dintre ultimii trei ani.") + E('C30') +
           " Comparăm aceeași fereastră, 1 octombrie–19 noiembrie (20 noiembrie e o zi incompletă în arhivă), ca să nu amestecăm sezoane diferite. Vârful absolut a fost totuși în februarie–martie 2025, deci 2026 nu este un record absolut." + E('C01'),
           "De ce aceeași perioadă", "Volumul de dosare variază cu anotimpul. O comparație între luni diferite ar putea arăta o creștere sau o scădere doar din cauza calendarului.", key=True)
    b += fig("FIGURA 3.2", "DECIZII FINALE / ZI LUCRĂTOARE · 1 OCT.–20 NOV. · 2023–2026",
             "Pe aceeași perioadă a anului, Registrul dă mai multe decizii decât în 2023, 2024 și 2025",
             "fi05_productie.svg",
             "Câte decizii finale s-au dat, în medie, pe zi lucrătoare, în aceeași perioadă a fiecărui an.",
             "Fiecare bară e un an. Linia punctată arată vârful absolut din februarie–martie 2025.",
             "Coada nu crește pentru că se lucrează mai puțin. Crește pentru că intră mai mult.",
             "Nu măsoară volumul de muncă: circa un sfert din decizii sunt actualizări CAEN, al căror efort pe dosar nu se vede în date; codurile CAEN sunt totodată cel mai des motiv de amânare." + E("C50"),
             ["C30", "C01"])
    b += h3("3.3 Vara a contat")
    b += P(hl("În august s-au dat cu circa " + str(100 - int(V('C07').strip('≈%'))) + "% mai puține decizii pe zi lucrătoare decât în iunie–iulie.") + E('C07') +
           " Scăderea a venit exact înaintea vârfului de cereri din septembrie. Sezonul august–octombrie aduce în fiecare an mai puține decizii; e un tipar cunoscut, de care planificarea poate ține seama." + E("C86"))
    b += h3("3.4 Schimbarea din 27 aprilie 2026")
    b += P("Cu luni înainte de valul de cereri, ceva s-a schimbat în felul în care circulă dosarele. " + hl("Din 27 aprilie 2026, aproape niciun dosar nu mai e rezolvat în două zile, în aproape toate județele.") + E('C32') +
           " Așteptarea obișnuită era atunci de doar câteva zile, deci nu era o coadă. " + hl("În aprilie–iunie 2026, majoritatea deciziilor au fost emise exact în a treia zi lucrătoare, inclusiv amânările: a apărut un termen minim de fapt.") + " Din iulie, coada a crescut peste acest prag, iar el nu se mai vede în date." + E('C101'),
           "Rezervă", "Cauza nu e documentată în date. Arătăm schimbarea, nu o explicăm. Doar ONRC poate spune ce s-a modificat în sistem.")
    b += concl("Registrul lucrează mai mult ca oricând în această perioadă a anului. Coada a crescut pentru că cererile au crescut mai repede, în sezonul august–octombrie, în care în fiecare an se emit mai puține decizii. Din aprilie, datele arată și o schimbare în ritmul deciziilor, a cărei cauză nu o cunoaștem.")
    return chapter(3, "rc-03", "Cum s-a ajuns aici",
                   "Patru perioade, din 2023 până azi. Criza de acum nu e o repetare a celei din 2024: producția e mare, dar nu ține pasul cu cererile.",
                   "Surse: BERC apr. 2023–nov. 2026 · ferestre comparabile 1 oct.–19 nov.", b)


def ch4():
    b = idea("Un dosar trece prin două cozi legate, cu ritmuri apropiate. De aceea, a întări doar una mută problema în cealaltă.")
    b += h3("4.1 Cum circulă un dosar")
    b += P("Gândiți-vă la un cabinet medical cu recepție și medic. Recepția preia pacientul și îi deschide fișa. Medicul pune diagnosticul. Dacă recepția lucrează mai repede decât medicul, sala de așteptare din fața cabinetului se umple. Dacă medicul ar fi mai rapid, oamenii s-ar aduna la recepție.",
           "Analogie", "La Registru, <strong>operarea</strong> e recepția: un operator introduce și verifică dosarul. <strong>Soluționarea</strong> e medicul: un registrator decide.")
    b += fig("FIGURA 4.1", "DRUMUL UNUI DOSAR · STOCURI OFICIALE LA 6 NOV. 2026",
             "Un dosar trece prin operare și apoi la registrator; ambele etape au un stoc mare",
             "fi04_flux.svg",
             "Cele două etape prin care trece orice cerere supusă soluționării și câte cereri așteptau în fiecare la 6 noiembrie.",
             "Săgețile arată drumul obișnuit. Săgeata roșie arată amânarea: registratorul cere acte și dă un termen.",
             "Peste jumătate din cereri (51,9%) nici nu ajunseseră încă la registrator.",
             "Nu arată cât durează fiecare etapă pentru un dosar anume. Datele publice nu au momentul trecerii dintre etape.",
             ["C28", "C29", "C03"])
    b += h3("4.2 Ce s-a întâmplat într-o singură săptămână")
    b += P("Ministerul Justiției a publicat stocurile celor două etape la 30 octombrie și la 6 noiembrie. Comparând cele două fotografii, vedem direcția. " +
           hl("Într-o săptămână, coada de operare a scăzut cu 8.300 de cereri, iar coada de la registrator a crescut cu 4.396.") + E('C33') +
           " Operarea a trimis mai departe mai multe dosare decât a putut soluționa etapa a doua. În total, stocul a scăzut ușor în acea săptămână, de la 208.318 la 204.414 cereri." + E('C85') +
           " O singură săptămână nu arată tendința: așteptarea dosarelor soluționate a continuat să crească." + E('C16'),
           "Cum se citește", "Bilanțul folosește doar două date oficiale. Nu arată ce s-a întâmplat în fiecare zi dintre ele.", key=True)
    b += fig("FIGURA 4.2", "STOCURI OFICIALE · 30 OCT. ȘI 6 NOV. 2026",
             "Într-o săptămână, operarea s-a golit parțial, iar coada de la registrator a crescut",
             "fi06_tandem.svg",
             "Câte cereri așteptau în fiecare etapă la două date oficiale, la o săptămână distanță.",
             "Barele albastre sunt operarea, cele portocalii registratorul. Cifrele colorate arată schimbarea.",
             "În acea săptămână, blocajul principal era la registrator. Operarea lucra mai repede.",
             "Nu înseamnă că operarea nu mai e o problemă. Ea rămâne aproape la fel de încărcată (secțiunea 4.3).",
             ["C33", "C29"])
    b += h3("4.3 Cele două etape sunt aproape la fel de încărcate")
    b += P("În acea săptămână, operarea a lucrat cu circa 16–20% mai repede decât soluționarea." + E('C34') +
           " " + hl("Diferența e mică, iar asta are o consecință practică importantă:") + " dacă mutăm oameni din operare la soluționare, operarea poate deveni rapid etapa mai lentă (capitolul 9).",
           "Verificare", "În eșantionul nostru din portal, circa jumătate din dosarele în așteptare erau încă la operare, la fel ca în cifra oficială." + E('C06'))
    b += h3("4.4 Online-ul nu sare peste operare")
    b += P("Ne-am putea aștepta ca o cerere depusă online să meargă direct la registrator. Datele arată altceva. " + hl("Cererile depuse în afara programului, deci doar online, nu trec mai repede: așteaptă chiar puțin mai mult.") + " Comparația e în aceeași zi și același județ." + E('C36'),
           "Exemplu", "O cerere trimisă duminică seara intră luni în aceeași coadă de operare. O preia tot un operator, ca pe cea depusă la ghișeu.")
    b += h3("4.5 Coada e națională")
    _c89 = V('C89').split(' · ')
    b += P("Așteptarea e apropiată în toate oficiile: între " + V('C49').split('–')[0] + " și " + V('C49').split('–')[1] + " zile pentru deciziile din 1–18 noiembrie." + E('C49') + " " +
           hl("Cea mai lungă așteptare e acum la oficiul " + _c89[0].rsplit(' ', 1)[0] + ", urmat de un grup de oficii cu valori aproape egale; înainte de valul național, episoade locale de întârziere au avut " + ", ".join(x.split(" +")[0] for x in V('C88').split(" · ")) + ".") + E('C89', 'C88') +
           " Diferențele de azi sunt de câteva zile: coada e în principal comună, la nivel național.",
           "Cum se citește clasamentul", "Clasamentul arată unde apar diferențele, ca să se știe unde să se intervină. Nu e o notă pentru personal: județul este oficiul de depunere, nu neapărat locul unde se soluționează dosarul, iar respingerile depind și de ce depun solicitanții. Clasamentele complete sunt în Volumul 5.")
    b += fig("FIGURA 4.3", "CLASAMENT PE OFICII · MEDIANA DECIZIILOR 1–18 NOV. 2026",
             "Toate oficiile sunt într-o bandă îngustă, dar diferențele există și pot fi localizate",
             "fi08_judete.svg",
             "Oficiile, ordonate după așteptarea obișnuită a deciziilor din 1–18 noiembrie, pe oficiul de depunere.",
             "Fiecare bară e un oficiu. Roșu: cele mai lungi 10%; verde: cele mai scurte 10%. Linia albastră e mijlocul oficiilor.",
             "Coada e în principal națională; diferențele de câteva zile arată unde merită verificat ce e diferit.",
             "Nu e o notă pentru personal: oficiul e cel de depunere, iar ordinea din 2025 nu prezice ordinea din 2026.",
             ["C49"])
    b += concl("Fiecare dosar trece prin două cozi, cu ritmuri apropiate. În săptămâna măsurată, coada de la registrator creștea, iar operarea era foarte aproape. Dacă întărești doar una, problema se mută în cealaltă.")
    return chapter(4, "rc-04", "Cele două cozi",
                   "Operarea și soluționarea, explicate pe un exemplu simplu. Bilanțul oficial din 30 octombrie–6 noiembrie arată unde se adună dosarele.",
                   "Surse: Nota MJ 30.10 și 6.11.2026 · BERC · eșantion myportal", b)


def ch5():
    b = idea("Cererile au crescut cu circa jumătate în august–octombrie. Cele mai multe au venit concentrat, înainte de sfârșitul perioadei inițiale de tranziție la CAEN Rev. 3.")
    b += h3("5.1 Cât a crescut cererea")
    b += P(hl("Ministerul Justiției raportează că cererile zilnice au crescut de la 4.533 la 6.931, adică cu circa 53%, între prima jumătate a anului și august–octombrie.") + E('C47') +
           " Producția a crescut și ea, dar nu în același ritm. Diferența s-a adunat în coadă.",
           "Cum am verificat", "Am reprodus cifrele Ministerului din datele noastre, cu numerele de înregistrare ale cererilor: " + V('C98') + " pentru prima jumătate a anului; pentru august–octombrie, vezi mai jos." + E('C98'))
    b += P(hl("Media pe trei luni ascunde însă un vârf: în septembrie au intrat " + V('C99').split(' / ')[1].split(' (')[0] + " de cereri pe zi lucrătoare, iar în octombrie și noiembrie intrările au revenit la " + V('C99').split(' / ')[2] + ", respectiv " + V('C99').split(' / ')[3].split(' ·')[0] + " pe zi, fără înmatriculările încă în curs. Cu ele, octombrie a fost aproape de ritmul de soluționare, iar noiembrie, sub el.") + E('C99') +
           " Stocul estimat din datele noastre a început să scadă încet: " + V('C100') + "; o parte din scădere vine din înmatriculările în curs, pe care eșantionul nu le vede." + E('C100') + " Coada s-a format, deci, în câteva săptămâni din septembrie, înainte de sfârșitul perioadei inițiale de tranziție la CAEN Rev. 3, și se golește acum mult mai încet decât s-a umplut.",
           "Cum am măsurat", "Fiecare cerere are un număr dintr-un contor național care crește în ordinea depunerii. Contorul numără și certificate sau informări; eșantionul din portal arată ce fel de cerere e în spatele fiecărui număr, iar buletinul arată când a fost decisă. Metoda e descrisă în anexa „Metodologia”.")
    b += P("Și eșantionul nostru din portal arată un vârf: în săptămâna de vârf din septembrie s-au depus de aproape două ori mai multe cereri decât într-o săptămână de vară." + E('C22') +
           " Vârful a venit chiar înainte de 25 septembrie, sfârșitul perioadei inițiale de tranziție la CAEN Rev. 3. În perioada de tranziție ambele versiuni ale codurilor sunt valabile, iar în textele citite nu am găsit o sancțiune sau un termen de decădere; perioada a fost prelungită cu 6 luni." + E('C152'),
           "Rezervă", "Estimare din eșantion, pentru toate tipurile de cereri, nu doar pentru cele care ajung la registrator.")
    b += h3("5.2 De ce se adună cererile înainte de datele-limită")
    b += P("Mulți depun aproape de o dată-limită. Asta e un comportament obișnuit, nu o problemă a firmelor. Când o dată-limită sau sfârșitul unei perioade de tranziție e același pentru sute de mii de firme, cererile vin concentrat în câteva săptămâni. Un sistem dimensionat pentru un flux constant nu poate absorbi un asemenea vârf fără coadă.",
           "Exemplu", "Dacă o sută de firme au de depus aceeași cerere într-un an, ele ar ocupa două pe săptămână. Dacă toate depun în ultima lună, ar fi peste douăzeci pe săptămână.")
    b += P(hl("Prelungirea unei perioade de tranziție nu schimbă acest comportament: mută doar momentul vârfului.") + " Dacă noua dată cade tot într-o perioadă aglomerată, vârful se repetă.")
    b += h3("5.3 Unele dosare trec mai repede")
    b += P("Nu toate dosarele așteaptă la fel. În 2–19 noiembrie, " + V('C38').split('·')[0].strip() + " și " + V('C38').split('·')[1].strip() + " au fost rezolvate în cel mult 14 zile, deși așteptarea obișnuită era de 53, respectiv 42 de zile." + E('C38') +
           " " + hl("Dosarele rapide sunt mai ales dosare fără probleme; coada nu e strict cronologică."),
           "Rezervă", "Dosarele rapide sunt, în mare parte, dosare fără probleme: aproape niciunul nu e respins. Cereri mai simple sau priorități prevăzute de lege sunt explicații plauzibile. Nu afirmăm că cineva sare coada." + E('C102'))
    b += h3("5.4 Cum se numără „soluționările”")
    b += P("Cifrele Ministerului de „soluționări” pe zi sunt mai mari decât deciziile finale din buletin. Diferența se explică dacă se numără și amânările ca soluționări." + E('C48') +
           " " + hl("Nu e o contradicție între date, ci o diferență de definiție.") + " Pentru comparații corecte, trebuie spus mereu ce se numără.")
    b += concl("Cererile au crescut mult și au venit concentrat înaintea datelor-limită. Sistemul nu poate absorbi un asemenea vârf fără coadă. O parte din dosare trece totuși mai repede, din motive pe care datele publice nu le arată.")
    return chapter(5, "rc-05", "Cererile și ritmul lor",
                   "Cât a crescut cererea, de ce vine concentrat și de ce unele dosare trec mai repede decât altele.",
                   "Surse: Nota MJ 6.11.2026 · BERC · eșantion myportal", b)


def ch6():
    b = idea("Circa una din cinci decizii este o amânare, iar aproape toate respingerile vin după o amânare neîndeplinită. Circa o cincime din amânări s-ar putea preveni cu verificări la depunere, iar aceleași verificări ar preveni și respingeri." + E("C144", "C139"))
    b += h3("6.1 Ce este o amânare")
    b += P("Când un dosar e incomplet, registratorul nu îl respinge imediat. Dă un termen de completare, de cel mult 15 zile. Asta e o amânare. Firma aduce actul lipsă, iar dosarul primește apoi o decizie." + E('C03'),
           "Exemplu", "Lipsește dovada că firma are dreptul să folosească spațiul declarat ca sediu. Registratorul amână și cere documentul. Firma îl depune, iar dosarul e reluat.")
    b += P("Pe lângă deciziile finale, se dau " + V('C03') + " amânări pe zi lucrătoare." + E('C03') +
           " Proporția e stabilă de ani de zile: circa una din cinci decizii." + E('C21') +
           " " + hl("Amânările nu au crescut în criză; doar că, într-o coadă lungă, fiecare amânare costă mai mult timp."))
    b += fig("FIGURA 6.1", "STRUCTURA DECIZIILOR · PE PERIOADE · 2023–2026",
             "Proporția amânărilor e aceeași de ani de zile: circa una din cinci decizii",
             "fi07_amanari.svg",
             "Din toate deciziile unei perioade, ce parte sunt admiteri, amânări și respingeri.",
             "Fiecare rând e o perioadă. Partea din mijloc, ocru, sunt amânările.",
             "Amânările nu sunt cauza crizei. Proporția lor nu s-a schimbat.",
             "Nu spune că amânările sunt inutile. Multe sunt necesare pentru un dosar corect.",
             ["C21", "C39"])
    b += h3("6.2 Cât așteaptă un dosar amânat")
    b += P(hl("Un dosar amânat în noiembrie a așteptat circa 42 de zile până la prima amânare, apoi circa 14 zile de la ultima amânare până la decizie.") + E('C37') +
           " Asta înseamnă că, după completare, dosarul nu reia coada de la capăt. Problema e prima parte: până la prima analiză, din cauza cozii, trec săptămâni.",
           "De ce contează", "Dacă actul lipsă ar fi semnalat la depunere, firma l-ar putea aduce imediat. Amânarea ar dispărea, iar dosarul n-ar mai pierde săptămâni.", key=True)
    b += h3("6.3 Respingerile și redepunerile")
    b += P("În criză, aproximativ 1 din 12 dosare finale e respins, față de 1 din 17 pe vechea platformă." + E('C39') + " Nivelul era însă similar și în 2025 și în prima jumătate a lui 2026, deci creșterea nu ține de criză." +
           " Cu identificatorul exact al firmei: " + hl("după o respingere, aproape jumătate din firme depun o nouă cerere în 30 de zile, față de una din șapte după o admitere.") + E('C103') +
           " " + hl("O respingere nu scoate dosarul din sistem: de obicei aduce încă un dosar în coadă.") + " Acesta trece din nou prin ambele etape." +
           " Aproape toate respingerile vin după o amânare neîndeplinită (secțiunea 6.5)." + E('C144'),
           "Rezervă", "„Depune din nou” înseamnă orice cerere ulterioară a aceleiași firme; comparația cu firmele admise arată cât e redepunere și cât activitate obișnuită." + E('C103', 'C40'))
    b += PSEC.section_html(V, E, hl, P, fig)
    b += RSEC.section_html(V, E, hl, P, fig)
    b += concl("Amânările și respingerile înseamnă analize repetate ale acelorași dosare. Ele nu au crescut ca proporție, dar într-o coadă lungă costă mult timp. Respingerea e de obicei o amânare nerezolvată, din aceleași cauze; lipsurile prinse la depunere ar scurta drumul fiecărui dosar și ar preveni ambele.")
    return chapter(6, "rc-06", "Amânări și respingeri",
                   "Ce este o amânare, cât durează, de ce se amână și se resping dosarele și ce se poate verifica automat la depunere.",
                   "Surse: BERC 2023–2026 · Legea 265/2022 art. 106 · buletine PDF (motivele amânărilor și ale respingerilor)", b)



def ch7():
    c70 = V('C70').split(' · '); mape = c70[0].split('≈')[1]; up = c70[1].replace('real ≥ prognozat în ', ''); mx = c70[2].replace('maxim ', '')
    c62c = V('C62').split(' (')[0]; c62r = V('C62').split('(')[1].rstrip(')')
    b = idea("Fără măsuri noi, coada nu se golește singură. Modelul verificat arată o așteptare de ordinul a patru-cinci luni în 2027, cu un vârf de peste cinci luni. Prognoza e dată ca interval, pentru că depinde de câte cereri vor veni.")
    b += h3("7.1 Cum lucrează prognoza")
    b += P("Prognoza folosește un model de coadă care pornește de la stocul de azi și adaugă, zi de zi, cererile care intră și dosarele care ies. Intrările includ fluxul obișnuit și cele trei valuri anunțate: actualizările CAEN, majorările de capital și sarcinile fiscale. Ieșirile pornesc de la ritmul de soluționare măsurat în ultimele zile. " +
           hl("Pentru că nimeni nu știe exact câte cereri vor veni, modelul rulează 2.000 de variante plauzibile; rezultatul e un interval, nu o singură cifră.") + E('C58', 'C69'),
           "De ce 2.000 de variante", "Fiecare variantă e o „lume posibilă”, cu alte valori pentru cereri, stoc și ritm de lucru. Mijlocul lor (mediana) e cazul central. Intervalul p10–p90 cuprinde 8 din 10 variante. Lățimea intervalului vine din ipotezele de intrare (Volumul 2), nu e o probabilitate măsurată.")
    b += P("Ce anume prognozăm: așteptarea unui dosar obișnuit, tratat în ordinea sosirii. Coada reală nu e strict cronologică: unele dosare trec mai repede, iar cele amânate stau mai mult." + E('C38', 'C74') + " Prognoza descrie deci dosarul tipic, nu fiecare dosar.",
           "Unități", "Modelul numără munca în dosare-echivalent: un dosar CAEN simplu valorează mai puțin decât unul obișnuit.")
    b += P("Prognoza măsoară altceva decât capitolul 2. Acolo am măsurat cât au așteptat dosarele soluționate acum. Aici estimăm cât va aștepta, până la decizie, un dosar depus la o anumită dată.",
           "Exemplu", "Un dosar de modificare soluționat în săptămâna 16–20 noiembrie a așteptat " + V('C14') + " zile. Unul depus azi va fi soluționat peste câteva săptămâni, când coada e mai lungă, deci va aștepta mai mult." + E('C14', 'C58'))
    b += h3("7.2 Ce arată prognoza fără măsuri noi")
    b += P(hl("Fără măsuri noi, un dosar depus acum ar aștepta, în cazul central, " + V('C58') + " zile; la mijlocul lui 2027, " + V('C59') + " zile; iar vârful ar ajunge la " + V('C60') + " zile.") + E('C58', 'C59', 'C60') +
           " Cifrele dintre paranteze sunt intervalul p10–p90. Creșterea vine din valurile de cereri anunțate pentru 2027: întâi actualizările CAEN, apoi majorările de capital. " +
           "În 2027, în model, raportul dintre munca intrată și capacitate este " + V('C67') + ": intră mai mult decât poate ieși, deci coada crește." + E('C67'),
           "Cum se citește", "„≈138 (105–175)” înseamnă: cazul central este de circa 138 de zile; în 8 din 10 variante, valoarea e între 105 și 175 de zile." + E('C59'), key=True)
    b += fig("FIGURA 7.1", "MODEL VERIFICAT · FĂRĂ MĂSURI · SĂPTĂMÂNAL PÂNĂ ÎN IUNIE 2028",
             "Fără măsuri noi, așteptarea urcă în 2027 și rămâne de ordinul lunilor până în 2028",
             "fi12_prognoza.svg",
             "Câte zile ar aștepta un dosar depus în fiecare săptămână, de acum până în iunie 2028, dacă nu se schimbă nimic.",
             "Linia roșie e cazul central. Banda roz cuprinde 8 din 10 variante simulate. Punctele marchează iunie 2027, decembrie 2027 și iunie 2028.",
             "Coada nu se golește singură: valurile de cereri din 2027 o împing în sus, iar banda largă arată cât de mult contează ipotezele.",
             "Nu e o predicție exactă pentru o anumită zi și nu include efectul OUG sau al altor măsuri.",
             ["C58", "C59", "C60", "C42"])
    b += h3("7.3 Câte dosare ar aștepta")
    b += P(hl("Fără măsuri noi, volumul de muncă în așteptare s-ar putea dubla față de punctul de pornire al modelului.") + " În iunie 2028, cazul central e de " + c62c + " dosare-echivalent, cu un interval foarte larg, " + c62r + "." + E('C62'),
           "Dosar-echivalent", "Un dosar CAEN simplu cere mai puțină muncă decât unul obișnuit. Modelul numără munca, exprimată în dosare standard. De aceea cifra nu se compară direct cu numărul oficial de cereri.")
    b += fig("FIGURA 7.2", "MODEL VERIFICAT · STOC ÎN AȘTEPTARE · FĂRĂ MĂSURI",
             "Fără măsuri noi, stocul crește în 2027 și rămâne ridicat",
             "fi14_stoc.svg",
             "Câtă muncă ar aștepta în sistem, săptămână de săptămână, în scenariul fără măsuri noi.",
             "Linia albastră e cazul central, banda e intervalul p10–p90. Rombul negru e stocul oficial comunicat de Ministerul Justiției la 6 noiembrie.",
             "Modelul pornește din același punct ca cifra oficială, apoi stocul crește odată cu valurile de cereri.",
             "Nu e numărul de firme care așteaptă. E volumul de muncă, exprimat în dosare standard.",
             ["C62", "C28"])
    b += h3("7.4 Cât de bine prognozează modelul")
    b += P("Am testat cea mai importantă intrare a modelului, ritmul de soluționare, pe nouă ferestre de câte patru săptămâni din 2026. De fiecare dată am prognozat ritmul doar din datele disponibile atunci și l-am comparat cu ce s-a întâmplat apoi. " +
           hl("Eroarea medie a fost de circa " + mape + "; în " + up + " ferestre ritmul real a fost cel puțin cel prognozat.") + E('C70') + " Testul e făcut în timp real: folosește doar deciziile publicate până la fiecare dată, iar ultimele zile sunt incomplete la momentul respectiv. Pe datele complete de azi, aceeași regulă ar fi supraestimat ritmul în cele mai multe ferestre; abaterea ține deci de întârzierea publicării, nu de model.",
           "Rezervă", "Testul validează ritmul de soluționare pe patru săptămâni, nu prognoza pe 2028 în ansamblu. Abaterea mare din septembrie (" + mx + ") vine dintr-o accelerare pe care modelul nu o putea anticipa." + E('C70'))
    b += fig("FIGURA 7.3", "TEST PE DATE NEVĂZUTE · RITMUL DE SOLUȚIONARE · 2026",
             "Ritmul de soluționare se prognozează bine pe patru săptămâni",
             "fi19_validare.svg",
             "Pentru nouă ferestre succesive: ritmul prognozat din datele de până atunci și ritmul observat apoi.",
             "Bara deschisă e prognoza, bara închisă e realitatea. Eticheta arată cu cât a diferit realitatea; roșu peste 10%.",
             "Ritmul de soluționare, principala intrare a modelului, se prognozează pe termen scurt cu o eroare de circa 5%.",
             "Nu validează valurile de cereri din 2027. Acelea sunt ipoteze bazate pe datele Ministerului.",
             ["C70"])
    b += P(hl("Am testat și modelul de coadă în întregime, pe trecut: pus să refacă lunile martie–septembrie 2026 cu intrările și capacitatea reale din BERC, reproduce așteptarea observată cu o eroare medie de 1–3 zile.") + E('C96') +
           " Același test arată și limita: o prognoză făcută doar cu ce se știa la începutul verii, fără să știe de valul de cereri, ar fi subestimat așteptarea cu până la circa 11 zile." + E('C97') +
           " Mecanismul e corect; incertitudinea principală e câte cereri vor veni. De aceea dăm grile și scenarii, nu o singură cifră.",
           "Cum s-a făcut testul", "Am pornit modelul de la trei date din trecut (martie, iunie, august 2026) și am comparat așteptarea prezisă pentru fiecare zi de depunere cu mediana observată în BERC, pentru cohortele deja decise.")
    b += fig("FIGURA 7.4", "TEST PE TRECUT · MODELUL DE COADĂ · DEPUNERI IUNIE–SEPTEMBRIE 2026",
             "Cu intrările reale, modelul reproduce așteptarea; fără să știe de val, o prognoză ar fi subestimat-o",
             "fi23_backtest.svg",
             "Așteptarea pe săptămâna depunerii: observată în BERC, refăcută de model cu intrările reale și prognozată la 1 iunie fără informații despre val.",
             "Linia neagră e realitatea. Linia verde aproape o atinge. Linia roșie punctată se îndepărtează când vin mai multe cereri.",
             "Modelul de coadă e corect; ce nu se poate ști dinainte e mărimea valurilor de cereri.",
             "Nu validează direct prognoza pentru 2027–2028; arată pe ce se poate și pe ce nu se poate conta.",
             ["C96", "C97"])
    b += h3("7.5 Anotimpurile cererilor")
    b += P(hl("Începutul anului aduce în mod obișnuit cu " + V('C71').split(' · ')[0] + " mai multe cereri pe zi decât noiembrie, iar iulie–august cu " + "5–6%" + " mai puține.") + E('C71') +
           " Valurile anunțate pentru începutul lui 2027 se suprapun deci peste un sezon deja aglomerat.",
           "De ce contează", "Capacitatea suplimentară e mai utilă dacă e gata în ianuarie. Aceeași capacitate adusă în vară ar găsi mai puține cereri.")
    b += fig("FIGURA 7.5", "PROFIL SEZONIER · CERERI PE ZI FAȚĂ DE NOIEMBRIE",
             "Ianuarie–martie sunt cele mai aglomerate luni ale anului",
             "fi20_sezon.svg",
             "Cu cât diferă, în mod obișnuit, cererile pe zi din fiecare lună față de noiembrie.",
             "Barele roșii sunt lunile mai aglomerate, cele verzi lunile mai liniștite.",
             "Orice plan de capacitate trebuie să țină cont de vârful obișnuit de la începutul anului.",
             "Nu include valurile excepționale (CAEN, capital). Acelea vin peste acest profil.",
             ["C71"])
    b += h3("7.6 Ipoteze pentru proiectul de OUG")
    b += P("Am rulat aceeași prognoză pentru trei ipoteze de livrare a proiectului de OUG: slabă, centrală și ridicată. Ele diferă prin câți oameni ajung efectiv la soluționare. " +
           hl("Livrarea contează mult: pe aceleași simulări, o livrare slabă câștigă puține zile, iar una ridicată peste două luni, în iunie 2028.") + " Valorile: " + V('C61') + " zile." + E('C61', 'C43'),
           "Ipoteze", "Livrare slabă: circa 5 posturi nete; centrală: 15, plus transferul unor acte (Art. III); ridicată: 30. Detaliile proiectului sunt în capitolul 9.")
    b += fig("FIGURA 7.6", "MODEL VERIFICAT · TREI IPOTEZE DE LIVRARE A OUG",
             "Cât ajută OUG depinde de câți oameni ajung efectiv la registrator",
             "fi13_ipoteze.svg",
             "Cazul central al așteptării, săptămână de săptămână, fără măsuri noi și în trei ipoteze de livrare a OUG.",
             "Fiecare linie e o ipoteză. Benzile pale arată intervalul p10–p90 pentru varianta fără măsuri noi și pentru livrarea ridicată.",
             "Chiar și livrarea ridicată lasă o așteptare de ordinul a două luni în iunie 2028.",
             "Nu spune care ipoteză se va realiza. Arată cât de mult contează livrarea.",
             ["C61", "C42", "C43"])
    b += concl("Fără măsuri noi, așteptarea crește în 2027 și rămâne de ordinul lunilor până în 2028. Prognoza e un interval, nu o cifră exactă, iar lățimea lui vine din ipotezele de intrare. Cât de mult ajută OUG depinde de câți oameni ajung efectiv la registrator.")
    return chapter(7, "rc-07", "Prognoza până în 2028",
                   "Ce se întâmplă dacă nu se schimbă nimic: așteptarea, stocul, sezonul cererilor și cât de bine prognozează modelul.",
                   "Model de coadă verificat (2.000 de variante) · BERC · Nota MJ 6.11.2026", b)


def ch8():
    c63 = V('C63').split(' · '); pos = c63[0].split('→ ')[1]; neg = c63[1].split('→ ')[1].split(' (')[0]; base = c63[1].split('față de ')[1].rstrip(')')
    b = idea("Coada e decisă de raportul dintre viteza de ieșire și viteza de intrare. Sistemul e atât de aproape de limită încât o schimbare de 10% în oricare dintre ele mută așteptarea din 2028 cu luni întregi.")
    b += h3("8.1 Ce este grila")
    b += P("Grila răspunde la o întrebare simplă: ce se întâmplă dacă intră mai multe sau mai puține cereri, iar Registrul lucrează mai repede sau mai încet? Fiecare rând e o schimbare a vitezei de intrare, iar fiecare coloană o schimbare a vitezei de ieșire, față de prognoza fără măsuri noi. Celula arată așteptarea în iunie 2028." + E('C63'),
           "Cum am calculat", "Am rulat același model verificat de 36 de ori, de fiecare dată cu alte procente aplicate tuturor intrărilor, inclusiv valurilor, și întregii capacități, din 19 noiembrie 2026. Celula încadrată reproduce exact prognoza fără măsuri noi.")
    b += P("Un exemplu de citire. Luați rândul „+10%” (vin cu o zecime mai multe cereri) și coloana „+20%” (Registrul soluționează cu o cincime mai mult). Celula arată circa 70 de zile în cazul central. Deci, chiar dacă cererile cresc, o capacitate care crește mai repede decât ele scurtează coada. " +
           hl("Regula grilei: coada scade mult doar când viteza de ieșire crește mai mult decât viteza de intrare; dacă cresc la fel, așteptarea scade doar puțin.") + E('C64'),
           "Două panouri", "Panoul din stânga arată cazul central. Panoul din dreapta arată cazul nefavorabil: valoarea depășită doar de 1 din 10 variante. Pentru planificare prudentă, contează panoul din dreapta.")
    b += fig("FIGURA 8.1", "GRILĂ DE SENSIBILITATE · INTRĂRI × IEȘIRI · IUNIE 2028",
             "Câteva procente în plus la ieșire valorează luni de așteptare",
             "fi15_grila.svg",
             "Așteptarea estimată în iunie 2028 pentru 36 de combinații de viteze. Stânga: cazul central. Dreapta: cazul nefavorabil (p90).",
             "Numărul din celulă = zile de așteptare în iunie 2028 (nu e un câștig și nu e un procent). Porniți de la celula încadrată: 136 de zile, fără schimbări. Coloanele = cât de repede soluționează Registrul; rândurile = câte cereri intră. Verde = coadă mică, roșu = coadă mare. «≤3» = coada e practic goală.",
             "Pe diagonală, când intrările și ieșirile cresc la fel, așteptarea scade doar puțin (stocul existent se lucrează ceva mai repede). Contează raportul dintre ele.",
             "Nu e un plan. Grila presupune că schimbarea începe imediat; în realitate, capacitatea nouă vine cu întârziere.",
             ["C63", "C64", "C65", "C66"])
    b += h3("8.2 De ce 10% contează atât de mult")
    b += P(hl("Cu aceleași cereri, o capacitate cu 10% mai mare ar reduce așteptarea din iunie 2028 la " + pos + " de zile, iar una cu 10% mai mică ar urca-o la " + neg + " de zile, față de " + base + ".") + E('C63') +
           " Motivul e că sistemul lucrează foarte aproape de limită: în 2027, raportul dintre munca intrată și capacitate e " + V('C67') + " în model." + E('C67') +
           " Când intră puțin mai mult decât iese, diferența se adună zi de zi.",
           "Analogie", "O cadă în care curge puțin mai multă apă decât se scurge se umple încet, dar sigur. Dacă scurgerea devine puțin mai rapidă decât robinetul, cada începe să se golească. Diferența e mică la robinet, dar uriașă după câteva luni.", key=True)
    b += P(hl("Când cererile și capacitatea cresc în același ritm, așteptarea scade doar puțin: " + V('C64') + " zile, față de " + V('C63').split('față de ')[1].rstrip(')') + ".") + E('C64') +
           " Deci nu volumul absolut decide, ci raportul. Iar dacă vin cu 10% mai multe cereri și capacitatea nu se schimbă, așteptarea ar ajunge la " + V('C66') + " zile." + E('C66'),
           "Cum se citește diagonala", "Celulele +10/+10, +20/+20 și +30/+30 din grilă au valori apropiate de celula centrală. O creștere a capacității care doar ține pasul cu cererile nu scurtează coada.")
    b += h3("8.3 Cât trebuie să crească ieșirea")
    b += P(hl("La cereri neschimbate, o capacitate cu circa o treime mai mare ar goli coada până la mijlocul lui 2028.") + E('C65') +
           " Cu +20%, cazul central coboară la circa trei săptămâni, dar cazul nefavorabil rămâne de ordinul a două luni și jumătate; abia la +40% coada e practic goală și în cazul nefavorabil." + E('C65') +
           " Doar prin personal, revenirea la câteva zile ar cere o capacitate suplimentară de " + V('C55') + "." + E('C55'),
           "Ce înseamnă «≤3»", "Modelul nu poate arăta o așteptare sub circa trei zile: atunci coada e practic goală. De aceea scriem «≤3», nu „3 zile”.")
    b += h3("8.4 Vârful nu dispare repede")
    b += P(hl("Chiar și cu o capacitate mult mai mare, valul de la începutul lui 2027 ar produce un vârf: " + V('C72') + " zile.") + E('C72') +
           " Capacitatea suplimentară trebuie să existe înainte de val, nu după el.",
           "De ce", "Valul CAEN vine concentrat în câteva luni. Chiar și un sistem care pe ansamblul anului ține pasul se aglomerează când primește o lună de cereri în câteva săptămâni.")
    b += fig("FIGURA 8.2", "GRILĂ DE SENSIBILITATE · VÂRFUL AȘTEPTĂRII 2026–2028",
             "Vârful din 2027 scade odată cu capacitatea, dar nu dispare",
             "fi16_grila_varf.svg",
             "Cel mai mare nivel al așteptării între acum și iunie 2028, pentru aceleași 36 de combinații.",
             "Citiți la fel ca figura 8.1. Valorile sunt mai mari decât în iunie 2028, pentru că vârful vine odată cu valul.",
             "Chiar cu +40% capacitate, vârful rămâne de ordinul a două luni dacă cererile nu scad.",
             "Nu arată când apare vârful. Momentul variază între variante.",
             ["C72", "C60"])
    b += h3("8.5 Ce împinge riscul în sus")
    b += P(hl("Valul de actualizări CAEN cântărește cel mai mult: fără el, vârful ar fi mai mic cu " + V('C68').split(' · ')[0] + " zile.") + E('C68') +
           " Valul de capital social și cel fiscal contează mai puțin, dar nu sunt neglijabile.",
           "Contrafactual", "Calculul elimină complet un val. Arată unde e pârghia, nu ce e realizabil: o parte din actualizări sunt necesare.")
    b += fig("FIGURA 8.3", "MODEL VERIFICAT · CE ADUCE FIECARE VAL DE CERERI",
             "Valul CAEN e cea mai mare sursă de risc",
             "fi17_valuri.svg",
             "Câte zile de așteptare s-ar evita dacă un val de cereri nu ar exista: la vârf (roșu) și în iunie 2028 (albastru).",
             "Punctul e mijlocul simulărilor, bara e intervalul p10–p90.",
             "Măsurile care reduc munca din valul CAEN, cum e conversia automată 1-la-1, au cea mai mare pârghie.",
             "Nu spune că valurile pot fi eliminate. Arată unde ar conta cel mai mult o reducere.",
             ["C68"])
    b += P("Am verificat și care incertitudini contează cel mai mult pentru vârf. " +
           hl("Trei lucruri decid vârful: câte cereri obișnuite vin, câte dosare se soluționează pe zi și cât de mare e valul CAEN.") + E('C69'),
           "Cum se citește", "Corelația de rang arată cât de strâns se mișcă vârful odată cu fiecare ipoteză, în cele 2.000 de variante. Pozitiv: crește riscul. Negativ: îl scade." + E('C69'))
    b += fig("FIGURA 8.4", "MODEL VERIFICAT · CE INCERTITUDINI CONTEAZĂ",
             "Ritmul cererilor și ritmul soluționării decid cel mai mult vârful",
             "fi18_factori.svg",
             "Cât de strâns e legat vârful așteptării de fiecare ipoteză a modelului.",
             "Barele roșii cresc riscul, cele verzi îl scad. Cu cât bara e mai lungă, cu atât ipoteza contează mai mult.",
             "Datele pe care merită investit în măsurare sunt intrările zilnice și ritmul de soluționare.",
             "Nu e o relație cauzală observată. E o măsură a sensibilității modelului.",
             ["C69"])
    b += counter_case([
        "Un argument contrar: grila presupune că o creștere de capacitate se obține imediat și se menține. În realitate, angajarea și instruirea durează. E adevărat: grila arată ce s-ar întâmpla, nu cât de ușor e de obținut.",
        "De aceea, capitolul 10 compară pachete concrete de măsuri, cu întârzierile lor de implementare.",
    ])
    b += concl("Ce decide coada e raportul dintre ieșiri și intrări. Sistemul e atât de aproape de limită încât 10% în plus sau în minus la capacitate înseamnă luni de așteptare. Cea mai mare pârghie e valul CAEN, iar capacitatea suplimentară trebuie să fie gata înainte de el.")
    return chapter(8, "rc-08", "Grila de risc: vitezele de intrare și ieșire",
                   "Ce se întâmplă dacă cererile sau capacitatea se schimbă cu câteva procente, cât trebuie să crească ieșirea și ce împinge riscul în sus.",
                   "Grilă pe modelul de coadă verificat · 36 de combinații × 2.000 de variante", b)


def ch9():
    b = idea("Proiectul de OUG ajută, dar nu readuce termenul la câteva zile. Efectul vine mai ales din capacitatea suplimentară la registrator, iar mutarea de personal din operare are o limită clară.")
    b += h3("9.1 Ce prevede proiectul, articol cu articol")
    b += P("Tabelul urmează textul integral pus în consultare la 18 noiembrie 2026. Modelul a fost rulat pe măsurile pe care le prevede textul, cu ipotezele de livrare declarate; verificarea fiecărei afirmații din preambul și din nota de fundamentare e în analiza separată a proiectului de OUG.",
           "Rezervă", "Consultarea publică e deschisă până la 24 noiembrie 2026; textul adoptat se poate schimba.")
    b += """<div class="tbl-wrap"><div class="tbl-head"><span class="tnum">Tabelul 9.1</span> Articolele proiectului și ce poate schimba fiecare</div>
<table class="oug-tbl"><thead><tr><th>Articol</th><th>Ce prevede</th><th>Etapa afectată</th><th>Ce poate schimba</th></tr></thead><tbody>
<tr><td>Art. I</td><td>Consilierii juridici specialiști ai ONRC (personal propriu) pot fi desemnați, prin decizie a directorului general, pentru motive temeinic justificate și cu acordul lor prealabil scris, să facă controlul de legalitate; au calitatea de registrator pentru actele lor și, dacă e cazul, drepturile salariale ale registratorului. Pe durata desemnării nu fac mențiunile din oficiu de la art. III.</td><td>Soluționare</td><td>Crește capacitatea registratorilor. Câștigul depinde de unde vin oamenii (secțiunea 9.3).</td></tr>
<tr><td>Art. II</td><td>Măsura din art. I se aplică până la 8 ianuarie 2028; tot până atunci se prelungește desemnarea conducerii de specialitate juridică pentru controlul de legalitate (Legea nr. 3/2026, care aprobă OUG nr. 109/2024).</td><td>Soluționare</td><td>Păstrează capacitatea temporară existentă și o adaugă pe cea din art. I.</td></tr>
<tr><td>Art. III</td><td>Introduce în Legea nr. 265/2022 art. 5^1 și 5^2: mențiunile în baza hotărârilor judecătorești și a actelor altor autorități se înscriu din oficiu de consilierii juridici specialiști, care verifică proveniența și concordanța actului, fără a examina legalitatea măsurii.</td><td>Soluționare</td><td>Scoate o parte mică din muncă de la registrator. Efect redus (secțiunea 9.2).</td></tr>
<tr><td>Art. IV</td><td>ONRC are 15 zile pentru optimizarea fluxului informatic al acestor mențiuni; art. III se aplică de la data optimizării.</td><td>Ambele</td><td>Condiție pentru Art. III. Efectul depinde de ce se livrează.</td></tr>
</tbody></table></div>"""
    b += P("Proiectul lucrează cu personalul existent. " + hl("Recrutarea de personal nou rămâne o măsură separată, iar efectul proiectului depinde de câți oameni ajung efectiv la soluționare.") + "")
    b += h3("9.2 Ce arată modelul verificat")
    b += P("Am testat proiectul pe modelul de coadă verificat, cu datele curente. Rezultatele sunt pentru iunie 2028 și sunt date ca intervale largi. " +
           hl("Fără măsuri noi, așteptarea ar fi de ordinul a patru luni; cu proiectul complet, de ordinul a trei luni.") + E('C42', 'C43') +
           " Doar Art. III schimbă foarte puțin: pe aceleași simulări, " + V('C44') + "." + E('C44') + " Concluzia robustă: proiectul singur nu readuce termenul la câteva zile.",
           "Cum se citește", "Punctul e valoarea de mijloc a simulărilor. Bara arată intervalul în care cade majoritatea rezultatelor. O eroare de 5% în capacitatea zilnică mută mult rezultatul, de aceea dăm ordine de mărime.", key=True)
    b += fig("FIGURA 9.1", "MODEL VERIFICAT · AȘTEPTARE ESTIMATĂ ÎN IUNIE 2028",
             "Proiectul de OUG ameliorează situația, dar așteptarea rămâne de ordinul lunilor",
             "fi09_oug.svg",
             "Așteptarea estimată în iunie 2028 în trei variante: fără măsuri noi, doar Art. III și proiectul complet.",
             "Punctul este mijlocul simulărilor. Bara arată intervalul p10–p90. Linia verde e reperul de 3 zile.",
             "Proiectul ajută, dar niciun interval nu se apropie de câteva zile.",
             "Nu este o predicție exactă. Câștigul nu se citește ca diferență între două puncte: se măsoară pe aceleași simulări (pentru Art. III, " + V('C44') + ").",
             ["C42", "C43", "C44"])
    b += h3("9.3 Limita mutării de personal din operare")
    b += P("Art. I poate aduce la soluționare consilieri juridici ai ONRC. Întrebarea e din ce activități vin ei. Dacă vin din operare, operarea pierde capacitate. " + hl("Pentru că cele două etape sunt aproape la fel de încărcate, câștigul are un optim și apoi dispare.") + E('C35'),
           "Analogie", "Dacă muți o persoană de la recepție la medic, cabinetul merge mai repede doar până când recepția devine mai lentă decât medicul. De acolo, mutarea face sala de așteptare de la recepție să crească.")
    b += fig("FIGURA 9.2", "MODEL ÎN TANDEM · CAPACITATE MUTATĂ DIN OPERARE",
             "Mutarea de personal din operare la registrator ajută doar până la un punct",
             "fi10_canibalizare.svg",
             "Ce poate procesa tot sistemul când o parte din capacitatea de operare este mutată la soluționare.",
             "Linia roșie e capacitatea sistemului. Ea urcă până la optim, apoi coboară. Liniile punctate verticale marchează optimul și punctul de câștig zero.",
             "Delegarea ajută cel mai mult când vine cu oameni noi sau din alte activități, nu din operare.",
             "Nu este textul OUG. Este un mecanism, calculat pe ipoteza că un om mutat face același număr de dosare în noua etapă.",
             ["C35", "C34"])
    b += counter_case([
        "Un argument contrar: juriștii delegați ar putea veni din activități care nu sunt operare, iar atunci problema canibalizării nu apare. E adevărat, și de aceea textul final contează.",
        "Datele publice nu arată însă din ce activități ar veni oamenii. Pentru o evaluare corectă, ar trebui publicat câți dintre juriștii eligibili lucrează azi la operare.",
    ])
    b += concl("Proiectul de OUG e un pas util, dar nu suficient. Cel mai mult ajută capacitatea nouă la registrator, fără a slăbi operarea. Pentru a readuce termenele la câteva zile, e nevoie de măsuri suplimentare, descrise în capitolul 10.")
    return chapter(9, "rc-09", "Proiectul de OUG, pe articole",
                   "Ce prevede fiecare articol, ce arată modelul verificat pentru iunie 2028 și de ce contează de unde vin juriștii delegați.",
                   "Surse: proiectul OUG și nota de fundamentare (textul integral, consultare MJ, 18.11.2026) · model de coadă verificat · model în tandem verificat", b)


def ch10():
    b = idea("Ajută măsurile care cresc ambele etape deodată sau care scot muncă din sistem. Prelungirea unei perioade de tranziție, singură, mută vârful fără să-l elimine.")
    rows = [
        ("Conversia automată a codurilor CAEN simple",
         "Când un cod vechi are un singur corespondent nou, schimbarea se poate face automat, fără dosar și fără registrator.",
         "Scoate dosare din ambele cozi deodată. Nu cere personal nou.",
         "Cere o regulă clară pentru ce înseamnă „simplu” și o modificare informatică."),
        ("Verificări automate înainte de depunere",
         "Portalul semnalează lipsurile formale înainte ca cererea să intre în coadă.",
         "Scade amânările și respingerile, deci analizele repetate (capitolul 6).",
         "Funcționează doar pentru erorile care pot fi detectate automat."),
        ("Procesare online fără operare manuală",
         "Cererile depuse structurat pe portal să treacă de etapa 1 fără reintroducere manuală.",
         "Eliberează operarea. Azi, online-ul nu sare peste operare (capitolul 4).",
         "Sistemul trebuie să aibă încredere în datele din formularul online."),
        ("Capacitate nouă la registrator, fără a slăbi operarea",
         "Delegare sau angajare de personal pentru controlul de legalitate.",
         "Crește etapa cu cea mai lungă coadă.",
         "Dacă oamenii vin din operare, câștigul e limitat (capitolul 9)."),
        ("Extinderea echilibrată a ambelor etape",
         "Capacitate adăugată atât la operare, cât și la soluționare.",
         "În modelul verificat, doar extinderea echilibrată golește ambele cozi.",
         "Cere resurse pentru două etape, nu pentru una."),
        ("Calendarul datelor-limită și al perioadelor de tranziție",
         "Datele-limită și sfârșitul perioadelor de tranziție care privesc multe firme să nu cadă în perioade deja aglomerate.",
         "Reduce vârfurile de cereri.",
         "Singur nu reduce volumul total; mută doar momentul vârfului."),
        ("Publicarea stocului pe tipuri și vârste",
         "ONRC să publice regulat câte dosare așteaptă în fiecare etapă, pe tipuri.",
         "Permite planificare și evaluarea corectă a măsurilor.",
         "Nu scurtează coada direct, dar arată unde să se intervină."),
    ]
    tbl = "".join(f"<tr><td><b>{a}</b></td><td>{c}</td><td>{d}</td><td>{e}</td></tr>" for a, c, d, e in rows)
    b += P("Fiecare pârghie de mai jos are un mecanism, un motiv pentru care ar funcționa și o capcană. Le prezentăm calitativ. Nu dăm cifre de efect pentru fiecare, pentru că efectul depinde de detalii de implementare pe care datele publice nu le arată.",
           "De ce fără cifre aici", "Pentru măsurile luate una câte una, estimările de efect sunt prea fragile. Pentru pachete de măsuri, secțiunea 10.3 dă intervalele modelului verificat.")
    b += f"""<div class="tbl-wrap"><div class="tbl-head"><span class="tnum">Tabelul 10.1</span> Pârghii: mecanism, de ce ar funcționa și capcana</div>
<table><thead><tr><th>Pârghie</th><th>Ce înseamnă</th><th>De ce ar funcționa</th><th>Capcana</th></tr></thead><tbody>{tbl}</tbody></table></div>"""
    b += h3("10.1 De ce o singură măsură nu ajunge")
    b += P(hl("Pentru că ambele etape sunt aproape la limită, o măsură care întărește doar una mută blocajul în cealaltă.") + E('C34') +
           " Măsurile care scot muncă din sistem, cum sunt conversia automată sau verificările înainte de depunere, ajută ambele etape deodată. De aceea ele au cel mai bun raport între efort și efect.",
           "Exemplu", "Dacă o mie de dosare CAEN simple pe zi nu mai intră deloc în coadă, operarea și registratorii primesc amândoi o mie de dosare mai puțin.", key=True)
    b += h3("10.2 Ce nu ajută singur")
    b += P(hl("Prelungirea termenului, fără alte măsuri, mută vârful în altă perioadă, fără să-l elimine.") + " Firmele depun tot aproape de noul termen. Dacă noul termen cade tot într-un sezon aglomerat, vârful se repetă.")
    b += h3("10.3 Ce arată modelul pentru pachete de măsuri")
    b += P("Modelul verificat a fost rulat și pentru pachete concrete de măsuri, cu întârzierile lor de implementare. " +
           hl("Un pachet minim realist, cu OUG prelungit, conversia CAEN 1-la-1, eșalonare și triaj, ar coborî așteptarea din iunie 2028, în model, la " + V('C54') + " zile.") + E('C54') +
           " Doar decongestionarea legislativă, fără personal nou, ar da " + V('C53') + " zile" + E('C53') + ", iar OUG extins cu ocuparea a 40% din posturile vacante finanțate, " + V('C52') + " zile." + E('C52') +
           " Pentru posturi există o limită legală: în 2026, concursurile pentru posturile vacante sunt suspendate. " + HIRE_40 + " O ocupare mai largă decât permit excepțiile ar cere o derogare prin lege sau OUG." + E('C153'),
           "Fragilitate", "Efectul fiecărei măsuri e o ipoteză de intrare, nu o măsurătoare. La o singură schimbare plauzibilă a ipotezelor, câștigul pachetului minim scade vizibil. De aceea dăm intervale și nu promitem un termen de câteva zile.", key=True)
    b += fig("FIGURA 10.1", "MODEL VERIFICAT · PACHETE DE MĂSURI · IUNIE 2028",
             "Pachetele care scot muncă din sistem coboară așteptarea mai mult decât proiectul OUG singur",
             "fi21_pachete.svg",
             "Așteptarea estimată în iunie 2028 pentru cinci variante: fără măsuri noi, proiectul OUG și trei pachete mai largi.",
             "Punctul e mijlocul simulărilor, bara e intervalul p10–p90. «≤3» înseamnă că, în variantele cele mai bune, coada e practic goală.",
             "Cel mai mult ajută combinația dintre capacitate suplimentară și scoaterea actualizărilor CAEN simple din coadă.",
             "Nu sunt promisiuni. Fiecare pachet depinde de ipoteze despre cât de bine se implementează fiecare măsură. Pachetul cu 40% din posturile vacante: " + HIRE_40[0].lower() + HIRE_40[1:],
             ["C42", "C43", "C52", "C53", "C54", "C153"])
    b += P("Trei cifre ajută la dimensionarea măsurilor. Circa un sfert din decizii sunt simple actualizări ale codului CAEN: " + V('C50') + "." + E('C50') +
           " Posturile ONRC aprobate, finanțate și ocupate sunt " + V('C51') + "." + E('C51') +
           " Iar " + hl("doar întărirea ambelor etape deodată reduce stocul total") + ": în modelul în tandem, dacă se întărește doar etapa registratorilor, aceștia rămân fără dosare, iar coada de operare ajunge la circa 199.000 de cereri." + E('C56'),
           "Exemplu", "Dacă dosarele CAEN simple ar fi convertite automat, fără dosar, ambele etape ar primi cu până la un sfert mai puține dosare. Munca economisită e mai mică de un sfert, pentru că un dosar CAEN simplu cere mai puțin efort decât unul obișnuit; ce parte din ele e convertibilă 1-la-1 nu se știe din datele publice.")
    b += open_question("Câți dintre consilierii juridici eligibili pentru delegare lucrează azi la operare? Răspunsul decide cât de mult poate ajuta Art. I. Doar ONRC are această informație.")
    b += concl("Cele mai bune măsuri scot muncă din sistem sau întăresc ambele etape deodată. Întărirea unei singure etape ajută doar până la un punct. Prelungirea unei perioade de tranziție, singură, amână problema.")
    return chapter(10, "rc-10", "Ce se poate face",
                   "Pârghiile disponibile, explicate pe rând: ce înseamnă, de ce ar funcționa și unde e capcana.",
                   "Bază: mecanismele măsurate în capitolele 4–9 · model în tandem verificat", b)


def ch11():
    b = idea("Cifrele din acest raport au trecut printr-un registru de verificare. Unde două surse independente se confirmă, avem încredere. Unde nu, spunem clar.")
    b += h3("11.1 Două surse care se verifică una pe alta")
    b += P("Folosim două surse independente. Buletinul oficial BERC conține fiecare decizie, cu data depunerii și data deciziei. Portalul myportal arată în ce etapă se află un dosar. Am verificat sursele una pe alta. " + hl("Pentru dosarele depuse în mai–septembrie, ambele surse dau aceleași valori lunare ale așteptării.") + E('C09'),
           "Rezervă", "Ambele surse măsoară doar dosarele deja soluționate. Acordul lor confirmă cifrele, dar nu elimină cenzurarea pentru lunile recente.")
    b += h3("11.2 Cum ne asigurăm că cifrele nu se schimbă")
    b += P("Toate cifrele sunt calculate o singură dată, dintr-un fișier blocat. Fiecare cifră are un cod, o sursă, scriptul care o produce și amprenta datelor de intrare. Dacă datele se schimbă, amprenta se schimbă, iar cifra trebuie reverificată. " + hl("Un verificator automat respinge orice cifră din text care nu are cod."))
    b += P("O verificare independentă a retras unele afirmații din versiunile anterioare: un calcul al productivității pe registrator, o afirmație despre ordinea strictă a dosarelor și câteva scenarii neverificate. Ele apar în Anexa B cu starea FAIL și nu sunt folosite în text.",
           "Transparență", "Păstrăm afirmațiile retrase în registru, ca să se vadă ce s-a corectat și de ce.")
    b += h3("11.3 Ce nu afirmăm")
    b += """<ul class="body-list notlist">
<li>Nu afirmăm că dosarele se rezolvă strict în ordinea depunerii. Datele arată că unele trec mai repede (capitolul 5).</li>
<li>Nu facem clasamente pe persoane (registratori). Clasamentele pe oficii arată unde apar diferențele, nu cine lucrează mai bine: oficiul din date e cel de depunere.</li>
<li>Nu afirmăm că producția din 2026 e un record absolut. Vârful a fost în februarie–martie 2025.</li>
<li>Nu dăm un număr de firme care așteaptă acum. BERC arată doar deciziile, nu cererile încă nerezolvate.</li>
<li>Nu dăm sfaturi despre ziua sau luna în care e mai bine să depuneți.</li>
<li>Nu explicăm cauza pasului de procedură din 27 aprilie 2026 și nici cauza dosarelor rapide. Le arătăm, nu le explicăm.</li>
<li>Nu dăm probabilități pentru scenarii. Le dăm ca intervale și ordine de mărime.</li>
<li>Nu afirmăm că vreun scenariu „ajunge la 3 zile”. Sub circa trei zile, coada e practic goală, iar metrica nu mai măsoară; scriem «≤3».</li>
</ul>"""
    b += h3("11.4 Ce ar trebui publicat")
    b += P(hl("Datele interne ale ONRC ar transforma estimările în măsurători.") + " Pentru o imagine completă, sunt necesare date pe care doar ONRC le are: stocul zilnic pe etape și pe tipuri de dosare, momentul trecerii dintre operare și soluționare și personalul activ pe fiecare etapă. Cu ele, evaluarea oricărei măsuri ar putea fi făcută pe date directe, nu pe estimări.")
    b += concl("Cifrele de aici sunt verificate pe două surse și au fiecare o proveniență. Unde datele nu ajung, spunem clar. Datele interne ale ONRC ar putea închide aceste goluri.")
    return chapter(11, "rc-11", "Cât de sigure sunt cifrele",
                   "Cum am verificat cifrele, ce a fost corectat și ce nu afirmăm.",
                   "Registru: claims_registry.csv · verificări: lint_numbers.py, Lean (Volumul 6)", b)



def ch12():
    OS = json.loads((ROOT / "independent_audit" / "out" / "osint_crosscheck.json").read_text(encoding="utf-8"))
    b = idea("Datele noastre sunt sursa de referință: buletinul BERC conține fiecare decizie, cu momentul depunerii și al soluționării. Cifrele publicate în presă le confirmă în cea mai mare parte; unde o cifră nu se reproduce din datele noastre, dăm valoarea noastră, definiția folosită și o explicație posibilă.")
    b += h3("12.1 Ierarhia surselor")
    b += P(hl("Buletinul BERC este sursa de referință pentru decizii și timpi: îl folosim integral, nu ca eșantion.") + " Ce nu e în BERC luăm din surse oficiale: stocul și intrările zilnice din notele Ministerului Justiției, etapa dosarelor din eșantionul nostru myportal. "
           "Presa și agregatorii sunt surse secundare: le comparăm cu datele noastre, dar nu le folosim în locul lor." + E('C91'),
           "Regula", "Când o cifră publică nu se reproduce din BERC, folosim cifra din BERC și spunem doar atât: valoarea noastră, definiția și perioada folosite și, cel mult, o explicație posibilă neutră (unități sau perioade diferite).", key=True)
    b += h3("12.2 Ce confirmă sursele publice")
    b += P(hl("Majoritatea cifrelor publicate despre coadă se regăsesc în datele noastre.") + " " + V('C91') + "." + E('C91') +
           " Cel mai clar exemplu: statistica oficială a înmatriculărilor și deciziile de admitere din buletin dau practic același număr pe primele nouă luni din 2026 și aceeași scădere în toamnă." + E('C92') +
           " Pragurile de timp din presă (peste 30, respectiv peste 40–45 de zile) sunt confirmate; pentru noiembrie, datele noastre arată chiar valori mai mari." + E('C84', 'C14'),
           "De ce contează", "Două surse independente care spun același lucru fac concluzia mult mai sigură decât oricare dintre ele singură.")
    b += h3("12.3 Ce nu se reproduce din datele noastre")
    b += P(hl("Cifra de peste 26.000 de cereri pe zi din nota de fundamentare a Ministerului (relatată și în presă) nu se reproduce din datele BERC analizate de noi pentru cererile de înregistrare.") +
           " Din datele noastre: cereri de înregistrare " + V('C98').split(' (')[0] + " în S1 2026; toate tipurile de cereri de pe contorul național, " + V('C165').split(' / ')[0] + " de numere pe zi lucrătoare în ianuarie–iulie 2026, față de " + V('C165').split(' / ')[1] + " în aceeași perioadă din 2025." + E('C93', 'C165', 'C98') +
           " Explicație posibilă: unități diferite (toate tipurile de cereri de pe contor, față de cererile de înregistrare).",
           "Cum am obținut cifra noastră", "Contorul național al numerelor de cerere: numărul maxim atins în ianuarie–iulie, împărțit la zilele lucrătoare legale; cererile de înregistrare: cererile cu decizie în BERC, pe luna depunerii.")
    b += P("Singura afirmație contrazisă, pentru aceeași perioadă, privește ordinea de soluționare. Presa descrie o procesare strict cronologică; în deciziile din 2–19 noiembrie, o parte din dosare trec mult mai repede decât ordinea depunerii." + E('C38') +
           " Explicații posibile: ordinea cronologică poate fi regula de repartizare, nu ordinea deciziilor; unele cereri au prioritate legală sau sunt mai simple; regula poate fi aplicată pe categorii. Datele arată rezultatul, nu cauza.")
    rows = "".join(f'<tr><td>{r["id"]}</td><td>{r["afirmatie"]}</td><td>{r["valoare_publica"]}</td><td>{r["valoarea_noastra"]}</td><td><b>{r["verdict"]}</b></td><td>{r.get("explicatii_posibile") or r["nota"]}</td></tr>' for r in OS["rows"])
    b += f"""<div class="tbl-wrap osint"><div class="tbl-head"><span class="tnum">Tabelul 12.1</span> Afirmațiile din presă despre coadă, față de datele noastre</div>
<table class="dt"><thead><tr><th>ID</th><th>Afirmația publică</th><th>Valoarea publică</th><th>Datele noastre</th><th>Verdict</th><th>Explicații posibile / notă</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Sursa: compilația de presă din 21.11.2026 (surse citate pentru fiecare afirmație în fișierul Excel, foaia „presa_vs_date_proprii”), comparată cu BERC, eșantionul myportal și nota MJ. Verdictul: CONFIRMAT (aceeași definiție, diferență mică), COMPATIBIL (alt indicator sau altă dată, dar consistent), CONTRAZIS (datele arată clar opusul, pentru aceeași perioadă și definiție), NU SE REPRODUCE din datele BERC analizate (posibil unități sau perioade diferite), NEVERIFICABIL din datele noastre.</p></div>"""
    b += h3("12.4 Dacă se confirmă cifrele publice despre CAEN")
    b += P("Prognoza de bază presupune un val CAEN suplimentar mai mic decât sugerează sursele publice. Nota Ministerului indică 902.243 de cereri CAEN încă așteptate, iar presa spune că aproape două treimi din firme nu și-au actualizat codurile. " +
           hl("Dacă firmele depun în masă înainte de sfârșitul perioadei de tranziție (1 aprilie 2027, după calculul nostru), așteptarea din iunie 2027 ar putea fi de " + V('C94').split(' (')[0] + " zile, față de circa 138 în prognoza de bază.") + E('C94', 'C59') +
           " " + hl("Conversia automată a codurilor CAEN simple ar reduce-o la " + V('C95').split(' (')[0] + " zile.") + E('C95'),
           "Rezervă", "Scenariu, nu prognoză: depinde de câte firme depun și când. Arată de ce conversia automată devine măsura decisivă dacă valul e mare.", key=True)
    b += fig("FIGURA 12.1", "MODEL VERIFICAT · SCENARIU DE CONFORMARE CAEN · IUNIE 2027",
             "Dacă valul CAEN e cât spun sursele publice, conversia automată devine decisivă",
             "fi22_caen.svg",
             "Așteptarea estimată în iunie 2027 dacă o parte din cele 902.243 de cereri CAEN rămase se depun până la sfârșitul perioadei de tranziție (1 aprilie 2027, după calculul nostru).",
             "Barele roșii: fără măsuri noi. Barele verzi: cu conversia automată a 75% din cererile CAEN. Bara subțire: intervalul p10–p90.",
             "Riscul crește repede cu numărul de firme care depun; conversia automată îl reduce la mai puțin de jumătate.",
             "Nu e o prognoză: e un test „ce-ar fi dacă”, pe același model verificat.",
             ["C94", "C95"])
    b += h3("12.5 Ce nu analizăm")
    b += P("Compilația de presă conține și informații despre contractele platformei, despre anchete și despre persoane. Acestea nu țin de coadă, nu pot fi verificate din datele noastre și nu sunt analizate în acest raport.")
    b += concl("Datele noastre și sursele publice spun, în mare, aceeași poveste. Unde o cifră nu se reproduce, rămânem la BERC și arătăm valoarea și definiția noastră. Cel mai mare risc pe care îl semnalează sursele publice e valul CAEN; față de el, conversia automată e măsura cu cel mai mare efect.")
    return chapter(12, "rc-12", "Sursele noastre și sursele publice",
                   "Ce confirmă presa, ce nu se reproduce din datele noastre și ce se întâmplă dacă cifrele publice despre CAEN se confirmă.",
                   "Surse: BERC (referință) · eșantion myportal · nota MJ · compilație de presă 21.11.2026", b)

# ================================================================== ANNEXES
def annexes():
    gl = [("Amânare", "Termen de completare dat de registrator, de cel mult 15 zile, când dosarul e incomplet."),
          ("BERC", "Buletinul Electronic al Registrului Comerțului: arhiva oficială a deciziilor."),
          ("Cenzurare la dreapta", "Când măsori durata doar pe dosarele terminate, iar cele încă în curs lipsesc. Rezultatul iese fals mic."),
          ("Decizie finală", "Admitere, respingere sau renunțare. Închide dosarul."),
          ("Mediană", "Valoarea din mijloc: jumătate din dosare stau mai puțin, jumătate mai mult."),
          ("myportal", "Portalul ONRC în care se vede etapa curentă a unui dosar."),
          ("OUG", "Ordonanță de urgență a Guvernului. Aici, proiectul din 18 noiembrie 2026."),
          ("Operare", "Etapa 1: un operator introduce și verifică dosarul."),
          ("Soluționare", "Etapa 2: un registrator decide asupra dosarului."),
          ("Interval p10–p90", "Intervalul în care cad 80% dintre rezultatele unei simulări."),
          ("Zi lucrătoare", "Zi fără weekend și fără sărbători legale."),
          ("Zi calendaristică", "Orice zi, inclusiv weekendurile și sărbătorile. Toate duratele din raport sunt în zile calendaristice."),
          ("Etapa 1 · operare", "Preluarea cererii: un operator introduce și verifică formal datele."),
          ("Etapa 2 · soluționare", "Controlul de legalitate și decizia registratorului."),
          ("Dosar / cerere", "În raport, un dosar este o cerere de înregistrare; un dosar poate cuprinde mai multe mențiuni."),
          ("Fără măsuri noi", "Scenariul de bază al prognozei: nicio măsură în plus față de situația de azi (fără OUG)."),
          ("Model verificat", "Motorul de prognoză al analizei, rerulat pe datele curente; rezultatele-cheie ale scenariilor au fost verificate separat (tot cu AI). Nu e un audit instituțional."),
          ("Reperul de 3 zile", "Echivalentul calendaristic al unei zile lucrătoare peste weekend (vineri → luni); sub el, coada e practic goală."),
          ("Prognoză", "Estimarea așteptării unui dosar depus la o dată viitoare, dacă ipotezele modelului se adeveresc."),
          ("Variantă simulată", "Una dintre cele 2.000 de „lumi posibile” ale modelului, fiecare cu alte valori plauzibile pentru cereri, stoc și ritm."),
          ("Caz central", "Mediana variantelor simulate: jumătate dau mai puțin, jumătate mai mult."),
          ("Caz nefavorabil (p90)", "Valoarea depășită doar de 1 din 10 variante simulate."),
          ("Grilă de sensibilitate", "Tabel care arată rezultatul modelului pentru mai multe combinații de ipoteze, aici viteza de intrare și viteza de ieșire."),
          ("Viteza de intrare / ieșire", "Câtă muncă nouă intră pe zi, respectiv câtă muncă soluționează Registrul pe zi."),
          ("Dosar-echivalent", "Unitate de muncă: un dosar standard. Un dosar CAEN simplu valorează mai puțin."),
          ("«≤3»", "Limita metricii: sub circa trei zile coada e practic goală, iar modelul nu mai distinge valori mai mici."),
          ("Test pe date nevăzute", "Prognoză făcută doar cu datele disponibile la un moment dat și comparată apoi cu realitatea."),
          ("Corelație de rang (Spearman)", "Măsură între −1 și 1 a cât de strâns urcă sau coboară două mărimi împreună."),
          ("Sezonalitate", "Variația obișnuită a cererilor de la o lună la alta, fără valurile excepționale.")]
    a = "".join(f"<tr><td><b>{x}</b></td><td>{y}</td></tr>" for x, y in gl)
    rows = sorted(REG.values(), key=lambda r: int(r["id"][1:]))
    # withdrawn (FAIL) claims: show only that they were withdrawn and why — never their numbers
    rb = "".join(
        (f'<tr><td>{r["id"]}</td><td>{r["public_ro"]}</td><td>{r["value"]}</td><td>{r["level"]}</td>'
         f'<td class="st-{r["status"]}">{r["status"]}</td><td>{r["rezerva_obligatorie"]}</td></tr>')
        if r["status"] != "FAIL" else
        (f'<tr><td>{r["id"]}</td><td><i>Afirmație retrasă</i></td><td>—</td><td>—</td>'
         f'<td class="st-FAIL">FAIL</td><td>{r["rezerva_obligatorie"].split(":")[0]}</td></tr>')
        for r in rows)
    rc = "".join(f'<tr><td>{r["id"]}</td><td>{r["source"]}</td><td><code>{r["script"]}</code></td>'
                 f'<td><code>{r["data_sha256"][:16]}…</code><br>{r["data_date"]}</td></tr>' for r in rows if r["status"] != "FAIL")
    return f"""
<section class="chapter" style="page: ra-a;"><div class="copen"><div class="cnum">Anexa A</div><h2>Glosar</h2></div>
<table class="gl-tbl"><tbody>{a}</tbody></table></section>
<section class="chapter" style="page: ra-b;{' display:none;' if BOOK else ''}"><div class="copen"><div class="cnum">Anexa B</div><h2>Registrul afirmațiilor</h2>
<p class="cdek">Fiecare cifră din raport, cu nivelul, starea și rezerva obligatorie. Nivel: A/E = observat direct, B/P = model sau scenariu, C/S = cifră preluată din sursă.</p></div>
<table class="reg-tbl claims-tbl"><thead><tr><th>ID</th><th>Afirmație</th><th>Valoare</th><th>Nivel</th><th>Stare</th><th>Rezervă</th></tr></thead><tbody>{rb}</tbody></table></section>
<section class="chapter" style="page: ra-c;{' display:none;' if BOOK else ''}"><div class="copen"><div class="cnum">Anexa C</div><h2>Metodă și reproducere</h2>
<p class="cdek">Pentru fiecare cifră publicabilă: sursa, scriptul care o produce și amprenta SHA-256 a datelor (primele 16 caractere; valoarea completă e în claims_registry.csv).</p></div>
<div class="cols">{P("Ordinea de reproducere: <code>reconcile_sources.py</code> blochează cifrele din BERC și portal; <code>generate_claims_registry.py</code> construiește registrul din ieșirile scripturilor; <code>generate_institutii_figures.py</code> desenează figurile; <code>build_raport_institutii.py</code> asamblează raportul. Verificarea: reimplementarea separată a cifrelor de nivel A, verificatorul de cifre și demonstrațiile Lean (Volumul 6).", "Date", "BERC: 4.077.510 decizii. Portal: 7.469 de numere de cerere sondate. Stocuri oficiale: Nota MJ din 30 octombrie și 6 noiembrie 2026.")}</div>
<table class="reg-tbl src-tbl"><thead><tr><th>ID</th><th>Sursă</th><th>Script</th><th>Amprentă și dată</th></tr></thead><tbody>{rc}</tbody></table>
<p class="note" style="margin-top:6mm">Declarație de interes: autorul a avut o activitate de înființare de societăți, închisă. Credit: analiză big data pe datele din BERC.</p></section>
<section class="chapter" style="page: ra-d;{' display:none;' if NOANNEX else ''}"><div class="copen"><div class="cnum">Anexa D</div><h2>{methodology.TITLE}</h2>
<p class="cdek">De unde vin datele, cum le-am prelucrat, ce înseamnă fiecare măsură, cum am verificat și ce riscuri rămân, explicate de la un capăt la altul.</p></div>
<div class="ai-annex">{methodology.body(hl)}</div></section>
<section class="chapter" style="page: ra-e;{' display:none;' if NOANNEX else ''}"><div class="copen"><div class="cnum">Anexa E</div><h2>{ai_annex.TITLE}</h2>
<p class="cdek">Transparență: ce a făcut inteligența artificială, ce a făcut autorul, ce cerințe a avut raportul, pe ce surse se bazează și ce nu se poate afla din ele.</p></div>
<div class="ai-annex">{ai_annex.body(hl)}</div></section>"""


# ================================================================== BUILD
def book_body(body):
    import book_style
    i = body.index('<section class="chapter"'); j = body.index(">", i) + 1      # banner at the top of chapter 1
    return book_refs(body[:j] + book_style.banner("main") + body[j:])


def build_html(pg):
    body = "\n".join([front(pg), ch1(), ch2(), ch3(), ch4(), ch5(), ch6(), ch7(), ch8(), ch9(), ch10(), ch11(), ch12(), annexes()])
    return f"""<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8">
<title>Coada de la Registrul Comerțului · noiembrie 2026 · Ștefan-Lucian Deleanu</title>
<link rel="stylesheet" href="fonts/fonts.css">
<style>{BASE_CSS}
{running_css()}
{EXTRA_CSS}</style></head><body>{book_body(body) if BOOK else body}</body></html>"""


def compile_pdf(html_path, pdf_path):
    if pdf_path.exists(): pdf_path.unlink()
    prof = tempfile.mkdtemp(prefix="onrc-inst-edge-")
    try:
        for _try in range(3):
            try:
                subprocess.run([str(EDGE), "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run",
                        "--disable-extensions", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                        f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
                break
            except subprocess.TimeoutExpired:
                print('Edge timeout, retrying', _try + 1)
        assert pdf_path.exists(), "Edge did not write the PDF"
    finally:
        shutil.rmtree(prof, ignore_errors=True)


MARKERS = {"synth": r"SINTEZĂ EXECUTIVĂ\s*·\s*PENTRU DECIDENȚI", "c1": r"^CAPITOLUL 1\s*$", "c2": r"^CAPITOLUL 2\s*$",
           "c3": r"^CAPITOLUL 3\s*$", "c4": r"^CAPITOLUL 4\s*$", "c5": r"^CAPITOLUL 5\s*$", "c6": r"^CAPITOLUL 6\s*$",
           "c7": r"^CAPITOLUL 7\s*$", "c8": r"^CAPITOLUL 8\s*$", "c9": r"^CAPITOLUL 9\s*$",
           "c10": r"^CAPITOLUL 10\s*$", "c11": r"^CAPITOLUL 11\s*$", "c12": r"^CAPITOLUL 12\s*$",
           "aa": r"^ANEXA A\s*$", **({} if BOOK else {"ab": r"^ANEXA B\s*$", "ac": r"^ANEXA C\s*$"}), **({} if NOANNEX else {"ad": r"^ANEXA D\s*$", "ae": r"^ANEXA E\s*$"})}

def toc_pages(pdf):
    import fitz
    d = fitz.open(str(pdf)); found = {}
    for p in range(0 if BOOK else 2, len(d)):          # book mode: no cover/TOC, chapter 1 is on page 1
        t = d[p].get_text("text").upper()
        for k, pat in MARKERS.items():
            if re.search(pat, t, re.M) and (k not in found or k.startswith("a")):   # annexes: last match (the TOC may list them)
                found[k] = str(p + 1)
    n = len(d); d.close(); return found, n


def main():
    HTML_OUT.write_text(build_html({}), encoding="utf-8"); compile_pdf(HTML_OUT, PDF_OUT)
    pg, n = toc_pages(PDF_OUT)
    HTML_OUT.write_text(build_html(pg), encoding="utf-8"); compile_pdf(HTML_OUT, PDF_OUT)
    pg2, n2 = toc_pages(PDF_OUT)
    print(f"PDF: {PDF_OUT} · {n2} pages · TOC: {pg2}")
    missing = set(MARKERS) - set(pg2) - ({"synth"} if BOOK else set())   # book mode: the synthesis opens the complete report
    if missing: print("WARNING: TOC markers not found:", missing)
    # guard: Edge silently shrinks the WHOLE document if any element overflows the page width
    import fitz, collections
    d = fitz.open(str(PDF_OUT)); sizes = collections.Counter()
    for p in d[int(pg2.get("c1", 5)) - 1:int(pg2.get("c2", 6))]:
        for blk in p.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:      # Edge embeds web fonts as anonymous Type3: use the size
                    sizes[round(sp["size"], 1)] += len(sp["text"])
    d.close()
    body = sizes.most_common(1)[0][0] if sizes else 0
    print(f"dominant text size on chapter pages: {body} pt")
    assert body >= 9.5, f"Document was shrunk to fit (body {body} pt): some element overflows the page width"


def main_exec():
    """Executive edition: the SAME cover, reading guide and synthesis as the full report."""
    fr = re.sub(r'(?s)<section class="front" style="page: rf-front;">.*?</section>', "", front({}))
    pk = fig("FIGURA 10.1", "MODEL VERIFICAT · PACHETE DE MĂSURI · IUNIE 2028",
             "Ce funcționează: pachetele care scot muncă din sistem coboară așteptarea mai mult decât proiectul OUG singur",
             "fi21_pachete.svg",
             "Așteptarea estimată în iunie 2028 pentru cinci variante: fără măsuri noi, proiectul OUG și trei pachete mai largi.",
             "Punctul e mijlocul simulărilor, bara e intervalul în care cad 8 din 10 variante. «≤3» = coada e practic goală.",
             "Cel mai mult ajută combinația dintre capacitate suplimentară și scoaterea actualizărilor CAEN simple din coadă.",
             "Nu sunt promisiuni: fiecare pachet depinde de cât de bine se implementează fiecare măsură. Pachetul cu 40% din posturile vacante: " + HIRE_40[0].lower() + HIRE_40[1:],
             ["C42", "C43", "C52", "C53", "C54", "C153"])
    note = ''
    v0 = lambda c: V(c).split(" (")[0]
    W = lambda a, b, c: (f'<p><b>Ce arată.</b> {a}</p><p><b>Pentru proiectul de OUG.</b> {b}</p><p><b>Impact.</b> {c}</p>')
    cards = [
        ("figures_institutii", "fi12_prognoza.svg", "Ce prognozăm: fără măsuri noi, așteptarea crește puternic în 2027", ["C59", "C60"], True,
         W("Câte zile ar aștepta un dosar depus în fiecare săptămână, până în iunie 2028, dacă nu se schimbă nimic. Linia e mijlocul simulărilor, banda arată 8 din 10 variante. "
           "Vârful ar ajunge la " + v0("C60") + " de zile." + E("C60"),
           "Chiar adoptat, proiectul coboară așteptarea din iunie 2028 doar la " + v0("C43") + " de zile, față de " + v0("C42") + " fără el: o îmbunătățire reală, dar termenul legal de o zi lucrătoare rămâne departe." + E("C42", "C43") +
           " Cel mai mare risc, valul de actualizări CAEN de la începutul lui 2027, nu e tratat direct de textul proiectului." + E("C68"),
           "Fiecare zi în plus cu stocul actual costă, în scenariul central, circa " + v0("C108") + " milioane de lei în economie." + E("C108"))),
        ("figures_institutii", "fi21_pachete.svg", "Ce schimbă fiecare măsură: așteptarea în iunie 2028, pe pachete", ["C54", "C52", "C153"], True,
         W("Cinci variante pentru iunie 2028: fără măsuri, proiectul de OUG și trei pachete mai largi. Punctul e mijlocul simulărilor, bara e intervalul.",
           "Proiectul singur: " + v0("C43") + " de zile; transferul unor acte administrative (Art. III) schimbă foarte puțin, efectul vine din capacitatea suplimentară." + E("C43", "C44") +
           " Conversia automată CAEN 1-la-1 și eșalonarea, fără personal nou: " + v0("C53") + " de zile." + E("C53") +
           " OUG extins plus ocuparea a 40% din posturile vacante: " + v0("C52") + " de zile, dar asta cere excepții de la suspendarea angajărilor din 2026." + E("C52", "C153") +
           " Pachetul minim realist: " + v0("C54") + " de zile." + E("C54"),
           "Concluzia pentru consultare: proiectul ar trebui completat cu conversia automată CAEN și cu excepția de la suspendarea angajărilor; altfel câștigul rămâne parțial.")),
        ("figures_institutii", "fi24_doua_cozi_schema.svg", "Cum circulă un dosar: două cozi, una după alta", ["C29", "C35"], True,
         W("Drumul unei cereri: intră în coada de operare (preluare și verificare formală), apoi în coada registratorului (decizie). Cifrele sunt stocul din fiecare coadă la 6 noiembrie, cererile noi pe zi și deciziile finale pe zi." + E("C28", "C29", "C99", "C01"),
           "Proiectul mută consilieri juridici spre soluționare (săgeata roșie). Mutarea ajută doar până la un prag; peste el, coada de operare crește la fel de repede cât scade cea a registratorului." + E("C35"),
           "Cu ambele cozi aproape egale, orice decizie de personal trebuie judecată pe tot drumul dosarului, nu pe o singură etapă." + E("C56"))),
        ("figures_institutii", "fi06_tandem.svg", "Cele două cozi: un dosar trece întâi prin operare, apoi la registrator", ["C29", "C56"], True,
         W("Stocul de cereri nesoluționate, împărțit pe cele două etape: operarea (preluarea și verificarea formală) și soluționarea (decizia registratorului). "
           "La 6 noiembrie, din " + V("C28") + " de cereri, " + V("C29") + " erau încă la operare: cele două cozi sunt aproape egale." + E("C28", "C29") +
           " În săptămâna 30 octombrie–6 noiembrie, operarea a lucrat cu circa 16–20% mai repede decât soluționarea, iar stocul de la registrator a crescut; e o singură săptămână, iar acel stoc poate cuprinde și dosare care așteaptă completarea de către solicitant." + E("C33", "C34"),
           "Proiectul mută consilieri juridici ai ONRC spre soluționare. Dacă ei sunt luați din operare, registratorii primesc mai puține dosare pregătite: "
           "întărirea doar a etapei de soluționare îi lasă pe registratori fără dosare, iar coada de la operare crește." + E("C56"),
           "Doar întărirea ambelor etape deodată reduce stocul total; o singură etapă întărită mută blocajul, nu îl elimină." + E("C56"))),
        ("figures_institutii", "fi10_canibalizare.svg", "Cât ajută mutarea oamenilor de la o coadă la alta", ["C35"], True,
         W("Câștigul de producție totală după câte dosare pe zi preiau la soluționare oamenii mutați din operare.",
           "Mutarea ajută până la un optim; peste el, ce se câștigă la registrator se pierde la operare, iar la un anumit prag câștigul dispare complet (" + V("C35") + ")." + E("C35") +
           " Concret: dacă delegarea din proiect se face luând oameni din operare, efectul are un plafon; dacă oamenii vin din alte activități ale ONRC sau din posturi noi ocupate, plafonul dispare.",
           "Recomandarea: delegați consilieri juridici din alte activități, nu din operare, și publicați câți dintre cei eligibili lucrează azi la operare; altfel nu se poate ști dacă mutarea ajută sau doar mută coada.")),
        ("figures_institutii", "fi15_grila.svg", "Cât contează viteza: intrări vs. capacitate", ["C63"], True,
         W("Așteptarea din iunie 2028 dacă cererile (rânduri) și capacitatea de soluționare (coloane) se abat de la scenariul central; stânga: cazul central, dreapta: varianta nefavorabilă.",
           "Sistemul e la limită: o capacitate cu 10% mai mare sau mai mică mută rezultatul de la circa " + V("C63").split("→ ")[1].split(" ·")[0].lstrip("≈") + " la circa " + V("C63").split("→ ")[2].split(" (")[0].lstrip("≈") + " de zile." + E("C63") +
           " Capacitatea adăugată de proiect contează doar dacă cresc ambele etape: dacă juriștii delegați sunt luați din operare, câștigul are o limită, iar întărirea unei singure etape mută blocajul." + E("C35", "C56"),
           "Mici diferențe de implementare (câți oameni, de unde sunt luați, cât de repede) schimbă rezultatul cu luni întregi.")),
        ("figures_institutii", "fi22_caen.svg", "Riscul valului CAEN și efectul conversiei automate", ["C94", "C95"], True,
         W("Așteptarea din iunie 2027 dacă firmele depun în masă actualizările CAEN înainte de sfârșitul perioadei de tranziție (roșu) și dacă codurile simple sunt convertite automat (verde).",
           "Dacă se confirmă cifrele publice, așteptarea ar putea urca la " + V("C94").split(" · ")[1].split("→ ")[1] + "–" + V("C94").split(" · ")[2].split("→ ")[1].split(" (")[0] + " de zile; conversia automată o reduce la mai puțin de jumătate." + E("C94", "C95") +
           " Perioada de tranziție se stabilește prin hotărâre de Guvern; conversia automată fără modificarea actului constitutiv cere însă o normă de rang legal, pe care o poate cuprinde chiar proiectul de OUG." + E("C152"),
           "E cea mai mare sursă de risc din prognoză și cea mai ieftină de redus.")),
        ("figures_impact", "i07_risc_venituri_2027.svg", "Venituri care nu intră în bugetul anului 2027 din cauza cozii", ["C122", "C124"], True,
         W("Pe trimestre ale anului 2027, veniturile bugetare care nu intră în bugetul anului din cauza cozii, fără măsuri (portocaliu) și cu un pachet realist (verde); liniile: intervalul de simulare de 95% (percentilele 2,5–97,5 ale variantelor simulate)." + E("C122"),
           "Proiectul de OUG costă " + V("C83") + "; " + REG["C125"]["public_ro"][0].lower() + REG["C125"]["public_ro"][1:] + E("C83", "C125"),
           "Reperul e o coadă normală, de 3 zile; cifra presupune deja că o parte se recuperează în același an. " + REG["C123"]["public_ro"] + E("C122", "C123"))),
        ("figures_impact", "i01_cost_lunar.svg", "Costul lunar al întârzierilor", ["C111", "C106"], True,
         W("Costul economic (sus) și încasările bugetare afectate (jos), lună de lună din 2024, în scenariul central; liniile verticale dau intervalul scenariilor.",
           "Proiectul de OUG costă cât circa două zile de coadă în economie; cifra zilnică nu se înmulțește însă cu numărul de zile, iar proiectul singur scurtează coada, nu o elimină: comparația dă doar un ordin de mărime." + E("C108", "C83", "C43"),
           "Pentru august–18 noiembrie 2026, costul economic e estimat la " + V("C106") + " de milioane de lei (prudent / central / tensionat)." + E("C106"))),
        ("figures_impact", "i08_motive_amanare.svg", "De ce se amână dosarele și ce se poate automatiza", ["C139", "C143"], True,
         W("Motivele amânărilor din 19 octombrie–18 noiembrie 2026, după nivelul de automatizare al soluției (standard, AI, AI avansat, judecata registratorului). Circa una din cinci decizii este o amânare." + E("C82"),
           "Proiectul nu tratează amânările. Verificările la depunere țin de ONRC, cu sprijinul ADR; o parte nu cer o lege nouă, dar cele care interoghează alte registre cer protocoale, Platforma națională de interoperabilitate și o evaluare de impact privind protecția datelor. Nu vedem sistemele interne ONRC: unele verificări pot exista deja." + E("C142", "C143"),
           "Cel mult circa " + V("C141").split(" (")[0].replace("≈", "") + " de amânări pe zi lucrătoare ar dispărea, iar analiza registratorilor s-ar muta spre dosarele noi." + E("C141"))),
        ("figures_impact", "i10_motive_respingere.svg", "Respingerile vin aproape toate din amânări nerezolvate", ["C144", "C150"], True,
         W("Ce a precedat respingerile și cum se încheie cererile amânate.",
           "Dintre cererile amânate, circa o treime ajung respinse; prevenirea amânărilor la depunere reduce deci și respingerile." + E("C146"),
           "O respingere aduce de obicei o nouă cerere: după o respingere, aproape jumătate din firme depun din nou în 30 de zile, deci aceeași muncă se face de două ori." + E("C103")))]
    def card(d, svg, title, ids, wide, intro=""):
        LS.FIG_DIR = str(HERE / d)
        take = REG[ids[0]]["public_ro"]
        return (f'<div class="ec{" wide" if wide else ""}"><div class="ect">{title}</div><div class="eci">{intro}</div>{LS.load_inline_svg(svg, svg.split(".")[0] + "_ex")}'
                f'<div class="ecc">{hl(take)}{E(*ids)}</div></div>')
    grid = "".join(card(*c) for c in cards)
    LS.FIG_DIR = str(HERE / "figures_institutii")
    charts = ('<style>.eg{display:grid;grid-template-columns:1fr 1fr;gap:5mm 6mm}.ec{break-inside:avoid}.ec.wide{grid-column:1 / -1}.ec.wide .ect{font-size:13pt}.ec.wide .ecc{font-size:11pt}.eci{font:400 10.2pt/1.45 var(--serif);margin:0 0 2mm}.eci p{margin:0 0 1.2mm}.eci b{font-family:var(--sans);font-weight:600}.ec{break-inside:auto}.ec svg{break-inside:avoid;max-height:82mm;display:block;margin:0 auto}.ec .eci{break-after:avoid}'
              '.ec svg{width:100%;height:auto}.ect{font:600 10.5pt/1.25 var(--sans);margin:0 0 1.5mm;border-top:.6mm solid var(--ink);padding-top:1.5mm}'
              '.ecc{font:400 9.6pt/1.42 var(--serif);margin-top:1mm}</style>'
              '<section class="front" style="page: rf-synth; break-before: auto; margin-top: 8mm;">' + GLOSS + '<div class="eyebrow" style="margin-top:5mm">Datele esențiale</div>'
              '<h2>Ce urmează și ce schimbă fiecare măsură</h2><div class="eg">' + grid + '</div></section>')
    annex = (f'<section class="front" style="page: rf-synth; break-before: auto;"><p class="note"><b>Despre acest document.</b> {ai_annex.DISCLAIMER} '
             'Metoda, toate figurile, limitele și registrul fiecărei cifre se află în raportul complet (Raport_ONRC_Coada_2026-11_COMPLET.pdf) și pe GitHub: '
             'github.com/Stefatorus/onrc-analiza-big-data-amanari.</p></section>')
    html_ = build_html({}).split("<body>")[0] + f"<body>{fr}{charts}{note}{annex}</body></html>"
    out_html = HERE / "Raport_ONRC_Coada_2026-11_EXECUTIV.html"
    out_pdf = DELIV / "Raport_ONRC_Coada_2026-11_EXECUTIV.pdf"
    out_html.write_text(html_, encoding="utf-8"); compile_pdf(out_html, out_pdf)
    import fitz
    n = len(fitz.open(str(out_pdf))); print(f"EXECUTIVE PDF: {out_pdf} · {n} pages")


if __name__ == "__main__":
    import sys
    if "--exec" in sys.argv:
        main_exec()
    else:
        main()
