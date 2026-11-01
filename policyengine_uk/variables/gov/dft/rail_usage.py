from policyengine_uk.model_api import *


class rail_usage(Variable):
    label = "rail usage"
    documentation = (
        "Rail usage quantity in base year (2020) price terms. "
        "Should be provided by policyengine-uk-data, derived from "
        "rail_subsidy_spending / fare_index at survey year. "
        "Projected by ORR passenger journeys per person, held flat from "
        "2026-27."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    # Per person, because household weights already grow by population; the
    # growth is that of gov.dft.rail.ridership_index (#1862).
    uprating = "gov.economic_assumptions.indices.orr.per_capita.rail_passenger_journeys"
