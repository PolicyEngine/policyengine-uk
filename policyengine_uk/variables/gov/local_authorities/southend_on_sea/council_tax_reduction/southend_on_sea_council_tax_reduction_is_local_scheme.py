from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_southend_on_sea,
)
from policyengine_uk.variables.household.demographic.country import Country


class southend_on_sea_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Southend-on-Sea's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        uc_relevant_period_pensioner = benunit(
            "southend_on_sea_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        )
        source_working_age = (
            ~has_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_relevant_period_pensioner)
        )
        return (
            (country == Country.ENGLAND)
            & is_southend_on_sea(local_authority)
            & source_working_age
        )
