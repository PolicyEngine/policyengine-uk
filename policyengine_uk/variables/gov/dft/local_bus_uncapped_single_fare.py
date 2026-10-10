from policyengine_uk.model_api import *


class local_bus_uncapped_single_fare(Variable):
    label = "local bus uncapped single fare"
    documentation = "Representative uncapped single fare for other-local-bus journeys, in pounds. Override to model a known fare; the default is an aggregate no-demand-response counterfactual."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        return parameters(period).gov.dft.bus.uncapped_single_fare
