# Sarcina: replicare independentă

Ești un analist independent. Ai primit DOAR conținutul acestui folder:
- `date/berc_decizii.pkl` — arhiva deciziilor BERC (pandas pickle; coloane: cat, app_nr, app, res, pub, county, sol, office, code4, jtype).
- `date/portal/harvest_*.jsonl` — eșantionul recoltat din portalul myportal.onrc.ro (un obiect JSON pe linie; fără nume, CNP, date de contact sau identificatori ai cererilor).
- `date/cifre_oficiale_MJ.md` — cifrele oficiale ale Ministerului Justiției.
- `date/compilatie_presa_2026-11-21.md` — afirmații din presă despre coadă.
- `raport/Raport_ONRC_Coada_2026-11_COMPLET.pdf` — raportul de verificat.

Reguli: nu citi niciun fișier din afara acestui folder. Scrie doar în `lucru/`. Refă singur analizele, cu codul tău, din datele brute.
Verifică independent cifrele-cheie ale raportului și spune, pentru fiecare: CONFIRMAT / DIFERIT (cu valoarea ta și explicația) / NEVERIFICABIL.
