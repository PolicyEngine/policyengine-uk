import pytest

from policyengine_uk import Simulation


def test_class_4_annual_maximum_applies_case_3_steps():
    year = 2026
    monthly_primary_class_1 = {f"{year}-{month:02d}": 500 for month in range(1, 13)}
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 100_000},
                    "ni_class_1_employee_primary": monthly_primary_class_1,
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )

    assert sim.calculate("ni_class_4_maximum", year)[0] == pytest.approx(
        1_748.60,
        abs=0.01,
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(1_748.60, abs=0.01)


def test_class_4_annual_maximum_does_not_bind_without_class_1():
    year = 2026
    sim = Simulation(
        situation={
            "people": {
                "person": {
                    "age": {year: 40},
                    "self_employment_income": {year: 60_000},
                }
            },
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {"household": {"members": ["person"]}},
        }
    )

    assert sim.calculate("ni_class_4_maximum", year)[0] == pytest.approx(
        2_456.60,
        abs=0.01,
    )
    assert sim.calculate("ni_class_4", year)[0] == pytest.approx(2_456.60, abs=0.01)
