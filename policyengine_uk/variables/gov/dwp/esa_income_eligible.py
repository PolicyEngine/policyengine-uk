from policyengine_uk.model_api import *


class esa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for income-related ESA after the capital test"
    documentation = (
        "Bounded capital-rule screen applied to reported income-related ESA "
        "awards. This is not a full entitlement model."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        capital = benunit("esa_income_assessable_capital", period)
        reported_award = add(benunit, period, ["esa_income_reported"]) > 0
        return reported_award & (capital <= ESA.capital.limit)
