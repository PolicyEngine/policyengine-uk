from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_herefordshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class herefordshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Herefordshire's local CTR scheme"
    definition_period = YEAR
    reference = "https://councillors.herefordshire.gov.uk/documents/s50131582/Approved%20202526%20Council%20Tax%20Reduction%20Scheme.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        has_uc_award = benunit("universal_credit", period) > 0
        source_working_age = (
            ~has_pensioner | relevant_income_based_benefit | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_herefordshire(local_authority)
            & source_working_age
        )
