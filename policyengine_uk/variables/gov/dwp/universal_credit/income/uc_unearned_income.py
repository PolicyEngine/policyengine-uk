from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test
        household = benunit.household
        total = add(benunit, period, p.income_definitions.unearned)
        tariff_income_applies = benunit("uc_tariff_income", period) > 0
        reported_capital = benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        property_capital = household(
            "other_residential_property_value", period
        ) + household("non_residential_property_value", period)
        capital_derived_income = (
            ((household("savings", period) > 0) | has_reported_capital)
            * benunit("savings_interest_income", period)
            + ((household("corporate_wealth", period) > 0) | has_reported_capital)
            * benunit("dividend_income", period)
            + ((property_capital > 0) | has_reported_capital)
            * benunit("property_income", period)
        )
        return total - tariff_income_applies * capital_derived_income
