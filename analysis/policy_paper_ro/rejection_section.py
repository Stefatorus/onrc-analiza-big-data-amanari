"""Secțiunea 6.5 «De ce se resping dosarele» pentru capitolul 6 din build_raport_institutii.py, plus câte un punct
pentru fișele pe profil (Volumul 0). Același tipar ca postponement_section.py.

    import rejection_section as RSEC
    b += RSEC.section_html(V, E, hl, P, fig)        # în ch6(), după secțiunea 6.4
    RSEC.short_item(V, E, hl, "it" | "onrc")

Fiecare cifră vine din registru prin V('Cxx') (C144–C151, plus C139 și C03 pentru comparație) și e citată cu E('Cxx').
Afirmațiile le inserează independent_audit/rejection_reasons/patch_claims.py din out/rejection_reasons.json.
Figura i10 o face generate_postponement_figures.py (o copiază și în figures_institutii/).
Scris cu ajutorul AI (Claude Opus 5.5), sub îndrumarea autorului.
"""
from __future__ import annotations

ID = dict(after_post="C144", unfulfilled="C145", outcomes="C146", causes="C147", types="C148", overlap="C149", avoidable="C150", coverage="C151")
POST_AVOID = "C139"          # postponements avoidable at filing (section 6.4)


def _first(v):
    return v.split(" (")[0]


def _parts(V):
    ap = V(ID["after_post"]).split(" · ")
    share = _first(ap[0]); med = ap[2].split("mediana: ")[1].split(" zile")[0]
    uf = _first(V(ID["unfulfilled"]))
    oc = V(ID["outcomes"]).split(" / "); rej = oc[0].split(" ")[0]; adm = oc[1].split(" ")[0]
    causes = {}
    for x in V(ID["causes"]).split(" · "):
        name, rest = x.rsplit(" ", 2)[0], x.rsplit(" ", 2)[1]
        causes[name] = rest
    ty = V(ID["types"]).split(" · "); reg = ty[0].split("fiscal ")[1].split(" (")[0]; amd = ty[1].split("CAEN ")[1].split(" (")[0]
    ov = V(ID["overlap"]); ov_any = ov.split(" ")[0]; ov_n = ov.split("n=")[1].rstrip(")")
    av = V(ID["avoidable"]).split(" · "); a_s, a_a = av[0], av[1]
    cov = V(ID["coverage"]); n_txt = cov.split(" (")[0]; cov_sh = cov.split("(")[1].split(" din")[0]
    pav = V(POST_AVOID).split(" · "); p_s, p_a = _first(pav[0]), _first(pav[1])
    return dict(share=share, med=med, uf=uf, rej=rej, adm=adm, causes=causes, reg=reg, amd=amd, ov_any=ov_any, ov_n=ov_n,
                a_s=a_s, a_a=a_a, n_txt=n_txt, cov_sh=cov_sh, p_s=p_s, p_a=p_a)


def section_html(V, E, hl, P, fig):
    p = _parts(V); c = p["causes"]
    b = '<h3>6.5 De ce se resping dosarele</h3>'
    b += P(hl("Respingerea este, aproape mereu, capătul unei amânări neîndeplinite.") + " În toată arhiva, " + p["share"] +
           " din respingerile din 19 octombrie–18 noiembrie 2026 au fost precedate de o amânare a aceleiași cereri. Respingerea a venit, la mijloc, la " + p["med"] +
           " zile după amânare, adică imediat după expirarea termenului de completare." + E(ID["after_post"]) +
           " În textul încheierilor, " + p["uf"] + " din respingeri spun explicit că lipsurile cerute la amânare nu au fost remediate sau au fost remediate doar parțial." + E(ID["unfulfilled"]),
           "Cum am măsurat", "Legătura cu amânarea vine din toată arhiva BERC, nu dintr-un eșantion. Motivele le-am citit în " + p["n_txt"] + " de încheieri de respingere publicate integral (" + p["cov_sh"] +
           " din respingerile din perioadă), cu aceeași metodă ca la amânări." + E(ID["coverage"]))
    b += P("Privit din partea cealaltă: " + hl("dintre cererile amânate în 1 septembrie–15 octombrie 2026 și soluționate până la 20 noiembrie, " + p["rej"] + " au fost respinse și " + p["adm"] + " admise.") +
           E(ID["outcomes"]) + " Peste o treime din amânări se încheie, deci, cu o respingere, iar firma depune de obicei o cerere nouă (secțiunea 6.3).",
           "Ce NU înseamnă", "Nu arată că registratorii resping prea ușor. Arată că lipsurile semnalate la amânare rămân, des, nerezolvate în termenul de completare.")
    b += P(hl("Cauzele sunt aceleași ca la amânări: obiectul de activitate și codurile CAEN (" + c["CAEN / declarația de autorizare"] + " din respingeri), sediul (" + c["sediu"] +
              ") și datele de identificare ale asociaților (" + c["date de identificare"] + ").") + E(ID["causes"]) +
           " La înmatriculări domină cazierul fiscal și avizele altor instituții (" + p["reg"] + "), la modificări codurile CAEN (" + p["amd"] + ")." + E(ID["types"]) +
           " În " + p["ov_n"] + " de cazuri în care am găsit și încheierea de amânare, respingerea reia cel puțin o cauză a amânării în " + p["ov_any"] + " din cazuri; eșantionul e mic." + E(ID["overlap"]),
           "Rezervă", "Ponderile cauzelor vin dintr-un eșantion de 150 de respingeri etichetat manual de un model AI, fără al doilea codificator; clasificarea automată le subestimează. "
           "Comparația pe tipuri vine din clasificarea automată; la înmatriculări eșantionul e mic, deci contează direcția, nu valoarea exactă." + E(ID["causes"], ID["types"]))
    b += P(hl("Pe eșantionul verificat, circa " + _first(p["a_s"]) + " din respingeri aveau numai cauze pe care o verificare la depunere le-ar fi prins, iar circa " + _first(p["a_a"]) + ", cel puțin una.") +
           E(ID["avoidable"]) + " Ponderile sunt apropiate de cele ale amânărilor (" + p["p_s"] + " și " + p["p_a"] + ")." + E(POST_AVOID) + " " +
           hl("De aceea, verificările la depunere din tabelul 6.1 previn și respingerile: o amânare evitată nu mai poate deveni o respingere."),
           "De ce contează", "Fiecare respingere evitată scutește o a doua analiză a dosarului și, de obicei, o cerere nouă care ar intra din nou în ambele cozi.", key=True)
    b += fig("FIGURA 6.3", "RESPINGERI ȘI AMÂNĂRI · ARHIVA BERC ȘI BULETINE PDF · 2026", "Respingerea vine după o amânare neîndeplinită, la expirarea termenului de completare",
             "i10_motive_respingere.svg",
             "Trei măsurători: câte respingeri au avut o amânare înainte, ce spune textul încheierii de respingere și cum se termină cererile amânate.",
             "Fiecare bară însumează 100%. Roșu: respingere sau lipsuri nerezolvate; ocru: rezolvate parțial; verde: admise; gri deschis: restul.",
             "Respingerea nu e un al doilea control, separat: e de obicei aceeași lipsă, găsită la amânare și nerezolvată în termen.",
             "Nu spune că fiecare respingere era evitabilă și nici că termenul de completare e prea scurt; datele nu arată de ce lipsa nu a fost rezolvată.",
             [ID["after_post"], ID["unfulfilled"], ID["outcomes"]])
    return b


def short_item(V, E, hl, profile="it"):
    p = _parts(V)
    if profile == "it":
        return hl("Aproape toate respingerile (" + p["share"] + ") vin după o amânare neîndeplinită, din aceleași cauze: aceleași verificări la depunere le previn pe amândouă.") + E(ID["after_post"], ID["overlap"])
    return hl("Aproape toate respingerile (" + p["share"] + ") vin după o amânare a aceleiași cereri, la expirarea termenului de completare; din cererile amânate, " + p["rej"] + " sunt respinse.") + E(ID["after_post"], ID["outcomes"])
