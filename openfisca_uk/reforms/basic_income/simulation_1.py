from openfisca_core.model_api import *
from openfisca_uk.entities import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax paid per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return 0.45 * person("taxable_income", period)


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
            person("is_senior", period) * 290
            + adult_young * 70
            + adult_old * 105
            + disabled_adult * 60
            + disabled_child * 105
            + person("is_child", period) * 105
        )


class family_basic_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of total basic income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members("basic_income", period))


class pension_income(Variable):
    value_type = float
    entity = Person
    label = u"Total pension income per week"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("private_pension_actual", period)


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
            - 25
        )


class family_net_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        benefits = [
            "child_tax_credit",
            "working_tax_credit",
            "child_benefit",
            "income_support",
            "housing_benefit_actual",
            "contributory_JSA",
            "income_JSA",
            "DLA_SC_actual",
            "DLA_M_actual",
            "pension_credit_actual",
            "BSP_actual",
            "AFCS_actual",
            "SDA_actual",
            "AA_actual",
            "carers_allowance_actual",
            "IIDB_actual",
            "ESA_actual",
            "incapacity_benefit_actual",
            "maternity_allowance_actual",
            "guardians_allowance_actual",
            "winter_fuel_payments_actual",
        ]
        return (
            family("family_total_income", period)
            + sum(map(lambda benefit: family(benefit, period), benefits))
            + 25
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
            - family("benefit_cap_reduction", period)
        )


class simulation_1(Reform):
    def apply(self):
        for changed_var in [
            income_tax,
            NI,
            family_net_income,
            family_total_income,
            pension_income,
        ]:
            self.update_variable(changed_var)
        for added_var in [basic_income, family_basic_income]:
            self.add_variable(added_var)
        for removed_var in ["child_benefit"]:
            self.neutralize_variable(removed_var)
