from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class pension_credit_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u'Whether eligible for Pension Credit'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        both_SP_age = benunit.min(benunit.members("is_SP_age", period))
        one_SP_age = benunit.max(benunit.members("is_SP_age", period))
        claiming_HB = benunit("housing_benefit", period, options=[ADD]) > 0
        return both_SP_age + (one_SP_age * claiming_HB) > 0

class pension_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u'Reported amount of Pension Credit per week'
    definition_period = YEAR

class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension credit amount per week"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        PC = benunit("pension_credit_GC", period) + benunit(
            "pension_credit_SC", period
        )
        return benunit("pension_credit_eligible", period.this_year) * PC


class pension_credit_MG(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Minimum Guarantee) amount per week"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        PC = parameters(period).benefits.pension_credit
        personal_allowance = (
            benunit("is_single", period) * PC.min_guarantee.single
            + benunit("is_couple", period) * PC.min_guarantee.couple
        )
        premiums = benunit("severe_disability_premium", period) + benunit("carer_premium", period)
        applicable_amount = personal_allowance + premiums
        return applicable_amount


class pension_credit_GC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Guarantee Credit) amount per week"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_applicable_income", period)
        return benunit("pension_credit_eligible", period.this_year) * max_(
            0, benunit("pension_credit_MG", period) - income
        )

class pension_credit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'Applicable income for Pension Credit'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        BENUNIT_MEANS_TESTED_BENEFITS = ["working_tax_credit"]
        PERSON_MEANS_TESTED_BENEFITS = ["total_disability_benefits", "state_pension"]
        benefits = aggr(benunit, period, PERSON_MEANS_TESTED_BENEFITS, options=[MATCH]) + add(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period, options=[MATCH])
            + benefits
        )
        return means_tested_income


class pension_credit_SC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Savings Credit) amount per week"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        PC = parameters(period).benefits.pension_credit
        income = benunit("pension_credit_applicable_income", period)
        MG_amount = benunit("pension_credit_MG", period)
        threshold = PC.savings_credit.single_threshold * benunit(
            "is_single", period
        ) + PC.savings_credit.couple_threshold * benunit(
            "is_couple", period
        )
        maximum_amount = PC.savings_credit.max_single * benunit(
            "is_single", period
        ) + PC.savings_credit.max_single * benunit("is_couple", period)
        income_above_threshold = max_(0, income - threshold)
        income_above_MG = max_(0, income - MG_amount)
        SC_amount = min_(
            income_above_threshold
            * (1 - PC.savings_credit.withdrawal_rate),
            maximum_amount,
        )
        deduction = income_above_MG * PC.savings_credit.withdrawal_rate
        SC_final_amount = max_(0, SC_amount - deduction)
        return max_(0, SC_final_amount)
