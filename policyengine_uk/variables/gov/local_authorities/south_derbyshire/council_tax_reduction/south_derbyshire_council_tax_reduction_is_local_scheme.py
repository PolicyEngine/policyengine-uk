from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_south_derbyshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class south_derbyshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under South Derbyshire's local CTR scheme"
    definition_period = YEAR
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        has_applicant_or_partner_pensioner = benunit.any(
            person("is_adult", period) & person("is_SP_age", period)
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
        uc_wtc_closure_pensioner = benunit(
            "south_derbyshire_council_tax_reduction_uc_working_tax_credit_closure_pensioner",
            period,
        )
        source_working_age = (
            ~has_applicant_or_partner_pensioner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_wtc_closure_pensioner)
        )
        return (
            (country == Country.ENGLAND)
            & is_south_derbyshire(local_authority)
            & source_working_age
        )
