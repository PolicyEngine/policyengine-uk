from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_east_hertfordshire_working_age,
    is_dudley_working_age,
    is_warrington_working_age,
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
        east_herts_params = parameters(
            period
        ).gov.local_authorities.east_hertfordshire.council_tax_reduction
        dudley_params = parameters(
            period
        ).gov.local_authorities.dudley.council_tax_reduction
        warrington_params = parameters(
            period
        ).gov.local_authorities.warrington.council_tax_reduction
        weekly_total_income = person("total_income", period) / WEEKS_IN_YEAR
        weekly_earned_income = (
            person("employment_income", period)
            + person("self_employment_income", period)
        ) / WEEKS_IN_YEAR
        classic_deduction = p.amount.calc(weekly_total_income, right=True) * WEEKS_IN_YEAR

        household = person.household
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        east_herts_working_age = is_east_hertfordshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        dudley_working_age = is_dudley_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        warrington_working_age = is_warrington_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        east_herts_deduction = (
            east_herts_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        dudley_deduction = dudley_params.non_dep_deduction.amount * WEEKS_IN_YEAR
        warrington_deduction = (
            warrington_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        local_deduction = select(
            [
                east_herts_working_age,
                warrington_working_age,
                dudley_working_age,
            ],
            [
                east_herts_deduction,
                warrington_deduction,
                dudley_deduction,
            ],
            classic_deduction,
        )
        local_exemption_applies = (
            east_herts_working_age | warrington_working_age | dudley_working_age
        )
        return where(
            local_exemption_applies & claimant_exempt,
            0.0,
            local_deduction,
        )
