from policyengine_uk.model_api import *


class income_support_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount of Income Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        amounts = IS.amounts
        younger_age = benunit("youngest_adult_age", period)
        older_age = benunit("eldest_adult_age", period)
        younger_under_18 = younger_age < 18
        younger_under_25 = younger_age < 25
        older_under_18 = older_age < 18
        has_children = benunit.any(benunit.members("is_child", period))
        single = benunit("is_single", period)
        single_under_25 = single & ~has_children & younger_under_25
        single_over_25 = single & ~has_children & ~younger_under_25
        lone_young = single & has_children & younger_under_18
        lone_old = single & has_children & ~younger_under_18
        couple_young = ~single & older_under_18
        couple_mixed = ~single & ~older_under_18 & younger_under_18
        couple_old = ~single & ~younger_under_18
        personal_allowance_weekly = select(
            [
                single_under_25,
                single_over_25,
                lone_young,
                lone_old,
                couple_young,
                couple_mixed,
                couple_old,
            ],
            [
                amounts.amount_16_24,
                amounts.amount_over_25,
                amounts.amount_lone_16_17,
                amounts.amount_lone_over_18,
                amounts.amount_couples_16_17,
                amounts.amount_couples_age_gap,
                amounts.amount_couples_over_18,
            ],
        )
        personal_allowance = personal_allowance_weekly * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
