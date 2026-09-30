from policyengine_uk.model_api import *


class housing_benefit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit assessable capital"
    documentation = (
        "Housing Benefit capital counted from the configured capital sources, "
        "allocated across benunits using a household adult-share proxy. Where "
        "the Pension Credit award is savings credit only, the Pension Credit "
        "assessment of capital is used instead."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        any_over_SP_age = benunit.any(person("is_SP_age", period))
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        household_capital = sum(household(source, period) for source in p.sources)
        benunit_adults = add(benunit, period, ["is_adult"])
        household_adults = benunit.max(
            person.household.sum(person.household.members("is_adult", period))
        )
        adult_divisor = max_(1, household_adults)
        household_capital_proxy = where(
            household_adults > 0,
            household_capital * benunit_adults / adult_divisor,
            0,
        )
        # SI 2006/214 reg 27(6) (NI: SR 2006/406 reg 25(6)): where the award of
        # Pension Credit is savings credit only, the Secretary of State's
        # calculation of capital is used, and the £16,000 limit applies to it.
        # The recalculation when capital rises above £16,000 during an
        # assessed income period (reg 27(7) and (8)) is not modelled.
        savings_credit_only = benunit("in_receipt_of_savings_credit_only", period)
        household_capital_proxy = where(
            savings_credit_only,
            benunit("pension_credit_assessable_capital", period),
            household_capital_proxy,
        )
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        return where(guarantee_credit, 0, max_(0, household_capital_proxy))
