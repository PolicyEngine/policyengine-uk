from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hartlepool,
)
from policyengine_uk.variables.household.demographic.country import Country


class hartlepool_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Hartlepool's local Council Tax Reduction scheme"
    definition_period = YEAR
    reference = "https://www.hartlepool.gov.uk/downloads/file/1484/hbc-council-tax-reduction-scheme-2026-27"

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
            "hartlepool_council_tax_reduction_uc_regulation_60a_pensioner", period
        )
        local_case = (
            has_working_age_adult
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (
            (country == Country.ENGLAND) & is_hartlepool(local_authority) & local_case
        )
