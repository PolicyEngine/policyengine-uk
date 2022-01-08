from openfisca_uk.model_api import *


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = "ESA (income-based) (reported amount)"
    definition_period = YEAR
    unit = "currency-GBP"


class would_claim_ESA_income(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim income-based ESA"
    documentation = "Whether this family would claim income-based Employment Support Allowance if eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reports_ESA_income = aggr(benunit, period, ["ESA_income_reported"]) > 0
        claims_all = benunit("claims_all_entitled_benefits", period)
        return reports_ESA_income | claims_all


class ESA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "ESA (income) eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"]) > 0


class claims_ESA_income(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims ESA (income)"
    documentation = "Claims income-based Employment and Support Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_claim = benunit("would_claim_ESA_income", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim & claims_legacy_benefits


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = "Employment and Support Allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"])
