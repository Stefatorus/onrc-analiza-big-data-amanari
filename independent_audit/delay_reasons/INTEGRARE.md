# Integrarea secțiunii „6.4 Analiza amânărilor” în raport

> **Notă AI:** pași scriși cu ajutorul inteligenței artificiale (Claude Opus 5.5), sub îndrumarea autorului.

Se rulează **după** ce celălalt agent a terminat builderele. Nimic din pașii de mai jos nu a fost aplicat încă.
Toate comenzile: `S:\Projects\SOLOResearch\venv\Scripts\python.exe -X utf8` (prescurtat `PY`). Nu instalați nimic în venv.

## Fișiere noi (gata)

| fișier | rol |
|---|---|
| `independent_audit/delay_reasons/08_solutions.py` | generează `out/postponement_solutions.json` (matrice + cadru legal + `claim_ids`) din `out/delay_reasons.json` și `out/stat_pack_ext.json` |
| `independent_audit/out/postponement_solutions.json` | matricea de soluții, efectele, citările legale; `claim_ids` = sursa unică a id-urilor |
| `independent_audit/delay_reasons/patch_claims.py` | inserează afirmațiile C126–C143 în `generate_claims_registry.py` (înainte de `def main():`) |
| `independent_audit/delay_reasons/SOLUTII.md` | versiunea lizibilă (română), cu anexa AI |
| `analysis/policy_paper_ro/generate_postponement_figures.py` | figurile `i08_motive_amanare` și `i09_evitabil_la_depunere` în `figures_impact/`, cu copie SVG în `figures_institutii/` |
| `analysis/policy_paper_ro/postponement_section.py` | `section_html(V, E, hl, P, fig)` și `short_items(V, E, hl, profile)` |

## Pași

### 0. Verificați că id-urile sunt libere

```
cd S:\Projects\SOLOResearch\independent_audit\delay_reasons
PY patch_claims.py --check
```
Dacă raportează coliziuni (celălalt agent a adăugat C126+): schimbați `CLAIM_IDS` în `08_solutions.py` (o singură editare), apoi `PY 08_solutions.py`. Secțiunea și patch-ul citesc id-urile din JSON.

### 1. Regenerați intrările (doar dacă s-a schimbat `delay_reasons.json` sau `stat_pack_ext.json`)

```
PY 08_solutions.py
cd ..\..\analysis\policy_paper_ro
PY generate_postponement_figures.py
```

### 2. Aplicați patch-ul registrului și regenerați registrul

```
cd S:\Projects\SOLOResearch\independent_audit
PY delay_reasons\patch_claims.py
PY generate_claims_registry.py
```
Așteptat: `+18 claims`, apoi registrul cu 18 afirmații în plus (proba pe copie: 141 = 123 + 18; 71 PASS, 62 WARN, 8 FAIL).
Patch-ul e idempotent (refuză a doua aplicare) și oprește importul dacă vreun id e deja folosit.

### 3. Capitolul 6 din `analysis/policy_paper_ro/build_raport_institutii.py`

a) La importuri (după `import methodology`, linia ~14):
```python
import postponement_section as PSEC
```
b) În `ch6()`, **înainte** de linia `b += concl("Amânările și respingerile înseamnă …")` (linia ~477), după secțiunea 6.3:
```python
    b += PSEC.section_html(V, E, hl, P, fig)
```
c) Opțional, în același `ch6()`:
- `idea(...)`: se poate adăuga „Circa o cincime din amânări se pot preveni cu verificări la depunere.” + `E('C139')`;
- `concl(...)`: propoziția „Erorile prinse înainte de depunere ar scurta drumul fiecărui dosar.” are acum o cifră în 6.4; se poate lăsa;
- `chapter(6, …, "Surse: BERC 2023–2026 · Legea 265/2022 art. 106")` → adăugați „· buletine PDF (motivele amânărilor)”.

Figura e „FIGURA 6.2”, tabelul „Tabelul 6.1”; capitolul 6 nu are alte tabele. `fig()` citește SVG-ul din `figures_institutii/` (copiat de pasul 1). Nu dați `fig()` o cale absolută: prefixul id-urilor SVG se face din numele fișierului.

### 4. Fișele pe profil (Volumul 0), `analysis/policy_paper_ro/volumes_extra.py`

La importuri: `import postponement_section as PSEC`.

- **Fișa „2” (Pentru conducerea ONRC)**, lista „Ce trebuie să știți” (linia ~66–68): adăugați la sfârșitul listei `*PSEC.short_items(V, E, hl, "onrc")[:2]`.
- **Fișa „3” (Pentru echipa IT)**, lista „Ce trebuie să știți” (linia ~78–80): adăugați `*PSEC.short_items(V, E, hl, "it")[:2]`.
- Fișele sunt de o pagină: luați 2 puncte (`[:2]`); al treilea doar dacă pagina încape.
- **Text devenit inexact, linia 46** (tabelul IT, rândul 2, coloana „Depinde de”): „Lista motivelor de amânare, pe frecvență (doar ONRC o are)” → de exemplu „Lista motivelor de amânare, pe frecvență (secțiunea 6.4)” + `E("C139")`. Coloana „Cum verificăm”: se poate adăuga „circa 230 de amânări pe zi mai puțin, ca plafon” + `E("C141")`.
- Rândul „Semnalarea lipsurilor la depunere” din fișa 2 (linia ~71) poate primi `E("C139")`.

`volumes_extra.py` folosește `V, E, hl` din `build_volume_stat` (aceleași semnături), deci `short_items` merge direct.

### 5. Opțional

- Volumul 4, secțiunea 4 („Amânările: analiză care nu se vede”, `volumes_extra.py` linia ~196): propoziția „Cele mai multe amânări pornesc de la acte lipsă la depunere.” poate fi precizată cu `PSEC.short_items(V, E, hl, "onrc")[0]`.
- `ai_annex.py`, linia 51 (lista de date cerute de la ONRC): „motivele amânărilor” → „motivele amânărilor, codificate (azi sunt doar text liber în buletin)”.
- Rotunjire: ponderea „date de identificare asociați” e 10,9% în registru (0,1095), dar 11,0% în `README.md`; în raport contează valoarea din registru.
- Ediția executivă (`main_exec`) și Volumul 7 (`impact_economic.py`) nu sunt atinse.
- **Model de cost:** `preventable_post_share` (canalul D, `cost_founded.py`) e azi o ipoteză 8/15/25%, „fără bază în date publice”; măsurarea dă 22,9% (21,5–24,3). Actualizarea schimbă C106–C113, deci e o decizie separată.

### 6. Reconstrucție și verificare

```
cd S:\Projects\SOLOResearch\analysis\policy_paper_ro
PY build_all_volumes.py
```
(construiește raportul principal, ediția executivă și volumele 0–6, apoi rulează `lint_numbers.py` pe HTML-uri). Sau separat:
```
PY build_raport_institutii.py
PY build_volume_stat.py --vol0
PY ..\raport_executiv_2026-11\lint_numbers.py Raport_ONRC_Coada_2026-11.html
PY ..\raport_executiv_2026-11\lint_numbers.py Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil.html
```
Verificați vizual în PDF: tabelul 6.1 nu iese din pagină (are stil propriu, `table-layout: fixed`, în `<style>` din secțiune), iar Edge nu micșorează paginile (vezi capcana „shrink-to-fit” din memorie).

## Ce s-a verificat deja (probă pe copie, 22.11.2026)

- `patch_claims.py` aplicat pe o copie a `generate_claims_registry.py` (cu `HERE` fixat pe folderul real și ieșirea redirecționată în scratch): rulează, scrie 141 de afirmații; C126–C143 au valorile așteptate (de ex. C127 `31,7% (IC 95%: 30,0–33,4%)`, C141 `≈230 (220–250) evitate · ≈460 … din 1.012 amânări / zi`).
- `claims_registry.csv` și `generate_claims_registry.py` reale: amprente SHA-256 identice înainte și după.
- Secțiunea randată singură din registrul de probă, cu `BASE_CSS`: `lint_numbers.py` → **LINT PASS**; tipărită cu Edge: tabelul încape pe lățimea paginii.
- **Calea reală de integrare** (pasul 3): `build_raport_institutii` importat, `REG` înlocuit cu registrul de probă, `PSEC.section_html(B.V, B.E, B.hl, B.P, B.fig)` inserat înainte de `concl` în `ch6()`, pagina tipărită cu `BASE_CSS + running_css() + EXTRA_CSS`: **LINT PASS**; A4, fără micșorare. Capitolul 6 trece de la 2 la 5 pagini: secțiunea are circa 3 pagini, din care tabelul 6.1 ocupă o pagină întreagă. Dacă trebuie scurtată: tabelul se poate muta într-o anexă (rămâne figura), sau se pot scurta coloanele „Soluție” și „Cadrul legal”.
- `generate_postponement_figures.py` a scris deja `i08_motive_amanare.svg` și `i09_evitabil_la_depunere.svg` și în `figures_institutii/` (fișiere noi; niciun fișier existent modificat).
- Proba independentă se poate repeta oricând: `PY postponement_section.py <claims_registry.csv> <out.html>`.
