"""The UC new-claimant draw follows the data source on MOCK households."""

import numpy as np
import pandas as pd
import pytest
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import Microsimulation, Simulation
import policyengine_uk.simulation as uk_simulation
from policyengine_uk.scenarios.uc_reform import add_universal_credit_reform

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = range(2026, 2030)
SHARES = (0.11, 0.13, 0.16, 0.22)
COUNT = 1_000


def _mock_frame():
    """One synthetic adult per benefit unit, with all years supplied."""
    ids = np.arange(COUNT)
    columns = {}
    for year in YEARS:
        for variable in (
            "person_id",
            "person_benunit_id",
            "person_household_id",
            "benunit_id",
            "household_id",
        ):
            columns[f"{variable}__{year}"] = ids
        columns[f"age__{year}"] = np.full(COUNT, 30)
        columns[f"uc_limited_capability_for_WRA__{year}"] = np.ones(COUNT, dtype=bool)
        columns[f"household_weight__{year}"] = np.ones(COUNT)
    return pd.DataFrame(columns)


@pytest.mark.parametrize(
    "simulation_class",
    [CoreSimulation, Simulation, Microsimulation],
    ids=["core", "uk", "uk_micro"],
)
def test_data_built_simulations_keep_the_seed_43_new_claimant_draw(simulation_class):
    kwargs = {"dataset": _mock_frame()}
    if simulation_class is CoreSimulation:
        kwargs["tax_benefit_system"] = uk_simulation.CountryTaxBenefitSystem()
        kwargs["default_calculation_period"] = 2026
    sim = simulation_class(**kwargs)
    add_universal_credit_reform(sim)

    draws = np.random.default_rng(43).random(COUNT)
    for year, share in zip(YEARS, SHARES):
        status = np.asarray(
            sim.calculate("uc_receives_new_claimant_health_element", year)
        )
        np.testing.assert_array_equal(status, draws < share)
        assert status.mean() == pytest.approx(share, abs=0.03)


@pytest.mark.parametrize(
    "simulation_class",
    [CoreSimulation, Simulation, Microsimulation],
    ids=["core", "uk", "uk_micro"],
)
def test_situations_keep_every_claimant_protected(simulation_class):
    situation = {
        "people": {
            "adult": {
                "age": {year: 30 for year in YEARS},
                "uc_limited_capability_for_WRA": {year: True for year in YEARS},
            }
        },
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {"household": {"members": ["adult"]}},
    }
    kwargs = {"situation": situation}
    if simulation_class is CoreSimulation:
        kwargs["tax_benefit_system"] = uk_simulation.CountryTaxBenefitSystem()
        kwargs["default_calculation_period"] = 2026
    sim = simulation_class(**kwargs)
    add_universal_credit_reform(sim)

    for year in YEARS:
        assert not np.asarray(
            sim.calculate("uc_receives_new_claimant_health_element", year)
        ).any()
