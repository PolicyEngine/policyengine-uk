from openfisca_core.model_api import *
from openfisca_uk.entities import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax paid per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return 0.45 * person("income_tax_applicable_amount", period)


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
        disabled_child = person("disabled", period) * person(
            "is_child", period
        )
        disabled_adult = person("disabled", period) * person(
            "is_adult", period
        )
        return (
            person("is_senior", period) * 175
            + adult_young * 80
            + adult_old * 95
            + disabled_adult * 80
            + disabled_child * 120
            + person("is_child", period) * 65
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
        return person("basic_income", period)


class reform_2(Reform):
    def apply(self):
        for changed_var in [
            income_tax,
            NI,
            non_means_tested_bonus
        ]:
            self.update_variable(changed_var)
        for added_var in [basic_income, benunit_basic_income]:
            self.add_variable(added_var)
        for removed_var in ["child_benefit", "state_pension"]:
            self.neutralize_variable(removed_var)
