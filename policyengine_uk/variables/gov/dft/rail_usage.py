from policyengine_uk.model_api import *


class rail_usage(Variable):
    label = "rail usage"
    documentation = (
        "Rail usage quantity in base year (2020) price terms. "
        "Should be provided by policyengine-uk-data, derived from "
        "rail_subsidy_spending / fare_index at survey year. "
        "Uprated by rail ridership growth trends (~1.9% annually)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.dft.rail.ridership_index"
