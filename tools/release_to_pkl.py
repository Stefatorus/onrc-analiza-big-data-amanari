"""Turn the release asset berc_decisions_min.csv.gz into data/analysis_decisions.pkl with the column names the scripts expect.

  python -X utf8 tools/release_to_pkl.py <berc_decisions_min.csv.gz>

The release file has NO application numbers and no document codes: the columns `app_nr` and `code4` are filled with
missing values. Scripts that need them (reserves_check/11-14, delay_reasons/02+07, rejection_reasons/02+07, the portal join)
need the full crawl, or for the counter series the counter_daily_*.csv.gz tables. docs/DATA.md lists what works.
"""
import sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import config  # noqa: E402


def main():
    m = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False)
    d = pd.DataFrame({"cat": m.category, "app_nr": pd.Series(float("nan"), index=m.index), "app": pd.to_datetime(m.filed_at),
                      "res": pd.to_datetime(m.decided_at), "pub": pd.to_datetime(m.published_at, errors="coerce"),
                      "county": m.county.replace("", None), "sol": m.outcome.replace("", None), "office": m.office.replace("", None),
                      "code4": None, "jtype": m.juridical_type.replace("", None)})
    for c in ("cat", "county", "sol", "office", "code4", "jtype"):
        d[c] = d[c].astype("category")
    config.BERC_PKL.parent.mkdir(parents=True, exist_ok=True)
    d.to_pickle(config.BERC_PKL)
    print(f"{len(d):,} decisions -> {config.BERC_PKL} (app_nr / code4 empty)")


if __name__ == "__main__":
    main()
