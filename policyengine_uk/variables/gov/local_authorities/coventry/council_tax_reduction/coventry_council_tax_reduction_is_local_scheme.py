from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_coventry,
)
from policyengine_uk.variables.household.demographic.country import Country


class coventry_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Coventry's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.coventry.gov.uk/downloads/file/46761/council-tax-support-scheme-2026-to-2027"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        person = benunit.members
        has_working_age_applicant_or_partner = benunit.any(
            person("is_adult", period) & ~person("is_SP_age", period)
        )
        source_local_class = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_coventry(local_authority)
            & source_local_class
        )
