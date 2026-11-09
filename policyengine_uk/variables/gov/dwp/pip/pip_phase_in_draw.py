from policyengine_uk.model_api import *


class pip_phase_in_draw(Variable):
    value_type = float
    entity = Person
    label = "PIP phase-in scenario draw"
    documentation = (
        "A uniform in [0, 1) that the dataset build assigns to each person "
        "and stores. It is an allocation device, not an observed fact: the "
        "opt-in PIP phase-in scenario removes a person's PIP in a year from "
        "2025 to 2029 when this draw falls below that year's phase-in share. "
        "Its situation default, 1.0, falls below no share. A simulation "
        "without the column keeps the scenario's own seeded draw."
    )
    definition_period = YEAR
    default_value = 1.0
