from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class tax(Variable):
    value_type = float
    entity = Person
    label = u"Total tax liability"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("tax_reported", period)


class reported_tax(Reform):
    def apply(self):
        self.update_variable(tax)


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit entitlement for the family"
    definition_period = YEAR
    reference = "Social Security Contributions and Benefits Act 1992 s. 141"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["child_benefit_reported"])


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"])


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["housing_benefit_reported"])


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["income_support_reported"])


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Job Seeker's Allowance (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["JSA_income_reported"])


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension credit amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["pension_credit_reported"])


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["working_tax_credit_reported"])


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Child Tax Credit entitled to"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["child_tax_credit_reported"])


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["universal_credit_reported"])


class benefits(Variable):
    value_type = float
    entity = Person
    label = u"Total simulated"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("benefits_reported", period)


class AA(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("AA_reported", period)


class AFCS(Variable):
    value_type = float
    entity = Person
    label = u"Armed Forces Compensation Scheme"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("AA_reported", period)


class BSP(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("BSP_reported", period)


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance_reported", period)


class DLA_M(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DLA_M_reported", period)


class DLA_SC(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DLA_SC_reported", period)


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("ESA_contrib_reported", period)


class IIDB(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("IIDB_reported", period)


class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("incapacity_benefit_reported", period)


class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("JSA_contrib_reported", period)


class PIP_DL(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class PIP_M(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PIP_M_reported", period)


class SDA(Variable):
    value_type = float
    entity = Person
    label = u"Severe Disablement Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("SDA_reported", period)


class state_pension(Variable):
    value_type = float
    entity = Person
    label = u"Income from the State Pension"
    definition_period = YEAR
    unit = "currency-GBP"
    documentation = "Gross State Pension payments"

    def formula(person, period, parameters):
        return person("state_pension_reported", period)


class reported_benefits(Reform):
    def apply(self):
        for var in [
            child_benefit,
            ESA_income,
            housing_benefit,
            income_support,
            JSA_income,
            pension_credit,
            working_tax_credit,
            child_tax_credit,
            universal_credit,
            AA,
            AFCS,
            BSP,
            carers_allowance,
            DLA_M,
            DLA_SC,
            ESA_contrib,
            IIDB,
            incapacity_benefit,
            JSA_contrib,
            PIP_M,
            PIP_DL,
            SDA,
            state_pension,
            benefits,
        ]:
            self.update_variable(var)


reported = (reported_tax, reported_benefits)
