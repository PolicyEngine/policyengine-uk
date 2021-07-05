from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class P_SEX(Variable):
    value_type = float
    entity = Person
    definition_period = ETERNITY


class P_INOTHBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INDISBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INRPINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INDUC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INTXCRED(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ROYYR1(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_SEINCAM2(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INRINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ININV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class H_HHRENT(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


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
    definition_period = YEAR


class P_UDEDUC1(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INPENINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_PROFIT1(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_PROFIT2(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_SEINCAMT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_1(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_2(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_3(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_4(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_5(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_6(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_7(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_8(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_9(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_10(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_11(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_12(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_13(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_14(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_15(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_16(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_17(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_18(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_19(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_21(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_22(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_23(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_24(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_25(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_26(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_27(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_28(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_29(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_ACCINT_ACCOUNT_CODE_30(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class H_SUBLET(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_INDINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_NINDINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_CHINCDV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_1(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_2(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_3(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_4(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_5(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_6(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_8(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_9(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_10(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_12(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_13(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_14(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_1014(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_15(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_16(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_17(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_19(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_21(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_22(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_24(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_30(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_31(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_32(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_33(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_34(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_35(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_36(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_37(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_61(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_62(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_65(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_66(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_69(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_70(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_78(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_81(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_82(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_83(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_90(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_91(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_92(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_94(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_95(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_96(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_97(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_98(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_99(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_102(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_103(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_104(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_105(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_106(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_107(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_108(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_109(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_110(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_BENAMT_BENEFIT_CODE_111(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_AGE80(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_AGE(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_PERSON(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_UPERSON(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_TYPEED2(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_TOTHOURS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_EMPSTATI(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_FUELAMT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_MILEAMT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_MOTAMT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class H_PTENTYP2(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class H_GBHSCOST(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class H_NIHSCOST(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class H_CTANNUAL(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class P_person_id(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class B_benunit_id(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR


class H_household_id(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class H_GVTREGNO(Variable):
    value_type = int
    entity = Household
    definition_period = ETERNITY


class H_TYPEACC(Variable):
    value_type = int
    entity = Household
    definition_period = ETERNITY


class H_BEDROOM6(Variable):
    value_type = int
    entity = Household
    definition_period = ETERNITY


FRS_variables = [
    H_BEDROOM6,
    H_TYPEACC,
    H_GVTREGNO,
    P_person_id,
    B_benunit_id,
    H_household_id,
    H_CTANNUAL,
    H_GBHSCOST,
    H_NIHSCOST,
    H_HHRENT,
    H_PTENTYP2,
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
    P_CHINCDV,
    P_BENAMT_BENEFIT_CODE_1,
    P_BENAMT_BENEFIT_CODE_2,
    P_BENAMT_BENEFIT_CODE_3,
    P_BENAMT_BENEFIT_CODE_4,
    P_BENAMT_BENEFIT_CODE_5,
    P_BENAMT_BENEFIT_CODE_6,
    P_BENAMT_BENEFIT_CODE_8,
    P_BENAMT_BENEFIT_CODE_9,
    P_BENAMT_BENEFIT_CODE_10,
    P_BENAMT_BENEFIT_CODE_12,
    P_BENAMT_BENEFIT_CODE_13,
    P_BENAMT_BENEFIT_CODE_14,
    P_BENAMT_BENEFIT_CODE_1014,
    P_BENAMT_BENEFIT_CODE_15,
    P_BENAMT_BENEFIT_CODE_16,
    P_BENAMT_BENEFIT_CODE_17,
    P_BENAMT_BENEFIT_CODE_19,
    P_BENAMT_BENEFIT_CODE_21,
    P_BENAMT_BENEFIT_CODE_22,
    P_BENAMT_BENEFIT_CODE_24,
    P_BENAMT_BENEFIT_CODE_30,
    P_BENAMT_BENEFIT_CODE_31,
    P_BENAMT_BENEFIT_CODE_32,
    P_BENAMT_BENEFIT_CODE_33,
    P_BENAMT_BENEFIT_CODE_34,
    P_BENAMT_BENEFIT_CODE_35,
    P_BENAMT_BENEFIT_CODE_36,
    P_BENAMT_BENEFIT_CODE_37,
    P_BENAMT_BENEFIT_CODE_61,
    P_BENAMT_BENEFIT_CODE_62,
    P_BENAMT_BENEFIT_CODE_65,
    P_BENAMT_BENEFIT_CODE_66,
    P_BENAMT_BENEFIT_CODE_69,
    P_BENAMT_BENEFIT_CODE_70,
    P_BENAMT_BENEFIT_CODE_78,
    P_BENAMT_BENEFIT_CODE_81,
    P_BENAMT_BENEFIT_CODE_82,
    P_BENAMT_BENEFIT_CODE_83,
    P_BENAMT_BENEFIT_CODE_90,
    P_BENAMT_BENEFIT_CODE_91,
    P_BENAMT_BENEFIT_CODE_92,
    P_BENAMT_BENEFIT_CODE_94,
    P_BENAMT_BENEFIT_CODE_95,
    P_BENAMT_BENEFIT_CODE_96,
    P_BENAMT_BENEFIT_CODE_97,
    P_BENAMT_BENEFIT_CODE_98,
    P_BENAMT_BENEFIT_CODE_99,
    P_BENAMT_BENEFIT_CODE_102,
    P_BENAMT_BENEFIT_CODE_103,
    P_BENAMT_BENEFIT_CODE_104,
    P_BENAMT_BENEFIT_CODE_105,
    P_BENAMT_BENEFIT_CODE_106,
    P_BENAMT_BENEFIT_CODE_107,
    P_BENAMT_BENEFIT_CODE_108,
    P_BENAMT_BENEFIT_CODE_109,
    P_BENAMT_BENEFIT_CODE_110,
    P_BENAMT_BENEFIT_CODE_111,
    P_AGE80,
    P_AGE,
    P_PERSON,
    P_UPERSON,
    P_TYPEED2,
    P_TOTHOURS,
    P_SEINCAMT,
    P_EMPSTATI,
    P_FUELAMT,
    P_MILEAMT,
    P_MOTAMT,
    P_SEINCAM2,
    P_INRINC,
    P_ROYYR1,
    P_ININV,
    P_INTXCRED,
    P_INDUC,
    P_INOTHBEN,
    P_INDISBEN,
    P_INRPINC,
    P_SEX,
]
