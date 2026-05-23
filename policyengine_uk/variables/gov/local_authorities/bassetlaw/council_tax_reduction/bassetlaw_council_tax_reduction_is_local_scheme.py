from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_bassetlaw,
)
from policyengine_uk.variables.household.demographic.country import Country


class bassetlaw_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Bassetlaw's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

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
        uc_relevant_period_pensioner = benunit(
            "bassetlaw_council_tax_reduction_uc_relevant_period_pensioner", period
        )
        uc_regulation_60a_pensioner = benunit(
            "bassetlaw_council_tax_reduction_uc_regulation_60a_pensioner",
            period,
        )
        uc_award_disregarded_for_pensioner_status = (
            uc_relevant_period_pensioner | uc_regulation_60a_pensioner
        )
        source_working_age = (
            ~has_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_award_disregarded_for_pensioner_status)
        )
        return (
            (country == Country.ENGLAND)
            & is_bassetlaw(local_authority)
            & source_working_age
        )
