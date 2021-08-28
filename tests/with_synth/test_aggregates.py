from openfisca_uk_data import SynthFRS
from openfisca_uk import Microsimulation
import pytest

sim = Microsimulation(dataset=SynthFRS)

# (variable, population average, absolute error window)
AVERAGE_TESTS = (("in_poverty_bhc", 0.15, 0.1),)


@pytest.mark.parametrize("variable,central_estimate,max_dist", AVERAGE_TESTS)
def test_person_level_averages(variable, central_estimate, max_dist):
    assert (
        abs(
            sim.calc(variable, map_to="person", period=2020).mean()
            - central_estimate
        )
        <= max_dist
    )


AGG_TESTS = (
    ("tax", 223e9, 20e9),
    ("income_tax", 160e9, 20e9),
    ("benefits", 220e9, 30e9),
)


@pytest.mark.parametrize("variable,central_estimate,max_dist", AGG_TESTS)
def test_aggregates(variable, central_estimate, max_dist):
    assert (
        abs(sim.calc(variable, period=2020).sum() - central_estimate)
        <= max_dist
    )
