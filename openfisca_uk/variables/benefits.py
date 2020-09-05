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

class JSA(Variable):
    value_type = float
    entity = Family
    label = u'JSA amount received per week'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        age = family('younger_adult_age', period)
        is_couple = family.nb_persons(Family.ADULT) == 2
        single_young = (age >= 18) * (age < 25) * (np.logical_not(is_couple))
        single_old = (age >= 25) * (np.logical_not(is_couple))
        personal_allowance = single_young * parameters(period).benefits.JSA.amount_18_24 + single_old * parameters(period).benefits.JSA.amount_over_25 + is_couple * parameters(period).benefits.JSA.amount_couple
        earnings_deduction = max_(0, family('family_earnings', period) - parameters(period).benefits.JSA.earn_disregard)
        pension_deduction = max_(0, family('family_pension_income', period) - parameters(period).benefits.JSA.pension_disregard)
        return max_(0, (personal_allowance - earnings_deduction - pension_deduction) * family('family_JSA_receipt', period))

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
        income_deduction = max_(0, family('family_total_income', period) - family('is_single', period) * parameters(period).benefits.income_support.income_disregard_single + family('is_couple', period) * parameters(period).benefits.income_support.income_disregard_couple + family('is_lone_parent', period) * parameters(period).benefits.income_support.income_disregard_lone)
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