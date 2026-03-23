from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    DUDLEY_WORKING_AGE_NON_DEP_WEEKLY_DEDUCTION,
    is_dudley,
)
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        weekly_income = person("total_income", period) / WEEKS_IN_YEAR
        classic_deduction = p.amount.calc(weekly_income, right=True) * WEEKS_IN_YEAR

        household = person.household
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        dudley_working_age = (
            (country == Country.ENGLAND)
            & ~has_pensioner
            & is_dudley(local_authority)
        )
        dudley_deduction = (
            DUDLEY_WORKING_AGE_NON_DEP_WEEKLY_DEDUCTION * WEEKS_IN_YEAR
        )
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        return where(
            dudley_working_age,
            where(claimant_exempt, 0.0, dudley_deduction),
            classic_deduction,
        )
