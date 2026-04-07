from types import SimpleNamespace

import numpy as np
import pandas as pd

from policyengine_uk.dynamics.progression import (
    calculate_employment_income_change,
)
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


def test_progression_labor_supply_response_clips_negative_earnings():
    result = calculate_employment_income_change(
        employment_income=np.array([-1_000.0, 0.0, 1_000.0]),
        derivative_changes=pd.DataFrame({"wage_rel_change": [0.1, 0.1, 0.1]}),
        income_changes=pd.DataFrame({"income_rel_change": [0.2, 0.2, 0.2]}),
        substitution_elasticities=np.array([0.15, 0.15, 0.15]),
        income_elasticities=np.array([-0.05, -0.05, -0.05]),
    )

    assert np.allclose(result["substitution_response"], [0.0, 0.0, 15.0])
    assert np.allclose(result["income_response"], [0.0, 0.0, -10.0])
    assert np.allclose(result["total_response"], [0.0, 0.0, 5.0])
