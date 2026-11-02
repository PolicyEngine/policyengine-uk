from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_supported_scheme,
)


class council_tax_reduction_scheme_supported(Variable):
    value_type = bool
    entity = BenUnit
    label = "Supported CTR scheme is available"
    documentation = (
        "Whether the model simulates the Council Tax Reduction scheme that "
        "applies to this family's claim: the pension-age scheme in England, "
        "the Scottish and Welsh schemes, and the working-age schemes of the "
        "English councils it models. The scheme follows the family's own "
        "pensioner status, so families in one household can fall under "
        "different schemes. A claiming family whose scheme is not simulated "
        "falls back to its reported reduction (council_tax_benefit)."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        country = benunit.household("country", period)
        has_pensioner = benunit("council_tax_reduction_pensioner", period)
        local_authority = benunit.household("local_authority", period)
        return is_supported_scheme(country, has_pensioner, local_authority)
