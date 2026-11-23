"""Task 5: measured LOWER BOUND for decisions 1 Aug-18 Nov 2026 using only measured exposure (decisions archive),
measured new-firm balance-sheet aggregates (_t3) and official rates (official_rates.json). No behavioural parameters:
the only maintained assumption is that a newly registered firm's cash flows are shifted, not lost, by the excess delay.

Notation (per admitted J registration i): e_i = max(0, wait_i - 3) excess calendar days; r = annual yield (decimal).
 (i)  deferred first-period turnover  F1 = p_active * q * (r/365) * sum(e_i^2)      [turnover of the e_i lost days arrives e_i days late]
 (ib) one-year stream shift          F1b = p_active * q * r * sum(e_i) / ... see below: 365*q*(r*e_i/365) = q*r*e_i per firm
 (ii) deferred taxes                  F2 = (t_direct + t_payroll) * (r/365) * sum(e_i^2); F2b = (t_direct + t_payroll) * r * sum(e_i)
 where q = median daily net turnover of new J firms with positive turnover filed (2025 cohort, >=180 days),
       p_active = share of the cohort that filed a balance sheet with turnover > 0,
       t_direct = median direct tax per calendar day (loss-inclusive) x p_active,
       t_payroll = mean employees per new firm (unfiled = 0) x statutory taxes per employee-day at the gross minimum wage.
Aggregates only -> cost_evidence/_t5_floor.json."""
import json, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'official_rates.json'), encoding='utf-8'))
T3 = {(x['cohort_year'], x['financial_year']): x for x in json.load(open(os.path.join(HERE, '_t3_new_firms.json')))}

d = pd.read_pickle('W:/SOLOResearch/analysis_decisions.pkl')[['cat', 'app', 'res', 'sol', 'jtype']]
d = d[(d.res >= '2026-08-01') & (d.res < '2026-11-19')].copy()
d['w'] = (d.res - d.app).dt.total_seconds() / 86400
d = d[d.w.between(0, 365)]
b = d[(d.cat == 'INMATRIC265') & (d.jtype == 'J') & (d.sol == 'Admis')]
e = b.w.sub(3).clip(lower=0)
S1, S2, N = float(e.sum()), float((e ** 2).sum()), int(len(b))
pub = pd.read_csv(os.path.join(HERE, '..', '..', 'analysis', 'policy_paper_ro', 'audit_data', 'cost_observed_exposure.csv'), index_col=0)['value']

c = T3[(2025, 2025)]
p_active = c['positive_turnover_n'] / c['onrc_n']
q = c['daily_turnover_median']
t_direct = c['direct_tax_per_day_median'] * p_active
emp = c['mean_employees'] * c['matched_with_turnover_field'] / c['onrc_n']      # unfiled firms counted as 0 employees

# statutory payroll taxes per employee-month at the gross minimum wage (weighted over the Aug-Nov window)
mw = R['min_wage_gross_lei_month_window']
untaxed = R.get('min_wage_untaxed_amount_lei', 0.0)
cas, cass, pit, cam = R['cas'], R['cass'], R['income_tax'], R['cam']
base = mw - untaxed
emp_contrib = base * (cas + cass)
employer = base * cam
# income tax only if explicitly enabled (2026 personal deduction at the minimum wage not verified -> excluded => lower bound)
income_tax = (mw - untaxed - emp_contrib) * pit if R.get('include_income_tax') else 0.0
payroll_month = emp_contrib + income_tax + employer
t_payroll = emp * payroll_month * 12 / 365

out = dict(window='admitted J registrations decided 1 Aug-18 Nov 2026, wait 0-365 days (analysis_decisions.pkl)',
           n_births=N, sum_excess_days=round(S1), sum_excess_days_squared=round(S2), mean_excess=round(S1 / N, 2),
           published_exposure_births=float(pub['approved_new_j']), published_excess_days=float(pub['observed_new_j_excess_days']),
           inputs=dict(q_median_daily_turnover=q, p_active=round(p_active, 4), t_direct_per_firm_day=round(t_direct, 3),
                       employees_per_new_firm=round(emp, 3), payroll_taxes_per_employee_month=round(payroll_month, 1),
                       t_payroll_per_firm_day=round(t_payroll, 3)),
           rates=R)
for label, r in (('1y', R['yield_1y']), ('10y', R['yield_10y']), ('policy', R['nbr_policy_rate'])):
    out[f'F1_turnover_deferral_quadratic_{label}'] = round(p_active * q * r / 365 * S2)
    out[f'F1b_turnover_one_year_shift_{label}'] = round(p_active * q * r * S1)
    out[f'F2_tax_deferral_quadratic_{label}'] = round((t_direct + t_payroll) * r / 365 * S2)
    out[f'F2b_tax_one_year_shift_{label}'] = round((t_direct + t_payroll) * r * S1)
    if R.get('va_share_business_economy'):
        out[f'F1_value_added_deferral_quadratic_{label}'] = round(p_active * q * R['va_share_business_economy'] * r / 365 * S2)
        out[f'F1b_value_added_one_year_shift_{label}'] = round(p_active * q * R['va_share_business_economy'] * r * S1)
# mechanical upper reference (NOT a floor): full loss of the excess days' taxes (no deferral)
out['reference_taxes_of_excess_days_if_lost_not_deferred'] = round((t_direct + t_payroll) * S1)
out['formulas'] = {
    'F1': 'p_active * q * (r/365) * sum_i e_i^2', 'F1b': 'p_active * q * r * sum_i e_i  (= 365*q*(r*e_i/365) summed: whole first year shifted by e_i)',
    'F2': '(t_direct + t_payroll) * (r/365) * sum_i e_i^2', 'F2b': '(t_direct + t_payroll) * r * sum_i e_i',
    't_payroll': 'employees_per_new_firm * (MW-untaxed)*(CAS+CASS+CAM) * 12/365  (income tax excluded)'}
json.dump(out, open(os.path.join(HERE, '_t5_floor.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
print(json.dumps(out, ensure_ascii=False, indent=1, default=float))
