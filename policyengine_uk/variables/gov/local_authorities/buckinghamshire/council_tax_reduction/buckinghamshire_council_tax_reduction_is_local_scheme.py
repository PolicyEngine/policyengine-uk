from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_buckinghamshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class buckinghamshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Buckinghamshire's local CTR scheme"
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        has_working_age_applicant_or_partner = benunit.any(
            person("is_adult", period) & ~person("is_SP_age", period)
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        has_uc_award = benunit("universal_credit", period) > 0
        transitional_protection = benunit(
            "buckinghamshire_council_tax_reduction_uc_transitional_protection_pensioner",
            period,
        )
        source_working_age = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | (has_uc_award & ~transitional_protection)
        )
        return (
            (country == Country.ENGLAND)
            & is_buckinghamshire(local_authority)
            & source_working_age
        )
