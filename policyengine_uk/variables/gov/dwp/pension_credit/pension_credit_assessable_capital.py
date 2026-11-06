from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import (
    exact_amount,
    round_to_penny,
    valued_capital,
    valued_person_capital,
)
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    pooled_person_capital,
)


class pension_credit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension Credit assessable capital"
    documentation = (
        "Pension Credit capital counted from the configured capital sources. "
        "The formula values each household source, less the ISA balances it "
        "counts in their holders' own benunits, at market value less 10% where a sale would incur "
        "expenses and less any debt secured on it (reg. 19), and values each "
        "such ISA balance as it values that household source. "
        "The "
        "formula allocates the household remainder only across the household's "
        "pension-age adults, so unrelated working-age adults leave a pensioner "
        "couple's share undiluted. The formula counts person-level sources, such as a "
        "Lifetime ISA and the cash and stocks and shares ISAs, only in the holder's "
        "own benunit and only for its claimant or partner (is_claimant_or_partner), "
        "and excludes dependants' capital. It subtracts the ISA balances from the "
        "household capital before allocating the remainder. A nonnegative "
        "`pension_credit_reported_capital` replaces the unit's calculated capital. The "
        "formula does not subtract another unit's capital report from the household "
        "remainder before allocating that remainder. The report and household sources "
        "measure different amounts."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        p = parameters(period).gov.dwp.pension_credit.income.capital
        household_capital = valued_capital(
            lambda source: (
                household(source, period)
                - pooled_person_capital(benunit, source, period, p)
            ),
            p,
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = valued_person_capital(
            benunit, period, parameters, p, claimant_or_partner
        )
        any_pension_age = benunit.any(
            person("has_attained_state_pension_credit_qualifying_age", period)
        )
        benunit_pension_age_adults = benunit.sum(
            person("has_attained_state_pension_credit_qualifying_age", period)
        )
        household_pension_age_adults = benunit.max(
            person.household.sum(
                person.household.members(
                    "has_attained_state_pension_credit_qualifying_age", period
                )
            )
        )
        adult_divisor = max_(1, household_pension_age_adults)
        household_capital_proxy = (
            household_capital * benunit_pension_age_adults / adult_divisor
        )
        reported_capital = exact_amount(
            benunit("pension_credit_reported_capital", period)
        )
        assessed_capital = where(
            reported_capital >= 0,
            reported_capital,
            household_capital_proxy + person_capital,
        )
        # A fraction of a penny is disregarded at the last stage (reg. 24A).
        return round_to_penny(
            where(any_pension_age, max_(0, assessed_capital), 0), p.round_down
        )
