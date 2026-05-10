from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_brentwood,
)
from policyengine_uk.variables.household.demographic.country import Country


class brentwood_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Brentwood's local Council Tax Reduction scheme"
    documentation = "Brentwood paragraph 5.1 covers working-age applicants and pension-age applicants whose partner is on Income Support, income-based JSA, income-related ESA, or Universal Credit. Paragraph 5.2 disregards a pension-age UC award where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"

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
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        uc_award_disregarded_for_pensioner_status = benunit(
            "brentwood_council_tax_reduction_uc_regulation_60a_pensioner", period
        )
        in_local_class = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_award_disregarded_for_pensioner_status)
        )
        return (
            (country == Country.ENGLAND)
            & is_brentwood(local_authority)
            & in_local_class
        )
