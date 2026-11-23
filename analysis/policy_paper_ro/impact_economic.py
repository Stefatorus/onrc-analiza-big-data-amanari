"""Volumul 7 · Impactul economic și bugetar al cozii (Partea 3 în raportul complet).

Trei niveluri, de la sigur la incert: (1) podeaua măsurată, doar date și dobânzi oficiale; (2) scenariul fundamentat,
cu fiecare parametru care are o bază în date (bilanțuri MF, Eurostat, buletine PDF, cote legale) citit din
cost_evidence.json; (3) analiza inițială, ca test de sensibilitate. Opțional: estimarea econometrică și venitul bugetar
la risc pentru 2027 (independent_audit/out/econometrics.json), dacă există. Toate cifrele din text vin din registrul
afirmațiilor (C104–C118 și următoarele); tabelele citesc direct ieșirile verificate.
"""
import json
import pandas as pd
import build_volume_stat as BV
from build_volume_stat import V, E, hl, sec, sub, P, cover, toc, IA, REG
import re
ORI = re.search(r"de circa (\S+) ori", REG["C111"]["public_ro"]).group(1)      # Oct 2026 vs a normal month (C111)
NFOUND = V("C116").split(" · ")[1].split(" parametri")[0]                      # e.g. «10 din 18» (C116)
PR = lambda c: REG[c]["public_ro"]
C112_C = "În canalul C" + REG["C112"]["rezerva_obligatorie"].split("În canalul C", 1)[1]     # channel-C stock factor, from the registry
DROP = re.search(r"cu circa (\d+)%", REG["C116"]["public_ro"]).group(1)          # founded vs initial central (C116)

KF = json.loads((IA / "out" / "cost_founded.json").read_text(encoding="utf-8"))
KC = json.loads((IA / "out" / "cost_check.json").read_text(encoding="utf-8"))
KM = json.loads((IA / "out" / "cost_monthly.json").read_text(encoding="utf-8"))
EC_F = IA / "out" / "econometrics.json"
SC = KF["scenarios"]["fundamentat"]; SC0 = KF["scenarios"]["initial"]
_W = {1: "o zi", 2: "două zile", 3: "trei zile", 4: "patru zile", 5: "cinci zile", 6: "șase zile", 7: "șapte zile", 8: "opt zile", 9: "nouă zile", 10: "zece zile"}
_days = lambda x: _W.get(int(x + .5), f"{int(x + .5)} de zile")
# how many days of queue (central, one more day with the stock) equal the whole OUG budget (C83, C108); computed, never typed
OUG_D_ECON = _days(KC["oug_budget_mil_lei"] * 1e6 / SC["central"]["daily_econ"])
OUG_D_TAX = _days(KC["oug_budget_mil_lei"] * 1e6 / SC["central"]["daily_tax"])
_SPREAD = SC["tensionat"]["total"] / SC["prudent"]["total"]                   # stressed / prudent (C106)
SPREAD_TXT = f"un factor de peste {int(_SPREAD // 5 * 5)}" if _SPREAD >= 10 else f"un factor de circa {int(_SPREAD + .5)}"
_PPS = next(x for x in KF["params"] if x["parametru"] == "preventable_post_share")
PPS_TXT = " / ".join(f"{100 * v:.1f}".replace(".", ",") for v in _PPS["fundamentat"]) + "%"

PNAME = {"pending": "Stocul de referință (cereri)", "pending_new_j_share": "Ponderea înmatriculărilor în stoc",
         "pending_new_excess_days": "Zile de așteptare rămase, înmatriculări", "pending_changes_excess_days": "Zile de așteptare rămase, mențiuni",
         "net_turnover_per_day": "Vânzări pe zi ale unei firme noi (lei)", "lost_turnover_fraction": "Partea de vânzări pierdută definitiv",
         "tax_share": "Cota fiscală efectivă pe vânzările pierdute", "value_added_share": "Ponderea valorii adăugate în vânzări",
         "seat_share": "Ponderea dosarelor de sediu", "inactivation_increment": "Probabilitatea în plus de inactivare fiscală",
         "seat_private_cost": "Cost privat pe inactivare (lei)", "seat_fiscal_cost": "Încasări afectate pe inactivare (lei)",
         "disjoint_blocked_changes_share": "Ponderea modificărilor cu impact separat", "blocked_change_cost": "Cost pe zi al unei modificări blocate (lei)",
         "blocked_change_tax_share": "Cota fiscală pe acest cost", "preventable_post_share": "Amânări evitabile",
         "private_cost_per_post": "Cost privat pe amânare (lei)", "admin_cost_per_post": "Cost public pe amânare (lei)"}
CH = [("A", "Activitate nouă pierdută (firme noi)"), ("B", "Inactivare fiscală după expirarea sediului"), ("C", "Alte modificări blocate"), ("D", "Amânări evitabile")]
real = KM["window_realized_mil"]
fmtv = lambda v: f"{v:.3f}".rstrip("0").rstrip(".").replace(".", ",") if v < 1 else f"{v:,.0f}".replace(",", ".")
TABLES = {
    "cost_scenarii": dict(columns=["scenario", "cost_economic_mil", "din_care_realizat_mil", "expunere_stoc_mil", "buget_mil", "pe_zi_economic_mil", "pe_zi_buget_mil"],
        rows=[dict(scenario=s, cost_economic_mil=SC[s]["total"] / 1e6, din_care_realizat_mil=real[s], expunere_stoc_mil=SC[s]["total"] / 1e6 - real[s],
                   buget_mil=SC[s]["tax"] / 1e6, pe_zi_economic_mil=SC[s]["daily_econ"] / 1e6, pe_zi_buget_mil=SC[s]["daily_tax"] / 1e6) for s in ("prudent", "central", "tensionat")],
        meta="Scenariul fundamentat. Fereastra: decizii 1.08–18.11.2026, plus expunerea condiționată a stocului de referință. „Pe zi” = încă o zi cu stocul de referință; nu se înmulțește cu numărul de zile.", src="cost_founded.json"),
    "cost_canale_tab": dict(columns=["canal", "prudent", "central", "tensionat", "pondere_centrala_pct"],
        rows=[dict(canal=f"{k} · {n}", prudent=SC["prudent"]["channels"][k] / 1e6, central=SC["central"]["channels"][k] / 1e6, tensionat=SC["tensionat"]["channels"][k] / 1e6,
                   pondere_centrala_pct=100 * SC["central"]["channels_share"][k]) for k, n in CH],
        meta="Milioane lei, scenariul fundamentat. Canalele sunt disjuncte; costul public al amânărilor e separat.", src="cost_founded.json"),
    "cost_ipoteze": dict(columns=["parametru", "initial", "fundamentat", "stare", "sursa"],
        rows=[dict(parametru=PNAME.get(r["parametru"], r["parametru"]), initial=" / ".join(fmtv(v) for v in r["initial"]),
                   fundamentat=" / ".join(fmtv(v) for v in r["fundamentat"]), stare=r["stare"], sursa=r["sursa"]) for r in KF["params"]],
        meta="Valorile prudent / central / tensionat (cote ca fracții), în analiza inițială și în scenariul fundamentat, cu starea și sursa fiecăreia.", src="cost_founded.json"),
    "cost_ancora": dict(columns=["cohorta", "exercitiu", "firme_noi_berc", "cu_bilant", "potrivire_pct", "mediana_lei", "medie_plafonata_lei", "medie_zilnica_lei"],
        rows=[dict(cohorta=str(r["cohort_year"]), exercitiu=str(r["financial_year"]), firme_noi_berc=r["onrc_n"], cu_bilant=r["matched_n"],
                   potrivire_pct=100 * r["matched_n"] / r["onrc_n"], mediana_lei=r["median_turnover"], medie_plafonata_lei=r["mean_all_cap_at_positive_p99"],
                   medie_zilnica_lei=r["mean_daily_at_least_180d_capped_p99"]) for r in KC["formation"]],
        meta="Înmatriculări admise (tip J) din BERC, potrivite după codul fiscal cu situațiile financiare depuse la Ministerul Finanțelor.", src="formation_turnover.csv"),
    "cost_substitutie": dict(columns=["regim", "central_mil", "prudent_mil", "tensionat_mil"], rows=KF["substitution"],
        meta="Cost net (economic și privat, plus costul public al amânărilor), dacă o parte din activitatea pierdută (A) e preluată de alte firme și o parte din costul modificărilor blocate (C) e recuperată. Scenariul fundamentat.", src="cost_founded.json"),
    "cost_verificare": dict(columns=["verificare", "rezultat"],
        rows=[dict(verificare="Reimplementare independentă a celor patru canale, pe intrările publicate", rezultat="reproduce toate cele trei scenarii ale analizei inițiale, la leu"),
              dict(verificare="Renumărarea intrărilor măsurate pe arhiva BERC curentă", rezultat="intrări cu până la circa 4% mai mari (decizii publicate ulterior); totaluri cu sub 1% mai mari"),
              dict(verificare="Suma lunară pe fereastră = partea realizată a contului", rezultat="identică (verificare automată)"),
              dict(verificare="Parametri cu bază în date sau surse oficiale", rezultat=f"{KF['n_founded']} din {KF['n_params']}; restul sunt ipoteze declarate"),
              dict(verificare="Ponderea valorii adăugate (inițial 45%)", rezultat="Eurostat: circa 28–30%; folosită în scenariul fundamentat"),
              dict(verificare="Ponderea modificărilor care pot bloca activitatea", rezultat="plafon măsurat în buletinele PDF: circa 15–22% din zilele în exces"),
              dict(verificare="Ponderea amânărilor evitabile la depunere (inițial 8 / 15 / 25%)", rezultat="măsurată în buletinele PDF, motivele amânărilor 19.10–18.11.2026: " + PPS_TXT + " (prudent: limita inferioară a ponderii stricte; central: ponderea strictă, toate motivele evitabile; tensionat: plafonul, cel puțin un motiv evitabil)")],
        meta="Verificare făcută pe 22.11.2026.", src="cost_founded.json"),
}
for k in ("cost_lunar", "cost_anual", "cost_lunar_canale"):
    TABLES[k] = dict(KM[k], src="cost_monthly.json")
BV.SP.update(TABLES)
BV.LABELS.update({"cost_economic_mil": "Cost economic (mil. lei)", "din_care_realizat_mil": "din care realizat", "expunere_stoc_mil": "expunerea stocului",
                  "buget_mil": "Buget afectat (mil. lei)", "pe_zi_economic_mil": "O zi în plus: economic", "pe_zi_buget_mil": "O zi în plus: buget",
                  "canal": "Canal", "pondere_centrala_pct": "% din central", "prudent": "Prudent", "central": "Central", "tensionat": "Tensionat",
                  "initial": "Inițial", "fundamentat": "Fundamentat", "stare": "Stare", "sursa": "Sursa", "parametru": "Parametru",
                  "cohorta": "Cohorta", "exercitiu": "Exercițiu", "firme_noi_berc": "Firme noi (BERC)", "cu_bilant": "Cu bilanț", "potrivire_pct": "Potrivire %",
                  "mediana_lei": "Mediană (lei)", "medie_plafonata_lei": "Medie plafonată (lei)", "medie_zilnica_lei": "Medie pe zi (lei)",
                  "regim": "Ce se recuperează", "central_mil": "Central (mil. lei)", "prudent_mil": "Prudent (mil. lei)", "tensionat_mil": "Tensionat (mil. lei)",
                  "rezultat": "Rezultat", "zile_exces_inmatriculari": "Zile în exces, înmatriculări", "zile_exces_mentiuni": "Zile în exces, mențiuni",
                  "economic_prudent_mil": "Economic, prudent", "economic_central_mil": "Economic, central", "economic_tensionat_mil": "Economic, tensionat",
                  "buget_prudent_mil": "Buget, prudent", "buget_central_mil": "Buget, central", "buget_tensionat_mil": "Buget, tensionat",
                  "canal_A_mil": "A · firme noi", "canal_B_mil": "B · sediu", "canal_C_mil": "C · alte modificări", "canal_D_mil": "D · amânări", "an": "An"})
BV.TEXT_COLS.update({"canal", "parametru", "sursa", "stare", "initial", "fundamentat", "cohorta", "exercitiu", "regim", "rezultat", "verificare", "an"})


def econometrics_section(n):
    """Causal estimate (natural experiment) and 2027 budget revenue at risk; claims C119–C125."""
    if not EC_F.exists() or "C125" not in REG:
        return ""
    fig = lambda svg, cap, ids: BV.fig(svg, cap, ids, fdir="figures_impact")
    return (sec(n, "Estimarea econometrică și riscul pentru veniturile din 2027") + P(
        "Întrebarea pentru buget este dacă așteptarea doar amână activitatea și taxele firmelor noi sau le reduce definitiv. Am folosit un experiment natural (ipoteza de identificare, explicată la final: aglomerarea oficiului influențează activitatea firmei doar prin durata așteptării): "
        "în aceeași săptămână, la același oficiu, cât a așteptat o firmă a depins de aglomerarea oficiului, nu de firma însăși. "
        "Așteptarea celorlalte firme depuse acolo atunci (variabilă instrumentală) prezice puternic așteptarea fiecărei firme." + E("C119") +
        " Am legat aproape toate înmatriculările din 2024 de bilanțurile depuse la Ministerul Finanțelor și am verificat rezultatul cu alte două metode (diferențe în diferențe în jurul lansării portalului din 2024 și un instrument național), plus teste placebo.") +
        '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
            hl("Așteptarea reduce activitatea din primul an: fiecare zi în plus înseamnă mai puține vânzări și mai puține taxe.") + E("C121"),
            hl("În anul următor, activitatea și taxele firmelor care au așteptat mai mult nu diferă măsurabil: datele nu arată o recuperare a ce s-a pierdut în primul an, dar nici nu exclud o pierdere care continuă.") + E("C120", "C121") +
            " Rezultatul e estimat pe așteptări de până la circa o lună; pentru așteptările de acum, mult mai lungi, nu putem exclude un efect."]) + "</ul>" + P(
        "Estimarea privește doar firmele noi, adică primul canal al contului de impact. Pentru ele, datele nu deosebesc o activitate doar amânată de una pierdută în parte. "
        "Nu spune nimic despre modificările blocate ale firmelor existente, care dau cea mai mare parte din costul pe scenarii." + E("C109") + " Acolo, ipoteza rămâne netestată, iar în cifrele pentru 2027 de mai jos partea modificărilor folosește ipotezele declarate ale analizei inițiale, nu o estimare.") +
        fig("i06_efect_cauzal.svg", "Efectul unei zile în plus de așteptare asupra impozitului direct plătit de o firmă nouă: în primul an (parțial) și în anul următor.", ["C120", "C121"]) +
        sub(f"{n}.1", "Riscul pentru veniturile bugetare din 2027") + P(
        "Combinăm prognoza cozii (2.000 de variante ale motorului verificat), volumele lunare de înmatriculări și modificări, efectele estimate mai sus, cu incertitudinea lor, și cotele legale din 2026. "
        + hl("Fără măsuri noi, circa " + V("C122").split(" (")[0] + " de milioane de lei din veniturile bugetare nu ar intra în bugetul anului 2027 din cauza cozii (valoarea mediană; interval de simulare de 95%, adică percentilele 2,5–97,5 ale variantelor simulate: " + V("C122").split(" (")[1].split(")")[0] + " milioane); o parte se poate recupera ulterior, dar datele nu exclud o pierdere durabilă.") + E("C122") +
        " Reperul e o coadă normală, de 3 zile, pentru cererile depuse din decembrie 2026; veniturile amânate din cererile depuse înainte, care ar intra în 2027, nu sunt scăzute. "
        "Cifra presupune deja că o parte din ce se pierde în zilele de așteptare se recuperează în același an." + E("C122") +
        " " + PR("C123") + E("C123") + " " + hl(PR("C124")) + E("C124") +
        " Din bilanțuri vin doar impozitul direct și angajații firmelor noi; TVA și toată partea modificărilor sunt ipoteze." + E("C122")) +
        fig("i07_risc_venituri_2027.svg", "Venituri bugetare care nu intră în bugetul anului 2027 din cauza cozii, pe trimestre, fără măsuri noi și cu un pachet realist de măsuri (mediana și intervalul de simulare de 95%).", ["C122", "C125"]) + P(
        hl("Un pachet realist de măsuri ar evita cea mai mare parte a acestei mutări de venituri.") + E("C125") +
        " Pentru Ministerul Finanțelor, concluzia practică: riscul merită inclus în evaluarea veniturilor pentru 2027 ca venit care nu intră în bugetul anului din cauza cozii; o parte se poate recupera ulterior, dar datele nu exclud o pierdere durabilă. Mărimea lui depinde direct de cât de repede se golește coada.") +
        P('<span class="note"><b>Specificația.</b> Efecte fixe de săptămână și de oficiu, plus forma juridică; erori standard grupate pe oficiu (ca variantă, pe oficiu și săptămână). Ipoteza de identificare: '
          "aglomerarea unui oficiu într-o săptămână, peste media oficiului și a săptămânii, influențează activitatea firmei doar prin durata așteptării. "
          "Un șoc local de cerere care aglomerează oficiul și schimbă și perspectivele firmelor noi ar încălca această ipoteză; testele placebo o verifică doar parțial. "
          "Cifrele de venituri pentru 2027 și cele din contul pe scenarii pentru 2026 răspund la întrebări diferite și nu se adună.</span>") + P('<span class="note"><b>Limite.</b> Efectul e estimat pe așteptări de până la circa o lună, iar prognoza pentru 2027 are așteptări de două–cinci ori mai lungi. '
          "Firmele care renunță înainte de decizie nu apar în date. Partea de TVA din veniturile unei firme noi și toată partea modificărilor din cifra pentru 2027 sunt ipoteze, nu estimări. Contul pe scenarii pentru 2026 presupune, fără o sursă, că o parte din vânzările amânate ale firmelor noi se pierd definitiv; estimarea econometrică nu poate nici confirma, nici exclude această ipoteză. Metoda completă, codul și tabelele sunt în dosarul de reproducere.</span>"))


def vol7(pg):
    BV.TN["n"] = 0; BV.FN["n"] = 0
    fig = lambda svg, cap, ids: BV.fig(svg, cap, ids, fdir="figures_impact")
    has_ec = bool(econometrics_section("x"))
    S = [("", "1", "Pe scurt", "1"), ("", "2", "Trei niveluri de siguranță", "2"), ("", "3", "Costul lună de lună", "3"),
         ("", "4", "Contul de impact, august–noiembrie 2026", "4"), ("", "5", "Ce înseamnă pentru buget", "5"), ("", "6", "Pe ce se sprijină fiecare cifră", "6"),
         ("", "7", "Ce mișcă cifra", "7")] + ([("", "8", "Estimarea econometrică și riscul pentru veniturile din 2027", "8")] if has_ec else []) + \
        [("", "9" if has_ec else "8", "Ce trebuie măsurat și limite", "9" if has_ec else "8"), ("", "10" if has_ec else "9", "Tabele", "10" if has_ec else "9")]
    b = cover("Impactul economic și bugetar al cozii", "Cât costă întârzierile de la Registrul Comerțului economia și bugetul de stat, lună de lună: ce se măsoară, ce se presupune și cât de sigure sunt cifrele.",
              "Volumul 7", "<dt>Pentru cine</dt><dd>Ministerul Finanțelor, ANAF, Ministerul Justiției, Guvern.</dd>"
              "<dt>Regula de onestitate</dt><dd>Zilele de întârziere sunt măsurate. Transformarea lor în lei folosește date oficiale unde există și ipoteze declarate unde nu există.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    b += sec("1", "Pe scurt") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        hl("Într-o lună obișnuită, întârzierile la Registru costă economia câteva milioane de lei; în octombrie și noiembrie 2026, de circa " + ORI + " ori mai mult.") + E("C111"),
        hl("Pentru august–18 noiembrie 2026, costul economic este estimat între circa " + V("C106").split(" / ")[0] + " și " + V("C106").split(" / ")[2] + " de milioane de lei, cu circa " + V("C106").split(" / ")[1] + " în scenariul central.") + E("C106") +
        " O parte s-a produs deja la dosarele decise; restul depinde de cât vor mai aștepta dosarele din stoc." + E("C112"),
        hl(PR("C107")) + E("C107"),
        hl("Fiecare zi în plus cu stocul actual costă, în scenariul central, circa " + V("C108").split(" (")[0] + " milioane de lei în economie și circa " + V("C108").split(" / ")[1].split(" (")[0] + " milioane la buget.") + E("C108"),
        "Parametrii modelului cu o bază în date sau în surse oficiale sunt acum " + NFOUND + "; cel care cântărește cel mai mult, costul unei modificări blocate, nu are." + E("C116", "C109"),
        "Fără nicio ipoteză, doar costul de finanțare al amânării, podeaua măsurată e mică; diferența până la scenarii vine din cât din activitate se pierde, nu doar se amână." + E("C115")] + ([
        hl(PR("C122")) + E("C122") + " " + PR("C124") + E("C124") +
        " În anul următor, estimarea econometrică nu găsește o diferență măsurabilă la firmele noi, dar nici nu exclude o pierdere care continuă." + E("C120") +
        " Cifra are un interval larg, extrapolează la așteptări mai lungi decât cele pe care a fost măsurat efectul și răspunde la altă întrebare decât contul pe scenarii pentru 2026, deci nu se adună cu el (secțiunea 8)."] if has_ec else [])) + "</ul>"
    b += sec("2", "Trei niveluri de siguranță") + P(
        "Cifrele de cost se citesc pe trei niveluri, de la sigur la incert. ") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "<b>Podeaua măsurată.</b> Doar date și dobânzi oficiale: cât costă amânarea vânzărilor și a taxelor firmelor noi, la dobânda titlurilor de stat. " + hl("Circa " + V("C115").split(" (")[0].replace("≈", "") + " milioane de lei pentru august–18 noiembrie.") + E("C115") + " E o limită de jos sigură, dar mică, pentru că presupune că nimic nu se pierde, doar se amână.",
        "<b>Scenariul fundamentat.</b> Aceleași formule ca analiza inițială, dar fiecare parametru care are o bază e luat din date: vânzările firmelor noi din bilanțurile depuse la Ministerul Finanțelor, ponderea valorii adăugate din statistica europeană, cota fiscală din impozitul măsurat și cotele legale din 2026, ponderile din textul buletinelor. " + hl("Acesta e scenariul folosit în tot raportul.") + E("C116", "C117", "C118"),
        "<b>Analiza inițială.</b> Scrisă pe 21 noiembrie, cu mai multe ipoteze; o păstrăm doar ca test de sensibilitate. Față de ea, scenariul fundamentat e cu circa " + DROP + "% mai mic." + E("C116")]) + "</ul>"
    b += sec("3", "Costul lună de lună") + P(
        "Aplicăm parametrii scenariului fundamentat pe zilele de întârziere măsurate ale dosarelor decise în fiecare lună, din ianuarie 2024. Rezultatul nu e o contabilitate, ci întârzierea exprimată în lei, comparabilă de la o lună la alta. "
        + hl("Toamna lui 2024, la lansarea noului portal, a fost primul vârf; toamna lui 2026 îl depășește clar.") + E("C111") + " " + REG["C113"]["public_ro"] + E("C113"))
    b += fig("i01_cost_lunar.svg", "Costul economic (sus) și încasările bugetare afectate (jos), pe luna deciziei, scenariul fundamentat; liniile verticale arată intervalul prudent–tensionat. Noiembrie 2026 e parțial.", ["C111"])
    b += P("În lunile obișnuite, costul de fond vine mai ales din amânările evitabile și din puținele dosare care trec de trei zile. Creșterea din toamna lui 2026 vine în cea mai mare parte din modificările blocate; costul firmelor noi care așteaptă înmatricularea a crescut și el de câteva ori." + E("C109", "C111"))
    b += fig("i02_canale_lunar.svg", "Costul economic pe canale, scenariul fundamentat, 2025–2026.", ["C109"])
    b += sec("4", "Contul de impact, august–noiembrie 2026") + P(
        "Contul adună costul realizat al dosarelor decise între 1 august și 18 noiembrie cu expunerea condiționată a stocului încă nedecis: zilele pe care acele dosare le vor mai aștepta, după prognoză." + E("C106", "C112") +
        " " + hl("Intervalul contează mai mult decât cifra centrală: între scenariul prudent și cel tensionat e " + SPREAD_TXT + ".") + E("C106"))
    b += fig("i03_cont_de_impact.svg", "Contul de impact pe scenarii: cost economic (stânga, împărțit în realizat și expunerea stocului) și încasări bugetare afectate (dreapta).", ["C106", "C107", "C112"])
    b += sec("5", "Ce înseamnă pentru buget") + P(
        "Calculul impozitează doar partea de activitate presupusă pierdută definitiv, nu venituri amânate: de aceea cifra centrală depinde de ipoteza, fără sursă, a părții pierdute. Cota fiscală efectivă e construită din impozitul direct plătit efectiv de firmele noi, contribuțiile la salariul minim pentru angajații lor și TVA pe valoarea adăugată." + E("C107")) + P(
        hl("Pentru buget, cifra cea mai utilă e cea zilnică: cât costă încă o zi cu stocul actual.") + E("C108") +
        " Comparată cu bugetul proiectului de OUG, în scenariul central economia pierde în circa " + OUG_D_ECON + " de coadă cât costă întreaga măsură, iar bugetul, în circa " + OUG_D_TAX + "." + E("C108", "C83") +
        " Nu se înmulțește cu numărul de zile, pentru că stocul și compoziția lui se schimbă; comparația dă doar un ordin de mărime, iar proiectul singur scurtează coada, nu o elimină." + E("C43"))
    b += sec("6", "Pe ce se sprijină fiecare cifră") + P(
        "Tabelul arată, pentru fiecare parametru, valorile din analiza inițială și din scenariul fundamentat, starea (măsurat, sursă oficială, plafon măsurat sau ipoteză) și sursa. " +
        hl("Ponderea valorii adăugate a scăzut de la 45% la circa 30% (Eurostat), vânzările pe zi ale unei firme noi au fost recalculate pe toate firmele înmatriculate, inclusiv cele fără activitate, iar ponderea modificărilor care pot bloca activitatea are acum un plafon măsurat.") + E("C117", "C118", "C104") +
        " Ponderea amânărilor evitabile la depunere (canalul D) nu mai e presupusă (8–25% în analiza inițială): vine din motivele amânărilor citite în buletine, între " +
        V("C139").split(" (")[0] + " (toate motivele evitabile) și " + V("C139").split(" · ")[1].split(" (")[0] + " (cel puțin un motiv evitabil)." +
        " O amânare e evitată doar dacă toate motivele ei sunt evitabile, așa că scenariul central folosește ponderea strictă, iar cel prudent limita ei inferioară; «cel puțin un motiv» e doar un plafon, folosit numai în scenariul tensionat." + E("C139", "C116") +
        " " + C112_C + E("C112")) + \
        BV.table("cost_ipoteze", "Parametrii, valorile și sursa lor", small=True)
    b += sec("7", "Ce mișcă cifra") + P(
        "Schimbăm pe rând câte un parametru, de la valoarea prudentă la cea tensionată. " + hl("Cel mai mult contează costul pe zi al unei modificări blocate, o ipoteză fără sursă publică.") + E("C109") +
        " Ca ordin de mărime, valoarea centrală reprezintă câteva procente din vânzările zilnice ale firmelor afectate; nu o putem verifica mai precis din datele publice.") + \
        fig("i04_sensibilitate.svg", "Cât se schimbă costul central (scenariul fundamentat) când se schimbă un singur parametru.", ["C109"]) + P(
        "La nivelul economiei, o parte din vânzările pierdute de o firmă blocată pot fi făcute de alta. " + hl(REG["C110"]["public_ro"]) + " " + REG["C110"]["rezerva_obligatorie"] + E("C110", "C83")) + \
        fig("i05_substitutie.svg", "Costul net dacă o parte din activitatea pierdută e preluată de alte firme, scenariile central și prudent, față de bugetul proiectului de OUG (scară logaritmică).", ["C110", "C83"])
    n = 8
    if has_ec:
        b += econometrics_section("8"); n = 9
    b += sec(str(n), "Ce trebuie măsurat și limite") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "<b>Legarea controlată ONRC–ANAF</b> (pseudonimizată): data notificării, a inactivării și a reactivării pentru firmele cu dosare de sediu în așteptare.",
        "<b>Declarațiile periodice ale firmelor noi</b> (vânzări lunare): ar măsura direct primele luni de activitate, perioada atinsă de întârziere.",
        "<b>Un eșantion de firme cu modificări blocate</b>, cu costul lor real: ar fixa ipoteza care cântărește cel mai mult." + E("C109"),
        "<b>Limite.</b> Bilanțurile acoperă circa jumătate din firmele noi, iar primul exercițiu poate avea doar câteva luni." + E("C104") +
        " Textul buletinelor PDF e disponibil doar pentru octombrie–noiembrie 2026." + E("C118") + " Costul lunar folosește aceiași parametri pentru toți anii. Cifrele nu includ costurile indirecte (încredere, investiții amânate)."]) + "</ul>"
    b += sec(str(n + 1), "Tabele") + BV.table("cost_scenarii", "Contul de impact pe scenarii (milioane lei)") + BV.table("cost_canale_tab", "Costul economic pe canale (milioane lei)") + \
        BV.table("cost_anual", "Cost realizat pe ani (milioane lei)") + BV.table("cost_lunar", "Cost realizat lunar (milioane lei)", small=True) + \
        BV.table("cost_ancora", "Ancora: vânzările firmelor noi în primul exercițiu (bilanțuri MF)", small=True) + \
        BV.table("cost_substitutie", "Costul net dacă activitatea e preluată de alte firme", small=True) + BV.table("cost_verificare", "Ce am verificat")
    return b, S


VOL = ("COADA DE LA REGISTRUL COMERȚULUI · IMPACT ECONOMIC ȘI BUGETAR", "Volumul 7", vol7, "Raport_ONRC_Coada_2026-11_VOL7_Impact_economic_si_bugetar")
