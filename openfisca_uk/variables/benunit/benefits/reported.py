from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class JSA_contributory_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class JSA_income_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class JSA_combined_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class child_tax_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class working_tax_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class income_support_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class child_benefit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY


class DLA_SC_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Disability Living Allowance (self-care) per week"
    definition_period = ETERNITY


class DLA_M_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Disability Living Allowance (mobility)"
    definition_period = ETERNITY


class pension_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Pension credit per week"
    definition_period = ETERNITY


class BSP_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Bereavement Support Payment / Widowed Parents Allowance per week"
    definition_period = ETERNITY


class AFCS_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Armed Forces Compensation Scheme per week"
    definition_period = ETERNITY


class SDA_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Severe Disability Allowance per week"
    definition_period = ETERNITY


class AA_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Attendance Allowance per week"
    definition_period = ETERNITY


class carers_allowance_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Carers Allowance per week"
    definition_period = ETERNITY


class IIDB_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Industrial Injury Disablement Benefit per week"
    definition_period = ETERNITY


class ESA_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Employment and Support Allowance per week"
    definition_period = ETERNITY


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Incapacity Benefit per week"
    definition_period = ETERNITY


class maternity_allowance_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Maternity Allowance per week"
    definition_period = ETERNITY


class guardians_allowance_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Guardians Allowance per week"
    definition_period = ETERNITY


class winter_fuel_payments_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Winter Fuel Payments per week"
    definition_period = ETERNITY


class universal_credit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Universal Credit per week"
    definition_period = ETERNITY


class PIP_DL_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Personal Independence Payment (Daily Living) per week"
    definition_period = ETERNITY


class PIP_M_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Personal Independence Payment (Mobility)"
    definition_period = ETERNITY


class housing_benefit_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"label"
    definition_period = ETERNITY
