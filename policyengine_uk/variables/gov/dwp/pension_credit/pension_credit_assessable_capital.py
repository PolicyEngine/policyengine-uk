from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import valued_capital


class pension_credit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension Credit assessable capital"
    documentation = (
        "Pension Credit capital counted from the configured capital sources, "
        "each valued at market value less 10% where a sale would incur "
        "expenses and less any debt secured on it (reg. 19), split only across pension-age adults in the household so pensioner "
        "couples pool capital together without dilution by unrelated working-"
        "age adults. Person-level sources, such as a Lifetime ISA, count "
        "only for the holder's own benunit, and only when the holder is its "
        "claimant or partner (is_claimant_or_partner): a dependant's capital "
        "is not the claimant's. Where `pension_credit_reported_capital` records "
        "the benefit unit's own capital (0 or more), it replaces the "
        "household proxy and the person-level sources. Unlike "
        "`uc_assessable_capital`, another benefit unit's recorded capital is "
        "not subtracted from the household capital that an unrecorded unit's "
        "proxy shares out: the recorded figure and the household sources come "
        "from different measures, so the proxy is left as it was."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        p = parameters(period).gov.dwp.pension_credit.income.capital
        household_capital = valued_capital(
            lambda variable: household(variable, period), p.sources, p.sale_expenses
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in p.person_sources
        )
        any_pension_age = benunit.any(person("is_SP_age", period))
        benunit_pension_age_adults = benunit.sum(person("is_SP_age", period))
        household_pension_age_adults = benunit.max(
            person.household.sum(person.household.members("is_SP_age", period))
        )
        adult_divisor = max_(1, household_pension_age_adults)
        household_capital_proxy = (
            household_capital * benunit_pension_age_adults / adult_divisor
        )
        reported_capital = benunit("pension_credit_reported_capital", period)
        assessed_capital = where(
            reported_capital >= 0,
            reported_capital,
            household_capital_proxy + person_capital,
        )
        return where(any_pension_age, max_(0, assessed_capital), 0)
