"""Aggregate official balance sheets joined locally to BERC formation cohorts."""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "audit_data"
ARTICLES = Path("W:/SOLOResearch/articles")
CKAN = "https://data.gov.ro/api/3/action/package_show"
PACKAGES = {2024: "d3caacb6-2c08-445e-94e6-8d36d00ab250", 2025: "situatii_financiare_2025"}


def balance(year, cache):
    response = requests.get(CKAN, params={"id": PACKAGES[year]}, timeout=30)
    response.raise_for_status()
    package = response.json()["result"]
    resources = {r["name"]: r for r in package["resources"]}
    stem = f"WEB_UU_AN{year}"
    dictionary = requests.get(resources[stem + ".csv"]["url"], timeout=30)
    dictionary.raise_for_status()
    assert "Capital subscris varsat;i11" in dictionary.text
    assert "Cifra de afaceri neta;i13" in dictionary.text
    resource = resources[stem + ".txt"]
    path = cache / resource["name"]
    if not path.exists() or path.stat().st_size != resource["size"]:
        with requests.get(resource["url"], stream=True, timeout=(20, 100)) as r:
            r.raise_for_status()
            with path.open("wb") as file:
                for chunk in r.iter_content(chunk_size=2**20):
                    file.write(chunk)
    assert path.stat().st_size == resource["size"]
    frame = pd.read_csv(path, usecols=["CUI", "I11", "I13", "I14", "I20"])
    frame = frame.drop_duplicates()
    collisions = int(frame.CUI.duplicated(keep=False).sum())
    frame = frame.drop_duplicates("CUI", keep=False)
    return frame, resource["url"], collisions


def formations(year):
    rows = []
    for archive_year in (year, year + 1):
        for fp in sorted((ARTICLES / str(archive_year)).glob("*INMATRIC265*.json")):
            if archive_year > year and fp.name[5:7] not in ("01", "02", "03"):
                continue
            for row in json.loads(fp.read_text(encoding="utf-8-sig")):
                if (str(row.get("registrationYear")) != str(year)
                        or row.get("juridicType") != "J" or row.get("resolution") != "Admis"
                        or (row.get("publicitySituation") or {}).get("identifier") != "INMATRIC265"
                        or not str(row.get("cui")).isdigit()):
                    continue
                date = row.get("resolutionDate") or ""
                if date[:4] == str(year):
                    rows.append((int(row["cui"]), date))
    result = pd.DataFrame(rows, columns=["CUI", "date"]).sort_values("date").drop_duplicates("CUI")
    result["date"] = pd.to_datetime(result.date, format="mixed", utc=True).dt.tz_convert(
        "Europe/Bucharest").dt.tz_localize(None).dt.normalize()
    return result[result.date.dt.year == year]


def summarize(cohort, balances, year, match_year):
    joined = cohort.merge(balances, on="CUI", how="left", validate="one_to_one")
    turnover = joined.I13.dropna()
    positive = turnover[turnover > 0]
    cap = positive.quantile(.99)
    daily = None
    if year == match_year:
        days = (pd.Timestamp(f"{year + 1}-01-01") - joined.date).dt.days
        daily = (joined.loc[days >= 180, "I13"] / days[days >= 180]).dropna()
    return dict(cohort_year=year, financial_year=match_year, onrc_n=len(cohort),
                matched_n=len(turnover), positive_n=len(positive),
                median_turnover=turnover.median(), median_positive=positive.median(),
                mean_turnover=turnover.mean(), mean_positive=positive.mean(),
                mean_all_cap_at_positive_p99=turnover.clip(upper=cap).mean(),
                mean_daily_at_least_180d_capped_p99=(daily.clip(upper=daily.quantile(.99)).mean() if daily is not None else np.nan),
                n_daily_at_least_180d=(len(daily) if daily is not None else 0))


def main():
    OUT.mkdir(exist_ok=True)
    cache = Path(tempfile.gettempdir()) / "onrc-review-finance"
    cache.mkdir(exist_ok=True)
    balances, meta = {}, []
    for y in (2024, 2025):
        balances[y], url, duplicates = balance(y, cache)
        data = balances[y]
        over = data.I13.gt(400000)
        paid = data.I11.between(0, 4999)
        meta.append(dict(year=y, url=url, unique_balance_rows=len(data), duplicate_conflict_rows=duplicates,
                         above_turnover=int(over.sum()), above_turnover_capital_below_5000=int((over & paid).sum()),
                         above_turnover_capital_missing=int((over & data.I11.isna()).sum())))
    (OUT / "finance_sources.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    cohorts = {y: formations(y) for y in (2024, 2025)}
    summary = pd.DataFrame([summarize(cohorts[y], balances[m], y, m) for y, m in [(2024, 2024), (2024, 2025), (2025, 2025)]])
    summary.to_csv(OUT / "formation_turnover.csv", index=False, float_format="%.2f")
    print(json.dumps(meta, indent=2))
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
