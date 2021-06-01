from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class PAY(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class TAXTERM(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class EXPS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class PENSION(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class SRP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class INCPBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class UBISJA(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class OSSBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class PROFITS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class INCPROP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class INCBBS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class DIVIDENDS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class OTHERINV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class OTHERINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class MOTHINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class BPADUE(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class MCAS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class P_FACT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class B_FACT(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR


class H_FACT(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR


class TAXINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class TOTTAX(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class SCOT_TXP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class GIFTAID(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class GIFTINV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class CAPALL(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class COVNTS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class DEFICIEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class EPB(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class MOTHDED(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class PENSRLF(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class AGERANGE(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR


SPI_variables = [
    AGERANGE,
    PAY,
    TAXTERM,
    EXPS,
    PENSION,
    SRP,
    INCPBEN,
    UBISJA,
    OSSBEN,
    PROFITS,
    INCPROP,
    INCBBS,
    DIVIDENDS,
    OTHERINV,
    OTHERINC,
    MOTHINC,
    BPADUE,
    MCAS,
    P_FACT,
    B_FACT,
    H_FACT,
    SCOT_TXP,
    TAXINC,
    TOTTAX,
    GIFTAID,
    GIFTINV,
    CAPALL,
    COVNTS,
    DEFICIEN,
    EPB,
    MOTHDED,
    PENSRLF,
]
