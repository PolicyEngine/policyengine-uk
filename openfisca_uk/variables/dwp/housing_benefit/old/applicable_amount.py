from openfisca_uk.model_api import *


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for Housing Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        HB = parameters(period).benefit.housing_benefit
        PA = HB.allowances
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_adult_age", period)
        u_18 = eldest_age < 18
        u_25 = eldest_age < 25
        o_25 = (eldest_age >= 25) & ~any_over_SP_age
        o_18 = (eldest_age >= 18) * ~any_over_SP_age
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        single_personal_allowance = (
            u_25 * PA.single.under_25
            + o_25 * PA.single.over_25
            + any_over_SP_age * PA.single.SP_age
        )
        couple_personal_allowance = (
            u_18 * PA.couple.both_under_18
            + o_18 * PA.couple.over_18
            + any_over_SP_age * PA.couple.SP_age
        )
        lone_parent_personal_allowance = (
            u_18 * PA.lone_parent.under_18
            + o_18 * PA.lone_parent.over_18
            + any_over_SP_age * PA.lone_parent.SP_age
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        housing_benefit_eligible = benunit("housing_benefit_eligible", period)
        return (personal_allowance + premiums) * housing_benefit_eligible