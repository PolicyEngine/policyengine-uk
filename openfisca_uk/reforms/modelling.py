from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("child_benefit_reported", period)


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("ESA_income_reported", period.this_year)


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("housing_benefit_reported", period.this_year)


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("income_support_reported", period.this_year)


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Job Seeker's Allowance (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("JSA_income_reported", period.this_year)


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension credit amount per week"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("pension_credit_reported", period.this_year)


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("working_tax_credit_reported", period.this_year)


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Tax Credit"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("child_tax_credit_reported", period.this_year)


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit amount per week"
    definition_period = MONTH

    def formula(benunit, period, parameters):
        return benunit("universal_credit_reported", period.this_year)


class reported_benefits(Reform):
    name = u"Disable simulation of benefits"

    def apply(self):
        SIMULATED = [
            working_tax_credit,
            child_tax_credit,
            child_benefit,
            ESA_income,
            housing_benefit,
            income_support,
            JSA_income,
            pension_credit,
            universal_credit,
        ]
        for benefit in SIMULATED:
            self.update_variable(benefit)
