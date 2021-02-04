from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_benefit_reported", period, options=[DIVIDE]))


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("ESA_income_reported", period, options=[DIVIDE]))


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("housing_benefit_reported", period, options=[DIVIDE]))


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_support_reported", period, options=[DIVIDE]))


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Job Seeker's Allowance (income-based)"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("JSA_income", period, options=[DIVIDE]))


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension credit amount per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_credit", period, options=[DIVIDE]))


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("working_tax_credit_reported", period, options=[DIVIDE]))


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_tax_credit_reported", period, options=[DIVIDE]))


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit amount per week"
    definition_period = MONTH
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("universal_credit_reported", period, options=[DIVIDE]))


class reported_benefits(Reform):
    def apply(self):
        BENEFITS = [
            child_benefit,
            ESA_income,
            housing_benefit,
            income_support,
            JSA_income,
            pension_credit,
            working_tax_credit,
            child_tax_credit,
            universal_credit,
        ]
        for benefit in BENEFITS:
            self.update_variable(benefit)
