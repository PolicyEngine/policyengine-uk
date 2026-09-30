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
        # Only the claimant's (or joint claimants') unearned income counts
        # (UC Regs 2013 reg 22(1)(a)).
        total = add_for_claimant_and_partner(
            benunit, period, p.income_definitions.unearned
        )
        tariff_income_applies = benunit("uc_tariff_income", period) > 0
        reported_capital = benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        property_capital = household(
            "other_residential_property_value", period
        ) + household("non_residential_property_value", period)
        capital_derived_income = (
            ((household("savings", period) > 0) | has_reported_capital)
            * add_for_claimant_and_partner(benunit, period, ["savings_interest_income"])
            + ((household("corporate_wealth", period) > 0) | has_reported_capital)
            * add_for_claimant_and_partner(benunit, period, ["dividend_income"])
            + ((property_capital > 0) | has_reported_capital)
            * add_for_claimant_and_partner(benunit, period, ["property_income"])
        )
        return total - tariff_income_applies * capital_derived_income
