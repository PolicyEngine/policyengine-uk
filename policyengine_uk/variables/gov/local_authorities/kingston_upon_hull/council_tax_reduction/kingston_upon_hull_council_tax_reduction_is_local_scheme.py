from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kingston_upon_hull,
)
from policyengine_uk.variables.household.demographic.country import Country


class kingston_upon_hull_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Kingston upon Hull's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.hull.gov.uk/downloads/file/239/council-tax-reduction-scheme-2025-to-2026"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        has_uc_award = benunit("universal_credit", period) > 0
        uc_relevant_period_pensioner = benunit(
            "kingston_upon_hull_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        )
        source_working_age = (
            ~has_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_relevant_period_pensioner)
        )
        return (
            (country == Country.ENGLAND)
            & is_kingston_upon_hull(local_authority)
            & source_working_age
        )
