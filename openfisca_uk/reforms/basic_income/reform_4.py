from openfisca_core.model_api import *
from openfisca_uk.entities import *


class income_tax_applicable_amount(Variable):
    value_type = float
    entity = Person
    label = u"Total taxable income per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return max_(
            person("employee_earnings", period)
            + person("self_employed_earnings", period)
            + person("state_pension", period)
            + person("pension_income", period)
            + person("taxed_means_tested_bonus", period)
            + person("interest", period),
            0,
        )


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax paid per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return 0.5 * person("income_tax_applicable_amount", period)

class NI(Variable):
    value_type = float
    entity = Person
    label = u"National Insurance paid per week"
    definition_period = ETERNITY
    reference = ["https://www.gov.uk/national-insurance"]

    def formula(person, period, parameters):
        return 0


class basic_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of basic income received per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        seniors = person("is_senior", period)
        WA_adults = person("is_working_age_adult", period)
        children = person("is_child", period)
        is_disabled = person("disabled", period)
        disabled_adults = (seniors * WA_adults) * is_disabled
        disabled_children = children * is_disabled
        return 175 * seniors + 107 * (WA_adults + children) + 107 * (disabled_adults + disabled_children)


class benunit_basic_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of basic income per week for the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("basic_income", period))

class household_basic_income(Variable):
    value_type = float
    entity = Household
    label = u'Amount of basic income per week for the benefit unit'
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("basic_income", period))


class non_means_tested_bonus(Variable):
    value_type = float
    entity = Person
    label = u"Amount of the basic income which is not subject to means tests"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("basic_income", period)


class reform_4(Reform):
    def apply(self):
        for changed_var in [income_tax, NI, non_means_tested_bonus]:
            self.update_variable(changed_var)
        for added_var in [basic_income, benunit_basic_income, household_basic_income]:
            self.add_variable(added_var)
        for removed_var in [
            "child_benefit",
            "income_support",
            "JSA_contrib",
            "JSA_income",
            "child_tax_credit",
            "working_tax_credit",
            "universal_credit",
            "state_pension",
            "housing_benefit",
            "pension_credit",
        ]:
            self.neutralize_variable(removed_var)
