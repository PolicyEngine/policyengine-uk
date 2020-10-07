from openfisca_core.model_api import *
from openfisca_uk.entities import *
import os

dir_name = os.path.dirname(__file__)


def modify_parameters(parameters):
    file_path = os.path.join(
        dir_name, "parameters", "reform_1", "new_income_tax.yaml"
    )
    reform_parameters_subtree = load_parameter_file(
        file_path, name="new_income_tax"
    )
    parameters.taxes.income_tax.add_child(
        "new_income_tax", reform_parameters_subtree
    )
    return parameters


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax paid per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        estimated_yearly_income = (
            person("income_tax_applicable_amount", period)
        ) * 52
        weekly_tax = (
            parameters(period).taxes.income_tax.new_income_tax.calc(
                estimated_yearly_income
            )
        ) / 52
        return weekly_tax


class NI(Variable):
    value_type = float
    entity = Person
    label = u"National Insurance paid per week"
    definition_period = ETERNITY
    reference = ["https://www.gov.uk/national-insurance"]

    def formula(person, period, parameters):
        return (
            0.12
            * (
                person("employee_earnings", period)
                + person("self_employed_earnings", period)
            )
            * (1 - person("is_state_pension_age", period))
        )


class basic_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of basic income received per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        adult_young = (person("age", period) >= 16) * (
            person("age", period) < 24
        )
        adult_old = (person("age", period) >= 24) * (
            person("age", period) < 65
        )
        return (
            person("is_senior", period) * 35
            + adult_young * 45
            + adult_old * 50
            + person("is_child", period) * 20
        )


class benunit_basic_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of basic income per week for the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("basic_income", period))


class non_means_tested_bonus(Variable):
    value_type = float
    entity = Person
    label = u"Amount of the basic income which is not subject to means tests"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return min_(25, person("basic_income", period))


class untaxed_means_tested_bonus(Variable):
    value_type = float
    entity = Person
    label = u"Amount of the basic income which is subject to means tests"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return max_(0, person("basic_income", period) - 25)


class reform_1(Reform):
    def apply(self):
        self.modify_parameters(modify_parameters)
        for changed_var in [
            income_tax,
            NI,
            untaxed_means_tested_bonus,
            non_means_tested_bonus,
        ]:
            self.update_variable(changed_var)
        for added_var in [basic_income, benunit_basic_income]:
            self.add_variable(added_var)
