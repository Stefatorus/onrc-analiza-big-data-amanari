"""Assemble out/cost_evidence.json (one entry per finding) from the aggregate outputs _t1/_t2/_t3/_t5 and
official_sources.json. Aggregates only."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out', 'cost_evidence.json')
ld = lambda f: json.load(open(os.path.join(HERE, f), encoding='utf-8'))
t1, t2, t3, t5, off = ld('_t1_amendment_types.json'), ld('_t2_amendment_firms.json'), ld('_t3_new_firms.json'), ld('_t5_floor.json'), ld('official_sources.json')
SRC1 = 'BERC bulletin PDFs 2026 (W:/SOLOResearch/bulletins/2026, 545 files, all parsed) linked to raw CERERE265 JSON by request nr + CUI + bulletin nr'
WIN1 = 'admitted amendments decided 1 Oct-18 Nov 2026 (only months the bulletin archive covers; used as proxy for 1 Aug-18 Nov)'
CAV1 = ('Bulletin archive = 455 of ~6,300 bulletins published 1 Oct-18 Nov (7.4% of decisions); CI covers sampling among collected bulletins only, '
        'not how they were collected. Sample over-represents long waits (mean excess 40.2 vs 35.0 d). Mix is time-varying (CAEN Rev.3 campaign): '
        'Sept-filed requests 46% CAEN-only, Oct/Nov-filed 8-10%. Aug-Sep 2026 decisions not observed.')
W = t1['window_aug1_nov18']
E = []


def add(id_, value, unit, window, n, source, method, caveat, ci=None, **kw):
    e = dict(id=id_, value=value, unit=unit, window=window, n=n, ci=ci, source=source, method=method, caveat=caveat); e.update(kw); E.append(e)


# ---------------- Task 1
add('T1.linkage', t1['linkage'], 'counts', 'all 2026 bulletins', t1['linkage']['pdf_decisions'], SRC1,
    'Split each bulletin on the registrar-office header; parse request nr, CUI, verb and the "având ca obiect" text; strict join to JSON.',
    '13 bulletins carry no attached decision text (index-only or corrupt). Registrations (1,482) excluded.')
add('T1.coverage', t1['sample_vs_population_oct1_nov18'], 'mixed', '1 Oct-18 Nov 2026', t1['sample_vs_population_oct1_nov18']['sample_n'], SRC1,
    'Compare sampled decisions with all admitted CERERE265 decisions in the JSON for the same dates.', t1['window_note'])
for k, v in W['any_of'].items():
    add(f'T1.any_of.{k}', v['share'], 'share of admitted amendments (any-of; entries can have several objects)', WIN1, v['n'], SRC1,
        'Regex flags on de-spaced, diacritic-free object text; cluster-robust (bulletin) ratio CI.', CAV1, ci=v['ci95'])
for k, v in W['primary'].items():
    add(f'T1.primary.{k}', v['share'], 'share of admitted amendments (mutually exclusive)', WIN1, v['n'], SRC1,
        'Priority: dissolution/deregistration/suspension > registered office change > secondary offices/work points > capital/shareholders/transfers '
        '> administrators/representatives > office-document prolongation/proof > other (name change, resumption) > CAEN Rev.3-only > other activity-code change.',
        CAV1, ci=v['ci95'])
for k, v in W['excess_day_weighted'].items():
    add(f'T1.excess_day_weighted.{k}', v['share'], 'share of excess (wait-3) days of admitted amendments', WIN1, v['n'], SRC1,
        'Same flags, weighted by each entry\'s excess days (the base channel C multiplies).', CAV1, ci=v['ci95'])
for k, v in t1['window_excl_seat_related'].items():
    add(f'T1.{k}', dict(count_share=v['count_share']['share'], excess_day_share=v['excess_day_share']['share']), 'share', WIN1, v['count_share']['n'], SRC1,
        'Blocking tier excluding entries that touch the registered office (address change or seat documents), i.e. disjoint from channel B.', CAV1,
        ci=dict(count=v['count_share']['ci95'], excess_day=v['excess_day_share']['ci95']))
for k, v in t1['window_wait_over_30'].items():
    add(f'T1.wait_over_30.{k}', v['share'], 'share of admitted amendments with wait > 30 days', WIN1, v['n'], SRC1,
        'Denominator of channel B (changes waiting > 30 days).', CAV1, ci=v['ci95'])
add('T1.poststratified_application_month', t1['oct_nov_poststratified_by_application_month'], 'share', WIN1, t1['sample_vs_population_oct1_nov18']['sample_n'], SRC1,
    'Shares re-weighted to the population mix of application months (corrects the long-wait over-representation).', CAV1)
add('T1.poststratified_county', t1['window_county_poststratified'], 'share', WIN1, W['n'], SRC1, 'Shares re-weighted to the population county mix.', CAV1)
for m_, v_ in t1['by_month'].items():
    add(f'T1.by_decision_month.{m_}', {k: x['share'] for k, x in v_['any_of'].items()}, 'share of admitted amendments (any-of)', f'decisions of {m_}', v_['n'], SRC1,
        'Any-of shares by decision month; cluster-robust (bulletin) 95% CI per share.',
        'Only Oct and Nov 2026 can be estimated; Jan-Sep 2026 monthly shares cannot be established (no bulletins with amendment decisions in those months).',
        ci={k: x['ci95'] for k, x in v_['any_of'].items()})
add('T1.by_application_month', t1['window_by_application_month'], 'share', WIN1, W['n'], SRC1, 'Any-of shares by application month.', CAV1)
add('T1.blocking_definition', dict(
        strict='office change | secondary offices/work points | capital | share transfer | appointment/revocation of administrators | resumption; not dissolution',
        core='strict + "modificare date asociați/administratori" (ONRC uses these for real shareholding/management changes and for personal-data updates)',
        upper='core + activity-code changes (non-Rev.3) + name change',
        not_blocking='CAEN Rev.3-only update, seat-document prolongation with no change, dissolution/deregistration/suspension'),
    'definition', WIN1, W['n'], SRC1, 'Classification rule.', 'A blocking-type share is a CEILING for the share with separate economic impact, not an estimate of it.')
add('T1.median_wait_by_primary', t1['window_median_wait_by_primary'], 'days', WIN1, W['n'], SRC1, 'Median wait by primary category.', CAV1)

# ---------------- Task 2
SRC2 = 'Raw CERERE265 JSON (cui) x Ministry of Finance balance sheets WEB_UU_AN2025 (2024 if missing), data.gov.ro'
for k in ('overall_firm_level', 'overall_excess_day_weighted', 'overall_decision_level'):
    v = t2[k]
    add(f'T2.{k}', v, 'lei per calendar day (I13/365) and employees (I20)', '1 Aug-18 Nov 2026 admitted CERERE265, wait 0-365', v['n'], SRC2,
        'Join by CUI; daily turnover = I13 / days in financial year; capped mean at p99; weighted variants by excess days.',
        'F (PFA/II) entities file no balance sheets (match 0%); J match ~70%. Turnover of the last filed year, not of 2026.')
add('T2.match_rate_by_jtype', t2['by_jtype_match_rate'], 'share', '1 Aug-18 Nov 2026', t2['decisions'], SRC2, 'Share of decisions whose CUI has a balance sheet with turnover.', '')
for k, v in t2['by_primary_category_linked_sample'].items():
    add(f'T2.by_primary.{k}', v, 'lei/day, employees', WIN1, v['n'], SRC2 + '; categories from T1 linked sample', 'As T2 overall, within the bulletin-linked sample.', CAV1)
for t in ('blocking_strict', 'blocking_core', 'caen_only', 'seat_related'):
    for suf in ('', '_excess_weighted'):
        v = t2[f'linked_sample_{t}{suf}']
        add(f'T2.linked.{t}{suf}', v, 'lei/day, employees', WIN1, v['n'], SRC2 + '; categories from T1', 'Firms with at least one entry of that tier.', CAV1)
mv = t2['model_vs_turnover']
for sc in mv:
    mv[sc]['pct_of_J_median_unmatched_as_zero'] = round(100 * mv[sc]['lei_per_change_day'] / t2['overall_firm_level']['J_median_daily_unmatched_as_zero'], 1)
add('T2.model_C_vs_turnover', mv, '% of daily net turnover', '1 Aug-18 Nov 2026', t2['overall_firm_level']['n'], SRC2,
    'Model cost per change-day (share x lei per blocked day; central 0.20 x 70 = 14 lei) divided by measured median and p99-capped mean daily turnover.',
    'Scale check only: turnover is not value added and not a cost; it does not found the 70 lei.')

# ---------------- Task 3
SRC3 = 'BERC INMATRIC265 JSON J registrations (audit_finance.py rule) x MF balance sheets 2024/2025'
for x in t3:
    add(f'T3.cohort{x["cohort_year"]}_fy{x["financial_year"]}', x, 'ratios / lei / employees', f'cohort {x["cohort_year"]}, financial year {x["financial_year"]}',
        x['onrc_n'], SRC3,
        'eff_direct_tax_simple = (I16-I18)/I13 (I13>0); eff_direct_tax_full = ((I16-I17)-(I18-I19))/I13 (includes micro tax paid by loss-makers); '
        'profit margin = I18/I13; employees I20 (unfiled = excluded unless stated); daily turnover over days since registration (>=180 d) or full year.',
        'Only ~47-57% of a cohort files a balance sheet with turnover. Direct tax is mostly the 1%/3% micro-enterprise tax. '
        'Aggregate margins are pulled up by firms with small turnover and large profit; medians are more representative.')

# derived composite tax share (direct + payroll at 2026 minimum wage + VAT on value added of VAT-registered turnover)
c25 = [x for x in t3 if x['cohort_year'] == 2025 and x['financial_year'] == 2025][0]
pay_day = (4325 - 200) * (0.25 + 0.10 + 0.0225) * 12 / 365
payroll_share = c25['mean_employees'] * pay_day / c25['daily_turnover_mean_capped_p99']
vat_lo, vat_hi = 0.21 * 0.276 * 0.46, 0.21 * 0.276 * 1.0
dt = c25['eff_direct_tax_full_aggregate']
add('T3.composite_tax_share', dict(direct=dt, payroll=round(payroll_share, 4), vat_low=round(vat_lo, 4), vat_high=round(vat_hi, 4),
                                   total_low=round(dt + payroll_share + vat_lo, 4), total_high=round(dt + payroll_share + vat_hi, 4)),
    'share of turnover', 'cohort 2025, FY2025 balance sheets, 2026 statutory rates', c25['onrc_n'], SRC3 + ' + Eurostat VA share + Fiscal Code rates',
    'direct = aggregate loss-inclusive direct tax / turnover; payroll = mean employees x (4,325-200) x 37.25% x 12/365 / capped mean daily turnover; '
    'VAT = 21% x VA share 27.6% (Eurostat 2024) x share of turnover in firms above the 395k lei threshold (46% excl. top 1%) .. 100%.',
    'Payroll proportional to lost sales is an assumption; voluntary VAT registration unknown; income tax excluded. '
    'Direct tax is measured on FY2025 when a 3% micro rate still existed; from 2026 only 1% applies, so 2.6% is an upper reference for 2026.')
for x in t3:
    add(f'T3.measured_VA_floor.cohort{x["cohort_year"]}_fy{x["financial_year"]}',
        dict(net_result_plus_direct_tax_aggregate=round(x['net_result_margin_aggregate'] + x['eff_direct_tax_full_aggregate'], 4),
             net_result_plus_direct_tax_median=round(x['net_result_margin_median'] + x['eff_direct_tax_full_median'], 4)),
        'share of turnover (lower bound of value added: excludes wages, social contributions, depreciation)', f'cohort {x["cohort_year"]}, FY {x["financial_year"]}',
        x['positive_turnover_n'], SRC3, '(I18-I19)/I13 + ((I16-I17)-(I18-I19))/I13 = gross result / turnover; aggregate and median over firms with I13>0.',
        'New J firms are service-heavy micro-firms where owners take income as profit; Eurostat 27.6% is economy-wide and trade-heavy. '
        'Gross result alone already reaches 20-31% of turnover, before any wages.')

# ---------------- Task 4
for o in off:
    E.append(o)

# ---------------- Task 5
SRC5 = 'analysis_decisions.pkl (exposure) + T3 cohort 2025 aggregates + official rates (T4)'
CAV5 = ('Counts only realised J registrations in the window (no pending stock, no amendments, no B/D). Only maintained assumption: cash flows are '
        'shifted, not lost. Current pkl has %d births / %.0f excess days vs published exposure %d / %.0f.' % (
        t5['n_births'], t5['sum_excess_days'], t5['published_exposure_births'], t5['published_excess_days']))
head = dict(turnover_basis=t5['F1_turnover_deferral_quadratic_1y'], value_added_basis=t5['F1_value_added_deferral_quadratic_1y'],
            taxes=t5['F2_tax_deferral_quadratic_1y'], total_value_added_plus_taxes=t5['F1_value_added_deferral_quadratic_1y'] + t5['F2_tax_deferral_quadratic_1y'])
add('T5.floor_headline', head, 'lei', t5['window'], t5['n_births'], SRC5,
    'F1 = p_active*q*(r/365)*sum e_i^2 ; F1_VA = F1 * VA share 27.6% ; F2 = (t_direct+t_payroll)*(r/365)*sum e_i^2 ; r = 1y T-bill 6.16%',
    CAV5, inputs=t5['inputs'], sums=dict(sum_e=t5['sum_excess_days'], sum_e2=t5['sum_excess_days_squared']))
add('T5.floor_variants', {k: v for k, v in t5.items() if k.startswith(('F1', 'F2'))}, 'lei', t5['window'], t5['n_births'], SRC5,
    json.dumps(t5['formulas'], ensure_ascii=False),
    'Rates 1y / 10y / policy. The "one_year_shift" variants (F1b/F2b) need an extra assumption (the whole first year of activity shifts by e_i) and are '
    'alternatives, not the floor. ' + CAV5)
add('T5.reference_not_a_floor', t5['reference_taxes_of_excess_days_if_lost_not_deferred'], 'lei', t5['window'], t5['n_births'], SRC5,
    '(t_direct + t_payroll) * sum e_i', 'Taxes of the excess days if LOST rather than deferred - a behavioural assumption, shown for scale only; NOT a floor.')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(_meta='Evidence base for the four-channel cost model (audit_costs.py). Aggregates only; no identifiers. Built by '
                     'independent_audit/cost_evidence/07_build_evidence_json.py.', findings=E),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
print('entries', len(E), '->', os.path.abspath(OUT))
