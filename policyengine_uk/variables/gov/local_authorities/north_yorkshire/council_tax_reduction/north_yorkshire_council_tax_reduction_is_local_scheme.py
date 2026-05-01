from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_north_yorkshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class north_yorkshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under North Yorkshire's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.northyorks.gov.uk/sites/default/files/2026-03/North%20Yorkshire%20Council%27s%20Council%20Tax%20Reduction%20Scheme%202026%20to%202027.pdf"

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
            "north_yorkshire_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        )
        source_working_age = (
            ~has_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_relevant_period_pensioner)
        )
        return (
            (country == Country.ENGLAND)
            & is_north_yorkshire(local_authority)
            & source_working_age
        )
