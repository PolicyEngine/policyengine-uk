from policyengine_uk.model_api import Scenario
from policyengine_uk import Simulation
from policyengine_uk.utils.stored_draws import input_source
import numpy as np

PHASE_IN_DRAW = "pip_phase_in_draw"


def phased_out_by_draw(draw, share) -> np.ndarray:
    """People whose draw falls below the year's phase-out share, compared in
    float64: a stored draw is a float32 value, and comparing it with a Python
    float in float32 would round the share first."""
    return np.asarray(draw, dtype=np.float64) < share


def modify_simulation(sim: Simulation):
    # The seeded stream, drawn only for a year that no stored draw reaches,
    # and then once: each person takes the value at their row.
    pip_seed = None
    draw_population = sim.get_variable_population(PHASE_IN_DRAW)

    start_year = 2025
    end_year = 2029

    for year in range(start_year, end_year + 1):
        if input_source(draw_population, PHASE_IN_DRAW, year) is not None:
            draw = sim.calculate(PHASE_IN_DRAW, year)
        else:
            if pip_seed is None:
                np.random.seed(42)  # For reproducibility
                pip_seed = np.random.random(len(sim.calculate("person_id")))
            draw = pip_seed
        # Copy: calculate returns the simulation's cached array.
        current_pip = np.array(sim.calculate("pip", year))
        percent_along_phase_in = (year - start_year) / (end_year - start_year)
        current_pip[phased_out_by_draw(draw, 0.25 * percent_along_phase_in)] = 0
        sim.set_input("pip", year, current_pip)
    return sim


reform_pip_phase_in = Scenario(
    simulation_modifier=modify_simulation,
)
