"""Task 4: write official_sources.json (figures read from official pages on 2026-11-22; URLs recorded)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = 'CONFIRMED by delegated research run (official page fetched 2026-11-22; not re-fetched by the auditor)'
V = 'CONFIRMED - re-read by the auditor on 2026-11-22'


def e(id_, v, unit, win, src, method, cav, status=C):
    return dict(id=id_, value=v, unit=unit, window=win, n=None, ci=None, source=src, method=method, caveat=cav, status=status)


FC = 'https://legislatie.just.ro/Public/DetaliiDocument/171282'
S = [
    e('T4.a.va_share_BN_exclK', 0.253, 'value added / net turnover', '2024',
      'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_ovw_act?geo=RO&lastTimePeriod=1&indic_sbs=NETTUR_MEUR&indic_sbs=AV_MEUR',
      'VA 130,584.9 / net turnover 515,689.7 million EUR; sections B-J + L-N summed (code B-N_X_K returned nothing)',
      'Eurostat label "Value added" (SBS factor-cost concept; the response does not repeat "at factor cost").'),
    e('T4.a.va_share_BS_exclO_S94', 0.276, 'value added / net turnover', '2024', 'same API as T4.a.va_share_BN_exclK',
      '151,721.83 / 549,585.53 million EUR (published aggregate)', ''),
    e('T4.a.va_share_micro_0_9', {'B-N_excl_K': 0.289, 'B-S_excl_O_S94': 0.304}, 'value added / net turnover', '2024',
      'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_sc_ovw?geo=RO&lastTimePeriod=1',
      '25,846.6 / 89,425.5 and 29,412.51 / 96,850.35 million EUR, size class 0-9 persons employed', 'B-N figure summed by section.'),
    e('T4.a.labour_productivity', {'total_BS': 31.82, 'micro_BS': 19.27, 'total_BN': 29.97, 'micro_BN': 19.74}, 'thousand EUR VA per person employed',
      '2024', 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_sc_ovw?geo=RO&lastTimePeriod=1', 'Apparent labour productivity', ''),
    e('T4.a.INS_crosscheck', None, '', '', 'INS "Rezultate si performante ale intreprinderilor"', 'not attempted', '', status='NOT CONFIRMED'),
    e('T4.b.min_wage', {'2026-01-01_to_2026-06-30': 4050, 'from_2026-07-01': 4325, 'hourly_from_2026-07-01': 25.949}, 'lei gross per month', '2026',
      'https://legislatie.just.ro/Public/DetaliiDocument/308231 (HG 146/2026); https://legislatie.just.ro/Public/DetaliiDocument/291450 (HG 1506/2024) + OUG 89/2025 preamble',
      'legal text', 'Aug-Nov 2026 window -> 4,325 lei. HG 146/2026 art. 1 re-read by the auditor.', status=V),
    e('T4.b.min_wage_exempt_amount', {'2026-01_to_06': 300, '2026-07_to_12': 200}, 'lei/month free of income tax and social contributions', '2026',
      'https://static.anaf.ro/static/10/Anaf/legislatie/OUG_89_2025.pdf (art. III)', 'legal text',
      'Only if base salary = minimum wage and gross <= 4,300 lei (H1) / 4,600 lei (H2).', status=V),
    e('T4.b.contribution_rates', {'CAS_employee': 0.25, 'CASS': 0.10, 'income_tax': 0.10, 'CAM_employer': 0.0225}, 'rate',
      '2026 (consolidated Fiscal Code, version 25.10.2026)', FC + ' (art. 138a, 156, 64(1), 220^3(1))', 'legal text',
      'The 2026 personal deduction at the minimum wage was not verified, so income tax is left out of the floor.'),
    e('T4.c.micro_tax', {'rate': 0.01, 'turnover_ceiling_eur': 100000}, 'rate / EUR', 'from 1 Jan 2026', FC + ' (art. 51(1), 47(1)(c))', 'legal text',
      'The 3% rate was abrogated by OUG 89/2025.'),
    e('T4.c.profit_and_dividend_tax', {'profit_tax': 0.16, 'dividend_tax_from_2026': 0.16}, 'rate', '2026',
      FC + ' (art. 17, 97(7)); https://static.anaf.ro/static/10/Anaf/legislatie/L_141_2025.pdf', 'legal text', ''),
    e('T4.c.vat', {'standard_rate_from_2025-08-01': 0.21, 'exemption_threshold_lei_from_2025-09-01': 395000}, 'rate / lei', '2026',
      FC + ' (art. 291(1), 310(1))', 'legal text', ''),
    e('T4.d.nbr_policy_rate', {'policy': 0.065, 'lending_facility': 0.075, 'deposit_facility': 0.055, 'in_force_since': '2024-08-08',
                               'last_board_meeting': '2026-11-12'}, 'rate', 'Nov 2026', 'https://www.bnr.ro/1970-rata-dobanzii-de-politica-monetara',
      'official table', ''),
    e('T4.d.yield_1y', 0.0616, 'weighted average yield, T-bill ROZOAXICMLV1 (maturity 28-10-2027)', 'auction 5 Nov 2026',
      'https://mfinante.gov.ro/static/10/Mfp/emisiuni/comof_05112026.pdf', 'MF auction communique (cut-off 6.19%, 966.6m lei allotted)', 'Image PDF; read from the rendered page.', status=V),
    e('T4.d.yield_10y', {'2026-10': 0.0677, '2026-09': 0.0671, '2026-08': 0.0643, '2026-07': 0.0609}, 'EMU convergence long-term interest rate',
      'Jul-Oct 2026', 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_mcby_m?geo=RO&lastTimePeriod=4',
      'Eurostat irt_lt_mcby_m (updated 2026-11-12)', 'November 2026 not yet published.'),
    e('T4.e.worldbank_bready_2024', {'llc_days': 6.5, 'cost_pct_income_per_capita': 0.3, 'onrc_registration_step_days': 3, 'onrc_fee_ron': 128},
      'days / % / RON', 'Subnational B-READY 2024, 9 Romanian cities',
      'https://openknowledge.worldbank.org/server/api/core/bitstreams/7fc14323-86f3-471c-8a06-c1cebb477a1d/content (p.53-54)', 'report',
      'Supports the 3-day benchmark of the model; does not price delay.'),
    e('T4.e.worldbank_doing_business_2020', {'procedures': 6, 'days': 20, 'onrc_step_days': 3, 'onrc_fee_ron': 122}, 'count / days / RON', 'DB2020 Bucharest',
      'https://documents1.worldbank.org/curated/en/639751575291022268/text/Doing-Business-2020-Comparing-Business-Regulation-in-190-Economies-Economy-Profile-of-Romania.txt',
      'report', 'Discontinued series.'),
    e('T4.e.ec_digital_company_law_IA', {'admin_burden_reduction_eur_per_year': 437e6, 'one_off_companies_eur': 311e6}, 'EUR, EU-wide', 'SWD(2023) 179',
      'https://data.consilium.europa.eu/doc/document/ST-7953-2023-ADD-5/en/pdf', 'impact assessment', 'EU-wide, not Romania; not a per-day delay cost.'),
    e('T4.e.ec_eu_inc_IA', {'registration_deadline_hours': 48, 'cost_ceiling_eur': 100, 'burden_reduction_eur_10y': [328e6, 440e6]}, 'EUR, EU-wide',
      'SWD(2026) 322 (18.3.2026)', 'https://www.cdep.ro/afaceri_europene/CE/2026/SWD(2026)%20322_EN_resume_impact_assessment_part1_v4.pdf',
      'impact assessment', 'EU-wide.'),
    e('T4.e.directive_2019_1151_deadline', None, '', '', 'EUR-Lex (empty response)', 'not retrieved', '', status='NOT CONFIRMED'),
    e('T4.e.cost_per_day_of_delay', None, '', '', 'World Bank / OECD / EC pages searched', 'no official per-day cost of registration delay found', '',
      status='NOT CONFIRMED'),
]
json.dump(S, open(os.path.join(HERE, 'official_sources.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# rates consumed by 06_measured_floor.py
R = {'min_wage_gross_lei_month_window': 4325, 'min_wage_untaxed_amount_lei': 200, 'cas': 0.25, 'cass': 0.10, 'income_tax': 0.10, 'cam': 0.0225,
     'include_income_tax': False, 'yield_1y': 0.0616, 'yield_10y': 0.0677, 'nbr_policy_rate': 0.065,
     'va_share_business_economy': 0.276, 'va_share_BN_exclK_summed': 0.253, 'va_share_micro': 0.289,
     '_notes': ('Aug-Nov 2026 are all after 1 Jul 2026 (HG 146/2026: 4,325 lei; OUG 89/2025 art. III: 200 lei/month exempt Jul-Dec 2026). '
                'Income tax excluded from the floor (2026 personal deduction at the minimum wage not verified). 1y = T-bill auction 5 Nov 2026 (MF/BNR), '
                '10y = Eurostat irt_lt_mcby_m Oct 2026, policy rate BNR. VA share = Eurostat sbs_ovw_act 2024 published aggregate B-S excl. O, S94 (27.6%).')}
json.dump(R, open(os.path.join(HERE, 'official_rates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(S), 'official-source entries')
