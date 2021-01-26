from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = u"Income Support (reported amount)"
    definition_period = YEAR

class benunit_income_support_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support (reported amount)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_support_reported", period))



class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for Income Support"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        lone_parent = benunit("is_lone_parent", period) * (
            benunit("youngest_child_age", period.this_year) <= 5
        )
        QUALIFYING_COMPONENTS = ["is_carer", "SSP"]
        eligible = (
            aggr(benunit, period, QUALIFYING_COMPONENTS) + lone_parent
        ) > 0
        under_SP_age = benunit.max(benunit.members("is_SP_age", period)) == 0
        eligible *= under_SP_age
        already_claiming = (
            benunit("benunit_income_support_reported", period) > 0
        )
        return (
            not_(benunit("ESA_income_eligible", period))
            * eligible
            * already_claiming
        )


class income_support_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount of Income Support"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        IS = parameters(period).benefits.income_support
        amounts = IS.amounts
        younger_age = benunit("youngest_adult_age", period.this_year)
        older_age = benunit("eldest_adult_age", period.this_year)
        kids = benunit("has_children", period)
        single = benunit("is_single", period)
        single_under_25 = single * not_(kids) * (younger_age < 25)
        single_over_25 = single * not_(kids) * (younger_age >= 25)
        lone_young = single * kids * (younger_age < 18)
        lone_old = single * kids * (younger_age >= 18)
        couple_young = not_(single) * (older_age < 18)
        couple_mixed = not_(single) * (older_age >= 18) * (younger_age < 18)
        couple_old = not_(single) * (younger_age >= 18)
        personal_allowance = select(
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
        premiums = (
            benunit("disability_premium", period)
            + benunit("severe_disability_premium", period)
            + benunit("enhanced_disability_premium", period)
            + benunit("carer_premium", period)
        )
        return (personal_allowance + premiums) * benunit(
            "income_support_eligible", period.this_year
        )


class income_support_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Means-tested income for Income Support"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        IS = parameters(period).benefits.income_support
        BENUNIT_MEANS_TESTED_BENEFITS = []
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = aggr(benunit, period, PERSON_MEANS_TESTED_BENEFITS) + add(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period, options=[MATCH])
            + benefits
        )
        applicable_income = max_(
            0,
            means_tested_income
            - benunit("is_single_person", period)
            * IS.means_test.income_disregard_single
            - benunit("is_couple", period)
            * IS.means_test.income_disregard_couple
            - benunit("is_lone_parent", period)
            * IS.means_test.income_disregard_lone_parent,
        )
        return applicable_income


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        IS = parameters(period).benefits.income_support
        amount = benunit("income_support_applicable_amount", period)
        relevant_income = benunit("income_support_applicable_income", period)
        return max_(
            0,
            (amount - relevant_income),
        )
