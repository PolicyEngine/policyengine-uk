from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_tewkesbury,
)
from policyengine_uk.variables.household.demographic.country import Country


class tewkesbury_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether the benefit unit is under Tewkesbury's local Council Tax Reduction"
        " scheme"
    )
    documentation = "Tewkesbury Borough Council has remained on the prescribed Default Scheme since 1 April 2013. Pension-age applicants without a working-age income-related benefit follow the prescribed pensioner scheme via simulated_council_tax_reduction_benunit, with paragraph 3 carve-outs for Universal Credit recipients during the relevant period and where regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014 applies."
    definition_period = YEAR
    reference = "https://minutes.tewkesbury.gov.uk/documents/s71351/Council%20Tax%20Reduction%20Scheme%20Report.pdf"

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
            "tewkesbury_council_tax_reduction_uc_relevant_period_pensioner", period
        ) | benunit(
            "tewkesbury_council_tax_reduction_uc_regulation_60a_pensioner", period
        )
        local_case = (
            has_working_age_adult
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (
            (country == Country.ENGLAND) & is_tewkesbury(local_authority) & local_case
        )
