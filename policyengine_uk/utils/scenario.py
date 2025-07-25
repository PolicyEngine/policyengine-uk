from pydantic import BaseModel
from typing import Optional, Callable, Dict
from policyengine_core.simulations import Simulation


class Scenario(BaseModel):
    parameter_changes: Optional[Dict[str, int | float | bool | Dict[str | int, int | float | bool]]] = None
    """ A dictionary of parameter changes to apply to the simulation."""
    simulation_modifier: Optional[Callable[['Simulation'], None]] = None
    """ A function that modifies the simulation before running it."""
