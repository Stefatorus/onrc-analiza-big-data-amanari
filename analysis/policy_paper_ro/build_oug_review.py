"""Build the Romanian Lab Edition review of the Ministry of Justice draft."""
import argparse
import html
import json
from pathlib import Path
import tempfile

import fitz
import numpy as np
import pandas as pd

from audit_charts import BLUE, GRID, NAVY, OCHRE, RUST, TEAL, chart_svg, date_axis, plt
from audit_forecast import MINISTRY_NOTE
from audit_layout import embedded_fonts, number as n
from audit_oug import RESULTS
from audit_reports import CAEN, EU, LAW239, LAW265, ext
from build_lab_report import compile_pdf
from build_lab_verified import INTERNAL_LINK, PAGE_REF, REFINEMENTS, read_targets
from lab_styles import BASE_CSS, badge, prose, pulls, takeaway
from lab_verified import MJ_DRAFT, chart, ref, tbl

HERE = Path(__file__).resolve().parent
STEM = "Evaluarea_proiectului_OUG_ONRC_18_noiembrie_2026"
DRAFT_DOC = ("https://www.just.ro/wp-content/uploads/2026/11/"
             "proiect-OUG-pentru-instituirea-unor-masuri-privind-activitatea-de-inregistrare-"
             "in-registrului-comertului-si-pentru-completarea-Legii-nr.265-2022.docx")
LAW3 = "https://www.senat.ro/Legis/Lista.aspx?cod=26396"
LAB_REPORT = "Raport_ONRC_2026_2028_StefanDeleanu_LabEdition_Verificata_v2.pdf"
TITLES = {
    "sinteza": "Verdictul în trei întrebări",
    "proiect": "Ce autorizează proiectul",
    "cifre": "Verificarea cifrelor din notă",
    "stoc": "Cele două etape ale restanței",
    "personal": "Cât poate aduce personalul redistribuit",
    "acte": "Ce poate elibera transferul administrativ",
    "istoric": "Ce susțin datele istorice",
    "test": "Cum am testat eficacitatea",
    "efect": "Cât ar scurta proiectul așteptarea",
    "suficienta": "Ce ar trebui pentru trei zile",
    "comparatie": "Proiectul față de măsurile din Lab Edition",
    "cost": "Ce știm despre costul bugetar",
    "decizie": "Ce ar trebui schimbat în proiect",
    "monitorizare": "Cum se verifică rezultatul după adoptare",
    "metoda": "Metodă și surse",
    "audit-complexitate": "Audit, backtesting și munca-echivalentă v1.0 vs. v2.0",
}
LABELS = {
    "referinta": "Fără măsuri noi", "oug_redus": "OUG · aport redus", "oug_central": "OUG · aport central",
    "oug_ridicat": "OUG · aport ridicat", "doar_art_iii": "Doar art. III",
    "oug_digital": "OUG + digitalizare", "oug_esalonare": "OUG + eșalonare din aprilie",
    "pachet": "OUG + digitalizare + eșalonare din aprilie",
    "pachet_dupa_caen": "OUG + digitalizare + eșalonare din iulie",
}


def data(name, index=None):
    return pd.read_csv(RESULTS / f"{name}.csv", index_col=index)


def section(key, idea, *contents):
    index = list(TITLES).index(key)
    label = "Sinteză" if not index else f"Analiză · {index:02d}"
    return f"""<section class="chapter verified brief-page" id="{key}" style="page: note">
      <div class="copen"><div class="cnum">{label}</div><h2>{TITLES[key]}</h2>
      <div class="cmeta">{ref("cuprins","Cuprins, p.")}</div></div>
      {takeaway(idea)}{"".join(contents)}</section>"""


def portal_table(rows):
    gov = {"H1 2026":("4.533","—"), "Ianuarie–iulie 2026":(">26.000","—"),
           "August–octombrie 2026":("6.931","—"), "Septembrie 2026":("—","4.912"),
           "Octombrie 2026":("—","5.098"), "2–17 noiembrie 2026":("—","—")}
    return tbl("Tabelul 1", "Medii zilnice în documentele ministerului și în arhiva BERC",
        ["Perioadă", "Intrări MJ", "Ieșiri MJ", "Finale BERC", "Finale + amânări", "Proxy portal¹"],
        [(r.period,*gov[r.period],n(r.strict_per_day),n(r.touches_per_day),n(r.portal_per_day)) for r in rows.itertuples()],
        (1,2,3,4,5), "¹ Diferențe ale numerelor de cerere, cumulate în perioadă și împărțite la zilele lucrătoare. Include servicii fără registrator.")


def stock_figure(audit):
    fig, ax = plt.subplots(figsize=(7.4,2.25))
    v1 = [audit["prior_unprocessed"],audit["current_unprocessed"]]
    v2 = [audit["prior_processed"],audit["current_processed"]]
    bars1 = ax.barh([1,0], np.array(v1)/1000, color=BLUE, height=.43)
    bars2 = ax.barh([1,0], np.array(v2)/1000, left=np.array(v1)/1000,color=OCHRE,height=.43)
    for bars, vs in [(bars1,v1),(bars2,v2)]:
        ax.bar_label(bars, labels=[n(v) for v in vs], label_type="center", color="white", fontweight="bold")
    ax.set_yticks([1,0],["30 oct. 2026","6 nov. 2026"])
    ax.set_xlabel("Mii de cereri restante")
    ax.set_xlim(0,233)
    ax.xaxis.grid(color=GRID)
    ax.legend([bars1,bars2],["Neprelucrate","Prelucrate, nesoluționate"],loc="upper center",ncol=2,bbox_to_anchor=(.5,1.18))
    fig.tight_layout()
    return chart_svg(fig)


def scenarios_figure():
    d = data("trajectory")
    d.date = pd.to_datetime(d.date)
    fig, ax = plt.subplots(figsize=(7.4,3.30))
    for key, color, style, label in [
        ("referinta",RUST,"-","Fără măsuri noi"),("oug_central",OCHRE,"--","Proiect · aport central"),
        ("oug_ridicat",BLUE,"-.","Proiect · aport ridicat"),("oug_digital",TEAL,"-","Proiect + digitalizare"),
    ]:
        q=d[d.scenario.eq(key)]
        ax.plot(q.date,q["median"],color=color,label=label,ls=style,lw=1.8)
        if key=="oug_central":
            ax.fill_between(q.date,q.p10,q.p90,color=color,alpha=.10,linewidth=0)
    ax.axvline(pd.Timestamp("2028-01-08"),color=NAVY,alpha=.6,lw=1,ls=":")
    ax.text(pd.Timestamp("2028-01-12"), 13, "Sfârșitul desemnărilor",color=NAVY,fontsize=7)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Zile calendaristice")
    ax.legend(loc="upper left",ncol=2)
    date_axis(ax,3)
    fig.tight_layout()
    return chart_svg(fig)


def target_figure(g):
    fig, ax = plt.subplots(figsize=(7.4,2.92))
    ax.plot(g.units_per_day,100*g.end_2027,color=OCHRE,ls="--",label="31 dec. 2027")
    ax.plot(g.units_per_day,100*g.end_june_2028,color=BLUE,ls="-.",label="30 iun. 2028")
    ax.plot(g.units_per_day,100*g.meets_both,color=TEAL,lw=2,label="Ambele date")
    ax.axvspan(100,900,color=RUST,alpha=.09,label="Aport redus–ridicat testat")
    ax.axhline(50,color=NAVY,lw=.6,ls=":")
    ax.set(xlabel="Unități standard suplimentare / zi lucrătoare",ylabel="Trageri cu cel mult 3 zile (%)",ylim=(0,103))
    ax.yaxis.grid(color=GRID)
    ax.legend(loc="upper left",ncol=2)
    fig.tight_layout()
    return chart_svg(fig)


def percent(v, decimals=1):
    return n(100*v,decimals)+"%"


def summary_row(d, scenario, periods):
    return tuple(f"{n(d.at[(scenario,p),'median'])} [{n(d.at[(scenario,p),'p10'])}–{n(d.at[(scenario,p),'p90'])}]" for p in periods)


def body():
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))
    inputs = data("policy_inputs","scenario")
    d = data("scenarios",["scenario","period"])
    g = data("target_grid")
    evidence = data("evidence_flows")
    past = data("historical_delegation")
    j = evidence.set_index("period")
    end = "2028-06-30"
    base, central, high, digital = (d.loc[(k,end)] for k in ("referinta","oug_central","oug_ridicat","oug_digital"))
    limit50 = g[g.meets_both.ge(.5)].iloc[0]
    limit80 = g[g.meets_both.ge(.8)].iloc[0]
    july_days = j.at["Ianuarie–iulie 2026","workdays"]-j.at["H1 2026","workdays"]
    july_implied = ((26000*j.at["Ianuarie–iulie 2026","workdays"]-4533*j.at["H1 2026","workdays"])/july_days)
    toc = "".join(f'<li><a class="toc-link" href="#{id_}"><span class="tn">{"Sinteză" if i==0 else f"{i:02d}"}</span>'
                  f'<span class="tt">{title}</span><span class="tpg">%%PG_{id_}%%</span></a></li>'
                  for i,(id_,title) in enumerate(TITLES.items()))
    pages = [
        f"""<section class="cover"><div class="eyebrow">Evaluare independentă · Consultare publică</div>
        <h1>Va reduce proiectul coada de la Registrul Comerțului?</h1>
        <p class="sub">Verificarea proiectului de ordonanță din 18 noiembrie 2026 și a notei de fundamentare. Comparație cu măsurile din Lab Edition.</p>
        <div class="threads" aria-hidden="true"><i class="t-e"></i><i class="t-s"></i><i class="t-m"></i><i class="t-p"></i></div>
        <p class="verdict">Proiectul poate scurta așteptarea și păstra capacitatea existentă. Pentru a readuce serviciul la trei zile, trebuie să elibereze un volum de muncă mult mai mare decât în scenariile de redistribuire testate.</p>
        <p class="verdict-sub">Cu un aport de 375 de dosare-standard pe zi lucrătoare, așteptarea mediană simulată la 30 iunie 2028 scade de la
        {n(base["median"])} la {n(central["median"])} zile calendaristice. Cu aceeași redistribuire și reducerea sarcinii repetitive din portal, mediana scade la {n(digital["median"])} de zile.</p>
        <dl class="meta"><dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
        <dt>Documente</dt><dd>Proiectul și nota Ministerului Justiției, publicate la 18 noiembrie 2026</dd>
        <dt>Analiză</dt><dd>Date BERC până la 18 noiembrie 2026 · 2.000 de trageri de scenariu</dd>
        <dt>Ediție</dt><dd>Lab Edition · 21 noiembrie 2026</dd></dl></section>""",
        f"""<section class="front front-toc" id="cuprins"><div class="eyebrow">Structura evaluării</div><h2>Cuprins</h2>
        <p class="note">Pentru o lectură rapidă, începeți cu verdictul la {ref('sinteza')}, rezultatele la {ref('efect')} și deciziile la {ref('decizie')}.
        Cifrele ministerului sunt verificate la {ref('cifre')}. Toate trimiterile funcționează în PDF și HTML.</p><ul class="toc">{toc}</ul>
        <p class="note">Marcaje: {badge('E')} observație din date · {badge('S')} document oficial · {badge('M')} estimare · {badge('P')} scenariu.</p>
        </section>""",
        section("sinteza", "Proiectul oferă sprijin temporar. Numărul de ore care ajung efectiv în coadă decide cât ajută, iar sarcina din portal decide dacă ajunge.",
            pulls([("204.414","cereri restante la 6 noiembrie",badge("S")+" Nota MJ, §2.2",False),
                   ("4.409","finale pe zi, 2–17 noiembrie",badge("E")+" BERC · 12 zile lucrătoare",False),
                   (n(central["median"])+" zile","OUG, aport central, la 30 iunie 2028",badge("P")+" mediană condiționată",False),
                   ("3 zile","reper operațional", "în zile calendaristice",True)]),
            tbl("Sinteză","Trei întrebări, trei criterii de verificare",["Întrebare","Răspuns și probă"],
                [("Intervenția are un mecanism plauzibil?","Da. Desemnările pot adăuga ore de control, iar art. III poate transfera anumite mențiuni către o echipă separată."),
                 ("Ar reduce așteptarea?","În scenariile cu aport net pozitiv, da. Efectul depinde de câți oameni acceptă și de capacitatea etapelor din jurul lor."),
                 ("Ar aduce serviciul la trei zile?","În scenariile testate pentru proiect, de regulă rămâne o coadă substanțială. Simularea indică aportul necesar la două repere de dată.")]),
            prose(f"Raportul compară proiectul cu măsurile din Lab Edition folosind aceleași trageri pentru cerere, stoc și capacitate de bază. "
                  f"Recalcularea separă salariile de volumele realizabile. Vezi {ref('test')} și {ref('comparatie')}."),
            prose("Verdictul de politică publică are două părți. Extinderea temporară merită folosită pentru a evita pierderea de capacitate și a reduce coada veche. "
                  "O revenire verificabilă cere un plan cu ore alocate, indicatori pe etape și un pilot pentru reducerea verificărilor repetitive.")),
        section("proiect","Proiectul propune două intervenții asupra personalului existent și o schimbare permanentă de traseu pentru unele mențiuni.",
            tbl("Cadru","Harta mecanismelor din textul pus în consultare",["Articol", "Ce se schimbă", "Ce trebuie urmărit"],
                [("I","Consilierul juridic specialist poate fi desemnat temporar pentru controlul de legalitate. Sunt prevăzute acordul scris, decizia motivată, statutul pentru actele emise și diferența salarială proporțională când se aplică.",
                  "Orele ajunse efectiv în control, supravegherea și atribuțiile din care persoana a fost mutată."),
                 ("II","Desemnarea de la art. I și prelungirea mecanismului existent pentru conducerea de specialitate juridică merg până la 8 ianuarie 2028.",
                  "Desemnații noi și capacitatea păstrată față de expirarea mecanismului actual."),
                 ("III","Noile art. 5¹–5² permit înscrieri din oficiu pentru acte eligibile, cu verificări de proveniență, identificare și concordanță. Clarificările revin emitentului.",
                  "Volum eligibil, durată, erori. Consilierul desemnat pentru control are incompatibilitatea de sarcini din art. I alin. (6)."),
                 ("IV","ONRC are 15 zile pentru optimizarea fluxului informatic. Art. III se aplică după optimizare. Procedurile începute înainte de intrarea în vigoare urmează legea de atunci.",
                  "Data punerii în producție și delimitarea cohortelor. Transferul nu trebuie aplicat retroactiv stocului modelat.")]),
            prose(f"Consultarea este deschisă până la 24 noiembrie 2026. Analiza privește textul publicat, cu dată de referință 21 noiembrie. "
                  f"Nota din §2.3 indică din eroare OUG 109/2014, în timp ce trimiterea corectă este OUG 109/2024, aprobată prin Legea nr. 3/2026. "
                  f"Formularea «funcții învestite» din art. III–IV merită armonizată cu «persoane» din notă. {ext(DRAFT_DOC,'Proiectul')} · {ext(LAW3,'Fișa parlamentară')}."),
            prose("Proiectul lucrează cu personal existent. Reîncadrarea sau recrutarea pe posturi vacante rămân măsuri distincte. "
                  "Textul fixează o autorizare și un termen, iar calendarul efectiv al desemnărilor rămâne o decizie de punere în aplicare.")),
        section("cifre","Nota susține corect ordinul de mărime al creșterii în august–octombrie din propria comparație. Seria de 26.000 pe zi nu se reproduce din datele BERC analizate de noi și are nevoie de o definiție publicată.",
            portal_table(evidence),
            prose(f"Creșterea de la 4.533 la 6.931 înseamnă {n(100*(6931/4533-1),1)}%, conform notei. Din aceeași notă, peste 26.000 pentru ianuarie–iulie "
                  "ar însemna o serie cu altă sferă sau alt numitor. Dacă numărăm cererile care apar ulterior în BERC, ianuarie–iulie dă aproximativ "
                  f"{n(j.at['Ianuarie–iulie 2026','filing_mature_per_day'])} pe zi lucrătoare. Diferențele contorului portalului, cu sferă mai largă, dau aproximativ "
                  f"{n(j.at['Ianuarie–iulie 2026','portal_per_day'])}. Creșterea de opt ori nu se reproduce din datele BERC analizate de noi pe o singură definiție; posibil, unități diferite."),
            prose(f"Pe același calendar de lucru și aceeași definiție, cele două valori ar corespunde unui nivel de peste {n(july_implied)} cereri pe zi în iulie, pe care nu îl regăsim în datele noastre. "
                  "Preambulul folosește primele șapte luni ca reper pentru creșterea ulterioară, iar nota calculează 53% față de primul semestru. "
                  "Cifrele ministerului pentru soluționări în septembrie și octombrie sunt mai apropiate de finalele plus amânările BERC decât de finalele în sens strict. "
                  "Apropierea nu dovedește ce include indicatorul oficial. Pentru reconciliere sunt necesare definiția unui caz închis, perioada exactă, calendarul zilelor și codurile incluse."),
            prose("În august–octombrie, multe cereri depuse nu erau încă vizibile în BERC la 18 noiembrie. Din acest motiv nu folosim cohorta de toamnă pentru a respinge "
                  f"nivelul de intrări raportat în notă. Verificarea trebuie făcută din registrul complet de intrări și ieșiri. {ext(MINISTRY_NOTE['source'],'Nota de fundamentare, §2.2')}.")),
        section("stoc","Între 30 octombrie și 6 noiembrie, stocul a scăzut cu 3.904 cereri. În același timp, numărul celor prelucrate și încă nesoluționate a crescut.",
            chart("Figura 1","Observație administrativă","O parte mai mare a restanței s-a mutat în etapa prelucrată",stock_figure(audit),
                "Prima etapă scade cu 8.300, a doua crește cu 4.396. La 6 noiembrie, a doua reprezintă 48,1% din total.",
                "Nivelurile din 30 octombrie sunt reconstruite din valorile și diferențele din nota publică.",
                ext(MINISTRY_NOTE["source"],"Ministerul Justiției, nota de fundamentare, §2.2.")),
            prose("O cerere poate trece în etapa de control fără să iasă din restanță. Același lucru se poate întâmpla dacă un consilier ajunge mai repede la o decizie "
                  "care rămâne apoi în așteptare pentru o completare. Cele două instantanee dovedesc mișcarea stocurilor, dar nu identifică de ce o cerere a rămas deschisă."),
            prose("Menținerea ritmului net de 3.904 pe săptămână ar cere circa 52 de săptămâni pentru stocul de 204.414. Calculul este doar un etalon aritmetic. "
                  "Vârsta cohortei, valurile CAEN și capitalul pot schimba atât ritmul, cât și direcția."),
            prose("Pentru o intervenție echilibrată, publicați intrările și ieșirile fiecărei etape, cererile în așteptare la solicitant și durata până la prima examinare. "
                  "Măriți simultan capacitatea de prelucrare dacă dosarele vechi rămân blocate înainte de controlul de legalitate.")),
        section("personal","1.250 de posturi ocupate arată un deficit la nivelul instituției. Aportul proiectului se măsoară în ore și dosare comparabile, după sarcinile deplasate.",
            tbl("Tabelul 2","Capacitatea declarată și conversia în scenarii",["Măsură","Valoare","Ce se poate deduce"],
                [("Posturi aprobate / finanțate / ocupate","1.792 / 1.384 / 1.250","69,75% din aprobate sunt ocupate. Aritmetic, 134 de posturi finanțate sunt neocupate dacă definițiile sunt aliniate."),
                 ("Scenariu redus","5 × 20 = 100","Cinci echivalente efective, cu 20 de unități standard pe zi fiecare."),
                 ("Scenariu central","15 × 25 = 375","Efectivul de 15 este un ipotetic echivalent de normă întreagă, după sarcinile deplasate."),
                 ("Scenariu ridicat","30 × 30 = 900","Ipoteză favorabilă. Reclamă mai multe ore disponibile și o rată susținută pe dosare comparabile.")],(1,)),
            prose("Echivalentul de normă întreagă este timpul net, nu numărul de decizii de desemnare. De pildă, 30 de persoane cu jumătate de normă net disponibilă "
                  "oferă 15 echivalente. Reducerea se aplică pentru activitatea proprie pe care persoana trebuie să o continue și timpul pe care echipa îl consumă pentru instruire."),
            prose("Pentru comparație, aceiași 93 de registratori au avut 31,4 și 38,2 decizii brute pe zi în 2024 și 2026. După excluderea tipurilor simple, medianele "
                  "sunt 22,0 în ambele perioade. Intervalul bootstrap pentru raportul medianelor comparabile este 0,85–1,09, condiționat de datele disponibile. "
                  "Cele trei zile din 2026 nu măsoară randamentul consilierilor nou desemnați."),
            prose("Plaja de 20–30 unități pe echivalent și pe zi este o ipoteză de operare. Nota nu publică numărul pe funcție, câți au consimțit, timpul net sau producția pe tip de dosar. "
                  "Rezultatul depinde de toate aceste variabile.")),
        section("acte","Art. III poate economisi timp în anumite operațiuni. Gradul în care ajută coada principală depinde de actele transferabile și de echipa care le primește.",
            tbl("Tabelul 3","Articole din categoria judiciară vizibile în BERC",
                ["Perioadă","CERERE_HJ265","Pe zi lucrătoare"],
                [(r.period,n(r.judicial_all),n(r.judicial_per_day,1)) for r in evidence.itertuples()
                 if r.period in ["H1 2026","Septembrie 2026","Octombrie 2026","2–17 noiembrie 2026"]],(1,2),
                "Categoria include articole de certificare și alte ieșiri. Indicatorul este un reper istoric parțial pentru flux, nu un inventar juridic al actelor de la art. III."),
            prose("Proveniența, identitatea, măsura și concordanța rămân de verificat. Mențiunile pot avea nevoie de clarificări. Economiile nete apar când echipa care preia "
                  "aceste operațiuni are timp și le rezolvă fără a produce o nouă restanță. Separarea rolurilor prevăzută de art. I alin. (6) este esențială."),
            prose(f"Populația de 422.093 de entități comunicată de ANAF cuprinde cazuri la diferite etape ale dizolvării și radierii. Art. VIII din Legea nr. 239/2025 "
                  f"atribuie expres registratorului constatarea condițiilor, iar în situații prevăzute și radierea ori numirea lichidatorului. "
                  f"O listă ANAF nu echivalează automat cu un act final ce poate fi înscris administrativ. {ext(LAW239,'Legea nr. 239/2025, art. VIII')}."),
            prose(f"Simulăm un transfer net de 25% din sarcina viitoare care ar folosi capacitatea comună în cazul central, și 50% în cel ridicat. "
                  f"Testat singur la 25%, art. III economisește median {n(d.at[('doar_art_iii',end),'median_saved'])} zile la 30 iunie 2028 pe trageri pereche. "
                  "Testul păstrează stocul inițial. Aplicarea cere o matrice pe tip de act și temei, mai ales pentru operațiunile prevăzute de lege specială.")),
        section("istoric","Ritmul a revenit după intervenția din 2024. Datele disponibile pot verifica această succesiune și puterea unei prognoze scurte, cu limite diferite.",
            tbl("Tabelul 4","Ferestre egale în jurul OUG nr. 109/2024",["Fereastră","Zile lucrătoare","Finale pe zi","Mediană (zile cal.)"],
                [(r.window,r.workdays,n(r.finals_per_day),n(r.median_wait,1)) for r in past.itertuples()],(1,2,3),
                "Ferestre de 28 de zile calendaristice în jurul datei de 12 septembrie 2024. BERC, finale stricte."),
            prose("În 2024, reluarea serviciului după migrarea din iulie a coincis cu măsura de desemnare și alte schimbări. Timpul median a rămas ridicat în primele patru "
                  "săptămâni după publicare. Fără data reală, orele și dosarele fiecărei desemnări, nu se poate izola cât din revenire i se datorează ordonanței."),
            prose(f"În 2–17 noiembrie 2026, ieșirile pe zi variază între {n(audit['recent_daily_min'])} și {n(audit['recent_daily_max'])}. "
                  f"Pentru săptămânile complete din 2026, percentila 10 a mediei zilnice este {n(audit['historical_5day_means_p10_p50_p90'][0])}, iar percentila 90 este "
                  f"{n(audit['historical_5day_means_p10_p50_p90'][2])}. Variația face ca o creștere mică să fie greu de atribuit după o singură săptămână."),
            prose("Pe nouă origini istorice, testul de patru săptămâni înainte are eroare procentuală absolută medie de 4,61% dacă folosește ultimele patru săptămâni "
                  "și 5,55% dacă folosește ultimele 12 zile lucrătoare. Pentru scenarii păstrăm ritmul recent de 4.409 finale și plaja de volum din Lab Edition. "
                  "Testul măsoară stabilitatea predicției de volum. Nu validează efectul desemnărilor.")),
    ]
    end_year = "2027-12-31"
    spring = "2027-03-31"
    summer = "2027-06-30"
    effect_dates = (spring,end_year,end,"peak")
    effects = ("referinta","oug_redus","oug_central","oug_ridicat","doar_art_iii")
    added = ("oug_central","oug_digital","oug_esalonare","pachet","pachet_dupa_caen")
    public_payroll = 480_000*12
    cost_rows = [
        (LABELS[k], n(inputs.at[k,"net_units_2027"]), n(public_payroll/inputs.at[k,"net_units_2027"],0)+" lei")
        for k in ("oug_redus","oug_central","oug_ridicat")
    ]
    sunset = data("management_expiry")
    days_for_rate = int(audit["workdays_2027"])
    endpoint_roug = d.loc[("oug_ridicat",end),"within_3"]
    pages.extend([
        section("test","Simularea testează ce s-ar întâmpla sub aceleași intrări și același stoc dacă proiectul ar aduce cantități diferite de muncă utilă.",
            tbl("Tabelul 5","Ipotezele descompuse pe mecanism",["Componentă","Cum intră în simulare"],
                [("Stoc de pornire","Plajă triunghiulară 145.000 / 200.000 / 300.000 cereri, ancorată în nota MJ și în actualizarea aproximativă la 17 noiembrie."),
                 ("Cerere obișnuită și valuri","Același model ca în Lab Edition, cu BERC, calendarul și populațiile din nota ministerului. Intrările obișnuite și valurile suplimentare sunt separate."),
                 ("Art. I–II, aport nou","+100 / +375 / +900 unități nete pe zi în scenarii separate, din 4 ianuarie 2027. Prima jumătate de ritm în primele 20 de zile lucrătoare. Aportul expiră la 8 ianuarie 2028."),
                 ("Art. III, mențiuni eligibile","Transfer net de 0% / 25% / 50% din componenta ANAF care ar folosi fluxul comun. Modelul îl aplică numai sarcinii viitoare, din 19 ianuarie."),
                 ("Alternativa digitală","60% din sarcina CAEN suplimentară scoasă din verificarea manuală și +4% capacitate persistentă de la 4 ianuarie. Efectul de pilot rămâne de măsurat."),
                 ("Eșalonare","Același total de muncă pentru valul ulterior de capital. Se schimbă numai datele. Varianta din iulie testează separarea mai strictă de CAEN.")]),
            prose("Datele de pornire sunt convenții pentru test, deoarece proiectul nu era adoptat la data evaluării. Aporturile sunt unități de muncă ale unui dosar-standard. "
                  "Un dosar CAEN, o majorare de capital și o operațiune administrativă pot consuma eforturi diferite. Aproximările reflectă această variație."),
            prose(f"Pentru fiecare din cele 2.000 de trageri, comparăm aceeași cerere nouă depusă la finalul zilei. Testăm și ce s-ar pierde dacă nu s-ar prelungi "
                  f"mandatul conducerii deja desemnate. Lista de ipoteze și testele sunt la {ref('metoda')}.", "Definiție", "<p>Un dosar-standard este o unitate de efort comună scenariilor.</p>")),
        section("efect","În scenariul central, proiectul ajută vizibil. În simulare, așteptarea rămâne de ordinul lunilor după încheierea sprijinului temporar.",
            chart("Figura 2","Timp pentru o cerere nouă","Redistribuirea reduce coada, iar digitalizarea mărește efectul",
                scenarios_figure(),"Liniile sunt medianele scenariilor. Banda marchează percentilele 10–90 pentru OUG cu aport central.",
                "Model zilnic, reprezentat săptămânal. Linia verticală marchează expirarea desemnărilor, care încetează conform proiectului la 8 ianuarie 2028.",
                "Calcule pe 2.000 de trageri, cu aceleași ipoteze de bază pentru fiecare scenariu."),
            tbl("Tabelul 6","Zile calendaristice · mediană [percentile 10–90]",
                ["Scenariu","31 mar. 2027","31 dec. 2027","30 iun. 2028","Vârf¹"],
                [(LABELS[k],*summary_row(d,k,effect_dates)) for k in effects],(1,2,3,4),
                "¹ Mediana maximului zilnic din fiecare tragere. Pe trageri pereche, câștigul median la 30 iunie 2028 este de "
                f"{n(central['median_saved'])} zile pentru aportul central și {n(high['median_saved'])} pentru aportul ridicat."),
            prose("Stocul central din model rămâne mai mic sub proiect decât în referință. El poate crește temporar în ambele scenarii pe durata valurilor. "
                  "O reducere comparativă a cozii poate fi relevantă chiar dacă serviciul rămâne peste pragul operațional.")),
        section("suficienta","Ca să țină reperul de trei zile, proiectul ar avea nevoie de un aport mult mai mare decât cele 100–900 unități pe zi testate.",
            chart("Figura 3","Test de suficiență","Câte simulări respectă cele trei zile la două repere",
                target_figure(g),"Curba verde cere ca aceeași tragere să îndeplinească reperul simultan la sfârșitul lui 2027 și la sfârșitul lui iunie 2028.",
                "Aportul suplimentar este temporar și include creșterea graduală. Transferul net din art. III rămâne la 25%. Verificăm o cerere depusă la închiderea fiecărei date.",
                "Grilă din 50 în 50 de unități pe zi. Proporțiile sunt condiționate de ipotezele modelului."),
            prose(f"Primul punct din grilă la care cel puțin jumătate din trageri îndeplinesc ambele repere este de {n(limit50.units_per_day)} unități nete pe zi "
                  f"({n(limit50.fte_at_25)} echivalente la 25 de unități pe zi). Pentru cel puțin 80% din trageri, primul punct este {n(limit80.units_per_day)} unități "
                  f"({n(limit80.fte_at_25)} echivalente). Sunt praguri condiționate de model, utile pentru a verifica ordinul de mărime al planului de personal."),
            prose(f"În cazul ridicat, cu 900 de unități pe zi și transfer mai mare prin art. III, {percent(endpoint_roug)} dintre trageri ajung la cel mult trei zile "
                  "la 30 iunie 2028. Pentru revenire durabilă contează vârsta stocului și dacă intrările obișnuite încap în capacitatea rămasă după expirare."),
            prose(f"Ca verificare simplă, 204.414 cereri împărțite la {days_for_rate} zile de lucru înseamnă aproximativ {n(204414/days_for_rate)} închideri nete pe zi "
                  "pentru golirea stocului într-un an, înaintea noilor valuri. Egalitatea dintre intrări și ieșiri oprește acumularea și lasă stocul în loc.")),
        section("comparatie","În testul cu același aport de personal, digitalizarea reduce cel mai mult așteptarea. Eșalonarea ajută numai dacă evită suprapunerea cu alte vârfuri.",
            tbl("Tabelul 7","Aceleași 15 echivalente efective și același transfer administrativ",
                ["Măsură","31 mar. 2027","30 iun. 2027","30 iun. 2028","Vârf"],
                [(LABELS[k],*summary_row(d,k,(spring,summer,end,"peak"))) for k in added],(1,2,3,4),
                "Valori în zile calendaristice, mediană [percentile 10–90]. Eșalonarea păstrează același volum de majorări ulterioare."),
            prose(f"Adăugarea digitalizării la cazul central reduce mediana de la {n(central['median'])} la {n(digital['median'])} de zile în iunie 2028. Reducerea provine "
                  "din ipotezele privind verificările CAEN și eficiența portalului. Eligibilitatea ar trebui testată pe reguli clare și cu escaladare la registrator."),
            prose("Mutarea depunerilor de capital mai devreme, din aprilie, poate suprapune o parte a sarcinii cu CAEN. Varianta din iulie testează o fereastră diferită. "
                  "Rezultatele cer programarea concomitentă a celor două fluxuri și actualizarea calendarului după intrările măsurate."),
            prose("Prioritatea pentru dosarele de sediu, raportarea zilnică și monitorizarea calității fac parte din planul nostru. Beneficiile respective nu sunt "
                  "adăugate numeric la curbe. Prioritatea schimbă distribuția așteptării, iar câștigul necesită urmărirea cererilor care rămân în fluxul obișnuit."),
            prose("Lab Edition folosea un sprijin de 12%, de ordinul a 500 de unități pe zi la capacitatea centrală, disponibil integral de la început. "
                  "Aici modelăm 375 după perioada de intrare în ritm și testăm separat art. III. Comparația pentru proiect este între rândurile din același tabel.")),
        section("cost","Calculul bugetar de 5,76 milioane lei se reproduce. Beneficiul cumpărat cu această sumă depinde de orele și capacitatea netă efectiv livrate.",
            tbl("Tabelul 8","Raport strict ilustrativ la suma din nota de fundamentare",
                ["Scenariu","Unități-standard suplimentare disponibile, 2027","Lei / unitate dacă se cheltuie întreaga sumă"],cost_rows,(1,2),
                "480.000 lei/lună × 12 luni. Împărțim aceeași sumă la capacitatea din fiecare scenariu. Rezultatul nu măsoară costul marginal, dosarele efectiv închise ori economiile bugetare."),
            prose(f"Nota atribuie cheltuiala diferențelor salariale legate de art. I și II. Valoarea de {n(public_payroll)} lei pentru 2027 este consistentă aritmetic. "
                  "Secțiunea 4 descrie încadrarea în bugetul aprobat în 2026 și precizează că nu se creează posturi. Pentru un calcul replicabil al cheltuielii trebuie publicate "
                  "numărul de persoane, durata efectivă și diferențele salariale pentru fiecare categorie de funcție."),
            prose("Costurile economice ale unei repartizări includ instruirea, verificările suplimentare și capacitatea retrasă din alte sarcini. Art. III este descris "
                  "fără diferențe salariale de registrator. Adaptarea IT, eventuala nevoie de clarificări și orele echipei care primește cazurile rămân costuri de implementare."),
            prose("Pentru o evaluare fiscală se măsoară separat costul operațional, rezultatele reale și efectele posibile asupra încasărilor. Raportul de impact din Lab Edition "
                  "arată expunerea în scenarii. Înmulțirea acelei expuneri cu zilele din simularea de aici ar confunda stocul, compoziția sa și cazurile eligibile.")),
        section("decizie","Păstrați instrumentul de redistribuire și condiționați extinderea de probe de capacitate pe etape. Completarea proiectului contează mai mult decât extinderea unei autorizări.",
            tbl("Recomandări","Ce se poate cere înainte de adoptare sau în planul de aplicare",
                ["Decizie","Formă de punere în aplicare","Probă la prima evaluare"],
                [("1. Reconciliați cifrele","Definiții și serii pentru intrări, finale, amânări și cereri la fiecare etapă. Precizați trimiterea legislativă și datarea CAEN.",
                  "Cifrele de 4.533 și peste 26.000 au populație, numitor și perioadă verificabile."),
                 ("2. Dimensionați desemnările","Buget de ore nete și repartizare pe tip de cerere. Raport separat pentru conducerea deja desemnată și consilierii nou intrați.",
                  "Crește numărul de finale per oră alocată, fără deteriorarea altor sarcini juridice."),
                 ("3. Delimitați art. III","Matrice act–temei–operator. Publicați data de la care funcționează fluxul și ce se întâmplă la clarificări.",
                  "Timpul net eliberat la registrator și stocul din noua etapă sunt ambele raportate."),
                 ("4. Începeți validările cu risc redus","Pilot pe documente recurente și conversii CAEN cu corespondență clară, cu trimiterea excepțiilor la registrator.",
                  "Se reduc amânările și atingerea manuală fără creșterea erorilor după înscriere."),
                 ("5. Programați valurile și tranziția","Coordonare cu ANAF și publicarea unui calendar al loturilor. Folosiți distribuția intrărilor pentru a separa capitalul de CAEN.",
                  "Stocul vechi scade înainte de expirare, iar planul arată capacitatea disponibilă după 8 ianuarie 2028.")]),
            prose("Reperul managerial de trei zile ajută la prioritizare. Termenul național are reguli proprii, iar pentru constituirea online din sfera directivei contează "
                  f"tipul societății și ceasul de la formalități complete și plata aplicabilă. {ext(LAW265,'Legea nr. 265/2022, art. 105–109')} · {ext(EU,'Directiva (UE) 2019/1151, art. 13g alin. (7)')}.")),
        section("monitorizare","Eficacitatea trebuie măsurată de la data desemnării reale, cu aceleași definiții de volum și calitate înainte și după schimbare.",
            tbl("Monitorizare","Ce trebuie publicat în primele opt săptămâni",["Indicator","Raportare minimă"],
                [("Intrări și sold","Cohorte pe dată, serviciu și etapă. Stoc prelucrat și neprelucrat, cu cazuri în așteptare la solicitant."),
                 ("Muncă disponibilă","Persoane active, ore nete pe rol, instruire și ore retrase din activități concurente."),
                 ("Calitate și viteză","Finale pe tip, mediană și p90 ale cererilor închise, timpii cohortelor și erori confirmate după decizie."),
                 ("Art. III","Numărul de acte eligibile primite și procesate, clarificări, refaceri, intervale între etape."),
                 ("Măsuri digitale","Cereri eligibile, intervenții manuale, validări respinse și erori la verificarea pe eșantion.")]),
            prose("Un test înainte–după pe aceeași săptămână poate confunda desemnarea cu valul cererilor. Introduceți treptat desemnările sau pilotul digital între grupuri "
                  "comparabile și păstrați un grup încă neexpus atunci când operațional este posibil. Măsurați tendințele anterioare, schimbările de mix "
                  "și migrarea cererilor între oficii. Păstrați agregatele și definiți dinainte criteriile de extindere."),
            tbl("Sensibilitate","Contribuția conducerii · termenele actual și propus",
                ["Unități/zi pierdute la expirare","Iunie 2028 fără prelungire","Iunie 2028 cu prelungire","Zile câștigate în perechi"],
                [(n(r.lost_units),n(r.june_2028_without_extension),n(r.june_2028_with_extension),n(r.median_extension_effect))
                 for r in sunset.itertuples()],(0,1,2,3),
                "Medianele sunt în zile calendaristice. În acest test, contribuția dispare după termen în ambele cazuri. Aportul conducerii nu este publicat."),
            prose("Dacă experimentul estimează un câștig mic sau observă migrarea stocului în altă etapă, ajustați repartizarea înainte de a extinde mecanismul. "
                  "Dacă se obține un câștig constant, validați-l pe mențiuni și înmatriculări separat.")),
        section("metoda","Verificările documentare pot fi refăcute din cele două fișiere publicate. Tabelele și simulările pornesc de la aceleași definiții din Lab Edition.",
            tbl("Anexă","Documente primare și reproducere",["Sursă","Ce verifică"],
                [(ext(MJ_DRAFT,"Consultarea publică a Ministerului Justiției"),"Data, statutul de proiect și fișierele publicate."),
                 (ext(DRAFT_DOC,"Proiectul din 18 noiembrie"),"Preambulul și art. I–IV. SHA-256 începe cu 897b10842ce797f4."),
                 (ext(MINISTRY_NOTE["source"],"Nota de fundamentare"),"§2.2–2.3, §3.5, §4.6 și §4.8. SHA-256 începe cu 5c32bd35b4cd091e."),
                 (ext(LAW3,"Parcursul OUG nr. 109/2024 și Legea nr. 3/2026"),"Anterioritatea intervenției și cadrul de prelungire."),
                 (ext(CAEN,"HG nr. 788/2026, Monitorul Oficial"),"Art. I–II pornesc o nouă perioadă de șase luni la intrarea în vigoare la 1 octombrie 2026. În proiectarea valului folosim 1 aprilie 2027, vecinătatea expirării."),
                 (ext(LAW239,"Legea nr. 239/2025"),"Art. VI și VII–VIII, capitalul, dizolvarea și radierea."),
                 (f'<a href="{LAB_REPORT}">Lab Edition, raportul național</a>',"Cadru de comparație. Fișierele locale audit_forecast.py și audit_oug.py reproduc calculele.")]),
            prose("Modelul folosește stocul de muncă rămas după capacitatea fiecărei zile, cu limită inferioară zero. Cererea standard se închide după prima zi în care "
                  "capacitatea cumulată ulterioară acoperă stocul plus o unitate. Benzile sunt percentile ale celor 2.000 de trageri, cu aceleași valori pentru compararea politicilor. "
                  "Prioritățile, productivitatea efectivă a consilierilor și blocajele din alte etape rămân de măsurat."),
            prose("Finalele stricte sunt admise sau respinse din CERERE265 și INMATRIC265, grupate după decizie. Amânările și categoria CERERE_HJ265 sunt separate. "
                  "Validarea retrospectivă folosește numai informația publicată până la fiecare origine. Tabelele efectului, grila și datele grafice se află în "
                  "<code>audit_data/oug_2026</code>.")),
        section("audit-complexitate", "Reconcilierea cifrelor MJ cu BERC, backtesting-ul out-of-sample (MAE 2,55 zile) și analiza muncii-echivalente în minute/zi confirmă că blocajul din 2026 ține de compoziția și volumul cererilor, nu de scăderea vitezei de lucru.",
            tbl("Tabelul 9", "Reconcilierea încrucișată dintre Nota MJ (18.11.2026), Bilanțurile MF (2025) și reconstrucția BERC",
                ["Indicator auditat", "Valoare oficială (MJ/MF)", "BERC / MF reconstruit", "Dif.", "Verdict de audit"],
                [(r.indicator, n(r.official_value, 1), n(r.berc_reconstructed_value, 1),
                  ("+" if r.difference_pct > 0 else "") + n(r.difference_pct, 2) + "%", r.validation_verdict)
                 for r in pd.read_csv(HERE / "audit_data" / "cross_source_reconciliation.csv").itertuples()], (1, 2, 3),
                "Explicație-cheie: «soluționările» din Nota MJ (4.912/zi în sept. și 5.098/zi în oct.) includ atât încheierile finale (Admis+Respins: 3.944/zi și 4.098/zi), cât și încheierile de amânare (AUTO_AMANARI: ~838/zi și ~1.106/zi)."),
            tbl("Tabelul 10", "Evoluția muncii-echivalente (minute/dosar, finale-standard/zi și ore-fereastră active/zi) înainte și după ONRC v2.0",
                ["Epocă operațională", "Finale brute/zi", "% CAEN-only", "Indice compl.", "Min. net / span", "Finale-std./zi", "Ore active/zi (FTE)"],
                [(r.era, n(r.raw_finals_day, 1), n(r.caen_only_share_pct, 1) + "%", n(r.avg_dossier_complexity_idx, 3) + "×",
                  n(r.net_min_per_avg_final, 2) + "m / " + n(r.span_min_per_avg_final, 2) + "m",
                  n(r.equiv_standard_finals_day, 1), n(r.implied_active_span_hours_day, 1) + "h (" + n(r.implied_fte_registrars_at_6_75h, 1) + ")")
                 for r in pd.read_csv(HERE / "audit_data" / "equivalent_work_evolution_v1_vs_v2.csv").itertuples()], (1, 2, 3, 4, 5, 6),
                "Ponderi calibrate pe 68.789 intervale exacte HH:MM:SS Pre-v2.0 (3 iun.–17 iul. 2024: mediană 6,30 min/dosar, medie 11,24 min fereastră / 7,80 min net) vs. 51.033 intervale Post-v2.0 (29 iul.–30 sept. 2024: mediană 14,43 min/dosar, +129% șoc software) și 10.803 finale din 545 buletine PDF din 2026 (18 zile lucrătoare cu acoperire înaltă din 19 oct.–18 nov. 2026, verificate manual pe 20 de buletine cu 100% potrivire)."),
            prose("<strong>Backtesting și Front-Testing (nov.–dec. 2026).</strong> Modelul a fost validat prin cinci teste independente: "
                  "(1) backtest FIFO pe criza lansării v2.0 din iul.–dec. 2024 (<strong>MAE = 1,8 zile</strong>); "
                  "(2) backtest FIFO + 11% culoar rapid pe acumularea iun.–nov. 2026 (<strong>MAE = 2,1 zile</strong>); "
                  "(3) validare în 9 pliuri la 4 săptămâni pe soluționări (<strong>MAPE = 4,61%</strong>); "
                  "(4) test out-of-sample al prognozei înghețate la 28.10.2026 pe cele 15 zile lucrătoare realizate 29.10–18.11.2026 (64.315 finale: <strong>MAE = 2,55 zile</strong> pe cohorte și <strong>2,57 zile / 4,9%</strong> pe zile de decizie; pe 18.11.2026 predicția a fost 58,0 zile vs. 57,9 zile observat); "
                  "(5) predicția falsificabilă pentru decembrie 2026 (<code>front_test_predictions_nov_dec_2026.csv</code>): frontul cozii FIFO termină vârful din 21–30 sept. (~14.620 intrări/zi) în jurul datei de 16–17 dec. 2026 (la ~77 zile mediană CERERE265), după care avansează de 3 ori mai rapid prin cohortele din octombrie (post-HG 788/2026), plafonând așteptarea la 77–81 zile."),
            prose("<strong>Verdictul Eficiență vs. Eficacitate (ONRC v1.0 vs. ONRC v2.0, 16 indicatori în <code>platform_v1_vs_v2_efficiency_effectiveness.csv</code>).</strong> "
                  "La nivel individual, pe dosare substanțiale comparabile (fără tipuri simple), eficiența pe ONRC v2.0 este egală sau ușor inferioară vechii platforme ONRC v1.0 (22,1 vs. 23,1 dosare substanțiale/zi pe 18 zile = 0,96×; 22,0 vs. 22,0 = 1,00× pe panelul pereche n=93; 27,1–29,5 vs. 32,4 dosare non-CAEN/zi = 0,84×–0,91×). Singurul câștig real de eficiență al v2.0 este alocarea națională în rețea (pooling 79% vs. 13%), al cărei efect per registrator nu poate fi identificat din date (estimarea anterioară a fost retrasă), în timp ce +18% vine din creșterea numărului de registratori activi/zi (81 → 95–96,5). "
                  "În schimb, pe <strong>eficacitate</strong> (atingerea scopului legal și calitatea din prima încercare), platforma veche ONRC v1.0 a fost net superioară: 74,9% dosare soluționate în ≤1 zi lucrătoare pe v1.0 (față de 35,7% pe v2.0 stabil, 1,1% după 27 apr. 2026 și 0,7% în criză), 90,3% înmatriculări în ≤5 zile lucrătoare UE pe v1.0 (față de 75,5% pe v2.0 stabil și 5,9% în criză), creșterea ratei respingerilor de la 5,7% (v1.0) la 7,8%–8,2% (v2.0) din lipsa validărilor automate la depunere, 0% reducere a ratei amânărilor (~20,4%) și 0,0% automatizare a celor 641.209 cereri CAEN Rev. 3."),
            tbl("Tabelul 11", "Audit Adversarial de Foolproofing (W1–W10) &amp; Teoreme Verificate Formal în Lean 4 (v4.16.0)",
                ["ID", "Punct slab auditat", "Teoremă Lean 4", "Test de stres &amp; Verdict"],
                [(html.escape(str(r.id)), html.escape(str(r.weakness_attack)), html.escape(str(r.formal_proof_theorem)),
                  html.escape(str(r.stress_test_result)) + " — <b>" + html.escape(str(r.verdict_robustness)) + "</b>")
                 for r in pd.read_csv(HERE / "audit_data" / "foolproofing_red_team_matrix.csv").itertuples()], (),
                "24 de teoreme (11 familii) compilate integral fără sorry (0 sorryAx) în formal_proofs/OnrcProofs.", split=True),
            tbl("Tabelul 12", "Model Predictiv pe Două Niveluri: Backtest 5 Regimuri &amp; Test Live 18–20.11.2026",
                ["Regim / Zi test", "N", "MAE Naiv / Monolitic", "MAE Nivel 2 / Cuplat CER", "MAE Zilnic ÎNM / Cuplat ÎNM"],
                [(html.escape(str(r.fold)), n(r.n_test_eval), n(r.naive_lag_mae_d, 2) + " z",
                  n(r.dossier_p50_mae_d, 2) + " z (Câștig " + n(r.skill_vs_naive_pct, 1) + "%)",
                  n(r.daily_inmatric_med_mae_d, 2) + " z")
                 for r in pd.read_csv(HERE / "audit_data" / "predictive_model_backtest_summary.csv").itertuples()]
                + [(html.escape(str(r.decision_day)) + " (Live)", n(r.n_obs_total),
                    "CER " + n(r.pred_mono_cerere_d, 1) + "z / ÎNM " + n(r.pred_mono_inmatric_d, 1) + "z",
                    "Obs " + n(r.obs_cerere_med_d, 1) + "z vs. " + n(r.pred_coupled_cerere_d, 1) + "z",
                    "Obs " + n(r.obs_inmatric_med_d, 1) + "z vs. " + n(r.pred_coupled_inmatric_d, 1) + "z")
                   for r in pd.read_csv(HERE / "audit_data" / "predictive_model_live_nov18_20.csv").itertuples()], [1],
                "Sursă: predictive_model_backtest_summary.csv & predictive_model_live_nov18_20.csv (4.077.510 decizii până la 21.11.2026).", split=True))
    ])
    return "\n".join(pages)


CSS = """
@page { @top-left { content: "ONRC · EVALUAREA PROIECTULUI DE ORDONANȚĂ"; }
 @bottom-left { content: "Analiză independentă · Ștefan-Lucian Deleanu · stefandeleanu.ro"; } }
@page front { @top-right { content: "Cuprins"; } }
@page note { @top-right { content: "Proiectul din 18 noiembrie 2026"; } }
.brief-page .copen { padding: 2mm 0 3mm; margin-bottom: 3mm; }
.brief-page .copen h2 { font-size: 25pt; }
.brief-page .takeaway { margin-bottom: 3.5mm; }
.brief-page .tbl-wrap { margin: 3.2mm 0 4mm; }
.brief-page td, .brief-page th { padding: 1.35mm 1.5mm; }
.brief-page code { font-size: .85em; }
.brief-page p { orphans: 2; widows: 2; }
.brief-page .prose p { margin-bottom: .62em; }
"""


def document(source):
    return f"""<!doctype html><html lang="ro"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Evaluarea proiectului OUG ONRC · 18 noiembrie 2026 · Lab Edition</title>
    <style>{embedded_fonts()}\n{BASE_CSS}\n{REFINEMENTS}\n{CSS}</style></head><body>{source}</body></html>"""


def build(qa_dir=None):
    source = body()
    destinations = set(INTERNAL_LINK.findall(source))
    with tempfile.TemporaryDirectory(prefix="onrc-oug-review-") as stage:
        html = Path(stage) / (STEM + ".html")
        pdf = html.with_suffix(".pdf")
        html.write_text(document(PAGE_REF.sub("00",source)),encoding="utf-8")
        compile_pdf(html,pdf)
        count, targets = read_targets(pdf,destinations)
        assert count >= 17, (count,targets)
        final = document(PAGE_REF.sub(lambda m: str(targets[m[1]]),source))
        html.write_text(final,encoding="utf-8")
        compile_pdf(html,pdf)
        assert read_targets(pdf,destinations)==(count,targets)
        with fitz.open(pdf) as doc:
            for i,p in enumerate(doc):
                if i:
                    text = p.get_text().splitlines()
                    assert str(i+1) in text[:5],(i+1,text[:5])
                    assert len(text)>18,(i+1,text)
                if qa_dir:
                    qa_dir.mkdir(exist_ok=True,parents=True)
                    p.get_pixmap(dpi=115).save(qa_dir / f"p{i+1:02d}.png")
        (HERE / pdf.name).write_bytes(pdf.read_bytes())
        (HERE / html.name).write_text(final,encoding="utf-8")
        print(f"Evaluare verificată: {count} pagini, {len(targets)} destinații", targets)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-dir",type=Path)
    build(parser.parse_args().qa_dir)
