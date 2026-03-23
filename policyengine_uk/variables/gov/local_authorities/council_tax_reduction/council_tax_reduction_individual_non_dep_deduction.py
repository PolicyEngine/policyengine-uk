from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_dudley_working_age,
)


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        dudley_params = parameters(
            period
        ).gov.local_authorities.dudley.council_tax_reduction
        weekly_income = person("total_income", period) / WEEKS_IN_YEAR
        classic_deduction = p.amount.calc(weekly_income, right=True) * WEEKS_IN_YEAR

        household = person.household
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        dudley_deduction = dudley_params.non_dep_deduction.amount * WEEKS_IN_YEAR
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        return where(
            dudley_working_age,
            where(claimant_exempt, 0.0, dudley_deduction),
            classic_deduction,
        )
