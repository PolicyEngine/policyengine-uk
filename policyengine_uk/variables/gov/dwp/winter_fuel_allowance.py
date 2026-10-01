from policyengine_uk.model_api import *


class winter_fuel_allowance(Variable):
    label = "Winter Fuel Allowance"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        in_scotland = household("country", period).decode_to_str() == "SCOTLAND"
        age = household.members("age", period)
        # Social Fund Winter Fuel Payment Regulations 2000 reg 2(1)(b): the
        # qualifying age for State Pension Credit. From 16 September 2024 SI
        # 2024/869 reg 2 uses pensionable age instead; the two agree for
        # every date of birth from 2019-20, so one test serves both.
        qualifying_age = household.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
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
        taxable_income = household.members("total_income", period)
        country = household("country", period).decode_to_str()
        in_england_or_wales = np.isin(country, ["ENGLAND", "WALES"])
        meets_income_passport = (
            household.any(
                qualifying_age
                & (
                    taxable_income
                    < wfp.eligibility.taxable_income_test.maximum_taxable_income
                )
            )
            & in_england_or_wales
            & wfp.eligibility.taxable_income_test.use_maximum_taxable_income
        )

        meets_mtb_requirement = (
            on_mtb | (not wfp.eligibility.require_benefits) | meets_income_passport
        )
        meets_spa_requirement = household.any(qualifying_age) | (
            not wfp.eligibility.state_pension_age_requirement
        )
        meets_higher_age_requirement = household.any(
            age >= wfp.eligibility.higher_age_requirement
        )
        qualifies_for_higher = (
            meets_mtb_requirement & meets_spa_requirement & meets_higher_age_requirement
        )
        qualifies_for_lower = (
            meets_mtb_requirement
            & meets_spa_requirement
            & ~meets_higher_age_requirement
        )

        return ~in_scotland * (
            wfp.amount.higher * qualifies_for_higher
            + wfp.amount.lower * qualifies_for_lower
        )
