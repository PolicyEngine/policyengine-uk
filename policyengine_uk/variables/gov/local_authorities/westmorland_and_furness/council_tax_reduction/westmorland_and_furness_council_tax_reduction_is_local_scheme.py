from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_westmorland_and_furness,
)
from policyengine_uk.variables.household.demographic.country import Country


class westmorland_and_furness_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether the benefit unit is under Westmorland and Furness's local CTR scheme"
    )
    definition_period = YEAR
    reference = "https://www.westmorlandandfurness.gov.uk/sites/default/files/2026-03/Westmorland%20%26%20Furness%20Council%20%20CTR%20Scheme%20202627%20%28accessible%20March%202026%29.pdf"

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
        source_working_age = (
            ~has_pensioner | relevant_income_based_benefit | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_westmorland_and_furness(local_authority)
            & source_working_age
        )
