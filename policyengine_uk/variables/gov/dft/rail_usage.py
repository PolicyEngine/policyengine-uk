from policyengine_uk.model_api import *


class rail_usage(Variable):
    label = "rail usage"
    documentation = (
        "Quantity of rail usage for this household, representing passenger journeys. "
        "Uprated by rail ridership growth trends (~1.9% annually)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "journey"
    uprating = "gov.dft.rail.ridership_index"
