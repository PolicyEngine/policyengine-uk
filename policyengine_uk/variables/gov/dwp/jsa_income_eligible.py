from policyengine_uk.model_api import *


class jsa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for income-based JSA after the capital test"
    documentation = (
        "Bounded capital-rule screen applied to reported income-based JSA awards. "
        "This is not a full entitlement model."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA.income
        capital = benunit("jsa_income_assessable_capital", period)
        reported_award = add(benunit, period, ["jsa_income_reported"]) > 0
        return reported_award & (capital <= JSA.capital.capital_limit)
