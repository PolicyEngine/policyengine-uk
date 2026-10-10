import math

from policyengine_uk import CountryTaxBenefitSystem


def test_legacy_benefit_age_threshold_parameters():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.eligibility.min_age("2025") == 18
    assert params.gov.dwp.ESA.eligibility.min_age("2025") == 16


def test_jsa_hours_parameter_still_exposed():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.hours.single("2025") == 16


def test_income_support_remunerative_work_hours_by_date():
    # IS Regs 1987 reg 5(1): 24 hours as made, 16 from 7 April 1992; reg 5(1A),
    # inserted from 7 October 1996, makes it 24 for the partner.
    work = CountryTaxBenefitSystem().parameters.gov.dwp.income_support.eligibility
    work = work.remunerative_work
    expected = {
        "1990-01-01": (24, 24),
        "1992-04-06": (24, 24),
        "1992-04-07": (16, 16),
        "1996-10-06": (16, 16),
        "1996-10-07": (16, 24),
        "2025-01-01": (16, 24),
    }
    for date, (claimant, partner) in expected.items():
        assert work.claimant_hours(date) == claimant, date
        assert work.partner_hours(date) == partner, date


def _round_up_to_50p(amount):
    # ESA Regs 2008 reg 45(9A): part of a pound under 50p rounds up to 50p,
    # and over 50p up to the next pound.
    return math.ceil(round(amount * 2, 6)) / 2


# The National Minimum Wage rate that reg 45 uses (reg 2(1): the reg 11 NMW
# Regulations 1999 rate, now the National Living Wage), from DMG ch. 41
# Appendix 5 and ADM ch. V3; April 2026 from DWP's 2026-27 rates.
NMW_RATES = {
    "2010-10-01": 5.93,
    "2011-10-01": 6.08,
    "2012-10-01": 6.19,
    "2013-10-01": 6.31,
    "2014-10-01": 6.50,
    "2015-10-01": 6.70,
    "2016-04-01": 7.20,
    "2017-04-01": 7.50,
    "2018-04-01": 7.83,
    "2019-04-01": 8.21,
    "2020-04-01": 8.72,
    "2021-04-01": 8.91,
    "2022-04-01": 9.50,
    "2023-04-01": 10.42,
    "2024-04-01": 11.44,
    "2025-04-01": 12.21,
    "2026-04-01": 12.71,
}


def _rate_in_force(on):
    return [rate for start, rate in sorted(NMW_RATES.items()) if start <= on][-1]


def test_esa_exempt_work_higher_limit_is_16_x_nmw_rounded_up():
    # Reg 45(4): £92 as made, £93 from 1 October 2009, then 16 x NMW from 11
    # April 2011 (SI 2011/674), rounded up under reg 45(9A).
    limit = CountryTaxBenefitSystem().parameters.gov.dwp.ESA.exempt_work
    limit = limit.higher_earnings_limit
    assert limit("2008-10-27") == 92
    assert limit("2009-09-30") == 92
    assert limit("2009-10-01") == 93
    assert limit("2011-04-10") == 93
    # Before 2015 parameters keep their statutory dates.
    for on in ["2011-04-11", "2011-10-01", "2012-10-01", "2013-10-01", "2014-10-01"]:
        assert limit(on) == _round_up_to_50p(16 * _rate_in_force(on)), on
    # From 2015 each year takes the value on 30 April (fiscal-year parameters).
    for year in range(2015, 2027):
        expected = _round_up_to_50p(16 * _rate_in_force(f"{year}-04-30"))
        assert limit(str(year)) == expected, year
    # DWP's published limits.
    assert limit("2024") == 183.5
    assert limit("2025") == 195.5
    assert limit("2026") == 203.5
    # Later years follow average earnings, rounded up to 50p like reg 45(9A).
    for year in range(2027, 2041):
        value = limit(str(year))
        assert value == _round_up_to_50p(value), year
        assert value >= limit(str(year - 1)), year


def test_esa_and_jsa_remunerative_work_parameters_by_date():
    dwp = CountryTaxBenefitSystem().parameters.gov.dwp
    exempt_work = dwp.ESA.exempt_work
    assert exempt_work.lower_earnings_limit("2008-10-27") == 20
    assert exempt_work.lower_earnings_limit("2026") == 20
    assert exempt_work.hours_limit("2008-10-27") == 16
    assert dwp.ESA.income.remunerative_work.partner_hours("2008-10-27") == 24
    work = dwp.JSA.remunerative_work
    for on in ["1996-10-07", "2001-03-19", "2025"]:
        assert work.claimant_hours(on) == 16, on
        assert work.partner_hours(on) == 24, on
    # The older parameters say the same thing.
    for year in range(2015, 2031):
        assert dwp.JSA.hours.single(str(year)) == work.claimant_hours(str(year))
        assert dwp.JSA.hours.couple(str(year)) == work.partner_hours(str(year))


def test_esa_self_employment_class_2_by_fiscal_year():
    # Reg 99(3)(a): Class 2 from the small profits threshold, from the lower
    # profits threshold from 2022-23 (SI 2022/1329), omitted from 2024-25 (SI
    # 2024/377). Fiscal-year values are read at 30 April.
    rule = CountryTaxBenefitSystem().parameters.gov.dwp.ESA.income
    rule = rule.self_employment_class_2
    assert rule.deducted("2008-10-27") and rule.deducted("2023")
    assert not rule.deducted("2024") and not rule.deducted("2026")
    assert not rule.above_lower_profits_threshold("2021")
    assert rule.above_lower_profits_threshold("2022")
