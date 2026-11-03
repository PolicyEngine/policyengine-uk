"""Minimum wage reforms change each continuing ESA claim's permitted work gate.

ESA Regulations 2008 reg. 45(4), (9A): less than 16 weekly hours with net
weekly earnings no greater than 16 times the highest minimum wage, rounded up
to 50p, is permitted work. These recipients have established limited capability
for work; reported awards are continuing awards subject to the model's bounded
screen, rather than newly calculated entitlements.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
NLW_REFORM = {
    f"gov.hmrc.minimum_wage.non_apprentice[{bracket}].amount": {str(YEAR): 13.18}
    for bracket in (2, 3, 4)
}


def _reported_claimants():
    return {
        "claimant": {
            "age": 50,
            "is_claimant_or_partner": True,
            "esa_income_reported": 3_000,
        },
        "partner": {"age": 48, "is_claimant_or_partner": True},
        "outside_adult": {
            "age": 40,
            "is_claimant_or_partner": False,
            "employment_income": 10_700,
            "hours_worked": 780,
            "esa_income_reported": 5_000,
        },
    }


def _calculate_by_person(simulation, variable, person_order):
    return dict(zip(person_order, simulation.calculate(variable, YEAR)))


@pytest.mark.parametrize(
    "person_order",
    [
        ("claimant", "partner", "outside_adult"),
        ("outside_adult", "claimant", "partner"),
        ("partner", "outside_adult", "claimant"),
    ],
)
def test_nlw_reform_changes_only_the_working_persons_gate(person_order):
    people = _reported_claimants()
    situation = {
        "people": {
            name: {variable: {YEAR: value} for variable, value in people[name].items()}
            for name in person_order
        },
        "benunits": {
            "unit": {"members": list(person_order), "would_claim_uc": {YEAR: False}}
        },
        "households": {"household": {"members": list(person_order)}},
    }
    for reform, limit, outside_works in [
        (None, 203.5, True),
        (NLW_REFORM, 211.0, False),
    ]:
        simulation = Simulation(situation=situation, reform=reform)
        # No tax or primary NI is due on £10,700: weekly ESA earnings are
        # £10,700 / 52 = £205.769..., between the old and reformed caps.
        actual_earnings = _calculate_by_person(
            simulation, "esa_exempt_work_earnings", person_order
        )
        assert actual_earnings == pytest.approx(
            {"claimant": 0, "partner": 0, "outside_adult": 10_700 / 52}
        )
        np.testing.assert_array_equal(
            simulation.calculate("esa_exempt_work_higher_earnings_limit", YEAR),
            [limit] * len(person_order),
        )
        assert _calculate_by_person(
            simulation, "esa_income_claimant_remunerative_work", person_order
        ) == {
            "claimant": False,
            "partner": False,
            "outside_adult": outside_works,
        }


@pytest.mark.parametrize("outside_first", [False, True])
def test_nlw_reform_preserves_the_couple_award_and_restores_separate_claim(
    outside_first,
):
    people = _reported_claimants()
    # A genuine second benefit unit has its own claimant. Only the person
    # gate test above groups the outside adult with the couple.
    people["outside_adult"]["is_claimant_or_partner"] = True
    person_order = (
        ("outside_adult", "partner", "claimant")
        if outside_first
        else ("claimant", "partner", "outside_adult")
    )
    benunits = {
        "couple": {"members": ["claimant", "partner"], "would_claim_uc": {YEAR: False}},
        "separate_claim": {
            "members": ["outside_adult"],
            "would_claim_uc": {YEAR: False},
        },
    }
    unit_order = (
        ("separate_claim", "couple") if outside_first else ("couple", "separate_claim")
    )
    situation = {
        "people": {
            name: {variable: {YEAR: value} for variable, value in people[name].items()}
            for name in person_order
        },
        "benunits": {name: benunits[name] for name in unit_order},
        "households": {"household": {"members": list(person_order)}},
    }
    for reform, eligible, awards in [
        (
            None,
            {"couple": True, "separate_claim": False},
            {"couple": 3_000, "separate_claim": 0},
        ),
        (
            NLW_REFORM,
            {"couple": True, "separate_claim": True},
            {"couple": 3_000, "separate_claim": 5_000},
        ),
    ]:
        simulation = Simulation(situation=situation, reform=reform)
        # Capital, other income and contribution-based ESA default to nil;
        # both units decline UC, so neither continuing report has closed.
        np.testing.assert_array_equal(
            simulation.calculate("esa_income_report_closed", YEAR),
            [False] * len(person_order),
        )
        np.testing.assert_array_equal(
            simulation.calculate("esa_income_assessable_capital", YEAR), [0, 0]
        )
        assert (
            dict(zip(unit_order, simulation.calculate("esa_income_eligible", YEAR)))
            == eligible
        )
        for variable in ("esa_income", "esa"):
            actual = dict(zip(unit_order, simulation.calculate(variable, YEAR)))
            assert actual == pytest.approx(awards, abs=0.01)
        assert dict(
            zip(
                unit_order, simulation.calculate("claimant_or_partner_esa_income", YEAR)
            )
        ) == pytest.approx(awards, abs=0.01)
