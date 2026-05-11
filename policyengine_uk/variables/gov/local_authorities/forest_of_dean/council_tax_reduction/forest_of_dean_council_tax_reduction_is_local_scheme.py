from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_forest_of_dean,
)
from policyengine_uk.variables.household.demographic.country import Country


class forest_of_dean_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether the benefit unit is under Forest of Dean's local Council Tax Support"
        " scheme"
    )
    documentation = "Paragraph 1.4 limits the working-age scheme to applicants who have not attained State Pension Credit qualifying age, plus pension-age applicants whose claimant or partner is on Income Support, income-based JSA or income-related ESA. Pure pension-age cases follow the prescribed pensioner scheme via simulated_council_tax_reduction_benunit."
    definition_period = YEAR
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

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
        local_case = has_working_age_adult | relevant_income_based_benefit
        return (
            (country == Country.ENGLAND)
            & is_forest_of_dean(local_authority)
            & local_case
        )
