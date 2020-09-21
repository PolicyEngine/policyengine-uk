from openfisca_core.model_api import *
from openfisca_uk.entities import *
import os

dir_name = os.path.dirname(__file__)


def modify_parameters(parameters):
    file_path = os.path.join(
        dir_name, "parameters", "simulation_2", "new_income_tax.yaml"
    )
    reform_parameters_subtree = load_parameter_file(file_path, name="new_income_tax")
    parameters.taxes.income_tax.add_child("new_income_tax", reform_parameters_subtree)
    return parameters


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax paid per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        estimated_yearly_income = (person("taxable_income", period)) * 52
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
        return 0.12 * person("taxable_income", period)


class basic_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of basic income received per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        adult_young = (person("age", period) >= 16) * (person("age", period) < 24)
        adult_old = (person("age", period) >= 24) * (person("age", period) < 65)
        return (
            person("is_senior", period) * 50
            + adult_young * 55
            + adult_old * 65
            + person("is_child", period) * 22
        )


class family_basic_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of total basic income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members("basic_income", period))


class family_total_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of total income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (
            family("family_earnings", period)
            + family("family_pension_income", period)
            + family("family_basic_income", period)
        )


class family_net_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return (
            family("family_total_income", period)
            + family("child_tax_credit", period)
            + family("working_tax_credit", period)
            + family("child_benefit", period)
            + family("income_support", period)
            + family("housing_benefit_actual", period)
            + family("contributory_JSA", period)
            + family("income_JSA", period)
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
            - family("benefit_cap_reduction", period)
        )


class simulation_2(Reform):
    def apply(self):
        self.modify_parameters(modify_parameters)
        for changed_var in [
            income_tax,
            NI,
            family_net_income,
            family_total_income,
        ]:
            self.update_variable(changed_var)
        for added_var in [basic_income, family_basic_income]:
            self.add_variable(added_var)
