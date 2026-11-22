"""Task 3: 2024 and 2025 J registration cohorts (same rule as analysis/policy_paper_ro/audit_finance.py) joined to
Ministry of Finance balance sheets: effective direct tax, employees, profitability, daily turnover.
Aggregates only -> cost_evidence/_t3_new_firms.json."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import json, os, numpy as np, pandas as pd
from pathlib import Path
HERE = os.path.dirname(os.path.abspath(__file__))
FIN = str(config.FIN_CACHE)
ARTICLES = config.ARTICLES_DIR
COLS = ['CUI', 'I13', 'I14', 'I15', 'I16', 'I17', 'I18', 'I19', 'I20']


def balance(year):
    f = pd.read_csv(os.path.join(FIN, f'WEB_UU_AN{year}.txt'), usecols=COLS).drop_duplicates()
    return f.drop_duplicates('CUI', keep=False)


def formations(year):   # identical filter to audit_finance.formations
    rows = []
    for archive_year in (year, year + 1):
        for fp in sorted((ARTICLES / str(archive_year)).glob('*INMATRIC265*.json')):
            if archive_year > year and fp.name[5:7] not in ('01', '02', '03'):
                continue
            for row in json.loads(fp.read_text(encoding='utf-8-sig')):
                if (str(row.get('registrationYear')) != str(year) or row.get('juridicType') != 'J' or row.get('resolution') != 'Admis'
                        or (row.get('publicitySituation') or {}).get('identifier') != 'INMATRIC265' or not str(row.get('cui')).isdigit()):
                    continue
                date = row.get('resolutionDate') or ''
                if date[:4] == str(year):
                    rows.append((int(row['cui']), date))
    r = pd.DataFrame(rows, columns=['CUI', 'date']).sort_values('date').drop_duplicates('CUI')
    r['date'] = pd.to_datetime(r.date, format='mixed', utc=True).dt.tz_convert('Europe/Bucharest').dt.tz_localize(None).dt.normalize()
    return r[r.date.dt.year == year]


def summarize(cohort, bal, cy, fy):
    j = cohort.merge(bal, on='CUI', how='left', validate='one_to_one')
    m = j[j.I13.notna()].copy()
    pos = m[m.I13 > 0].copy()
    for c in ('I16', 'I17', 'I18', 'I19'):
        pos[c] = pos[c].fillna(0)
    pos['tax_simple'] = pos.I16 - pos.I18                               # task definition (profit-making firms only)
    pos['tax_full'] = (pos.I16 - pos.I17) - (pos.I18 - pos.I19)        # gross result - net result (also loss-makers, micro tax)
    r_s, r_f = pos.tax_simple / pos.I13, pos.tax_full / pos.I13
    cap = pos.I13.quantile(.99)
    out = dict(cohort_year=cy, financial_year=fy, onrc_n=len(cohort), matched_with_turnover_field=len(m),
               match_rate=round(len(m) / len(cohort), 4), positive_turnover_n=len(pos),
               eff_direct_tax_simple_median=round(float(r_s.median()), 4),
               eff_direct_tax_simple_aggregate=round(float(pos.tax_simple.sum() / pos.I13.sum()), 4),
               eff_direct_tax_full_median=round(float(r_f.median()), 4),
               eff_direct_tax_full_aggregate=round(float(pos.tax_full.sum() / pos.I13.sum()), 4),
               eff_direct_tax_full_aggregate_excl_top1pct_turnover=round(float(pos[pos.I13 <= cap].tax_full.sum() / pos[pos.I13 <= cap].I13.sum()), 4),
               share_tax_full_between_0_5_and_1_5pct=round(float(r_f.between(.005, .015).mean()), 4),
               share_tax_full_between_2_5_and_3_5pct=round(float(r_f.between(.025, .035).mean()), 4),
               share_loss_makers_paying_tax=round(float(((pos.I17 > 0) & (pos.tax_full > 0)).sum() / max(1, (pos.I17 > 0).sum())), 4),
               share_ge1_employee=round(float((m.I20.fillna(0) >= 1).mean()), 4),
               mean_employees=round(float(m.I20.fillna(0).mean()), 3),
               mean_employees_capped_p99=round(float(m.I20.fillna(0).clip(upper=m.I20.fillna(0).quantile(.99)).mean()), 3),
               median_employees=float(m.I20.fillna(0).median()),
               profit_margin_aggregate_I18_over_I13=round(float(pos.I18.sum() / pos.I13.sum()), 4),
               net_result_margin_aggregate=round(float((pos.I18 - pos.I19).sum() / pos.I13.sum()), 4),
               net_result_margin_aggregate_excl_top1pct=round(float((pos[pos.I13 <= cap].I18 - pos[pos.I13 <= cap].I19).sum() / pos[pos.I13 <= cap].I13.sum()), 4),
               net_result_margin_median=round(float(((pos.I18 - pos.I19) / pos.I13).median()), 4),
               net_result_over_total_revenue_aggregate=round(float((pos.I18 - pos.I19).sum() / pos.I14.fillna(0).sum()), 4),
               total_revenue_over_turnover_aggregate=round(float(pos.I14.fillna(0).sum() / pos.I13.sum()), 3),
               eff_direct_tax_full_over_total_revenue_aggregate=round(float(pos.tax_full.sum() / pos.I14.fillna(0).sum()), 4),
               share_profitable=round(float((pos.I18 > 0).mean()), 4),
               share_turnover_over_395k=round(float((m.I13 > 395000).mean()), 4), share_turnover_over_300k=round(float((m.I13 > 300000).mean()), 4),
               median_turnover_all_matched=round(float(m.I13.median()), 0), median_turnover_positive=round(float(pos.I13.median()), 0))
    # daily turnover: full-year firms -> /365(366); same-year cohort -> days since registration, >=180 days
    if fy == cy:
        days = (pd.Timestamp(f'{fy + 1}-01-01') - m.date).dt.days
        d = (m.I13.clip(lower=0) / days)[days >= 180]
    else:
        d = m.I13.clip(lower=0) / (366 if fy % 4 == 0 else 365)
    out.update(daily_n=int(len(d)), daily_turnover_median=round(float(d.median()), 1),
               daily_turnover_mean_capped_p99=round(float(d.clip(upper=d.quantile(.99)).mean()), 1),
               daily_turnover_p25=round(float(d.quantile(.25)), 1), daily_turnover_p75=round(float(d.quantile(.75)), 1))
    # direct tax per calendar day (loss-inclusive), same day base
    if fy == cy:
        days = (pd.Timestamp(f'{fy + 1}-01-01') - pos.date).dt.days; keep = days >= 180
        td = (pos.tax_full / days)[keep]
    else:
        td = pos.tax_full / (366 if fy % 4 == 0 else 365)
    out.update(direct_tax_per_day_mean_capped=round(float(td.clip(upper=td.quantile(.99)).mean()), 2), direct_tax_per_day_median=round(float(td.median()), 2))
    return out


def main():
    bal = {y: balance(y) for y in (2024, 2025)}
    coh = {y: formations(y) for y in (2024, 2025)}
    res = [summarize(coh[y], bal[f], y, f) for y, f in [(2024, 2024), (2024, 2025), (2025, 2025)]]
    json.dump(res, open(os.path.join(HERE, '_t3_new_firms.json'), 'w', encoding='utf-8'), indent=1)
    print(pd.DataFrame(res).T.to_string())


if __name__ == '__main__':
    main()
