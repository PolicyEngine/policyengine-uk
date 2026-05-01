from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_camden_working_age,
)


class camden_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Camden CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.camden.council_tax_reduction
        household = person.household
        working_age = is_camden_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_earned_income = earned_income / WEEKS_IN_YEAR
        deduction_applies = (person("age", period) > 25) & (
            weekly_earned_income > ctr.non_dep_deduction.earnings_threshold
        )
        liability = household("council_tax", period)
        deduction = liability * ctr.non_dep_deduction.liability_rate
        return working_age * where(deduction_applies, deduction, 0.0)
