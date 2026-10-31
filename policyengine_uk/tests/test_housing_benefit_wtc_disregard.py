"""Housing Benefit WTC reservation against an independent statutory oracle.

SI 2006/213 reg 27(1)-(2), Sch 4 para 17(1), (3), and Sch 5 para 56
select the earnings or WTC disregard before childcare. Qualifying earnings,
the standard and accommodation disregards, childcare and work conditions are
assessed inputs. The pension-age and Northern Ireland provisions apply the
same ordering.

For every generated family, the WTC disregard lies between zero and both
WTC and the additional disregard amount. The model never applies both the
additional earnings and WTC disregards, including when a dataset,
``set_input`` or a reform supplies or replaces the childcare deduction.
Childcare uses only the remaining earnings and credits, and assessed income
equals, and never falls below, the independent scalar legal calculation.
That calculation settles paragraph 17 by trying both outcomes, rather than
assuming the full-charge shortcut the model uses. Where paragraph 56 does not
apply, the model agrees with the previous path, reproduced by a reform that
sets the new disregard to zero. Supplying the deduction the model calculates
leaves every result unchanged.

The annual model uses 52 weeks, with the SI 2020/371 reg 5 temporary amount
in 2020 and no ongoing tax-credit awards from model year 2025. Accommodation
amounts are supplied as assessed inputs, so the properties cover the earnings
test's arithmetic in every year; in law the accommodation disregard (from 5
October 2026) and WTC (to 5 April 2025) coexist only under a reform that
keeps tax credits. Populations use core situations with independently
supplied income components; they never load a survey dataset or infer
tax-credit awards from those incomes.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.errors import CycleError
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation

from policyengine_uk import Simulation as UKSimulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.model_api import BenUnit, Variable, YEAR, min_
from policyengine_uk.system import system
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
)


TOLERANCE = 0.02
YEARS = (2018, 2020, 2021, 2024, 2025, 2026)
REGIONS = ("LONDON", "SCOTLAND", "WALES", "NORTHERN_IRELAND")
PROPERTY_SETTINGS = settings(
    max_examples=5,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
CHILDCARE = "housing_benefit_applicable_income_childcare_element"
LIMIT = "housing_benefit_childcare_earnings_limit"


def case(**overrides):
    result = dict(
        net=5_200,
        standard=1_300,
        accommodation=0,
        childcare=4_160,
        supplied=None,
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


def pounds(maximum):
    return st.integers(0, maximum * 100).map(lambda pence: pence / 100)


@st.composite
def families(draw, supplied=False):
    return case(
        net=draw(pounds(40_000)),
        standard=draw(st.sampled_from([260, 520, 1_040, 1_300])),
        accommodation=draw(st.one_of(st.just(0), pounds(6_500))),
        childcare=draw(pounds(25_000)),
        supplied=draw(pounds(25_000)) if supplied else None,
        children=draw(st.integers(0, 2)),
        wtc=draw(pounds(10_000)),
        ctc=draw(pounds(10_000)),
        other=draw(pounds(20_000)),
        worker=draw(st.booleans()),
        pension_age=draw(st.booleans()),
        region=draw(st.sampled_from(REGIONS)),
    )


@st.composite
def populations(draw):
    # A supplied deduction is set for the whole population, as a dataset
    # column or a set_input call sets it.
    supplied = draw(st.booleans())
    return draw(st.lists(families(supplied), min_size=1, max_size=12))


POPULATIONS = populations()
SUPPLIED_POPULATIONS = st.lists(families(supplied=True), min_size=1, max_size=12)
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
    case(net=2_000, standard=260, accommodation=1_000, childcare=0, wtc=1_000),
    case(net=2_000, standard=260, accommodation=6_000, childcare=0, wtc=1_000),
    case(net=8_000, accommodation=1_000, childcare=4_160, wtc=500),
    *(case(region=region) for region in REGIONS),
]
SUPPLIED_EDGE_CASES = [
    # The review's case: earnings cover the supplied nil deduction.
    case(supplied=0),
    case(supplied=3_900),
    case(supplied=4_160),
    case(net=6_349.20, supplied=4_160),
    case(net=6_349.19, supplied=4_160),
    case(net=2_000, standard=260, accommodation=1_000, childcare=0, supplied=0),
    case(net=2_000, standard=260, accommodation=500, childcare=0, supplied=0),
    case(childcare=25_000, children=2, supplied=100, wtc=5_000),
    case(worker=False, supplied=0),
]


def legal_components(unit, year):
    """Apply the regulations to scalar assessed inputs in annual pounds."""
    net = unit["net"]
    standard = min(net, unit["standard"])
    # Sch 4 para 18 takes the earnings the other disregards leave.
    accommodation = min(unit["accommodation"], net - standard)
    cap = 15_600 if unit["children"] > 1 else 9_100 if unit["children"] else 0
    charge = min(unit["childcare"], cap)
    additional_amount = 1_929.20 if year == 2020 else 889.20
    earnings = net - standard - accommodation

    def deduction(reserve):
        if unit["supplied"] is not None:
            return unit["supplied"]
        # Reg 27(1)(c), (2): earnings, then the credits that remain after
        # the Sch 5 disregards.
        return min(charge, earnings + unit["wtc"] - reserve + unit["ctc"])

    def covers(reserve):
        # Sch 4 para 17(1), (3): the other disregards, the deductible
        # childcare and the additional amount, compared in statutory pence.
        return round(net * 100) >= round(
            (standard + accommodation + deduction(reserve) + additional_amount) * 100
        )

    # Sch 5 para 56 applies "except in a case which falls under" para 17(1).
    # Try para 17(1) with every credit available; where it fails, reserve
    # the WTC and check that the smaller credit pool keeps it failing.
    reserve = 0
    if unit["worker"] and year < 2025 and not covers(0):
        reserve = min(unit["wtc"], additional_amount)
        assert not covers(reserve), "no consistent paragraph 17 outcome"
    additional = additional_amount if unit["worker"] and covers(reserve) else 0
    childcare = deduction(reserve)
    limit = earnings + unit["wtc"] - reserve + unit["ctc"]
    income = max(
        0,
        net
        + unit["wtc"]
        + unit["ctc"]
        + unit["other"]
        - standard
        - accommodation
        - additional
        - reserve
        - childcare,
    )
    return dict(
        childcare=childcare,
        reserve=reserve,
        earnings_disregard=standard + accommodation + additional,
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


def simulation(units, year, previous=False, tax_benefit_system=None):
    supplied = [unit["supplied"] is not None for unit in units]
    assert all(supplied) or not any(supplied), "supply the deduction for all"
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
            "housing_benefit_specified_or_temporary_accommodation_disregard": {
                year: unit["accommodation"]
            },
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
        if unit["supplied"] is not None:
            benunits[f"family_{index}"][CHILDCARE] = {year: unit["supplied"]}
        households[f"household_{index}"] = {
            "members": members,
            "region": {year: unit["region"]},
        }
    if tax_benefit_system is None:
        tax_benefit_system = without_wtc_reservation(system) if previous else system
    return Simulation(
        tax_benefit_system=tax_benefit_system,
        situation={"people": people, "benunits": benunits, "households": households},
    )


OUTPUTS = {
    "childcare": CHILDCARE,
    "reserve": "housing_benefit_wtc_disregard",
    "earnings_disregard": "housing_benefit_applicable_income_disregard",
    "limit": LIMIT,
    "income": "housing_benefit_applicable_income",
}


def results(sim, year):
    return {
        key: np.asarray(sim.calculate(variable, year), dtype=float)
        for key, variable in OUTPUTS.items()
    }


def calculate(units, year, previous=False):
    return results(simulation(units, year, previous), year)


def assert_one_additional_disregard(units, actual):
    """The additional earnings disregard and a positive WTC disregard never
    both apply to a benefit unit."""
    standard = np.array([min(unit["net"], unit["standard"]) for unit in units])
    net = np.array([unit["net"] for unit in units])
    accommodation = np.minimum(
        [unit["accommodation"] for unit in units], net - standard
    )
    additional = actual["earnings_disregard"] - standard - accommodation
    both = (additional > TOLERANCE) & (actual["reserve"] > TOLERANCE)
    assert not both.any(), [unit for unit, b in zip(units, both) if b]


def test_issue_2730_reserves_wtc_before_childcare():
    sim = simulation([case()], 2024)
    # Calculate an existing variable first: main reproduces a numeric
    # failure (4,000 instead of 3,900), without needing the new variable.
    assert sim.calculate(CHILDCARE, 2024)[0] == pytest.approx(3_900, abs=TOLERANCE)
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
    assert sim.calculate(CHILDCARE, 2024)[0] == 3_900
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
    assert sim.calculate(CHILDCARE, 2024)[0] == 3_900
    assert sim.calculate("housing_benefit_applicable_income", 2024)[0] == 6_340


@PROPERTY_SETTINGS
@given(units=POPULATIONS, year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
@example(units=EDGE_CASES, year=2020)
@example(units=EDGE_CASES, year=2025)
@example(units=SUPPLIED_EDGE_CASES, year=2024)
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
@example(units=SUPPLIED_EDGE_CASES, year=2020)
def test_wtc_disregard_is_bounded_and_does_not_stack_with_earnings(units, year):
    actual = calculate(units, year)
    annual_amount = 1_929.20 if year == 2020 else 889.20
    assert np.all(actual["reserve"] >= 0)
    assert np.all(
        actual["reserve"]
        <= np.minimum([unit["wtc"] for unit in units], annual_amount) + TOLERANCE
    )
    assert_one_additional_disregard(units, actual)


@PROPERTY_SETTINGS
@given(units=SUPPLIED_POPULATIONS, year=st.sampled_from(YEARS))
@example(units=[case(supplied=0)], year=2024)
@example(units=SUPPLIED_EDGE_CASES, year=2024)
def test_additional_earnings_and_wtc_disregards_never_both_apply(units, year):
    """Earnings, WTC, the standard and accommodation disregards and a
    supplied childcare deduction never give a benefit unit both additional
    disregards."""
    assert_one_additional_disregard(units, calculate(units, year))


@PROPERTY_SETTINGS
@given(units=POPULATIONS, year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
@example(units=EDGE_CASES, year=2025)
@example(units=SUPPLIED_EDGE_CASES, year=2024)
def test_previous_path_agrees_where_paragraph_56_does_not_apply(units, year):
    unchanged = [unit for unit in units if legal_components(unit, year)["reserve"] == 0]
    supplied = units[0]["supplied"] is not None
    # Always include a work-condition failure, no WTC, and sufficient
    # earnings, so every population exercises the differential check.
    unchanged.extend(
        [
            case(worker=False, supplied=0 if supplied else None),
            case(wtc=0, supplied=3_000 if supplied else None),
            case(net=20_000, childcare=1_000, supplied=1_000 if supplied else None),
        ]
    )
    actual = calculate(unchanged, year)
    previous = calculate(unchanged, year, previous=True)
    for variable in actual:
        np.testing.assert_allclose(
            actual[variable], previous[variable], rtol=0, atol=TOLERANCE
        )


@PROPERTY_SETTINGS
@given(units=st.lists(families(), min_size=1, max_size=12), year=st.sampled_from(YEARS))
@example(units=EDGE_CASES, year=2024)
@example(units=EDGE_CASES, year=2020)
def test_supplying_the_calculated_deduction_changes_nothing(units, year):
    """The full-charge test and a test reading the supplied deduction are two
    implementations of Sch 4 para 17(3)(b): supplying the deduction the
    model calculates must leave every result unchanged."""
    calculated = calculate(units, year)
    supplied = [
        {**unit, "supplied": float(value)}
        for unit, value in zip(units, calculated["childcare"])
    ]
    replayed = calculate(supplied, year)
    for variable in calculated:
        np.testing.assert_allclose(
            replayed[variable], calculated[variable], rtol=0, atol=TOLERANCE
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


def test_negative_wtc_gives_no_disregard():
    actual = calculate([case(net=500, standard=260, childcare=0, wtc=-100)], 2024)
    assert actual["reserve"][0] == 0


@pytest.mark.parametrize(
    "accommodation,reserve,earnings_disregard",
    [
        # Sch 4 para 17(3)(a): 2,000 >= 260 + 889.20, so para 17(1) applies.
        (0, 0, 260 + 889.20),
        # 2,000 < 260 + 1,000 + 889.20, so para 56 reserves 889.20 of WTC.
        (1_000, 889.20, 260 + 1_000),
    ],
)
def test_accommodation_disregard_counts_in_the_additional_earnings_test(
    accommodation, reserve, earnings_disregard
):
    unit = case(
        net=2_000,
        standard=260,
        accommodation=accommodation,
        childcare=0,
        children=0,
        wtc=1_000,
    )
    actual = calculate([unit], 2024)
    assert actual["reserve"][0] == pytest.approx(reserve, abs=TOLERANCE)
    assert actual["earnings_disregard"][0] == pytest.approx(
        earnings_disregard, abs=TOLERANCE
    )


def test_supplied_childcare_deduction_keeps_one_additional_disregard():
    sim = simulation([case()], 2024)
    sim.set_input(CHILDCARE, 2024, [0])
    actual = results(sim, 2024)
    # Sch 4 para 17: 5,200 >= 1,300 + 0 + 889.20, so para 56 does not apply.
    assert actual["earnings_disregard"][0] == pytest.approx(2_189.20, abs=TOLERANCE)
    assert actual["reserve"][0] == 0
    # 5,200 + 100 - 2,189.20 - 0, as without the WTC disregard.
    assert actual["income"][0] == pytest.approx(3_110.80, abs=TOLERANCE)


def test_supplied_childcare_limit_keeps_one_additional_disregard():
    sim = simulation([case()], 2024)
    sim.set_input(LIMIT, 2024, [0])
    actual = results(sim, 2024)
    assert actual["childcare"][0] == 0
    assert actual["earnings_disregard"][0] == pytest.approx(2_189.20, abs=TOLERANCE)
    assert actual["reserve"][0] == 0
    assert actual["income"][0] == pytest.approx(3_110.80, abs=TOLERANCE)


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_dataset_supplied_childcare_deduction_keeps_one_additional_disregard():
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 1],
            "person_household_id": [1, 1],
            "age": [40, 8],
            "childcare_expenses": [4_160.0, 0.0],
        }
    )
    benunit = pd.DataFrame(
        {
            "benunit_id": [1],
            "housing_benefit_net_earnings": [5_200.0],
            "housing_benefit_special_earnings_disregard": [1_300.0],
            "housing_benefit_permitted_work_disregard": [0.0],
            "housing_benefit_specified_or_temporary_accommodation_disregard": [0.0],
            "housing_benefit_on_passporting_benefit": [False],
            "meets_housing_benefit_additional_earnings_disregard_conditions": [True],
            "num_relevant_children_for_housing_benefit_childcare": [1],
            "working_tax_credit": [100.0],
            "child_tax_credit": [0.0],
            CHILDCARE: [0.0],
        }
    )
    household = pd.DataFrame(
        {
            "household_id": [1],
            "region": ["LONDON"],
            "tenure_type": ["RENT_PRIVATELY"],
            "council_tax": [1_500.0],
            "rent": [0.0],
            "household_weight": [1.0],
        }
    )
    sim = UKSimulation(
        dataset=UKSingleYearDataset(
            person=person, benunit=benunit, household=household, fiscal_year=2024
        )
    )
    assert sim.calculate(CHILDCARE, 2024)[0] == 0
    assert sim.calculate(
        "housing_benefit_applicable_income_disregard", 2024
    ) == pytest.approx([2_189.20], abs=TOLERANCE)
    assert sim.calculate("housing_benefit_wtc_disregard", 2024)[0] == 0


class neutralized_childcare(Reform):
    def apply(self):
        self.neutralize_variable(CHILDCARE)


class half_capped_childcare(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return hb_capped_childcare_charges(benunit, period, parameters) / 2


half_capped_childcare.__name__ = CHILDCARE


class halve_capped_childcare(Reform):
    def apply(self):
        self.update_variable(half_capped_childcare)


class input_childcare(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit childcare deduction without a formula"
    definition_period = YEAR


input_childcare.__name__ = CHILDCARE


class childcare_without_formula(Reform):
    def apply(self):
        self.replace_variable(input_childcare)


@pytest.mark.parametrize(
    "reform,childcare,income",
    [
        # Nil deduction: 5,200 + 100 - (1,300 + 889.20).
        (neutralized_childcare, 0, 3_110.80),
        (childcare_without_formula, 0, 3_110.80),
        # 2,080 deduction: 5,200 >= 1,300 + 2,080 + 889.20, so para 17(1)
        # applies; 5,200 + 100 - 2,189.20 - 2,080.
        (halve_capped_childcare, 2_080, 1_030.80),
    ],
)
def test_reformed_childcare_deduction_keeps_one_additional_disregard(
    reform, childcare, income
):
    sim = simulation([case()], 2024, tax_benefit_system=reform(system))
    actual = results(sim, 2024)
    assert actual["childcare"][0] == pytest.approx(childcare, abs=TOLERANCE)
    assert actual["earnings_disregard"][0] == pytest.approx(2_189.20, abs=TOLERANCE)
    assert actual["reserve"][0] == 0
    assert actual["income"][0] == pytest.approx(income, abs=TOLERANCE)


class limit_reading_childcare(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

    def formula(benunit, period, parameters):
        charges = hb_capped_childcare_charges(benunit, period, parameters) / 2
        return min_(charges, benunit(LIMIT, period))


limit_reading_childcare.__name__ = CHILDCARE


class limit_reading_reform(Reform):
    def apply(self):
        self.update_variable(limit_reading_childcare)


def test_replacement_deduction_reading_the_limit_stops_with_a_cycle():
    """A replacement deduction that reads the earnings and tax-credit limit
    depends on the WTC disregard, which reads that deduction: the engine
    stops rather than return figures that grant both disregards. Without
    active tax credits the disregard reads nothing, so the reform runs."""
    reformed = limit_reading_reform(system)
    with pytest.raises(CycleError):
        simulation([case()], 2024, tax_benefit_system=reformed).calculate(
            "housing_benefit_applicable_income", 2024
        )
    actual = results(simulation([case()], 2025, tax_benefit_system=reformed), 2025)
    assert actual["reserve"][0] == 0
    assert actual["childcare"][0] == pytest.approx(2_080, abs=TOLERANCE)


def test_revived_tax_credits_with_the_accommodation_disregard():
    """Under a reform that keeps tax credits, the 2027 accommodation
    disregard (£77.73 a week from 5 October 2026) can leave earnings short
    of the additional amount, and para 56 then reserves WTC."""
    year = 2027
    unit = case(net=2_000, standard=260, childcare=0, children=0, wtc=1_000)
    people = {
        "adult": {
            "age": {year: 40},
            "is_claimant_or_partner": {year: True},
            "employment_income": {year: unit["net"]},
        }
    }
    family = {
        "members": ["adult"],
        "in_specified_or_temporary_accommodation": {year: True},
        "housing_benefit_net_earnings": {year: unit["net"]},
        "housing_benefit_special_earnings_disregard": {year: unit["standard"]},
        "housing_benefit_permitted_work_disregard": {year: 0},
        "housing_benefit_on_passporting_benefit": {year: False},
        "housing_benefit_pension_age_regulations_apply": {year: False},
        "meets_housing_benefit_additional_earnings_disregard_conditions": {year: True},
        "working_tax_credit": {year: unit["wtc"]},
        "child_tax_credit": {year: 0},
    }
    sim = UKSimulation(
        situation={
            "people": people,
            "benunits": {"family": family},
            "households": {"home": {"members": ["adult"]}},
        },
        reform={"gov.dwp.tax_credits.active": {"2027": True}},
    )
    accommodation = sim.calculate(
        "housing_benefit_specified_or_temporary_accommodation_disregard", year
    )[0]
    assert accommodation == pytest.approx(77.73 * 52, abs=TOLERANCE)
    # 2,000 < 260 + min(4,041.96, 1,740) + 889.20: para 56 reserves 889.20.
    assert sim.calculate("housing_benefit_wtc_disregard", year)[0] == pytest.approx(
        889.20, abs=TOLERANCE
    )
    assert sim.calculate(
        "housing_benefit_applicable_income_disregard", year
    ) == pytest.approx([2_000], abs=TOLERANCE)
