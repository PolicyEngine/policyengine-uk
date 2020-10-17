from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables


class external_child_maintenance(Variable):
    value_type = float
    entity = BenUnit
    label = "Reported weeklyised amount of maintenance paid to dependent children living away from home"
    definition_period = ETERNITY


# Derived variables


class benunit_benefit_modelling(Variable):
    value_type = float
    entity = BenUnit
    label = "Difference between reported benefits and simulated benefits"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        ADDED_BENEFITS = ["working_tax_credit", "child_tax_credit", "child_benefit", "income_support", "JSA_income", "pension_credit", "housing_benefit", "universal_credit"]
        REMOVED_BENEFITS = ["working_tax_credit_reported", "WTC_lump_sum_reported", "child_tax_credit_reported", "CTC_lump_sum_reported", "JSA_income_reported", "child_benefit_reported", "income_support_reported", "SFL_IS_reported", "SFL_JSA_reported", "DWP_IS_reported", "DWP_JSA_reported", "universal_credit_reported", "DWP_UC_reported", "SFL_UC_reported", "housing_benefit_reported", "pension_credit_reported"]
        added_sum = sum(map(lambda benefit : benunit(benefit, period), ADDED_BENEFITS))
        removed_sum = sum(map(lambda benefit : benunit.sum(benunit.members(benefit, period)), REMOVED_BENEFITS))
        return added_sum - removed_sum


class benunit_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income of the benefit unit (not including benefits)"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income", period))


class benunit_pension_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_income", period))

class benunit_state_pension(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("state_pension", period))


class benunit_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Earnings of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("earnings", period))


class benunit_post_tax_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Post-tax income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("post_tax_income", period))


class benunit_gross_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Gross income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("gross_income", period))


class benunit_net_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Net income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("net_income", period))


class equiv_benunit_net_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Equivalised net income of the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("benunit_net_income", period) / benunit(
            "benunit_equivalisation"
        )

class benunit_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u'Amount of Income Tax per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_tax", period))

class benunit_NI(Variable):
    value_type = float
    entity = BenUnit
    label = u'Amount of National Insurance per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("NI", period))