"""Single place for every machine-specific path (PROPOSED, phase 1 draft).

Every pipeline script imports from here instead of hard-coding W:\\, S:\\, C:\\Users\\... paths.
run_all.py puts the repository root on PYTHONPATH, so `from config import BERC_PKL` works from any sub-folder.

Two kinds of locations:
  * READ-ONLY raw inputs. They may live anywhere (e.g. an external drive) and are set by env vars:
      ONRC_ARTICLES_DIR   BERC article JSON, <YYYY>/<date>_<CAT>.json        (default <repo>/data/berc_articles)
      ONRC_LEGACY_DIRS    ';'-separated legacy per-dossier crawl folders     (default <repo>/data/berc_counties*)
      ONRC_BULLETINS_DIR  BERC bulletin PDFs for 2026                         (default <repo>/data/bulletins/2026)
      ONRC_PORTAL_DIR     myportal sample (see PLAN.md, option A/B)           (default <repo>/data/portal)
  * WRITABLE derived data. ALWAYS inside the repository (<repo>/data/...), so a run can never overwrite the
    reference copies the published registry fingerprints (e.g. the author's analysis_decisions.pkl):
      BERC_PKL   <repo>/data/analysis_decisions.pkl   (built by analysis/build_decisions.py; for --skip-raw, COPY it here)
      FIN_CACHE  <repo>/data/mf_balances               (audit_finance.py downloads here; you may COPY an existing cache)
      WORK_DIR   <repo>/data/work                      (record-level intermediates; never committed)
Tools:
      ONRC_EDGE  Microsoft Edge / Chromium executable (default: auto-detect)
      ONRC_LAKE  Lean `lake` executable (default: PATH, then ~/.elan/bin)
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent
DATA_DIR = REPO / "data"

# --- read-only raw inputs
ARTICLES_DIR = Path(os.environ.get("ONRC_ARTICLES_DIR", DATA_DIR / "berc_articles"))
LEGACY_COUNTIES_DIRS = [Path(p) for p in os.environ["ONRC_LEGACY_DIRS"].split(";")] if os.environ.get("ONRC_LEGACY_DIRS") \
    else [DATA_DIR / "berc_counties_backup", DATA_DIR / "berc_counties"]
BULLETINS_DIR = Path(os.environ.get("ONRC_BULLETINS_DIR", DATA_DIR / "bulletins" / "2026"))
PORTAL_DIR = Path(os.environ.get("ONRC_PORTAL_DIR", DATA_DIR / "portal"))

# --- writable derived data: fixed inside the repo (no env override on purpose)
BERC_PKL = DATA_DIR / "analysis_decisions.pkl"
FIN_CACHE = DATA_DIR / "mf_balances"
WORK_DIR = DATA_DIR / "work"
for _p in (BERC_PKL, FIN_CACHE, WORK_DIR):
    assert REPO in _p.resolve().parents, f"writable path outside the repo: {_p}"


# --- external tools
def _edge() -> str | None:
    env = os.environ.get("ONRC_EDGE")
    if env:
        return env
    for cand in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                 "/usr/bin/microsoft-edge", "/opt/microsoft/msedge/msedge",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if Path(cand).exists():
            return cand
    return shutil.which("msedge") or shutil.which("microsoft-edge") or shutil.which("chromium") or shutil.which("google-chrome")


def _lake() -> str | None:
    return os.environ.get("ONRC_LAKE") or shutil.which("lake") or (
        str(Path.home() / ".elan" / "bin" / "lake") if (Path.home() / ".elan" / "bin").exists() else None)


EDGE_PATH = _edge()
LAKE = _lake()
WORK_DIR.mkdir(parents=True, exist_ok=True)   # inside <repo>/data (gitignored); the only directory created at import
