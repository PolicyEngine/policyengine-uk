from policyengine_uk.model_api import *


class local_bus_uncapped_single_fare(Variable):
    label = "local bus uncapped single fare"
    documentation = (
        "Optional uncapped single fare for a person's other-local-bus journeys, "
        "in pounds. When supplied, the person's single tickets are capped at "
        "this one fare; otherwise the model uses the table of uncapped single "
        "fares in gov.dft.bus.uncapped_single_fares."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
