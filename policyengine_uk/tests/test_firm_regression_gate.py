"""Regression gate: the firm entity leaves household results unchanged.

The fixture ``fixtures/firm_regression_gate_base.json`` holds results
computed at the branch's base commit (70014b3) for a fixed set of household
situations, with no firm entity in the model. Each test recomputes them on
the current tree and requires exact equality: the firm-side rules are built
but not wired into any household tax or benefit, so household results must
match to the last bit.

To regenerate the fixture, run ``compute_gate_values()`` from this module
with the base commit's ``policyengine_uk`` first on the import path, and
write its result as JSON (Python's ``json`` writes floats at ``repr``
precision, which round-trips exactly).
"""

import json
from pathlib import Path

import numpy as np
import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "firm_regression_gate_base.json"
YEARS = (2025, 2026)
BASE_COMMIT = "70014b3"

HOUSEHOLD_VARIABLES = (
    "gov_tax",
    "household_tax",
    "household_net_income",
    "gov_balance",
    "household_benefits",
)

# Raise the employer Class 1 main rate from 15% to 20%: the employer NI
# incidence path (ni_employer, employer_ni_* contrib variables) runs with a
# baseline, so the reform proves it is unchanged too.
EMPLOYER_NI_REFORM = {
    "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {
        "2025-01-01.2030-12-31": 0.2
    }
}
REFORM_VARIABLES = HOUSEHOLD_VARIABLES + ("ni_employer",)


def _household(members, **household_inputs):
    return {"members": list(members), **household_inputs}


def situations(year: int) -> dict:
    """Varied single-household situations for ``year``."""

    def person(age, **incomes):
        return {"age": {year: age}, **{k: {year: v} for k, v in incomes.items()}}

    def single(name, region="LONDON", household=None, **person_inputs):
        return {
            "people": {name: person(**person_inputs)},
            "benunits": {"benunit": {"members": [name]}},
            "households": {
                "household": _household(
                    [name], region={year: region}, **(household or {})
                )
            },
        }

    couple_members = ["parent1", "parent2", "child1", "child2"]
    return {
        "single_earner": single(
            "adult", region="NORTH_WEST", age=35, employment_income=32_000
        ),
        "couple_with_children_on_uc": {
            "people": {
                "parent1": person(34, employment_income=14_000),
                "parent2": person(32),
                "child1": person(7),
                "child2": person(3),
            },
            "benunits": {
                "benunit": {"members": couple_members, "would_claim_uc": {year: True}}
            },
            "households": {
                "household": _household(
                    couple_members,
                    region={year: "WEST_MIDLANDS"},
                    rent={year: 9_600},
                    tenure_type={year: "RENT_PRIVATELY"},
                )
            },
        },
        "pensioner": single(
            "pensioner",
            region="SOUTH_WEST",
            age=72,
            state_pension=11_500,
            private_pension_income=6_000,
            savings_interest_income=1_200,
        ),
        "self_employed": single(
            "trader", region="EAST_MIDLANDS", age=45, self_employment_income=48_000
        ),
        "high_earner_with_dividends": single(
            "director",
            region="SOUTH_EAST",
            age=52,
            employment_income=160_000,
            dividend_income=40_000,
            property_income=12_000,
        ),
        "renter_in_scotland": single(
            "renter",
            region="SCOTLAND",
            household={
                "rent": {year: 7_800},
                "tenure_type": {year: "RENT_PRIVATELY"},
                "council_tax": {year: 1_400},
                "full_rate_vat_consumption": {year: 9_000},
                "reduced_rate_vat_consumption": {year: 600},
            },
            age=28,
            employment_income=27_500,
        ),
        "low_paid_lone_parent_wales": {
            "people": {
                "parent": person(29, employment_income=11_000),
                "child": person(4),
            },
            "benunits": {
                "benunit": {
                    "members": ["parent", "child"],
                    "would_claim_uc": {year: True},
                }
            },
            "households": {
                "household": _household(
                    ["parent", "child"],
                    region={year: "WALES"},
                    rent={year: 6_000},
                    tenure_type={year: "RENT_FROM_COUNCIL"},
                )
            },
        },
        "two_earner_couple_london": {
            "people": {
                "a": person(41, employment_income=55_000),
                "b": person(39, employment_income=38_000, self_employment_income=6_000),
            },
            "benunits": {"benunit": {"members": ["a", "b"]}},
            "households": {
                "household": _household(
                    ["a", "b"],
                    region={year: "LONDON"},
                    tenure_type={year: "OWNED_WITH_MORTGAGE"},
                    council_tax={year: 2_100},
                    full_rate_vat_consumption={year: 21_000},
                    petrol_spending={year: 1_500},
                )
            },
        },
    }


def _values(simulation, variables, year) -> dict:
    return {
        name: [
            float(value)
            for value in np.asarray(simulation.calculate(name, year), dtype=float)
        ]
        for name in variables
    }


def compute_case(case: str) -> dict:
    """The gate values of one case, ``"<situation>/<year>"`` or
    ``"<situation>/<year>/employer_ni_reform"``, under the
    ``policyengine_uk`` on the import path."""
    from policyengine_uk import Simulation
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    name, year, *reform = case.split("/")
    year = int(year)
    situation = situations(year)[name]
    if reform:
        simulation = Simulation(situation=situation, reform=EMPLOYER_NI_REFORM)
        return _values(simulation, REFORM_VARIABLES, year)
    simulation = Simulation(situation=situation)
    return _values(simulation, HOUSEHOLD_VARIABLES + tuple(GOV_TAX_VARIABLES), year)


CASES = sorted(
    f"{name}/{year}{suffix}"
    for year in YEARS
    for name in situations(year)
    for suffix in ("", "/employer_ni_reform")
)


def compute_gate_values() -> dict:
    """Every gate value: run this against the base commit to write the
    fixture."""
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    return {
        "base_commit": BASE_COMMIT,
        "gov_tax_variables": list(GOV_TAX_VARIABLES),
        "cases": {case: compute_case(case) for case in CASES},
    }


@pytest.fixture(scope="module")
def base():
    return json.loads(FIXTURE.read_text())


def test_gov_tax_variables_are_unchanged(base):
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    assert list(GOV_TAX_VARIABLES) == base["gov_tax_variables"]


def test_fixture_covers_every_case(base):
    assert sorted(base["cases"]) == CASES
    assert len(CASES) == 2 * len(YEARS) * len(situations(YEARS[0]))


def test_employer_ni_reform_moves_ni_employer(base):
    """The reform case must exercise employer NI, or it proves nothing."""
    case = "single_earner/2025"
    assert sum(base["cases"][f"{case}/employer_ni_reform"]["ni_employer"]) > sum(
        base["cases"][case]["ni_employer"]
    )


@pytest.mark.parametrize("case", CASES)
def test_household_results_match_base_exactly(base, case):
    expected = base["cases"][case]
    actual = compute_case(case)
    assert sorted(actual) == sorted(expected)
    mismatches = {
        name: (expected[name], actual[name])
        for name in expected
        if not np.array_equal(np.array(expected[name]), np.array(actual[name]))
    }
    assert not mismatches, mismatches
