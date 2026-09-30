from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (UC Regs 2013 reg 22); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        p = parameters(period).gov.dwp.universal_credit.means_test
        household = benunit.household
        total = add_for_members(benunit, period, p.income_definitions.unearned, members)
        tariff_income_applies = benunit("uc_tariff_income", period) > 0
        reported_capital = benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        property_capital = household(
            "other_residential_property_value", period
        ) + household("non_residential_property_value", period)
        capital_derived_income = (
            ((household("savings", period) > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["savings_interest_income"], members)
            + ((household("corporate_wealth", period) > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["dividend_income"], members)
            + ((property_capital > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["property_income"], members)
        )
        return total - tariff_income_applies * capital_derived_income
