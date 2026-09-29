"""Universal Credit Act 2025: the standard allowance and the LCWRA element.

s1 takes the standard allowance out of the section 150 review for 2026-27 to
2029-30 and sets a minimum: the 2025-26 amount raised by September CPI each
year (Step 2) times 1 + that year's uplift (Step 3: 2.3%, 3.1%, 4.0%, 4.8%).
s3 freezes the LCWRA element for the same years. These tests compute the s1
minimum independently from the 2025-26 amounts and compare it with the
model's projection, and check the freeze and the return to September CPI
uprating from April 2030.
"""

import pytest

import policyengine_uk.scenarios.uc_reform as uc_reform
from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.system import system

UC = "gov.dwp.universal_credit"
UPLIFT = {2026: 0.023, 2027: 0.031, 2028: 0.040, 2029: 0.048}
# Published 2025-26 and 2026-27 monthly amounts (Benefit and pension rates
# 2026 to 2027).
AMOUNTS_2025 = {
    "SINGLE_YOUNG": 316.98,
    "SINGLE_OLD": 400.14,
    "COUPLE_YOUNG": 497.55,
    "COUPLE_OLD": 628.10,
}
AMOUNTS_2026 = {
    "SINGLE_YOUNG": 338.58,
    "SINGLE_OLD": 424.90,
    "COUPLE_YOUNG": 528.34,
    "COUPLE_OLD": 666.97,
}


def rise(parameters, year):
    return parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating(
        f"{year}-01-01"
    )


def standard_allowance(parameters, claimant_type, year):
    amounts = parameters.gov.dwp.universal_credit.standard_allowance.amount
    return getattr(amounts, claimant_type)(f"{year}-04-30")


def statutory_minimum(parameters, amount_2025, year):
    """s1(2): Step 2 compounds September CPI from 2025-26; Step 3 adds the
    year's uplift without compounding it."""
    step_2 = amount_2025
    for tax_year in range(2026, year + 1):
        step_2 *= 1 + rise(parameters, tax_year)
    return step_2 * (1 + UPLIFT[year])


@pytest.mark.parametrize("claimant_type", ["SINGLE_OLD", "COUPLE_YOUNG", "COUPLE_OLD"])
def test_april_2026_amounts_are_the_statutory_minimum(claimant_type):
    minimum = statutory_minimum(system.parameters, AMOUNTS_2025[claimant_type], 2026)
    assert minimum == pytest.approx(AMOUNTS_2026[claimant_type], abs=0.01)


def test_single_under_25_amount_for_2026_is_above_the_minimum():
    """£338.58 exceeds the s1 minimum of £336.59; projections keep that
    margin in proportion."""
    minimum = statutory_minimum(system.parameters, AMOUNTS_2025["SINGLE_YOUNG"], 2026)
    assert minimum == pytest.approx(336.59, abs=0.01)
    assert AMOUNTS_2026["SINGLE_YOUNG"] > minimum


@pytest.mark.parametrize("claimant_type", list(AMOUNTS_2025))
def test_projection_follows_the_act_to_2029_30(claimant_type):
    parameters = system.parameters
    published = AMOUNTS_2026[claimant_type]
    minimum_2026 = statutory_minimum(parameters, AMOUNTS_2025[claimant_type], 2026)
    assert standard_allowance(parameters, claimant_type, 2026) == published
    for year in (2027, 2028, 2029):
        expected = (
            published
            * statutory_minimum(parameters, AMOUNTS_2025[claimant_type], year)
            / minimum_2026
        )
        assert standard_allowance(parameters, claimant_type, year) == pytest.approx(
            expected, rel=1e-5
        ), year


@pytest.mark.parametrize("claimant_type", list(AMOUNTS_2025))
def test_september_cpi_uprating_resumes_from_april_2030(claimant_type):
    parameters = system.parameters
    for year in range(2030, 2036):
        before = standard_allowance(parameters, claimant_type, year - 1)
        after = standard_allowance(parameters, claimant_type, year)
        assert after / before - 1 == pytest.approx(rise(parameters, year), abs=2e-5)


def test_lcwra_element_is_frozen_to_2029_30_then_rises_by_september_cpi():
    parameters = system.parameters
    lcwra = parameters.gov.dwp.universal_credit.elements.disabled.amount
    for year in (2026, 2027, 2028, 2029):
        assert lcwra(f"{year}-04-30") == 217.26
    assert lcwra("2030-04-30") == pytest.approx(
        217.26 * (1 + rise(parameters, 2030)), rel=1e-5
    )


def test_uplift_is_a_lever():
    """Setting the uplift to zero from 2027-28 leaves the standard allowance
    on September CPI alone after April 2026."""
    simulation = Simulation(
        situation={
            "people": {"person": {"age": {2026: 30}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        },
        scenario=Scenario(
            parameter_changes={
                f"{UC}.rebalancing.standard_allowance_uplift": {
                    "year:2027-01-01:10": 0.023
                }
            },
            applied_before_data_load=True,
        ),
    )
    parameters = simulation.tax_benefit_system.parameters
    assert standard_allowance(parameters, "SINGLE_OLD", 2027) == pytest.approx(
        424.90 * (1 + rise(parameters, 2027)), rel=1e-5
    )


def test_protected_lcwra_amount_for_2026_is_the_published_rate():
    """s4: the protected LCWRA amount keeps standard allowance plus LCWRA
    rising at least with September CPI. The model's protection scales the
    2025-26 combined award by the benefit index, so with September CPI it
    gives the published £429.80: (£400.14 + £423.27) x 1.038 - £424.90."""
    simulation = Simulation(
        situation={
            "people": {"person": {"age": {2026: 30}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )
    protected = uc_reform._protected_existing_health_element_monthly(simulation, 2026)
    assert protected == pytest.approx(429.80, abs=0.01)
