from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test
        total = add(benunit, period, p.income_definitions.unearned)
        tariff_income_applies = benunit("uc_tariff_income", period) > 0
        capital_derived_income = add(
            benunit, period, p.income_definitions.capital_derived
        )
        return total - tariff_income_applies * capital_derived_income
