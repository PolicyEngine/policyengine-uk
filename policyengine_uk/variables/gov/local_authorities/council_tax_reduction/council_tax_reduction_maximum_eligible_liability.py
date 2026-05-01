from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_warrington_working_age,
    is_dudley_working_age,
    is_stockport_working_age,
)


class council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        warrington_working_age = is_warrington_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        stockport_working_age = is_stockport_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        return select(
            [dudley_working_age, warrington_working_age, stockport_working_age],
            [
                household(
                    "dudley_council_tax_reduction_maximum_eligible_liability",
                    period,
                ),
                household(
                    "warrington_council_tax_reduction_maximum_eligible_liability",
                    period,
                ),
                household(
                    "stockport_council_tax_reduction_maximum_eligible_liability",
                    period,
                ),
            ],
            default=household("council_tax", period),
        )
