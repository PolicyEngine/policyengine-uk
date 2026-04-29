from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_chesterfield_working_age,
    is_darlington_working_age,
    is_east_hertfordshire_working_age,
    is_dudley_working_age,
    is_gateshead_working_age,
    is_kings_lynn_and_west_norfolk_working_age,
    is_merton_working_age,
    is_norwich_working_age,
    is_southwark_working_age,
    is_stevenage_working_age,
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
        chesterfield_params = parameters(
            period
        ).gov.local_authorities.chesterfield.council_tax_reduction
        darlington_params = parameters(
            period
        ).gov.local_authorities.darlington.council_tax_reduction
        east_herts_params = parameters(
            period
        ).gov.local_authorities.east_hertfordshire.council_tax_reduction
        gateshead_params = parameters(
            period
        ).gov.local_authorities.gateshead.council_tax_reduction
        kings_lynn_params = parameters(
            period
        ).gov.local_authorities.kings_lynn_and_west_norfolk.council_tax_reduction
        stevenage_params = parameters(
            period
        ).gov.local_authorities.stevenage.council_tax_reduction
        merton_params = parameters(
            period
        ).gov.local_authorities.merton.council_tax_reduction
        norwich_params = parameters(
            period
        ).gov.local_authorities.norwich.council_tax_reduction
        southwark_params = parameters(
            period
        ).gov.local_authorities.southwark.council_tax_reduction
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
        classic_deduction = (
            p.amount.calc(weekly_total_income, right=True) * WEEKS_IN_YEAR
        )

        household = person.household
        local_authority = household("local_authority", period)
        country = household("country", period)
        has_pensioner = household(
            "council_tax_reduction_household_has_pensioner", period
        )
        chesterfield_working_age = is_chesterfield_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        darlington_working_age = is_darlington_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        east_herts_working_age = is_east_hertfordshire_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        gateshead_working_age = is_gateshead_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        kings_lynn_working_age = is_kings_lynn_and_west_norfolk_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        stevenage_working_age = is_stevenage_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        merton_working_age = is_merton_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        norwich_working_age = is_norwich_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        southwark_working_age = is_southwark_working_age(
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
        chesterfield_deduction = (
            chesterfield_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        darlington_deduction = (
            darlington_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        stevenage_deduction = (
            stevenage_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        gateshead_deduction = (
            gateshead_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        kings_lynn_deduction = (
            kings_lynn_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        merton_deduction = (
            merton_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        norwich_deduction = (
            norwich_params.non_dep_deduction.amount.calc(weekly_earned_income)
            * WEEKS_IN_YEAR
        )
        southwark_deduction = (
            southwark_params.non_dep_deduction.amount.calc(weekly_earned_income)
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
                chesterfield_working_age,
                darlington_working_age,
                east_herts_working_age,
                gateshead_working_age,
                kings_lynn_working_age,
                stevenage_working_age,
                merton_working_age,
                norwich_working_age,
                southwark_working_age,
                warrington_working_age,
                dudley_working_age,
            ],
            [
                chesterfield_deduction,
                darlington_deduction,
                east_herts_deduction,
                gateshead_deduction,
                kings_lynn_deduction,
                stevenage_deduction,
                merton_deduction,
                norwich_deduction,
                southwark_deduction,
                warrington_deduction,
                dudley_deduction,
            ],
            classic_deduction,
        )
        local_exemption_applies = (
            chesterfield_working_age
            | darlington_working_age
            | east_herts_working_age
            | gateshead_working_age
            | kings_lynn_working_age
            | stevenage_working_age
            | merton_working_age
            | norwich_working_age
            | southwark_working_age
            | warrington_working_age
            | dudley_working_age
        )
        return where(
            local_exemption_applies & claimant_exempt,
            0.0,
            local_deduction,
        )
