"""Uprating of the Scottish Carer Supplement.

Social Security (Scotland) Act 2018 s.86B requires Scottish Ministers to bring
forward legislation raising each figure of assistance given under Chapter 2 of
Part 2, carer's assistance included, to at least its s.86A inflation-adjusted
level. Their measure is the 12 months to September CPI, rounded to the nearest
5p (Social Security Assistance in Scotland: up-rating for inflation in
2026-27, sections 2 and 3). SSI 2026/170 reg 12(3) raised the Carer Support
Payment component from 83.30 to 86.45 and the Scottish Carer Supplement from
11.29 to 11.70: both are the 3.8% September 2025 rate, rounded to 5p. The
supplement had no uprating metadata, so the model froze it at 11.70 a week from
2027 while the Carer Support Payment component kept rising.

Invariants, for every year from 2027 to 2039, the last year of the uprating
index:

1. Differential: the supplement and the Carer Support Payment component grow
   by the same factor from their April 2026 rates.
2. That factor is gov.benefit_uprating_cpi relative to 2026, so the supplement
   never falls while the index does not.
3. Metamorphic: setting CPI growth in the year before to g scales both
   components by 1 + g on the year, to within the rounding of the index.

The YAML tests in tests/policy/baseline/gov/social_security_scotland check
that a Carer Support Payment recipient in Scotland gets 52 weeks of the rate.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem

BASE_YEAR = 2026
YEARS = range(BASE_YEAR + 1, 2040)
SUPPLEMENT_2026 = 11.70
CSP_RATE_2026 = 86.45


@pytest.fixture(scope="module")
def parameters():
    return CountryTaxBenefitSystem().parameters


@pytest.mark.parametrize("year", YEARS)
def test_supplement_uprates_with_carer_support_payment(parameters, year):
    csp = parameters.gov.social_security_scotland.carer_support_payment
    index = parameters.gov.benefit_uprating_cpi
    factor = index(str(year)) / index(str(BASE_YEAR))

    assert csp.supplement(str(BASE_YEAR)) == SUPPLEMENT_2026
    assert csp.rate(str(BASE_YEAR)) == CSP_RATE_2026
    assert csp.supplement(str(year)) / SUPPLEMENT_2026 == pytest.approx(
        csp.rate(str(year)) / CSP_RATE_2026, rel=1e-12
    )
    assert csp.supplement(str(year)) == pytest.approx(
        SUPPLEMENT_2026 * factor, rel=1e-12
    )
    if index(str(year)) >= index(str(year - 1)):
        assert csp.supplement(str(year)) >= csp.supplement(str(year - 1))


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    year=st.integers(min_value=BASE_YEAR + 1, max_value=2035),
    growth=st.floats(min_value=0, max_value=0.12),
)
def test_supplement_follows_prior_year_cpi(year, growth):
    system = CountryTaxBenefitSystem()
    system.reset_parameters()
    cpi = system.parameters.gov.economic_assumptions.yoy_growth.obr
    shocked = [
        value_at_instant
        for value_at_instant in cpi.consumer_price_index.values_list
        if value_at_instant.instant_str == f"{year - 1}-01-01"
    ]
    assert len(shocked) == 1
    shocked[0].value = growth
    system.process_parameters()

    csp = system.parameters.gov.social_security_scotland.carer_support_payment
    supplement_growth = csp.supplement(str(year)) / csp.supplement(str(year - 1))
    rate_growth = csp.rate(str(year)) / csp.rate(str(year - 1))

    assert supplement_growth == pytest.approx(1 + growth, abs=1e-4)
    assert supplement_growth == pytest.approx(rate_growth, rel=1e-12)
