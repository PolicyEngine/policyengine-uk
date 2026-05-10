from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hart,
)
from policyengine_uk.variables.household.demographic.country import Country


class hart_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Hart's local Council Tax Support scheme"
    definition_period = YEAR
    reference = "https://www.hart.gov.uk/sites/default/files/2026-04/Council-Tax-Reduction-Scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        has_working_age_adult = benunit.any(
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
        uc_exception = benunit(
            "hart_council_tax_reduction_uc_relevant_period_pensioner", period
        ) | benunit("hart_council_tax_reduction_uc_regulation_60a_pensioner", period)
        local_case = (
            has_working_age_adult
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (country == Country.ENGLAND) & is_hart(local_authority) & local_case
