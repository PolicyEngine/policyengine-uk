from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_south_gloucestershire,
)
from policyengine_uk.variables.household.demographic.country import Country


class south_gloucestershire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under South Gloucestershire's local CTR scheme"
    definition_period = YEAR
    reference = [
        "https://beta.southglos.gov.uk/apply-for-council-tax-reduction/",
        "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf",
    ]

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
        uc_pensioner_protection = benunit(
            "south_gloucestershire_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        ) | benunit(
            "south_gloucestershire_council_tax_reduction_uc_regulation_60a_pensioner",
            period,
        )
        source_local_class = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_pensioner_protection)
        )
        return (
            (country == Country.ENGLAND)
            & is_south_gloucestershire(local_authority)
            & source_local_class
        )
