from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_supported_scheme,
)


class council_tax_reduction_scheme_supported(Variable):
    value_type = bool
    entity = Household
    label = "Supported CTR scheme is available"
    definition_period = YEAR

    def formula(household, period, parameters):
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        return is_supported_scheme(local_authority, country, has_pensioner)
