import pytest

from policyengine_uk import Simulation


def test_class_4_annual_maximum_uses_current_main_rate_factor():
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
        46_484,
        abs=0.01,
    )
