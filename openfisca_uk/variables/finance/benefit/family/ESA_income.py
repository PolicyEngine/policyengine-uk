from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"ESA (income-based) (reported amount)"
    definition_period = YEAR


class would_claim_ESA_income(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim income-based ESA"
    documentation = "Whether this family would claim income-based Employment Support Allowance if eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            aggr(benunit, period, ["ESA_income_reported"])
            + benunit("claims_all_entitled_benefits", period)
            > 0
        )


class ESA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"ESA (income) eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"]) > 0


class claims_ESA_income(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Claims ESA (income)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("would_claim_ESA_income", period) & benunit(
            "claims_legacy_benefits", period
        )


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"])
