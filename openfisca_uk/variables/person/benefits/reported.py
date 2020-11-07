from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of State Pension receipt"
    definition_period = ETERNITY


class JSA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of JSA (total)"
    definition_period = ETERNITY


class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of JSA (contributory) receipt"
    definition_period = ETERNITY


class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of JSA (income-based) receipt"
    definition_period = ETERNITY


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Child Tax Credit receipt"
    definition_period = ETERNITY


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Working Tax Credit receipt"
    definition_period = ETERNITY


class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Income Support receipt"
    definition_period = ETERNITY


class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Child Benefit receipt"
    definition_period = ETERNITY


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = (
        u"Reported amount of Disability Living Allowance (self-care) per week"
    )
    definition_period = ETERNITY


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Disability Living Allowance (mobility)"
    definition_period = ETERNITY


class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Pension credit per week"
    definition_period = ETERNITY


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Bereavement Support Payment / Widowed Parents Allowance per week"
    definition_period = ETERNITY


class AFCS_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Armed Forces Compensation Scheme per week"
    definition_period = ETERNITY


class SDA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Severe Disability Allowance per week"
    definition_period = ETERNITY


class AA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Attendance Allowance per week"
    definition_period = ETERNITY


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Carers Allowance per week"
    definition_period = ETERNITY


class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = (
        u"Reported amount of Industrial Injury Disablement Benefit per week"
    )
    definition_period = ETERNITY


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Employment and Support Allowance (contributory) per week"
    definition_period = ETERNITY


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Employment and Support Allowance (income-based) per week"
    definition_period = ETERNITY


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Incapacity Benefit per week"
    definition_period = ETERNITY


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Maternity Allowance per week"
    definition_period = ETERNITY


class guardians_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Guardians Allowance per week"
    definition_period = ETERNITY


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Winter Fuel Allowance per week"
    definition_period = ETERNITY


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Universal Credit per week"
    definition_period = ETERNITY


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Personal Independence Payment (Daily Living) per week"
    definition_period = ETERNITY


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Personal Independence Payment (Mobility)"
    definition_period = ETERNITY


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Housing Benefit receipt"
    definition_period = ETERNITY


class war_pension_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of War Widows Pension receipt"
    definition_period = ETERNITY


class GTA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Government training allowances receipt"
    definition_period = ETERNITY


class other_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of any other benefit"
    definition_period = ETERNITY


class WTC_lump_sum_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported weeklyised lump sum payment for Working Tax Credit"
    definition_period = ETERNITY


class CTC_lump_sum_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported weeklyised lump sum payment for Child Tax Credit"
    definition_period = ETERNITY


class SFL_IS_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Income Support, net of Social Fund Loan repayments"
    definition_period = ETERNITY


class SFL_JSA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of JSA, net of Social Fund Loan repayments"
    definition_period = ETERNITY


class SFL_UC_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of universal credit, net of Social Fund Loan repayments"
    definition_period = ETERNITY


class DWP_IS_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported third party IS payments from DWP, after deductions"
    definition_period = ETERNITY


class DWP_JSA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported third party JSA payments from DWP, after deductions"
    definition_period = ETERNITY


class DWP_UC_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported third party UC payments from DWP, after deductions"
    definition_period = ETERNITY


class FG_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported weeklyised Funeral Grant payment"
    definition_period = ETERNITY


class MG_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported weeklyised Maternity Grant payment"
    definition_period = ETERNITY


class widows_payment_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported weeklyised Widows Payment"
    definition_period = ETERNITY


class DWP_loan_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported loan from DWP"
    definition_period = ETERNITY


class LA_loan_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported loan or grant from the Local Authority"
    definition_period = ETERNITY


class total_disability_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Total disability benefits reported"
    definition_period = ETERNITY
