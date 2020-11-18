from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class housing_benefit_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u'Whether eligible for Housing Benefit'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.max(benunit.members("living_in_social_housing", period) * benunit.members("is_renting", period))


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount for Housing Benefit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        HB = parameters(period).benefits.housing_benefit
        PA = HB.allowances
        eligible_housing_costs = benunit.sum(
            benunit.members("personal_rent", period)
        )
        eldest_age = benunit("eldest_adult_age", period.this_year)
        u_18 = eldest_age < 18
        u_25 = eldest_age < 25
        o_25 = (eldest_age >= 25) * (eldest_age < 65)
        o_18 = (eldest_age >= 18) * (eldest_age < 65)
        SP = eldest_age >= 65
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        personal_allowance = (
            single
            * (
                u_25 * PA.single.under_25
                + o_25 * PA.single.over_25
                + SP * PA.single.SP_age
            )
            + couple
            * (
                u_18 * PA.couple.both_under_18
                + o_18 * PA.couple.over_18
                + SP * PA.couple.SP_age
            )
            + lone_parent
            * (
                u_18 * PA.lone_parent.under_18
                + o_18 * PA.lone_parent.over_18
                + SP * PA.lone_parent.SP_age
            )
        )
        premiums = add(benunit, period, ["disability_premium", "severe_disability_premium", "enhanced_disability_premium", "carer_premium"])
        return personal_allowance + premiums

class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'Relevant income for Housing Benefit'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        means_test = parameters(period).benefits.housing_benefit.means_test
        BENUNIT_MEANS_TESTED_BENEFITS = ["working_tax_credit"]
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
            * means_test.income_disregard_single
            - benunit("is_couple", period)
            * means_test.income_disregard_couple
            - benunit("is_lone_parent", period)
            * means_test.income_disregard_lone_parent
            - (benunit("benunit_hours", period.this_year) > means_test.worker_hours)
            * means_test.worker_income_disregard,
        )
        return applicable_income

class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u'Housing Benefit'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        rent = benunit.sum(benunit.members("personal_rent", period))
        amount = benunit("housing_benefit_applicable_amount", period)
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(period).benefits.housing_benefit.means_test.withdrawal_rate
        final_amount = rent - max_(0, income - amount) * withdrawal_rate
        return final_amount