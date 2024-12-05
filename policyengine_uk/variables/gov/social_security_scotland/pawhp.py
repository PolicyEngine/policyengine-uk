from policyengine_uk.model_api import *


class pawhp(Variable):
    label = "Pension Age Winter Heating Payment"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        in_scotland = (
            household("country", period).decode_to_str() == "SCOTLAND"
        )
        age = household.members("age", period)
        is_SP_age = household.members("is_SP_age", period)
        wfp = parameters(period).gov.social_security_scotland.pawhp
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

        qualifies_for_base = ~meets_mtb_requirement & meets_spa_requirement

        return in_scotland * (
            wfp.amount.higher * qualifies_for_higher
            + wfp.amount.lower * qualifies_for_lower
            + wfp.amount.base * qualifies_for_base
        )
