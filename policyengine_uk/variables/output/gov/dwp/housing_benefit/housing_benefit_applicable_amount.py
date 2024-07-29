from policyengine_uk.model_api import *


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Housing Benefit amount"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_eligible"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_adult_age", period)
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~any_over_SP_age
        o_18 = (eldest_age >= younger_age_threshold) * ~any_over_SP_age
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        single_personal_allowance = (
            u_25 * p.single.younger
            + o_25 * p.single.older
            + any_over_SP_age * p.single.aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger
            + o_18 * p.couple.older
            + any_over_SP_age * p.couple.aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + any_over_SP_age * p.lone_parent.aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
