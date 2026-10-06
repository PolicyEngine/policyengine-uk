from policyengine_uk.model_api import *


class local_bus_single_fare_share(Variable):
    label = "local bus single fare share"
    documentation = "Share of fare-paying boardings bought as single tickets. Dataset input; the fallback is the 2024 NTS other-local-bus mean."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(person, period, parameters):
        return parameters(period).gov.dft.bus.default_single_fare_share
