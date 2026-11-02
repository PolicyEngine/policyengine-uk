"""Class 1A changes enter the existing employer-NI incidence budget.

The assertions use the employer's piecewise cash budget, independently of the
incidence formulas. Class 1A itself is computed from real company-car inputs
(SSCBA 1992 s.10); neither that liability nor a wage response is supplied.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.scenarios import company_car_tax_rise_2030
from policyengine_uk.scenarios.company_car_tax_rise_2030 import (
    COMPANY_CAR_TAX_RISE_2030,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

INCIDENCE = "gov.contrib.policyengine.employer_ni"
EMPLOYER_RATE = "gov.hmrc.national_insurance.class_1.employer_scale[1].rate"


def values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def situation(year, pay, *, age=40, price=40_000, emissions=120):
    return {
        "people": {
            "person": {
                "age": {year: age},
                "employment_income": {year: pay},
                "company_car_list_price": {year: price},
                "company_car_co2_emissions": {year: emissions},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


def assert_cost_agreement(simulation, year):
    for world, replica in [
        (simulation.baseline, "baseline_employer_cost"),
        (simulation, "adjusted_employer_cost"),
    ]:
        # These fixtures have no statutory pay or employer pension. Checking
        # the independently assembled total prevents all cost replicas from
        # agreeing merely because they share the same omitted Class 1A.
        cash_and_ni = values(world, "employment_income", year) + values(
            world, "ni_employer", year
        )
        np.testing.assert_allclose(
            values(world, "employer_cost", year), cash_and_ni, atol=0.02, rtol=0
        )
        np.testing.assert_allclose(
            values(simulation, replica, year), cash_and_ni, atol=0.02, rtol=0
        )


@pytest.mark.parametrize("age", [40, 20])
def test_class_1a_rate_change_preserves_total_employer_cost(age):
    year, pay = 2026, 80_000 if age == 40 else 30_000
    simulation = Simulation(
        situation=situation(year, pay, age=age),
        reform={EMPLOYER_RATE: {"2026-04-06.2100-12-31": 0.16}},
    )
    baseline_parameters = simulation.baseline.tax_benefit_system.parameters(str(year))
    reform_parameters = simulation.tax_benefit_system.parameters(str(year))
    baseline_class_1 = baseline_parameters.gov.hmrc.national_insurance.class_1
    reform_class_1 = reform_parameters.gov.hmrc.national_insurance.class_1
    rb = baseline_class_1.employer_scale.components[1].rate
    rr = reform_class_1.employer_scale.components[1].rate
    tb = baseline_class_1.employer_scale.components[1].threshold * 52
    tr = reform_class_1.employer_scale.components[1].threshold * 52
    if age < 21:
        tb = max(tb, baseline_class_1.thresholds.upper_secondary_threshold * 52)
        tr = max(tr, reform_class_1.thresholds.upper_secondary_threshold * 52)

    # HMRC 480 Appendix 2: a 120g/km petrol car has a 30% benefit in
    # 2026-27, hence 40,000 * .30 = 12,000. The actual Class 1A follows
    # the secondary percentage (SSCBA 1992 s.10(5)).
    benefit = 12_000
    assert values(simulation, "benefits_in_kind", year) == pytest.approx([benefit])
    assert values(simulation.baseline, "ni_class_1a", year) == pytest.approx(
        [rb * benefit]
    )
    assert values(simulation, "ni_class_1a", year) == pytest.approx([rr * benefit])
    baseline_total = pay + rb * max(pay - tb, 0) + rb * benefit
    target = baseline_total - rr * benefit
    expected_pay = target if target <= tr else (target + rr * tr) / (1 + rr)
    assert expected_pay > 0
    assert values(simulation, "employment_income", year) == pytest.approx(
        [expected_pay], abs=0.02
    )
    assert values(simulation, "baseline_employer_cost", year) == pytest.approx(
        [baseline_total], abs=0.02
    )
    assert values(simulation, "adjusted_employer_cost", year) == pytest.approx(
        [baseline_total], abs=0.02
    )
    if age == 20:
        # Under-21 Class 1 zero-rating is not a Class 1A exemption.
        assert values(simulation, "ni_class_1_employer", year) == pytest.approx([0])
        assert expected_pay == pytest.approx(29_880, abs=0.02)
    assert_cost_agreement(simulation, year)


def test_company_car_scenario_changes_pay_without_a_class_1_schedule_change():
    year, initial_pay = 2030, 80_000
    simulation = Simulation(
        situation=situation(year, initial_pay, price=50_000, emissions=0),
        scenario=company_car_tax_rise_2030,
    )
    baseline_parameters = simulation.baseline.tax_benefit_system.parameters(str(year))
    reform_parameters = simulation.tax_benefit_system.parameters(str(year))
    baseline_class_1 = baseline_parameters.gov.hmrc.national_insurance.class_1
    reform_class_1 = reform_parameters.gov.hmrc.national_insurance.class_1
    r = baseline_class_1.employer_scale.components[1].rate
    assert reform_class_1.employer_scale.components[1].rate == r
    assert (
        reform_class_1.employer_scale.components[1].threshold
        == baseline_class_1.employer_scale.components[1].threshold
    )
    assert (
        reform_parameters.gov.contrib.policyengine.employer_ni.employee_incidence == 1
    )
    haircut = baseline_parameters.gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate
    expected_opening_pay = initial_pay * (1 - haircut)
    assert values(simulation.baseline, "employment_income", year) == pytest.approx(
        [expected_opening_pay], abs=0.02
    )
    # The existing scenario moves the zero-emission percentage from 9 to
    # 10 points, without a new NI parameter: benefit 4,500 -> 5,000.
    assert values(simulation.baseline, "benefits_in_kind", year) == pytest.approx(
        [4_500]
    )
    assert values(simulation, "benefits_in_kind", year) == pytest.approx([5_000])
    class_1a_change = values(simulation, "ni_class_1a", year) - values(
        simulation.baseline, "ni_class_1a", year
    )
    assert class_1a_change == pytest.approx([r * 500])
    expected_change = -r * 500 / (1 + r)
    assert values(simulation, "employer_ni_fixed_employer_cost_change", year) == (
        pytest.approx([expected_change], abs=0.02)
    )
    assert values(simulation, "employment_income", year) == pytest.approx(
        [expected_opening_pay + expected_change], abs=0.02
    )
    assert_cost_agreement(simulation, year)
    np.testing.assert_allclose(
        values(simulation, "adjusted_employer_cost", year),
        values(simulation, "baseline_employer_cost", year),
        atol=0.02,
        rtol=0,
    )


def weighted_car_simulation(employee, consumer, capital):
    # One person in household 1, two in household 2. Neither exposures nor
    # person weights are uniform, and the third person has no company car.
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2, 3],
                "person_benunit_id": [1, 2, 2],
                "person_household_id": [1, 2, 2],
                "age": [40, 40, 45],
                "employment_income": [80_000, 60_000, 70_000],
                "company_car_list_price": [50_000, 100_000, 0],
                "company_car_co2_emissions": [0, 0, 0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "household_weight": [2, 3],
                "region": ["LONDON", "WALES"],
                "council_tax": [0, 0],
                "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
                "rent": [0, 0],
                "corporate_wealth": [10_000, 60_000],
                "food_and_non_alcoholic_beverages_consumption": [3_000, 8_000],
            }
        ),
        fiscal_year=2030,
    )
    return Simulation(
        dataset=dataset,
        reform={
            **COMPANY_CAR_TAX_RISE_2030,
            **{
                f"{INCIDENCE}.{name}_incidence": {"2030-04-06.2100-12-31": share}
                for name, share in [
                    ("employee", employee),
                    ("consumer", consumer),
                    ("capital", capital),
                ]
            },
        },
    )


def test_partial_incidence_allocates_the_weighted_class_1a_residual():
    simulation = weighted_car_simulation(employee=0.5, consumer=0.2, capital=0.6)
    year = 2030
    r = (
        simulation.tax_benefit_system.parameters(str(year))
        .gov.hmrc.national_insurance.class_1.employer_scale.components[1]
        .rate
    )
    delta_a = r * np.asarray([500, 1_000, 0])
    np.testing.assert_allclose(
        values(simulation, "ni_class_1a", year)
        - values(simulation.baseline, "ni_class_1a", year),
        delta_a,
        atol=0.01,
        rtol=0,
    )
    # With an unchanged above-threshold schedule, the full wage response
    # is -delta_a/(1+r). Half incidence leaves exactly half delta_a in costs.
    np.testing.assert_allclose(
        values(simulation, "employment_income", year)
        - values(simulation.baseline, "employment_income", year),
        -0.5 * delta_a / (1 + r),
        atol=0.02,
        rtol=0,
    )
    assert_cost_agreement(simulation, year)
    residual = values(simulation, "adjusted_employer_cost", year) - values(
        simulation, "baseline_employer_cost", year
    )
    np.testing.assert_allclose(residual, 0.5 * delta_a, atol=0.02, rtol=0)
    weights = values(simulation, "person_weight", year)
    np.testing.assert_array_equal(weights, [2, 3, 3])
    total = np.dot(weights, residual)
    assert total > 0
    consumer = values(simulation, "employer_ni_response_consumer_incidence", year)
    capital = values(simulation, "employer_ni_response_capital_incidence", year)
    # Household exposures are divided by membership, then normalised using
    # person weights: consumption [3000,4000,4000], wealth [10000,30000,30000].
    np.testing.assert_allclose(
        consumer,
        0.2 * total * np.asarray([3_000, 4_000, 4_000]) / 30_000,
        atol=0.01,
        rtol=0,
    )
    np.testing.assert_allclose(
        capital,
        0.6 * total * np.asarray([10_000, 30_000, 30_000]) / 200_000,
        atol=0.01,
        rtol=0,
    )
    assert np.dot(weights, consumer) == pytest.approx(0.2 * total, abs=0.02)
    assert np.dot(weights, capital) == pytest.approx(0.6 * total, abs=0.02)
    # Declared shares sum to .8, so .2 remains unallocated; do not renormalise.
    assert np.dot(weights, consumer + capital) == pytest.approx(0.8 * total, abs=0.02)


def test_all_three_zero_shares_preserve_static_scoring_with_real_exposures():
    simulation = weighted_car_simulation(employee=0, consumer=0, capital=0)
    year = 2030
    np.testing.assert_allclose(
        values(simulation, "employment_income", year),
        values(simulation.baseline, "employment_income", year),
        atol=0.01,
        rtol=0,
    )
    for variable in [
        "employer_ni_fixed_employer_cost_change",
        "employer_ni_response_consumer_incidence",
        "employer_ni_response_capital_incidence",
    ]:
        np.testing.assert_allclose(
            values(simulation, variable, year), 0, atol=0, rtol=0
        )
    delta_a = values(simulation, "ni_class_1a", year) - values(
        simulation.baseline, "ni_class_1a", year
    )
    assert delta_a[:2].min() > 0
    assert_cost_agreement(simulation, year)
    np.testing.assert_allclose(
        values(simulation, "adjusted_employer_cost", year)
        - values(simulation, "baseline_employer_cost", year),
        delta_a,
        atol=0.02,
        rtol=0,
    )


@pytest.mark.parametrize("pay", [0, 1])
def test_class_1a_change_preserves_zero_pay_and_the_cash_pay_floor(pay):
    simulation = Simulation(
        situation=situation(2030, pay, price=50_000, emissions=0),
        scenario=company_car_tax_rise_2030,
    )
    # A £75 Class 1A increase cannot be absorbed in zero or £1 of cash pay.
    # Allow a penny for float32 currency cancellation at the cash-pay floor.
    assert values(simulation, "employment_income", 2030) == pytest.approx([0], abs=0.01)
    assert_cost_agreement(simulation, 2030)
    assert (
        values(simulation, "adjusted_employer_cost", 2030)[0]
        > values(simulation, "baseline_employer_cost", 2030)[0]
    )
