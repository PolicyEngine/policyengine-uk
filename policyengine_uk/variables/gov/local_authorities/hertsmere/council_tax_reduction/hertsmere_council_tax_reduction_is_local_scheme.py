from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hertsmere,
)
from policyengine_uk.variables.household.demographic.country import Country


class hertsmere_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Hertsmere's local Council Tax Reduction scheme"
    documentation = "Hertsmere paragraph 1.6 covers the local Class D/E means test and paragraph 1.8 routes Universal Credit applicants to Class G. Pension-age UC awards are disregarded during the relevant period or where regulation 60A applies."
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

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
            "hertsmere_council_tax_reduction_uc_relevant_period_pensioner", period
        ) | benunit(
            "hertsmere_council_tax_reduction_uc_regulation_60a_pensioner", period
        )
        in_class_d_or_e = (has_working_age_adult | relevant_income_based_benefit) & (
            ~has_uc_award
        )
        in_class_g = has_uc_award & (has_working_age_adult | ~uc_exception)
        return (
            (country == Country.ENGLAND)
            & is_hertsmere(local_authority)
            & (in_class_d_or_e | in_class_g)
        )
