from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_chichester,
)
from policyengine_uk.variables.household.demographic.country import Country


class chichester_council_tax_reduction_is_local_scheme(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is under Chichester's local CTR scheme"
    definition_period = YEAR
    reference = "https://chichester.moderngov.co.uk/documents/s30863/09.1%20Appendix%201%20Local%20Council%20Tax%20Reduction%20Scheme%20Rules%202026%20-%202027.pdf"

    def formula(benunit, period, parameters):
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        source_working_age = (
            ~has_pensioner | relevant_income_based_benefit | has_uc_award
        )
        return (
            (country == Country.ENGLAND)
            & is_chichester(local_authority)
            & source_working_age
        )
