from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_west_berkshire,
)
from policyengine_uk.variables.household.demographic.country import Country


class west_berkshire_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under West Berkshire's local Council Tax Reduction scheme"
    documentation = "West Berkshire treats applicants as working-age (and so subject to the local scheme) where they have not attained pension credit age, or where they have but the claimant or partner is on Universal Credit, Jobseeker's Allowance, Income Support, Employment and Support Allowance, or another working-age benefit. Pension-age applicants with none of those benefits go to the national prescribed pensioner scheme."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66426/Council-Tax-Reduction-Scheme-Leaflet-2026-27/pdf/CTR_Scheme_Leaflet_2026.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        person = benunit.members
        has_working_age_applicant_or_partner = benunit.any(
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
            "west_berkshire_council_tax_reduction_uc_relevant_period_pensioner",
            period,
        ) | benunit(
            "west_berkshire_council_tax_reduction_uc_regulation_60a_pensioner",
            period,
        )
        in_local_class = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_exception)
        )
        return (
            (country == Country.ENGLAND)
            & is_west_berkshire(local_authority)
            & in_local_class
        )
