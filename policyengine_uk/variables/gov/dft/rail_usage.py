from policyengine_uk.model_api import *


class rail_usage(Variable):
    label = "rail usage"
    documentation = (
        "Base rail spending for this household before fare adjustments. "
        "Uprated by rail ridership growth trends (~1.9% annually). "
        "Multiplied by fare_index to get rail_subsidy_spending."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.dft.rail.ridership_index"
