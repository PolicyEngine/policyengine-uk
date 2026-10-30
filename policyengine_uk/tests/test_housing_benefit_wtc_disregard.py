"""Housing Benefit WTC reservation against an independent statutory oracle.

SI 2006/213 reg 27(1)-(2), Sch 4 para 17(1), (3), and Sch 5 para 56
select the earnings or WTC disregard before childcare. Qualifying earnings,
the standard disregard, childcare and work conditions are assessed inputs.
The pension-age and Northern Ireland provisions apply the same ordering.

For every generated family, the WTC disregard lies between zero and both
WTC and the additional disregard amount. The model never applies both the
additional earnings and WTC disregards. Childcare uses only the remaining
earnings and credits, and assessed income equals, and never falls below,
the independent scalar legal calculation. Where paragraph 56 does not
apply, the model agrees with the previous path, reproduced by a reform
that sets the new disregard to zero.

The annual model uses 52 weeks, with the SI 2020/371 reg 5 temporary amount
in 2020 and no ongoing tax-credit awards from model year 2025. Populations
use core situations with independently supplied income components; they
never load a survey dataset or infer tax-credit awards from those incomes.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation

from policyengine_uk.model_api import BenUnit, Variable, YEAR
from policyengine_uk.system import system


TOLERANCE = 0.02
YEARS = (2018, 2020, 2021, 2024, 2025, 2026)
REGIONS = ("LONDON", "SCOTLAND", "WALES", "NORTHERN_IRELAND")
PROPERTY_SETTINGS = settings(
    max_examples=5,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def case(**overrides):
    result = dict(
        net=5_200,
        standard=1_300,
        childcare=4_160,
        children=1,
        wtc=100,
        ctc=0,
        other=0,
        worker=True,
        pension_age=False,
        region="LONDON",
    )
    result.update(overrides)
    return result


@st.composite
def families(draw):
    return case(
        net=draw(st.integers(0, 4_000_000)) / 100,
        standard=draw(st.sampled_from([260, 520, 1_040, 1_300])),
        childcare=draw(st.integers(0, 2_500_000)) / 100,
        children=draw(st.integers(0, 2)),
        wtc=draw(st.integers(0, 1_000_000)) / 100,
        ctc=draw(st.integers(0, 1_000_000)) / 100,
        other=draw(st.integers(0, 2_000_000)) / 100,
        worker=draw(st.booleans()),
        pension_age=draw(st.booleans()),
        region=draw(st.sampled_from(REGIONS)),
    )


POPULATIONS = st.lists(families(), min_size=1, max_size=12)
EDGE_CASES = [
    case(),
    case(net=0),
    case(net=500, standard=260, childcare=0, children=0, wtc=2_000),
    case(wtc=2_000, ctc=500, childcare=6_000),
    case(wtc=0, ctc=2_000),
    case(worker=False),
    case(net=6_349.19, other=1_000),
    case(net=6_349.20, other=1_000),
    case(net=6_349.21, other=1_000),
    case(pension_age=True),
    case(children=2, childcare=25_000, wtc=10_000, ctc=10_000),
    *(case(region=region) for region in REGIONS),
]


def legal_components(unit, year):
    """Apply the regulations to scalar assessed inputs in annual pounds."""
    net = unit["net"]
    standard = min(net, unit["standard"])
    cap = 15_600 if unit["children"] > 1 else 9_100 if unit["children"] else 0
    charge = min(unit["childcare"], cap)
    additional_amount = 1_929.20 if year == 2020 else 889.20
    # Sch 4 para 17(3): earnings must cover the standard, qualifying
    # childcare and additional amount. Compare money in statutory pence.
    covers_additional = round(net * 100) >= round(
        (standard + charge + additional_amount) * 100
    )
    additional = additional_amount if unit["worker"] and covers_additional else 0
    # Sch 5 para 56 applies only when para 17(1) does not apply.
    reserve = (
        min(unit["wtc"], additional_amount)
        if year < 2025 and unit["worker"] and not covers_additional
        else 0
    )
    # Reg 27(1)-(2): childcare follows the Schedule 4/5 disregards. When
    # additional earnings qualify, the full charge already fits earnings.
    limit = net - standard + unit["wtc"] - reserve + unit["ctc"]
    childcare = min(charge, limit)
    income = max(
        0,
        net
        + unit["wtc"]
        + unit["ctc"]
        + unit["other"]
        - standard
        - additional
        - reserve
        - childcare,
    )
    return dict(
        childcare=childcare,
        reserve=reserve,
        earnings_disregard=standard + additional,
        limit=limit,
        income=income,
    )


class previous_wtc_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.empty_array()


previous_wtc_disregard.__name__ = "housing_benefit_wtc_disregard"


class without_wtc_reservation(Reform):
    def apply(self):
        self.update_variable(previous_wtc_disregard)


def simulation(units, year, previous=False):
    people, benunits, households = {}, {}, {}
    for index, unit in enumerate(units):
        adult = f"adult_{index}"
        # Pin every ordinary-income component independently of upstream
        # award/tax calculations, while the full HB income formula runs.
        zero_income = {
            variable: {year: 0}
            for variable in (
                "self_employment_income",
                "property_income_after_finance_costs",
                "carers_allowance",
                "carer_support_payment",
                "esa_contrib",
                "jsa_contrib",
                "state_pension",
                "maternity_allowance",
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
                "iidb",
                "sda",
                "incapacity_benefit",
                "spousal_maintenance_income",
                "widowed_parents_allowance",
                "pension_contributions",
                "income_tax_before_winter_fuel_payment_charge",
                "national_insurance",
            )
        }
        people[adult] = {
            **zero_income,
            "age": {year: 70 if unit["pension_age"] else 40},
            "is_claimant_or_partner": {year: True},
            "employment_income": {year: unit["net"]},
            "private_pension_income": {year: unit["other"]},
            "childcare_expenses": {year: unit["childcare"]},
        }
        members = [adult]
        for child_index in range(unit["children"]):
            child = f"child_{index}_{child_index}"
            members.append(child)
            people[child] = {
                "age": {year: 8},
                "is_claimant_or_partner": {year: False},
                "is_child_or_young_person_for_legacy_benefits": {year: True},
            }
        benunits[f"family_{index}"] = {
            "members": members,
            "housing_benefit_net_earnings": {year: unit["net"]},
            "housing_benefit_special_earnings_disregard": {
                year: min(unit["net"], unit["standard"])
            },
            "housing_benefit_permitted_work_disregard": {year: 0},
            "housing_benefit_specified_or_temporary_accommodation_disregard": {year: 0},
            "housing_benefit_on_passporting_benefit": {year: False},
            "housing_benefit_pension_age_regulations_apply": {
                year: unit["pension_age"]
            },
            "in_receipt_of_guarantee_credit": {year: False},
            "in_receipt_of_savings_credit_only": {year: False},
            "meets_housing_benefit_additional_earnings_disregard_conditions": {
                year: unit["worker"]
            },
            "working_tax_credit": {year: unit["wtc"]},
            "child_tax_credit": {year: unit["ctc"]},
            # Preserve synthetic awards even after cessation to isolate the
            # active-scheme guard from the existing tax-credit formulas.
            "tax_credits": {year: unit["wtc"] + unit["ctc"]},
            "income_support": {year: 0},
            "claimant_or_partner_jsa_income": {year: 0},
            "claimant_or_partner_esa_income": {year: 0},
            "housing_benefit_tariff_income": {year: 0},
            "housing_benefit_maintenance_disregard": {year: 0},
            "housing_benefit_widowed_parents_allowance_income": {year: 0},
        }
        households[f"household_{index}"] = {
            "members": members,
            "region": {year: unit["region"]},
        }
    return Simulation(
        tax_benefit_system=without_wtc_reservation(system) if previous else system,
        situation={"people": people, "benunits": benunits, "households": households},
    )


def calculate(units, year, previous=False):
    sim = simulation(units, year, previous)
    return {
        key: np.asarray(sim.calculate(variable, year), dtype=float)
        for key, variable in {
            "childcare": "housing_benefit_applicable_income_childcare_element",
            "reserve": "housing_benefit_wtc_disregard",
            "earnings_disregard": "housing_benefit_applicable_income_disregard",
            "limit": "housing_benefit_childcare_earnings_limit",
            "income": "housing_benefit_applicable_income",
        }.items()
    }


def test_issue_2730_reserves_wtc_before_childcare():
    sim = simulation([case()], 2024)
    # Calculate an existing variable first: main reproduces a numeric
    # failure (4,000 instead of 3,900), without needing the new variable.
    assert sim.calculate("housing_benefit_applicable_income_childcare_element", 2024)[
        0
    ] == pytest.approx(3_900, abs=TOLERANCE)
    assert sim.calculate("housing_benefit_wtc_disregard", 2024)[0] == 100
    assert sim.calculate("housing_benefit_applicable_income", 2024)[0] == 0


def test_lone_parent_uses_the_existing_earnings_and_work_conditions():
    sim = simulation([case()], 2024)
    # Let the existing rules assess the earnings, ordinary disregard and
    # work condition rather than supplying those intermediate assessments.
    for variable in (
        "housing_benefit_net_earnings",
        "housing_benefit_special_earnings_disregard",
        "meets_housing_benefit_additional_earnings_disregard_conditions",
    ):
        sim.delete_arrays(variable, 2024)
    sim.set_input("weekly_hours", 2024, [16, 0])
    assert sim.calculate("housing_benefit_wtc_disregard", 2024)[0] == 100
    assert (
        sim.calculate("housing_benefit_applicable_income_childcare_element", 2024)[0]
        == 3_900
    )
    assert sim.calculate("housing_benefit_applicable_income", 2024)[0] == 0


@pytest.mark.parametrize("region", ["LONDON", "NORTHERN_IRELAND"])
def test_savings_credit_only_uses_the_corrected_childcare_modification(region):
    sim = simulation([case(pension_age=True, region=region)], 2024)
    for variable, value in {
        "in_receipt_of_savings_credit_only": True,
        "pension_credit_income": 10_000,
        "pension_credit": 500,
        "pension_credit_earnings_disregard": 1_040,
        "pension_credit_war_pension_income": 0,
    }.items():
        sim.set_input(variable, 2024, [value])
    # SI 2006/214 reg 27(4)(b), (5), reg 33(9); NI SR 2006/406 reg
    # 25(4)(b), (5), reg 31(9): correct the childcare modification using
    # the remaining WTC pool. The listed modifications do not deduct the
    # WTC reserve directly from the Secretary of State's assessment.
    # 10,000 + 500 - 3,900 - (1,300 - 1,040) = 6,340.
    assert sim.calculate("housing_benefit_wtc_disregard", 2024)[0] == 100
    assert (
        sim.calculate("housing_benefit_applicable_income_childcare_element", 2024)[0]
        == 3_900
    )
    assert sim.calculate("housing_benefit_applicable_income", 2024)[0] == 6_340


@PROPERTY_SETTINGS
@given(units=POPULATIONS, year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
@example(units=EDGE_CASES, year=2020)
@example(units=EDGE_CASES, year=2025)
def test_assessed_income_equals_and_never_falls_below_the_regulations(units, year):
    actual = calculate(units, year)
    expected = [legal_components(unit, year) for unit in units]
    for key, values in actual.items():
        np.testing.assert_allclose(
            values, [unit[key] for unit in expected], rtol=0, atol=TOLERANCE
        )
    assert np.all(
        actual["income"] + TOLERANCE >= np.array([unit["income"] for unit in expected])
    )


@PROPERTY_SETTINGS
@given(units=POPULATIONS, year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
def test_wtc_disregard_is_bounded_and_does_not_stack_with_earnings(units, year):
    actual = calculate(units, year)
    annual_amount = 1_929.20 if year == 2020 else 889.20
    assert np.all(actual["reserve"] >= 0)
    assert np.all(
        actual["reserve"]
        <= np.minimum([unit["wtc"] for unit in units], annual_amount) + TOLERANCE
    )
    standard = np.array([min(unit["net"], unit["standard"]) for unit in units])
    additional = actual["earnings_disregard"] - standard
    assert np.all((additional <= TOLERANCE) | (actual["reserve"] <= TOLERANCE))


@PROPERTY_SETTINGS
@given(units=POPULATIONS, year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
@example(units=EDGE_CASES, year=2025)
def test_previous_path_agrees_where_paragraph_56_does_not_apply(units, year):
    unchanged = [unit for unit in units if legal_components(unit, year)["reserve"] == 0]
    # Always include a work-condition failure, no WTC, and sufficient
    # earnings, so every population exercises the differential check.
    unchanged.extend(
        [case(worker=False), case(wtc=0), case(net=20_000, childcare=1_000)]
    )
    actual = calculate(unchanged, year)
    previous = calculate(unchanged, year, previous=True)
    for variable in actual:
        np.testing.assert_allclose(
            actual[variable], previous[variable], rtol=0, atol=TOLERANCE
        )


@pytest.mark.parametrize("offset", [-0.01, 0, 0.01])
def test_additional_earnings_threshold_includes_equality(offset):
    unit = case(net=6_349.20 + offset)
    actual = calculate([unit], 2024)
    assert actual["reserve"][0] == (100 if offset < 0 else 0)
    assert actual["earnings_disregard"][0] == pytest.approx(
        1_300 if offset < 0 else 2_189.20, abs=TOLERANCE
    )


@pytest.mark.parametrize("year", YEARS)
def test_wtc_disregard_honours_the_historical_amount_and_cessation(year):
    unit = case(net=500, standard=260, childcare=0, children=0, wtc=2_000)
    actual = calculate([unit], year)
    expected = 0 if year >= 2025 else 1_929.20 if year == 2020 else 889.20
    assert actual["reserve"][0] == pytest.approx(expected, abs=TOLERANCE)
    assert actual["income"][0] == pytest.approx(2_240 - expected, abs=TOLERANCE)
