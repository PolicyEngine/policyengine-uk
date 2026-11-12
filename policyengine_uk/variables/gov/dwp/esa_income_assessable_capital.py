from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import (
    round_to_penny,
    valued_capital,
    valued_person_capital,
)
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    pooled_person_capital,
)


class esa_income_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for income-related ESA"
    documentation = (
        "Household capital apportioned to the benefit unit for the income-related ESA "
        "capital test. "
        "The formula values each household source, less the ISA balances it "
        "counts in their holders' own benunits, at market value less 10% where a sale would incur "
        "expenses and less any debt secured on it (reg. 113), and values each "
        "such ISA balance as it values that household source. "
        "For capital whose owner the data do not identify, the model "
        "allocates the full household remainder to any benunit with a reported "
        "income-related ESA award and falls back to a claimant-and-partner share when "
        "nobody in the household reports such an award. No regulation sets that "
        "allocation; it approximates ownership the data don't record. The formula "
        "counts person-level sources, such as a Lifetime ISA and the cash and stocks "
        "and shares ISAs, only in the holder's own benunit and only for its claimant "
        "or partner (is_claimant_or_partner), and excludes dependants' capital. It "
        "subtracts the ISA balances from the household capital before allocating the "
        "remainder."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2008/794/regulation/83"

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        person = benunit.members
        claiming_esa_income = add(benunit, period, ["esa_income_reported"]) > 0

        household_capital = valued_capital(
            lambda source: (
                benunit.max(person.household(source, period))
                - pooled_person_capital(benunit, source, period, ESA.capital)
            ),
            ESA.capital,
        )
        # Regulation 83(2) excludes children's and young persons' capital.
        # The claimant/partner weights approximate otherwise unobserved ownership.
        benunit_claimants_and_partners = add(
            benunit, period, ["is_claimant_or_partner"]
        )
        household_reporting_claimants = benunit.max(
            person.household.sum(person("esa_income_reported", period) > 0)
        )
        household_claimants_and_partners = benunit.max(
            person.household.sum(person("is_claimant_or_partner", period))
        )
        fallback_divisor = max_(1, household_claimants_and_partners)
        claiming_proxy = where(claiming_esa_income, household_capital, 0)
        fallback_proxy = (
            household_capital * benunit_claimants_and_partners / fallback_divisor
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = valued_person_capital(
            benunit, period, parameters, ESA.capital, claimant_or_partner
        )
        household_share = where(
            household_reporting_claimants > 0, claiming_proxy, fallback_proxy
        )
        # A fraction of a penny is disregarded at the last stage (reg. 3(a)).
        return round_to_penny(household_share + person_capital, ESA.capital.round_down)
