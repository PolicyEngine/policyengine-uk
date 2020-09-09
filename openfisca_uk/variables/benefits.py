from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables

## Person

class JSA_receipt(Variable):
    value_type = bool
    entity = Person
    label = u'Whether receiving JSA'
    definition_period = ETERNITY

class IS_receipt(Variable):
    value_type = bool
    entity = Person
    label = u'Whether receiving JSA'
    definition_period = ETERNITY

# Derived variables

class looking_for_work(Variable):
    value_type = bool
    entity = Family
    label = u'Whether looking for work'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family('family_JSA_receipt', period) > 0

class contributory_JSA(Variable):
    value_type = float
    entity = Family
    label = u'JSA (contributory) amount received per week'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        age = family('younger_adult_age', period)
        is_couple = family.nb_persons(Family.ADULT) == 2
        single_young = (age >= 18) * (age < 25) * (np.logical_not(is_couple))
        single_old = (age >= 25) * (np.logical_not(is_couple))
        personal_allowance = single_young * parameters(period).benefits.JSA.contrib.amount_18_24 + single_old * parameters(period).benefits.JSA.contrib.amount_over_25 + is_couple * parameters(period).benefits.JSA.contrib.amount_couple
        earnings_deduction = max_(0, family('family_earnings', period) - parameters(period).benefits.JSA.contrib.earn_disregard)
        pension_deduction = max_(0, family('family_pension_income', period) - parameters(period).benefits.JSA.contrib.pension_disregard)
        return max_(0, (personal_allowance - earnings_deduction - pension_deduction) * family('family_JSA_receipt', period))

class income_JSA(Variable):
    value_type = float
    entity = Family
    label = u'JSA (income-based) amount received per week'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        younger_age = family('younger_adult_age', period)
        older_age = family('older_adult_age', period)
        personal_allowance = family('is_single', period) * ((younger_age < 25) * parameters(period).benefits.JSA.income.amount_16_24 + (younger_age >= 25) * parameters(period).benefits.JSA.income.amount_over_25) + family('is_couple', period) * ((younger_age < 18) * (older_age < 18) * parameters(period).benefits.JSA.income.amount_couples_16_17 + (younger_age >= 18) * (older_age >= 18) * parameters(period).benefits.JSA.income.amount_couples_over_18 + (younger_age < 18) * (younger_age >= 25) * parameters(period).benefits.JSA.income.amount_couples_age_gap) + family('is_lone_parent', period) * ((younger_age < 18) * parameters(period).benefits.JSA.income.amount_lone_16_17 + (younger_age >= 18) * parameters(period).benefits.JSA.income.amount_lone_over_18)
        means_tested_income = family('family_post_tax_income', period) + family('contributory_JSA', period)
        income_deduction = max_(0, means_tested_income - family('is_single', period) * parameters(period).benefits.JSA.income.income_disregard_single + family('is_couple', period) * parameters(period).benefits.JSA.income.income_disregard_couple + family('is_lone_parent', period) * parameters(period).benefits.JSA.income.income_disregard_lone)
        return family('looking_for_work', period) * max_(0, (personal_allowance - income_deduction))

class JSA_actual(Variable):
    value_type = float
    entity = Family
    label = u'Actual JSA amount received per week'
    definition_period = ETERNITY

class income_support(Variable):
    value_type = float
    entity = Family
    label = u'Income Support amount received per week'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        younger_age = family('younger_adult_age', period)
        older_age = family('older_adult_age', period)
        personal_allowance = family('is_single', period) * ((younger_age < 25) * parameters(period).benefits.income_support.amount_16_24 + (younger_age >= 25) * parameters(period).benefits.income_support.amount_over_25) + family('is_couple', period) * ((younger_age < 18) * (older_age < 18) * parameters(period).benefits.income_support.amount_couples_16_17 + (younger_age >= 18) * (older_age >= 18) * parameters(period).benefits.income_support.amount_couples_over_18 + (younger_age < 18) * (younger_age >= 25) * parameters(period).benefits.income_support.amount_couples_age_gap) + family('is_lone_parent', period) * ((younger_age < 18) * parameters(period).benefits.income_support.amount_lone_16_17 + (younger_age >= 18) * parameters(period).benefits.income_support.amount_lone_over_18)
        means_tested_income = family('family_post_tax_income', period) + family('contributory_JSA', period)
        income_deduction = max_(0, means_tested_income - family('is_single', period) * parameters(period).benefits.income_support.income_disregard_single + family('is_couple', period) * parameters(period).benefits.income_support.income_disregard_couple + family('is_lone_parent', period) * parameters(period).benefits.income_support.income_disregard_lone)
        return max_(0, (personal_allowance - income_deduction) * family('family_IS_receipt', period))

class income_support_actual(Variable):
    value_type = float
    entity = Family
    label = u'Actual income support amount received per week'
    definition_period = ETERNITY

class child_benefit(Variable):
    value_type = float
    entity = Family
    label = u'Child Benefit amount received per week'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        num_children = family.nb_persons(Family.CHILD)
        eldest_amount = min_(num_children, 1) * parameters(period).benefits.child_benefit.amount_eldest
        additional_amount = max_(num_children - 1, 0) * parameters(period).benefits.child_benefit.amount_additional
        return eldest_amount + additional_amount

class child_benefit_actual(Variable):
    value_type = float
    entity = Family
    label = u'Actual child benefit amount received per week'
    definition_period = ETERNITY

class child_tax_credit_pre_means_test(Variable):
    value_type = float
    entity = Family
    label = u'Child Tax Credit amount received per year, before means testing'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        num_exempt_children = family.sum(family.members('is_CTC_child_limit_exempt', period))
        non_exempt_children = family.nb_persons(Family.CHILD) - num_exempt_children
        spaces_left = max_(0, 2 - num_exempt_children)
        children_eligible = num_exempt_children + min_(spaces_left, non_exempt_children)
        yearly_amount = parameters(period).benefits.child_tax_credit.family_element + parameters(period).benefits.child_tax_credit.child_element * children_eligible
        return yearly_amount

class child_working_tax_credit_combined(Variable):
    value_type = float
    entity = Family
    label = u'Child and Working Tax Credit amount received per week, means tested'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        child_tax_credit_amount = family('child_tax_credit_pre_means_test', period)
        working_tax_credit_amount = family('working_tax_credit_pre_means_test', period)
        eligible_for_both = (child_tax_credit_amount > 0) * (working_tax_credit_amount > 0)
        threshold = eligible_for_both * parameters(period).benefits.working_tax_credit.income_threshold + (child_tax_credit_amount > 0) * (1 - eligible_for_both) * parameters(period).benefits.child_tax_credit.income_threshold
        reduction = max_(0, (family('family_total_income', period) * 52 - threshold)) * parameters(period).benefits.child_tax_credit.income_reduction_rate
        means_tested_amount = max_(0, (child_tax_credit_amount + working_tax_credit_amount) - reduction)
        return means_tested_amount / 52

class benefit_cap_reduction(Variable):
    value_type = float
    entity = Family
    label = u'Amount benefit income is reduced by'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        is_exempt = family('working_tax_credit_pre_means_test', period) > 0
        benefit_cap = family('is_single', period) * parameters(period).benefits.benefit_cap.amount_single + (family.nb_persons() > 1) * parameters(period).benefits.benefit_cap.amount_family
        affected_benefits = family('income_support', period) + family('contributory_JSA', period) + family('income_JSA', period) + family('housing_benefit_actual', period) + family('child_benefit', period)
        reduction = max_(0, affected_benefits - benefit_cap)
        return where(is_exempt, 0, reduction)

class working_tax_credit_pre_means_test(Variable):
    value_type = float
    entity = Family
    label = u'Working Tax Credit amount received per year, before means testing'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        hours_worked = family.sum(family.members('hours_worked', period))
        eligible = family('is_single', period) * (hours_worked >= parameters(period).benefits.working_tax_credit.hours_requirement_single) + family('is_couple', period) * (hours_worked >= parameters(period).benefits.working_tax_credit.hours_requirement_couple) + family('is_lone_parent', period) * (hours_worked >= parameters(period).benefits.working_tax_credit.hours_requirement_lone_parent)
        amount = parameters(period).benefits.working_tax_credit.amount_basic + (hours_worked >= parameters(period).benefits.working_tax_credit.hours_requirement_single) * parameters(period).benefits.working_tax_credit.amount_worker + family('is_couple', period) * parameters(period).benefits.working_tax_credit.amount_couple + family('is_lone_parent', period) * parameters(period).benefits.working_tax_credit.amount_lone_parent
        return amount * eligible