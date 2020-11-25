from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_core import periods
import numpy as np


def poverty_rate(sim, period="2020-01-06", population="people", mode="ahc"):
    pop = sim.calculate("household_weight", period) * sim.calculate(
        f"{population}_in_household", period
    )
    total = np.sum(pop)
    in_poverty = np.sum(
        pop
        * sim.calculate(
            f"in_poverty_{mode}", periods.period(period).first_week
        )
    )
    return in_poverty / total
