"""Synthetic invariants for the IS earnings-only disregard (#2621).

Schedule 8 paragraphs 5, 6(a) and 9 limit the baseline disregard; regulations
36(2) and 38(2) apply it to net earnings only. These tests exercise the real
formulas with generated families and actual tax/NI calculations, without data.
The HB/CTR differential uses the frozen helper from main at 6030cbc0b.
"""

from copy import deepcopy

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from legacy_net_earnings_main_reference import person_net_earnings as main_earnings
from policyengine_uk import Simulation

YEAR = 2025
SETTINGS = settings(max_examples=12, deadline=None, derandomize=True, database=None)
MONEY = st.one_of(st.just(0), st.integers(1, 60_000))
SMALL_MONEY = st.one_of(st.just(0), st.integers(1, 5_000))
PERSON = st.fixed_dictionaries(
    {
        "employment_income": MONEY,
        "self_employment_income": st.one_of(MONEY, st.integers(-20_000, -1)),
        "statutory_sick_pay": SMALL_MONEY,
        "statutory_maternity_pay": SMALL_MONEY,
        "statutory_paternity_pay": SMALL_MONEY,
        "private_pension_income": MONEY,
        "spousal_maintenance_income": SMALL_MONEY,
        "social_security_income": SMALL_MONEY,
        "pension_contributions": SMALL_MONEY,
        "property_income": SMALL_MONEY,
        "savings_interest_income": SMALL_MONEY,
        "dividend_income": SMALL_MONEY,
    }
)
FAMILY = st.fixed_dictionaries(
    {
        "shape": st.sampled_from(("single", "couple", "lone_parent")),
        "adults": st.lists(PERSON, min_size=2, max_size=2),
        "country": st.sampled_from(("ENGLAND", "SCOTLAND", "WALES")),
        "pension_age": st.booleans(),
    }
)
FAMILIES = st.lists(FAMILY, min_size=1, max_size=6)


@pytest.fixture(scope="module")
def template():
    return Simulation(situation={"people": {"template": {"age": {YEAR: 40}}}})


def simulate(template, families):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, family in enumerate(families):
        members = []
        adults = family["adults"][: 2 if family["shape"] == "couple" else 1]
        for adult_index, inputs in enumerate(adults):
            name = f"adult_{index}_{adult_index}"
            members.append(name)
            values = {
                "age": 70 if family["pension_age"] else 40,
                "is_parent": family["shape"] == "lone_parent",
                "is_claimant_or_partner": True,
                "is_council_tax_reduction_applicant_or_partner": True,
                **inputs,
            }
            situation["people"][name] = {
                variable: {YEAR: value} for variable, value in values.items()
            }
        if family["shape"] == "lone_parent":
            name = f"child_{index}"
            members.append(name)
            situation["people"][name] = {
                "age": {YEAR: 1},
                "is_claimant_or_partner": {YEAR: False},
                "is_council_tax_reduction_applicant_or_partner": {YEAR: False},
                # A child's earnings cannot enlarge the adults' cap.
                "employment_income": {YEAR: 4_000},
            }
        situation["benunits"][f"unit_{index}"] = {
            "members": members,
            "income_support_assessable_capital": {YEAR: 0},
        }
        situation["households"][f"household_{index}"] = {
            "members": members,
            "country": {YEAR: family["country"]},
        }
    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(situation)
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    return simulation


def calculate(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR), dtype=float)


@SETTINGS
@given(families=FAMILIES)
def test_applicable_income_is_nonnegative_and_disregard_is_bounded(template, families):
    simulation = simulate(template, families)
    income = calculate(simulation, "income_support_applicable_income")
    disregard = calculate(simulation, "income_support_earnings_disregard")
    net = calculate(simulation, "income_support_net_earnings")
    parameters = simulation.tax_benefit_system.parameters(YEAR)
    means_test = parameters.gov.dwp.income_support.means_test
    limits = np.array(
        [
            getattr(means_test, f"income_disregard_{family['shape']}") * 52
            for family in families
        ]
    )
    assert np.all(income >= 0)
    assert np.all(disregard >= 0)
    assert np.all(disregard <= net + 0.01)
    assert np.all(disregard <= limits + 0.01)


@SETTINGS
@given(families=FAMILIES)
def test_zero_earnings_equals_income_without_a_disregard(template, families):
    families = deepcopy(families)
    for family in families:
        for adult in family["adults"]:
            adult.update(employment_income=0, self_employment_income=0)
    simulation = simulate(template, families)
    without_disregard = simulate(template, families)
    without_disregard.set_input(
        "income_support_earnings_disregard", YEAR, [0] * len(families)
    )
    np.testing.assert_array_equal(
        calculate(simulation, "income_support_earnings_disregard"), 0
    )
    np.testing.assert_array_equal(
        calculate(simulation, "income_support_applicable_income"),
        calculate(without_disregard, "income_support_applicable_income"),
    )


@SETTINGS
@given(
    families=FAMILIES,
    source=st.sampled_from(
        (
            "private_pension_income",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "statutory_paternity_pay",
            "spousal_maintenance_income",
            "social_security_income",
        )
    ),
    increase=st.integers(1, 5_000),
)
def test_applicable_income_does_not_fall_as_other_income_rises(
    template, families, source, increase
):
    higher = deepcopy(families)
    for family in higher:
        family["adults"][0][source] += increase
    before = calculate(simulate(template, families), "income_support_applicable_income")
    after = calculate(simulate(template, higher), "income_support_applicable_income")
    assert np.all(after >= before - 0.05)


@SETTINGS
@given(families=FAMILIES, pay_override=st.one_of(st.none(), SMALL_MONEY))
def test_hb_and_ctr_net_earnings_equal_main(template, families, pay_override):
    families = deepcopy(families)
    if pay_override is not None:
        for family in families:
            family["adults"][0]["employment_benefits"] = pay_override
    variables = ("housing_benefit_net_earnings", "council_tax_reduction_net_earnings")
    simulation = simulate(template, families)
    head = {name: calculate(simulation, name) for name in variables}
    # Both caller formulas are unchanged from main. Replace only their bound
    # helper in a fresh simulation, restoring it even when an assertion fails.
    with pytest.MonkeyPatch.context() as patch:
        for name in variables:
            variable = simulation.tax_benefit_system.get_variable(name)
            formula = next(iter(variable.formulas.values()))
            patch.setitem(formula.__globals__, "person_net_earnings", main_earnings)
        main = simulate(template, families)
        for name in variables:
            np.testing.assert_array_equal(
                head[name], calculate(main, name), err_msg=name
            )
