from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_cheshire_west_and_chester,
)
from policyengine_uk.variables.household.demographic.country import Country


class cheshire_west_and_chester_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether the benefit unit is under Cheshire West and Chester's local CTR scheme"
    )
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
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
        relevant_period_pensioner = benunit(
            "cheshire_west_and_chester_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        )
        source_working_age = (
            ~has_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~relevant_period_pensioner)
        )
        return (
            (country == Country.ENGLAND)
            & is_cheshire_west_and_chester(local_authority)
            & source_working_age
        )
