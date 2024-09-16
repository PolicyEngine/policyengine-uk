from policyengine_uk.model_api import *


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Winter fuel allowance"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.benefit_uprating_cpi"


class winter_fuel_allowance(Variable):
    label = "Winter Fuel Allowance"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        age = household.members("age", period)
        is_SP_age = household.members("is_SP_age", period)
        wfp = parameters(period).gov.dwp.winter_fuel_payment
        on_mtb = (
            add(
                household,
                period,
                [
                    "pension_credit",
                    "income_support",
                    "esa_income",
                    "jsa_income",
                ],
            )
            > 0
        )
        meets_mtb_requirement = on_mtb | ~wfp.eligibility.require_benefits
        meets_spa_requirement = (
            household.any(is_SP_age)
            | ~wfp.eligibility.state_pension_age_requirement
        )
        meets_higher_age_requirement = household.any(
            age >= wfp.eligibility.higher_age_requirement
        )
        qualifies_for_higher = (
            meets_mtb_requirement
            & meets_spa_requirement
            & meets_higher_age_requirement
        )
        qualifies_for_lower = (
            meets_mtb_requirement
            & meets_spa_requirement
            & ~meets_higher_age_requirement
        )

        return (
            wfp.amount.higher * qualifies_for_higher
            + wfp.amount.lower * qualifies_for_lower
        )
