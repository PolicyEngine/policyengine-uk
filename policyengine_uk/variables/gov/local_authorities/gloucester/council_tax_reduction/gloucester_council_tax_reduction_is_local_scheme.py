from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_gloucester,
)
from policyengine_uk.variables.household.demographic.country import Country


class gloucester_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Gloucester's local Council Tax Support scheme"
    definition_period = YEAR
    reference = [
        "https://www.gloucester.gov.uk/council-tax/council-tax-support/",
        "https://www.gloucester.gov.uk/media/ruwinppa/local-council-tax-support-policy-2026-v2.pdf",
    ]

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        adult = person("is_adult", period)
        source_working_age_case = benunit.any(adult) & ~benunit.any(
            adult & person("is_SP_age", period)
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
        source_local_class = (
            source_working_age_case | relevant_income_based_benefit | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_gloucester(local_authority)
            & source_local_class
        )
