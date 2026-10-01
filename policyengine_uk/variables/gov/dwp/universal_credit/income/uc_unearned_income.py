from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    documentation = (
        "The claimant's unearned income, or joint claimants' combined "
        "unearned income. Income of a child, a qualifying young person or "
        "anyone else in the benefit unit who is not a claimant does not count."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 22(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 8(3) and (4)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/8",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 66(1)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 22(1)(a) deducts "all of the claimant's unearned income (or in
        # the case of joint claimants all of their combined unearned income)".
        # Person-level sources count for claimants only; benefit-unit sources
        # (tariff income from capital) are added as they are.
        p = parameters(period).gov.dwp.universal_credit.means_test
        claimants = benunit.members("is_uc_assessed_claimant", period)
        household = benunit.household
        total = add_for_members(
            benunit, period, p.income_definitions.unearned, claimants
        )
        tariff_income_applies = benunit("uc_tariff_income", period) > 0
        reported_capital = benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        property_capital = household(
            "other_residential_property_value", period
        ) + household("non_residential_property_value", period)
        capital_derived_income = (
            ((household("savings", period) > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["savings_interest_income"], claimants)
            + ((household("corporate_wealth", period) > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["dividend_income"], claimants)
            + ((property_capital > 0) | has_reported_capital)
            * add_for_members(benunit, period, ["property_income"], claimants)
        )
        return total - tariff_income_applies * capital_derived_income
