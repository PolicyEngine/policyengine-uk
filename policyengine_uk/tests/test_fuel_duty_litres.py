import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.system import system


def test_fuel_duty_is_litres_times_statutory_rate():
    year = 2025
    situation = {
        "people": {
            "adult": {
                "age": {year: 35},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["adult"],
            },
        },
        "households": {
            "household": {
                "members": ["adult"],
                "region": {year: "LONDON"},
                "petrol_spending": {year: 2_000.0},
                "diesel_spending": {year: 1_000.0},
            },
        },
    }
    simulation = Microsimulation(situation=situation)

    fuel_duty = simulation.calculate("fuel_duty", year).values[0]
    litres = (
        simulation.calculate("petrol_litres", year).values[0]
        + simulation.calculate("diesel_litres", year).values[0]
    )
    rate = system.parameters.gov.hmrc.fuel_duty.petrol_and_diesel(year)

    assert fuel_duty == pytest.approx(litres * rate)
