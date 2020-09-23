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
        return person("is_adult", period) * 190


class family_basic_income(Variable):
    value_type = float
    entity = Family
    label = u"Amount of total basic income per week across the family"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members("basic_income", period))


class family_net_income(Variable):
    value_type = float
    entity = Family
    label = u"Net income after taxes and benefits"
    definition_period = ETERNITY

    def formula(family, period, parameters):
        benefits = [
            "family_basic_income",
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
            - family.sum(family.members("income_tax", period))
            - family.sum(family.members("NI", period))
            - family("benefit_cap_reduction", period)
        )


class simulation_4(Reform):
    def apply(self):
        for changed_var in [income_tax, NI, family_net_income]:
            self.update_variable(changed_var)
        for added_var in [basic_income, family_basic_income]:
            self.add_variable(added_var)
