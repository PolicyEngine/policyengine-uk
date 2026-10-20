"""OBR Tables A1/A2 group married and cohabiting couples together.

The numerical oracles below are the tables' third earnings quintile, not
estimates from a population dataset. Legal marriage remains a separate input
for tax rules. Relationship membership, not the number of adults, identifies
the couple used by the labour supply modules.

Source: https://obr.uk/docs/dlm_uploads/NICS-Cut-Impact-on-Labour-Supply-Note.pdf
"""

from functools import lru_cache

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.dynamics import participation
from policyengine_uk.dynamics.progression import (
    calculate_labour_net_income_elasticities,
    calculate_labour_substitution_elasticities,
)
from policyengine_uk.model_api import Scenario

YEAR = 2025
pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
KINDS = ["substitution", "income", "participation"]


def couple_situation(married, child_age=1, earnings=(50_000, 30_000)):
    people = {
        "father": {
            "age": 35,
            "gender": "MALE",
            "employment_income": earnings[0],
            "hours_worked": 1_800 if earnings[0] else 0,
            "employment_status": "FT_EMPLOYED" if earnings[0] else "UNEMPLOYED",
            "is_claimant_or_partner": True,
        },
        "mother": {
            "age": 34,
            "gender": "FEMALE",
            "employment_income": earnings[1],
            "hours_worked": 1_800 if earnings[1] else 0,
            "employment_status": "FT_EMPLOYED" if earnings[1] else "UNEMPLOYED",
            "is_claimant_or_partner": True,
        },
    }
    if child_age is not None:
        people["child"] = {"age": child_age, "is_claimant_or_partner": False}
    return {
        "people": people,
        "benunits": {"family": {"members": list(people), "is_married": married}},
        "households": {"home": {"members": list(people), "household_weight": 1}},
    }


@pytest.fixture(scope="module")
def couple_simulation(cloned_uk_tax_benefit_system):
    # Each coefficient function only reads its simulation; share the pair
    # across the three independent tests of the same demographic case.
    @lru_cache(maxsize=None)
    def build(married, child_age, earnings):
        return Simulation(situation=couple_situation(married, child_age, earnings))

    yield build
    build.cache_clear()


def elasticity(sim, kind):
    if kind == "substitution":
        return calculate_labour_substitution_elasticities(sim, YEAR)
    if kind == "income":
        return calculate_labour_net_income_elasticities(sim, YEAR)
    return participation.calculate_participation_elasticities(
        sim, np.full(len(sim.calculate("age", YEAR)), 3)
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("child_age", [None, 1, 4, 8, 14])
@pytest.mark.parametrize(
    "earnings", [(50_000, 30_000), (30_000, 50_000), (0, 30_000), (50_000, 0)]
)
def test_couples_use_obr_partnered_group(couple_simulation, kind, child_age, earnings):
    substitution = {None: 0.14, 1: 0.301, 4: 0.439, 8: 0.173, 14: 0.160}
    income = {None: 0, 1: -0.185, 4: -0.173, 8: -0.102, 14: -0.063}
    working_partner = {None: 0.259, 1: 0.453, 4: 0.589, 8: 0.453, 14: 0.302}
    nonworking_partner = {None: 0.130, 1: 0.194, 4: 0.253, 8: 0.194, 14: 0.130}
    expected = {
        "substitution": [0.15, substitution[child_age]],
        "income": [-0.05, income[child_age]],
        "participation": [
            0.136,
            (working_partner if earnings[0] else nonworking_partner)[child_age],
        ],
    }[kind]

    for married in [True, False]:
        sim = couple_simulation(married, child_age, earnings)
        assert sim.calculate("is_couple", YEAR).tolist() == [True]
        assert sim.calculate("is_married", YEAR).tolist() == [married]
        np.testing.assert_allclose(elasticity(sim, kind)[:2], expected)


@pytest.mark.parametrize("kind", KINDS)
def test_nonpartner_adult_does_not_turn_a_lone_mother_into_a_couple(kind):
    # A dependent student is an adult in the dynamics' age-18 composition,
    # but is not the parent's partner. Explicit relationship inputs avoid
    # making a new inference about the relationship from their ages.
    sim = Simulation(
        situation={
            "people": {
                "mother": {
                    "age": 40,
                    "gender": "FEMALE",
                    "employment_income": 30_000,
                    "is_claimant_or_partner": True,
                },
                "student": {
                    "age": 18,
                    "employment_status": "STUDENT",
                    "is_claimant_or_partner": False,
                },
                "child": {"age": 1, "is_claimant_or_partner": False},
            },
            "benunits": {"family": {"members": ["mother", "student", "child"]}},
        }
    )
    assert sim.calculate("benunit_count_adults", YEAR).tolist() == [2]
    assert sim.calculate("is_couple", YEAR).tolist() == [False]
    expected = {"substitution": 0.094, "income": -0.037, "participation": 0.717}
    assert elasticity(sim, kind)[0] == expected[kind]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("gender", ["MALE", "FEMALE"])
def test_single_parent_group_is_independent_of_legal_marriage(kind, gender):
    # A separated parent can remain legally married. This checks grouping
    # invariance, without prescribing a new lone-father coefficient: the
    # inherited male lone-parent treatment is outside this correction.
    results = []
    for married in [False, True]:
        sim = Simulation(
            situation={
                "people": {
                    "parent": {"age": 35, "gender": gender},
                    "child": {"age": 1},
                },
                "benunits": {
                    "family": {"members": ["parent", "child"], "is_married": married}
                },
            }
        )
        assert sim.calculate("is_couple", YEAR).tolist() == [False]
        results.append(elasticity(sim, kind)[0])
    assert results[0] == results[1]


@pytest.mark.parametrize("child_age", [1, 8])
@pytest.mark.parametrize("earnings", [(40_000, 30_000), (30_000, 40_000)])
def test_cohabiting_progression_reaches_employment_income(child_age, earnings):
    # Both wages exceed the personal allowance, avoiding legitimate marriage
    # allowance differences in the real household tax calculation.
    outcomes = []
    for married in [True, False]:
        sim = Microsimulation(
            situation=couple_situation(married, child_age, earnings),
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.18},
                    "gov.dynamic.obr_labour_supply_assumptions": {str(YEAR): True},
                }
            ),
        )
        before = np.asarray(sim.calculate("employment_income", YEAR)).copy()
        response = sim.apply_dynamics(YEAR).progression
        after = np.asarray(sim.calculate("employment_income", YEAR)).copy()
        assert len(response) == 2
        assert abs(response["total_response"].iloc[0]) > 1
        np.testing.assert_allclose(
            after[:2], before[:2] + response["total_response"], atol=0.01
        )
        outcomes.append(
            (
                np.asarray(response, dtype=float),
                after,
                np.asarray(sim.calculate("hbai_household_net_income", YEAR)),
            )
        )
    for married, cohabiting in zip(*outcomes):
        np.testing.assert_allclose(cohabiting, married, atol=0.01)


def test_cohabiting_participation_reaches_employment_income(monkeypatch):
    # Hold incentives, earnings quintile and random draw fixed to isolate
    # demographic classification through the actual participation consumer.
    # This is a mechanics regression, not a population participation forecast.
    monkeypatch.setattr(
        participation,
        "calculate_earnings_quintile",
        lambda *args: np.full(3, 3),
    )
    monkeypatch.setattr(
        participation, "impute_wages_for_nonworkers", lambda *args: np.zeros(3)
    )
    monkeypatch.setattr(np.random, "random", lambda: 0.02)
    outcomes = []
    for married in [True, False]:
        sim = Microsimulation(
            situation=couple_situation(married),
            scenario=Scenario(
                parameter_changes={
                    "gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.18}
                }
            ),
        )

        def controlled_gain_to_work(current, *args, **kwargs):
            return pd.DataFrame(
                {
                    "gain_to_work": np.full(
                        3, 10_000 if current is sim.baseline else 5_000, dtype=float
                    ),
                    "in_work_income": np.full(3, 20_000, dtype=float),
                    "out_of_work_income": np.full(3, 10_000, dtype=float),
                }
            )

        monkeypatch.setattr(
            participation, "calculate_gain_to_work", controlled_gain_to_work
        )
        response = participation.apply_participation_responses(sim, YEAR)
        np.testing.assert_allclose(
            response["direct_participation_change"], [-0.034, -0.11325]
        )
        assert response["participation_response"].tolist() == [True, True]
        np.testing.assert_array_equal(sim.calculate("employment_income", YEAR), 0)
        np.testing.assert_array_equal(sim.calculate("hours_worked", YEAR), 0)
        outcomes.append(np.asarray(response, dtype=float))
    np.testing.assert_allclose(outcomes[0], outcomes[1])
