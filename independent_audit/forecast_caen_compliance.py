"""Scenariu de conformare CAEN, constrâns de sursele publice, pe motorul de prognoză verificat (audit_forecast.py), nemodificat.

Motorul presupune un val CAEN suplimentar de 140–390 mii de cereri (mod 245 mii), ian.–apr. 2027. Nota MJ dă
902.243 de cereri CAEN încă așteptate, iar presa 62,76% din firme rămase. Aici înlocuim mărimea valului cu 50% / 80% / 100%
din 902.243 (aceeași formă în timp, același efort pe dosar, aceleași 2.000 de variante) și raportăm iunie 2027, vârful
și iunie 2028, fără măsuri noi.
Gărzi: varianta „motor” reproduce 74 / 136 / 214,1 în iunie 2028; audit_data/ rămâne neschimbat.

Run:  ..\\venv\\Scripts\\python.exe -X utf8 forecast_caen_compliance.py   -> out/forecast_caen_compliance.json
"""
from __future__ import annotations
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PP = HERE.parent / "analysis" / "policy_paper_ro"
sys.path.insert(0, str(PP))
import audit_forecast as AF  # noqa: E402

MJ_CAEN = AF.MINISTRY_NOTE["caen_remaining_expected"]          # 902.243
SHARES = [None, 0.5, 0.8, 1.0]                                   # None = engine's own assumption
AUTO = 0.75   # share of CAEN filings removed by automatic 1-to-1 conversion (same assumption as audited package P4)


def tree_hash(d: Path) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("*")) if p.is_file()}


def q(v): return [float(x) for x in np.percentile(v, [10, 50, 90])]


def main():
    before = tree_hash(AF.OUT)
    m = AF.prepare_workload()
    assert tree_hash(AF.OUT) == before, "audit_data changed"
    dates, opening = m["dates"], m["opening"]
    n = len(dates); june28 = n - 1
    june27 = int(np.searchsorted(dates.values, np.datetime64("2027-06-30")))
    wave = m["params"]["dosare_caen_suplimentare"].to_numpy()[:, None]
    base_other = m["ordinary"] + m["late"]
    out = dict(_meta="Valul CAEN scalat la o pondere din cele 902.243 de cereri CAEN rămase (nota MJ), pe motorul verificat, fără măsuri noi. "
                     "Forma în timp (ian.–apr. 2027) și efortul pe dosar rămân cele ale motorului.",
               mj_caen_remaining=MJ_CAEN, engine_wave_p10_p50_p90=q(wave[:, 0]), scenarios=[])
    after = (dates >= "2027-01-04")[None, :]
    for sh, auto in [(x, 0.0) for x in SHARES] + [(0.5, AUTO), (0.8, AUTO), (1.0, AUTO)]:
        caen = m["caen"] if sh is None else m["caen"] * (sh * MJ_CAEN / wave)
        caen = caen * (1 - auto * after)
        stock, cal, _ = AF.simulate(m["initial"], base_other + caen, m["capacity"], opening)
        r = dict(pondere=("motor (140–390 mii)" if sh is None else sh), automatizare_caen=auto, val_cereri=(None if sh is None else round(sh * MJ_CAEN)),
                 iun2027=q(cal[:, june27]), varf=q(cal.max(axis=1)), iun2028=q(cal[:, june28]),
                 stoc_iun2028_p50=float(np.median(stock[:, june28])))
        if sh is None:
            assert [round(r["iun2028"][0]), round(r["iun2028"][1]), round(r["iun2028"][2], 1)] == [74, 136, 214.1], r["iun2028"]
        out["scenarios"].append(r)
        print(f"{str(r['pondere']) + (' +auto75' if auto else ''):22} iun.2027 {r['iun2027'][1]:6.0f} ({r['iun2027'][0]:.0f}–{r['iun2027'][2]:.0f})  vârf {r['varf'][1]:6.0f}  iun.2028 {r['iun2028'][1]:6.0f} ({r['iun2028'][0]:.0f}–{r['iun2028'][2]:.0f})")
    (HERE / "out" / "forecast_caen_compliance.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
