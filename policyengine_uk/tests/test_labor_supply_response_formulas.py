from types import SimpleNamespace

import numpy as np

from policyengine_uk.variables.gov.simulation.labor_supply_response.income_elasticity_lsr import (
    income_elasticity_lsr,
)
from policyengine_uk.variables.gov.simulation.labor_supply_response.substitution_elasticity_lsr import (
    substitution_elasticity_lsr,
)


class FakePerson:
    def __init__(self, values):
        self.values = values

    def __call__(self, variable, period):
        return np.array(self.values[variable])


class FakeParameters:
    def __init__(self, income_elasticity=0.1, substitution_elasticity=0.2):
        self.gov = SimpleNamespace(
            simulation=SimpleNamespace(
                labor_supply_responses=SimpleNamespace(
                    income_elasticity=income_elasticity,
                    substitution_elasticity=substitution_elasticity,
                )
            )
        )

    def __call__(self, period):
        return self


def test_income_elasticity_lsr_clips_negative_earnings():
    person = FakePerson(
        {
            "employment_income_before_lsr": [-1_000, 0, 1_000],
            "relative_income_change": [0.1, 0.1, 0.1],
        }
    )

    result = income_elasticity_lsr.formula(
        person, 2025, FakeParameters(income_elasticity=0.1)
    )

    assert np.allclose(result, np.array([0.0, 0.0, 10.0]))


def test_substitution_elasticity_lsr_clips_negative_earnings():
    person = FakePerson(
        {
            "employment_income_before_lsr": [-1_000, 0, 1_000],
            "relative_wage_change": [0.2, 0.2, 0.2],
        }
    )

    result = substitution_elasticity_lsr.formula(
        person, 2025, FakeParameters(substitution_elasticity=0.2)
    )

    assert np.allclose(result, np.array([0.0, 0.0, 40.0]))
