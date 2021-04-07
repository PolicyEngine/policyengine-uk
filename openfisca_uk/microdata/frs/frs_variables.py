from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class P_GROSS4(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class B_GROSS4(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

class H_GROSS4(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR

class P_UGRSPAY(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_UDEDUC1(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_INPENINC(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_PROFIT1(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_PROFIT2(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_1(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_2(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_3(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_4(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_5(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_6(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_7(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_8(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_9(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_10(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_11(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_12(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_13(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_14(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_15(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_16(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_17(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_18(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_19(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_21(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_22(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_23(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_24(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_25(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_26(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_27(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_28(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_29(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_ACCINT_ACCOUNT_CODE_30(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class H_SUBLET(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_INDINC(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_NINDINC(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_CHINCDV(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK


FRS_variables = [
    P_GROSS4, 
    B_GROSS4, 
    H_GROSS4,
    P_UGRSPAY,
    P_UDEDUC1,
    P_INPENINC,
    P_PROFIT1,
    P_PROFIT2,
    P_ACCINT_ACCOUNT_CODE_1,
    P_ACCINT_ACCOUNT_CODE_2,
    P_ACCINT_ACCOUNT_CODE_3,
    P_ACCINT_ACCOUNT_CODE_4,
    P_ACCINT_ACCOUNT_CODE_5,
    P_ACCINT_ACCOUNT_CODE_6,
    P_ACCINT_ACCOUNT_CODE_7,
    P_ACCINT_ACCOUNT_CODE_8,
    P_ACCINT_ACCOUNT_CODE_9,
    P_ACCINT_ACCOUNT_CODE_10,
    P_ACCINT_ACCOUNT_CODE_11,
    P_ACCINT_ACCOUNT_CODE_12,
    P_ACCINT_ACCOUNT_CODE_13,
    P_ACCINT_ACCOUNT_CODE_14,
    P_ACCINT_ACCOUNT_CODE_15,
    P_ACCINT_ACCOUNT_CODE_16,
    P_ACCINT_ACCOUNT_CODE_17,
    P_ACCINT_ACCOUNT_CODE_18,
    P_ACCINT_ACCOUNT_CODE_19,
    P_ACCINT_ACCOUNT_CODE_21,
    P_ACCINT_ACCOUNT_CODE_22,
    P_ACCINT_ACCOUNT_CODE_23,
    P_ACCINT_ACCOUNT_CODE_24,
    P_ACCINT_ACCOUNT_CODE_25,
    P_ACCINT_ACCOUNT_CODE_26,
    P_ACCINT_ACCOUNT_CODE_27,
    P_ACCINT_ACCOUNT_CODE_28,
    P_ACCINT_ACCOUNT_CODE_29,
    P_ACCINT_ACCOUNT_CODE_30,
    H_SUBLET,
    P_INDINC,
    P_NINDINC,
    P_CHINCDV
]