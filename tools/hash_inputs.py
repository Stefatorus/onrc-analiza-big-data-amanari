"""Refresh analysis/raport_executiv_2026-11/data_hashes.json from the local inputs.

The claims registry stamps each claim with the SHA-256 of the data it rests on:
  BERC   = SHA-256 of data/analysis_decisions.pkl
  PORTAL = SHA-256 of the concatenation of the myportal harvest_*.jsonl files in sorted-name order.
The myportal sample is not published (row level), so without it the committed PORTAL value is kept and marked "frozen":
it refers to the author's raw harvest (9 files) and cannot be re-verified by third parties.

  python -X utf8 tools/hash_inputs.py
"""
from __future__ import annotations
import datetime as dt, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import config  # noqa: E402

DH = REPO / "analysis" / "raport_executiv_2026-11" / "data_hashes.json"


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    old = json.loads(DH.read_text(encoding="utf-8")) if DH.exists() else {}
    out = dict(old)
    p = config.BERC_PKL
    out["BERC_analysis_decisions.pkl"] = dict(sha256=sha_file(p), bytes=p.stat().st_size,
                                              mtime=dt.date.fromtimestamp(p.stat().st_mtime).isoformat())
    files = sorted(config.PORTAL_DIR.glob("harvest_*.jsonl"))
    if files:
        h = hashlib.sha256()
        for f in files:
            h.update(f.read_bytes())
        out["portal_harvest_all"] = dict(sha256=h.hexdigest(), files=len(files))
    else:
        out["portal_harvest_all"] = dict(old.get("portal_harvest_all", {}), frozen=True)
    lc = REPO / "independent_audit" / "out" / "LOCKED_CONSTANTS.json"
    if lc.exists():
        out["LOCKED_CONSTANTS.json"] = dict(sha256=sha_file(lc))
    DH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
