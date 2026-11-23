"""Secțiunea 6.4 «Analiza amânărilor: de ce se amână dosarele și ce se poate automatiza» pentru
capitolul 6 din build_raport_institutii.py, plus 2–3 puncte pentru fișele pe profil (Volumul 0).

    import postponement_section as PSEC
    b += PSEC.section_html(V, E, hl, P, fig)              # în ch6(), înainte de b += concl(...)
    PSEC.short_items(V, E, hl, "it")  /  PSEC.short_items(V, E, hl, "onrc")

Fiecare cifră vine din registru prin V('Cxx') și e citată cu E('Cxx'). Id-urile se citesc din
independent_audit/out/postponement_solutions.json (claim_ids), aceleași pe care le inserează
independent_audit/delay_reasons/patch_claims.py. Figura i08 trebuie să existe în figures_institutii/
(o copiază generate_postponement_figures.py).

Probă independentă (fără builder):
    ..\\..\\venv\\Scripts\\python -X utf8 postponement_section.py <claims_registry.csv> <out.html>
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PS = json.loads((HERE.parent.parent / "independent_audit" / "out" / "postponement_solutions.json").read_text(encoding="utf-8"))
ID = PS["claim_ids"]
ROWS = PS["matrix"]                      # sorted by share, descending

NAME = {"CAEN": "Obiect de activitate, coduri CAEN, declarația de autorizare", "SEDIU": "Sediu: dovada folosinței, valabilitate, acorduri, adresă",
        "CERERE": "Cererea de înregistrare și anexa fiscală", "ACT": "Act constitutiv, hotărâri, mandatul administratorului",
        "SOLICITANT": "Solicitant: identitate, împuternicire", "ASOC_ID": "Datele de identificare ale asociaților",
        "INSTIT": "Avize ale altor instituții (cazier fiscal, ANAF, autorizații)", "CAPITAL": "Capital social: dovada vărsării, structură",
        "SEMN": "Semnătura și forma actelor", "BEN_REAL": "Declarația de beneficiar real", "DENUM": "Denumirea", "TARIF": "Tariful de publicare"}
SOL = {"CAEN": "Coduri alese numai din CAEN Rev.3, fără text liber; declarația de autorizare generată din codurile alese; limita pentru PFA verificată. AI doar ca sugestie de cod din descrierea activității.",
       "SEDIU": "Data de expirare a dovezii verificată la depunere; adresa din nomenclatorul stradal, aceeași în toate actele; acordul vecinilor cerut automat pentru locuințe.",
       "CERERE": "Formular structurat cu câmpuri obligatorii și regulile anexei fiscale aplicate direct; avertisment dacă există altă cerere în curs.",
       "ACT": "Listă de acte pe tipul cererii și starea firmei verificată automat; un asistent AI compară actul actualizat cu hotărârea și semnalează neconcordanțele registratorului.",
       "SOLICITANT": "Semnatarul comparat cu rolurile din registru; împuternicirea cerută automat când lipsește calitatea; calitatea de avocat verificată în registrul profesiei.",
       "ASOC_ID": "Date precompletate din registru și din evidența persoanelor; diferențele arătate la depunere.",
       "INSTIT": "Cazierul fiscal și atestarea fiscală interogate la ANAF înainte de depunere; nu înlătură impedimentul, îl arată mai devreme.",
       "CAPITAL": "Dovada vărsării obligatorie și calcule automate ale părților sociale și ale structurii după majorare.",
       "SEMN": "Validarea automată a semnăturii electronice calificate la încărcare.",
       "BEN_REAL": "Declarația cerută automat când se schimbă asociații; beneficiarul trebuie să fie persoană fizică.",
       "DENUM": "Validator de denumire la rezervare (de ex. PFA cu numele titularului).",
       "TARIF": "Tariful de publicare calculat automat din textul încărcat."}
LEGAL_EXTRA = {"CERERE": "Dir. 2017/1132, art. 13h", "SEDIU": "Legea 242/2022, art. 11", "SOLICITANT": "Legea 242/2022, art. 11; Dir. 2017/1132, art. 13g",
               "ASOC_ID": "Legea 242/2022, art. 11; Dir. 2017/1132, art. 13g", "INSTIT": "Legea 242/2022, art. 11 și art. 17", "SEMN": "eIDAS",
               "BEN_REAL": "Legea 129/2019"}


def legal_cell(r):
    lv = r["levels_involved"]; ai = "Doar cu AI" in lv; aip = "Doar cu AI avansat" in lv
    parts = ["GDPR art. 6 și art. 25" + ("; art. 22 și art. 35" if ai or aip else "")]
    if ai or aip:
        parts.append("AI Act art. 4" + (", art. 6 alin. (3)" if aip else ""))
    if r["code"] in LEGAL_EXTRA:
        parts.append(LEGAL_EXTRA[r["code"]])
    if aip or "Nu se poate automatiza" in lv:
        parts.append("decizia: Legea 265/2022, art. 28")
    return "; ".join(parts)


LVL_CSS = {"Standard": "lv-s", "Doar cu AI": "lv-ai", "Doar cu AI avansat": "lv-aip", "Nu se poate automatiza": "lv-j"}

CSS = """<style>
.amn-tbl { table-layout: fixed; width: 100%; border-collapse: collapse; font: 400 6.3pt/1.28 var(--sans); }
.amn-tbl th { text-align: left; font: 600 5.4pt var(--mono); text-transform: uppercase; color: var(--ink-2); border-bottom: .35mm solid var(--ink); padding: .6mm .8mm; }
.amn-tbl td { border-bottom: .2mm solid var(--rule-2); padding: .55mm .8mm; vertical-align: top; }
.amn-tbl td:nth-child(7) { font-size: 5.8pt; color: var(--ink-2); }
.amn-tbl td, .amn-tbl th { overflow-wrap: normal; word-break: normal; hyphens: manual; }
.amn-tbl th:nth-child(1) { width: 24mm; } .amn-tbl th:nth-child(2) { width: 13mm; } .amn-tbl th:nth-child(4) { width: 19mm; }
.amn-tbl th:nth-child(5) { width: 16mm; } .amn-tbl th:nth-child(6) { width: 15mm; } .amn-tbl th:nth-child(7) { width: 28mm; }
.amn-tbl .amn-sec { font: 400 5.7pt/1.25 var(--sans); color: var(--ink-2); }
.amn-tbl .lv { font-weight: 600; } .amn-tbl .lv-s { color: #16665C; } .amn-tbl .lv-ai { color: #B86E14; } .amn-tbl .lv-aip { color: #14324D; } .amn-tbl .lv-j { color: #A63228; }
.amn-tbl tr { break-inside: avoid; }
</style>"""


def _first(v):            # "31,7% (IC 95%: 30,0–33,4%)" -> "31,7%"
    return v.split(" (")[0]


def _parts(V):
    cov = V(ID["coverage"]); n = cov.split(" (")[0]; sh = cov.split("(")[1].split(" din")[0]
    av = V(ID["avoidable"]).split(" · "); strict, anyp = _first(av[0]), _first(av[1])
    cap = V(ID["capacity"]).split(" · "); cap_s = cap[0].split(" (")[0].lstrip("≈"); cap_a = cap[1].split(" cu")[0].lstrip("≈")
    lv = V(ID["levels"]); counts = lv.split(" din")[0].split(" / "); N = lv.split(" din ")[1].split(" ·")[0]
    n_j = lv.split("rămâne în ")[1].split(" din")[0]
    val = V(ID["validation"]).split(" · "); any_ok = val[1].split(" cel")[0]
    pc = {c: _first(V(ID[c])) for c in NAME}
    return dict(n=n, sh=sh, strict=strict, anyp=anyp, cap_s=cap_s, cap_a=cap_a, n_std=counts[0], N=N, n_j=n_j, any_ok=any_ok, pc=pc)


def table_html(V, E):
    head = "".join(f"<th>{h}</th>" for h in ("Motiv", "Pondere", "Soluție (de verificat dacă nu există deja)", "Nivel de automatizare", "Complexitate", "Unde acționează", "Cadrul legal"))
    body = ""
    for r in ROWS:
        c, lvl = r["code"], r["headline"]
        sec = [l for l in r["levels_involved"] if l != lvl]
        lvtxt = f'<span class="lv {LVL_CSS[lvl]}">{lvl}</span>' + (f'<br><span class="amn-sec">și: {", ".join(sec)}</span>' if sec else "")
        body += (f"<tr><td>{NAME[c]}</td><td>{_first(V(ID[c]))}<br>{E(ID[c]).strip()}</td><td>{SOL[c]}</td><td>{lvtxt}</td><td>{r['complexity']}</td>"
                 f"<td>{', '.join(r['where'])}</td><td>{legal_cell(r)}{E(ID['legal'])}</td></tr>")
    return (CSS + '<div class="tbl-wrap"><div class="tbl-head"><span class="tnum">Tabelul 6.1</span> Motivele de amânare și ce se poate face pentru fiecare</div>'
            f'<table class="amn-tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
            '<p class="note">Pondere = partea din amânări care invocă motivul; o amânare poate avea mai multe motive, deci ponderile nu se adună. '
            'Estimări dintr-o clasificare automată verificată pe un eșantion.' + E(ID["validation"]) + ' Nivelul e cel al soluției principale; „și:” arată soluțiile secundare. '
            'Standard = reguli fixe, fără AI; „Nu se poate automatiza” = judecata registratorului. '
            '<b>Tabelul acoperă și respingerile:</b> ele reiau, aproape mereu, cauzele unei amânări neîndeplinite (secțiunea 6.5).' + E("C144", "C149") + '</p></div>')


def section_html(V, E, hl, P, fig):
    p = _parts(V); pc = p["pc"]; C = ID
    b = '<h3>6.4 Analiza amânărilor: de ce se amână dosarele și ce se poate automatiza</h3>'
    b += P("În versiunile anterioare ale raportului am scris că motivele amânărilor nu sunt disponibile. Ele se pot citi totuși: fiecare încheiere de amânare publicată în buletin are un câmp „Motivul amânării”, iar legea cere ca motivele să fie afișate (Legea 265/2022, art. 106 alin. (2)). " +
           hl("Am citit motivul pentru " + p["n"] + " de amânări din 19 octombrie–18 noiembrie 2026, adică " + p["sh"] + " din amânările din această perioadă.") + E(C["coverage"]) +
           " Oficiile și tipurile de firme sunt reprezentate ca în arhivă. Concluziile privesc doar această fereastră.",
           "Cum am măsurat", "Am extras textul din buletinele PDF, am șters datele personale și am grupat motivele în douăsprezece categorii. Pe un eșantion verificat separat, clasificarea a găsit cel puțin un motiv corect în " + p["any_ok"] + " din cazuri; setul complet e mai rar corect." + E(C["validation"]))
    b += P(hl("Cele mai dese motive sunt obiectul de activitate și codurile CAEN (" + pc["CAEN"] + " din amânări), sediul (" + pc["SEDIU"] + "), cererea și anexa fiscală (" + pc["CERERE"] + ") și actul constitutiv cu hotărârile (" + pc["ACT"] + ").") +
           E(C["CAEN"], C["SEDIU"], C["CERERE"], C["ACT"]) + " O amânare poate avea mai multe motive, de aceea procentele nu se adună. Urmează identitatea solicitantului și împuternicirea, datele asociaților, avizele altor instituții și capitalul social.",
           "Rezervă", "Ponderile sunt estimări ale unei clasificări automate. Categoria „cererea” e supra-estimată, pentru că multe texte pomenesc cererea doar ca mijloc de corectură; registrul dă și valoarea ajustată." + E(C["CERERE"]))
    b += fig("FIGURA 6.2", "MOTIVELE AMÂNĂRILOR · 19.10–18.11.2026", "Ce lipsește cel mai des la depunere și ce fel de soluție are fiecare motiv",
             "i08_motive_amanare.svg",
             "Pentru fiecare motiv, partea din amânări care îl invocă; culoarea arată nivelul de automatizare al soluției principale.",
             "Bara e ponderea, linia neagră e intervalul de încredere. În dreapta: pătrat plin = soluția principală, pătrat gol = soluții secundare (S = standard, AI, AI+ = AI avansat, J = judecata registratorului).",
             "Pentru aproape toate motivele, soluția principală este o verificare la depunere fără inteligență artificială. Partea care dispare cu adevărat e mai mică: vezi paragraful următor.",
             "Culoarea verde nu înseamnă că toată bara dispare: la CAEN, sediu, capital și alte instituții, o parte cere judecata registratorului, iar barele nu se adună. Nu spune nici că amânările sunt nejustificate: lipsurile sunt reale, doar că sunt găsite târziu.",
             [C["CAEN"], C["SEDIU"], C["CERERE"], C["ACT"], C["levels"], C["avoidable"]])
    b += P(hl("Circa una din cinci amânări (" + p["strict"] + ") avea numai motive pe care o verificare la depunere le-ar fi prins; în aproape jumătate (" + p["anyp"] + "), cel puțin un motiv era de acest fel.") + E(C["avoidable"]) +
           " Registrul dă circa " + V("C03").lstrip("≈") + " de amânări pe zi lucrătoare." + E("C03") + " " +
           hl("Verificările la depunere ar scoate deci cel mult circa " + p["cap_s"] + " de amânări pe zi, iar în circa " + p["cap_a"] + " de amânări pe zi ar rămâne cel puțin un motiv mai puțin.") + E(C["capacity"]) +
           " Fiecare amânare evitată scutește firma de un termen de completare (după completare, decizia vine în circa " + V("C37").split(" / ")[1].split(",")[0] + " zile) și pe registrator de o a doua analiză a aceluiași dosar." + E("C37"),
           "Ce NU înseamnă", "Nu sunt decizii finale în plus: o amânare evitată scoate o decizie de amânare, nu adaugă o admitere. Cifrele sunt un plafon, pentru că presupun că verificarea prinde tot ce e evitabil. Soluțiile pentru motivele doar parțial evitabile (CAEN, sediu, act constitutiv) ar adăuga la efect, dar efectul lor nu se poate măsura din date." + E(C["capacity"]), key=True)
    b += table_html(V, E)
    b += P(hl("Pentru " + p["n_std"] + " din cele " + p["N"] + " motive, soluția principală este o verificare la depunere fără inteligență artificială: câmpuri obligatorii, calcule, nomenclatoare și interogarea altor registre.") + E(C["levels"]) +
           " Doar concordanța dintre actul constitutiv actualizat și hotărâre cere un model AI avansat, care semnalează neconcordanțele, fără să decidă. Citirea actelor scanate și sugerarea codului CAEN se pot face cu AI obișnuit, tot ca ajutor. " +
           hl("În " + p["n_j"] + " motive, o parte rămâne oricum la judecata registratorului: ce activitate e permisă, ce titlu de sediu e valabil, ce efect are o faptă din cazierul fiscal.") + E(C["levels"]),
           "Dacă nu există deja", "Nu vedem sistemele interne ale ONRC. O parte din aceste verificări poate exista deja; tabelul e o listă de verificat, nu o constatare. Interogarea altor registre depinde de Platforma națională de interoperabilitate (Legea 242/2022).")
    b += P(hl("Decizia rămâne la registrator: legea îi dă lui soluționarea cererii, prin încheiere, iar o decizie luată numai de un program ar avea nevoie de o autorizare expresă în lege.") + E(C["legal"]) +
           " După evaluarea noastră, regulamentul european privind inteligența artificială nu trece înregistrarea firmelor printre utilizările cu risc ridicat; oricum, obligațiile pentru risc ridicat s-ar aplica abia din decembrie 2027, după amânarea adoptată în iulie 2026. "
           "Se aplică însă deja instruirea personalului care folosește AI și informarea celor care vorbesc cu un asistent AI pe portal. Citirea automată a actelor de identitate cere și o evaluare de impact privind protecția datelor." + E(C["legal"]),
           "Rezervă", "Încadrarea juridică este interpretarea noastră, nu un aviz; trimiterile exacte la articole sunt în anexa tehnică a analizei amânărilor." + E(C["legal"]))
    b += P("Ce ar ajuta imediat: un cod pentru fiecare motiv de amânare, publicat în încheiere. În buletinul public, motivul apare ca text liber; nu știm dacă sistemul intern al ONRC are deja o clasificare. " +
           hl("Cu un cod de motiv publicat, ONRC ar putea raporta lunar ce lipsește la depunere și ar ști ce verificare să construiască întâi, dintre cele care nu există deja."))
    return b


def short_items(V, E, hl, profile="it"):
    p = _parts(V); pc = p["pc"]; C = ID
    if profile == "it":
        return [hl("Circa una din cinci amânări (" + p["strict"] + ") avea numai lipsuri pe care o verificare automată la depunere le-ar fi prins.") + E(C["avoidable"]),
                hl("Pentru " + p["n_std"] + " din " + p["N"] + " motive de amânare ajung reguli fixe, fără AI; doar concordanța actelor cere un model AI avansat, ca ajutor pentru registrator.") + E(C["levels"], C["legal"]),
                hl("De construit întâi: codurile CAEN Rev.3 cu declarația de autorizare (motiv în " + pc["CAEN"] + " din amânări) și verificarea dovezii de sediu (" + pc["SEDIU"] + ").") + E(C["CAEN"], C["SEDIU"])]
    return [hl("Cele mai dese motive de amânare: CAEN (" + pc["CAEN"] + "), sediul (" + pc["SEDIU"] + "), cererea și anexa fiscală (" + pc["CERERE"] + ").") + E(C["CAEN"], C["SEDIU"], C["CERERE"]),
            hl("Verificările la depunere ar scoate cel mult circa " + p["cap_s"] + " de amânări pe zi lucrătoare, din circa " + V("C03").lstrip("≈") + ".") + E(C["capacity"], "C03"),
            hl("Decizia rămâne la registrator; un program poate doar pregăti și semnala lipsurile.") + E(C["legal"])]


# ------------------------------------------------------------------ standalone proof (no builder needed)
if __name__ == "__main__":
    import csv, sys
    import lab_styles as LS
    from lab_styles import BASE_CSS, hl as _hl, prose
    reg_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    REG = {r["id"]: r for r in csv.DictReader(open(reg_path, encoding="utf-8"))}
    LS.FIG_DIR = str(HERE / "figures_institutii")

    def _V(cid):
        r = REG[cid]; assert r["status"] in ("PASS", "WARN"), cid
        return r["value"]

    def _E(*ids):
        for i in ids: assert REG[i]["status"] in ("PASS", "WARN"), i
        return " " + " ".join(f'<span class="eid">[{i}]</span>' for i in ids)

    def _P(body, mt="", mh="", key=False): return prose(body, mt, mh, key_flag=key)

    def _fig(fnum, tag, title, svg, arata, citeste, inseamna, nu, ids):
        return ('<figure class="chart">' f'<div class="fnum"><span>{fnum}</span><span>{tag}</span></div>'
                f'<div class="ftitle">{title}</div>{LS.load_inline_svg(svg, svg.split(".")[0])}<dl class="decode">'
                f'<dt>Ce arată</dt><dd>{arata}</dd><dt>Cum se citește</dt><dd>{citeste}</dd><dt>Ce înseamnă</dt><dd>{inseamna}</dd><dt>Ce NU înseamnă</dt><dd>{nu}</dd></dl>'
                f'<p class="fsrc"><b>Sursă și verificare.</b>{_E(*ids)}</p></figure>')
    body = section_html(_V, _E, _hl, _P, _fig)
    sheets = "".join(f"<h4>Fișa {k}</h4><ul>" + "".join(f"<li>{x}</li>" for x in short_items(_V, _E, _hl, k)) + "</ul>" for k in ("it", "onrc"))
    out.write_text(f'<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8"><title>Probă 6.4</title><link rel="stylesheet" href="{(HERE / "fonts" / "fonts.css").as_uri()}">'
                   f'<style>{BASE_CSS}</style></head><body><section class="chapter"><div class="cols">{body}{sheets}</div></section></body></html>', encoding="utf-8")
    print("wrote", out)
