from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_dartford,
)
from policyengine_uk.variables.household.demographic.country import Country


class dartford_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Dartford's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"

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
        source_working_age = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_dartford(local_authority)
            & source_working_age
        )
