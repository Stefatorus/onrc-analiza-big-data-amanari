"""OUG (emergency ordinance) scenario analysis on the locked two-stage model.

The 18-Nov-2026 draft OUG delegates legal staff as temporary registrators (more Stage-2
capacity) and lets them skip repeating legality controls. The decisive question (Lean T13c,
'cannibalisation'): if the delegated staff are TAKEN FROM operare (Stage 1), does total
output fall? We test it on the LOCKED numbers and write out/oug_scenarios.json.

All inputs from LOCKED_CONSTANTS.json — nothing re-derived here.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent / "out"
L = json.loads((OUT / "LOCKED_CONSTANTS.json").read_text(encoding="utf-8"))

# --- locked anchors ---
C2 = L["throughput_finals_per_day"]          # 4,176 Stage-2 finals/day (measured)
FPD_REG = L["files_per_day_per_registrator_finals"]   # ~25 files/day/registrator
REG = L["registrators"]                      # 165
BACKLOG = L["backlog_total_report"]          # 210,000
SPLIT1 = L["backlog_split_stage1"]           # 0.485
# operare (Stage 1) is faster per person than soluționare; conservative ratio from portal
OP_FPD = 45                                  # operator throughput/day (operare is lighter than judging)
C1 = C2 * 1.15                               # Stage-1 capacity a bit above Stage-2 (portal: S1 drains)
# forward demand: remaining CAEN+Law239 overhang bunched before 1 Apr 2027 (procrastination)
HORIZON_WD = 85                              # working days 24 Nov 2026 -> 1 Apr 2027
BASE_ARR = C2                                # steady-state judged arrivals ≈ finals rate
OVERHANG = (500_000, 900_000)                # remaining filings range (report sec.3)


def project(extra_reg_net=0, reg_from_operare=0, automation=0.0, bypass=0.0,
            overtime=0.0, deadline_wd=HORIZON_WD, overhang=700_000):
    """Return (backlog_end, stage1_end, stage2_end) after the horizon.
    extra_reg_net: delegated registrators that are NET NEW staff.
    reg_from_operare: delegated registrators TAKEN FROM operare (cannibalisation).
    automation: fraction of overhang removed (1-to-1 CAEN auto-converted).
    bypass: fraction of Stage-1 load removed (online skips re-operation).
    overtime: temporary capacity multiplier.
    """
    s1 = BACKLOG * SPLIT1
    s2 = BACKLOG * (1 - SPLIT1)
    # capacities with levers
    c2 = (C2 + (extra_reg_net + reg_from_operare) * FPD_REG) * (1 + overtime)
    c1 = (C1 - reg_from_operare * OP_FPD) * (1 + overtime) * (1 + bypass)
    c1 = max(c1, 0)
    # arrivals over horizon: baseline + overhang bunched toward the deadline (procrastination,
    # most mass in the final third) minus automation
    oh = overhang * (1 - automation)
    arr = np.full(deadline_wd, BASE_ARR, float)
    w = np.exp(np.linspace(0, 2.2, deadline_wd)); w /= w.sum()   # procrastination weight
    arr += oh * w
    for t in range(deadline_wd):
        operated = min(s1 + arr[t], c1)       # Stage 1 out
        s1 = s1 + arr[t] - operated
        solved = min(s2 + operated, c2)       # Stage 2 out
        s2 = s2 + operated - solved
    return s1 + s2, s1, s2


def band(**kw):
    los = project(overhang=OVERHANG[0], **kw)
    his = project(overhang=OVERHANG[1], **kw)
    return los[0], his[0]


def main():
    scen = []
    def add(key, label, note, **kw):
        lo, hi = band(**kw)
        scen.append(dict(key=key, label=label, note=note,
                         backlog_lo=round(lo), backlog_hi=round(hi)))
    add("S0", "Fără măsuri (status quo)", "Coada crește necontrolat până la termen.")
    add("OUG_net", "OUG: +50 registratori NOI", "Personal net nou la etapa 2 — nu golește operarea.",
        extra_reg_net=50)
    add("OUG_cann", "OUG: +50 LUAȚI din operare", "Dacă delegații vin din operare, prima coadă se adâncește.",
        reg_from_operare=50)
    add("OUG_big", "OUG: +100 registratori NOI", "Capacitate mare nouă la etapa 2.", extra_reg_net=100)
    add("AUTO", "Automatizare CAEN 1-la-1 (−60%)", "Scoate dosarele simple din ambele cozi.",
        automation=0.60)
    add("DEADLINE", "Doar prelungire termen (+3 luni)", "Mută vârful, nu-l elimină.",
        deadline_wd=HORIZON_WD + 63)
    add("COMBO", "Combinat: +100 noi + automatizare + IT", "Singura care normalizează coada.",
        extra_reg_net=100, automation=0.60, bypass=0.5, overtime=0.15)
    # cannibalisation sweep: net output vs how many delegated come from operare
    sweep = []
    for frm in range(0, 81, 10):
        lo, hi = band(extra_reg_net=50 - 0, reg_from_operare=frm)
        sweep.append(dict(from_operare=frm, backlog_mid=round((lo + hi) / 2)))
    out = {"anchors": {"C2": C2, "C1": round(C1), "FPD_REG": FPD_REG, "REG": REG,
                       "OP_FPD": OP_FPD, "backlog": BACKLOG, "horizon_wd": HORIZON_WD},
           "scenarios": scen, "cannibalisation_sweep": sweep}
    (OUT / "oug_scenarios.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    print("=== OUG SCENARIOS (backlog at 1 Apr 2027, range over overhang 500k-900k) ===")
    for s in scen:
        print(f"  {s['label']:34} {s['backlog_lo']/1000:>5.0f}k - {s['backlog_hi']/1000:<5.0f}k   {s['note']}")
    print("\n=== CANNIBALISATION: delegated registrators taken FROM operare ===")
    for s in sweep:
        print(f"  {s['from_operare']:>2} from operare -> backlog ~{s['backlog_mid']/1000:.0f}k")
    print(f"\nwrote {OUT/'oug_scenarios.json'}")


if __name__ == "__main__":
    main()
