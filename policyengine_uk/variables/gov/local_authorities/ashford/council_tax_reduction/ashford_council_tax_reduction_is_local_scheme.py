from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_ashford,
)
from policyengine_uk.variables.household.demographic.country import Country


class ashford_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Ashford's local CTR scheme"
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

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
        has_uc_award = benunit("universal_credit", period) > 0
        uc_relevant_period_pensioner = benunit(
            "ashford_council_tax_reduction_uc_relevant_period_pensioner", period
        )
        uc_regulation_60a_pensioner = benunit(
            "ashford_council_tax_reduction_uc_regulation_60a_pensioner",
            period,
        )
        uc_award_disregarded_for_pensioner_status = (
            uc_relevant_period_pensioner | uc_regulation_60a_pensioner
        )
        source_working_age = (
            has_working_age_applicant_or_partner
            | relevant_income_based_benefit
            | (has_uc_award & ~uc_award_disregarded_for_pensioner_status)
        )
        return (
            (country == Country.ENGLAND)
            & is_ashford(local_authority)
            & source_working_age
        )
