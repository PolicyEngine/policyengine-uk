from policyengine_uk.model_api import Scenario
from policyengine_uk import Simulation
import numpy as np


def modify_simulation(sim: Simulation):
    np.random.seed(42)  # For reproducibility
    pip_seed = np.random.random(len(sim.calculate("person_id")))

    start_year = 2025
    end_year = 2029

    for year in range(start_year, end_year + 1):
        current_pip = sim.calculate("pip", year)
        percent_along_phase_in = (year - start_year) / (end_year - start_year)
        current_pip[pip_seed < 0.25 * percent_along_phase_in] = 0
        sim.set_input("pip", year, current_pip)
    return sim


reform_pip_phase_in = Scenario(
    simulation_modifier=modify_simulation,
)
