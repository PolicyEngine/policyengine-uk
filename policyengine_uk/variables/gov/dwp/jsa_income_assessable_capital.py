from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    counted_person_sources,
    pooled_person_capital,
)


class jsa_income_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for income-based JSA"
    documentation = (
        "Household capital apportioned to the benefit unit for the income-based JSA "
        "capital test. For capital whose owner the data do not identify, the model "
        "allocates the full household remainder to any benunit with a reported "
        "income-based JSA award and falls back to a claimant-and-partner share when "
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
    reference = "https://www.legislation.gov.uk/uksi/1996/207/regulation/88"

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA.income
        person = benunit.members
        claiming_jsa_income = add(benunit, period, ["jsa_income_reported"]) > 0

        household_capital = sum(
            benunit.max(person.household(source, period))
            - pooled_person_capital(benunit, source, period, JSA.capital)
            for source in JSA.capital.sources
        )
        # Regulation 88(2) excludes children's and young persons' capital.
        # The claimant/partner weights approximate otherwise unobserved ownership.
        benunit_claimants_and_partners = add(
            benunit, period, ["is_claimant_or_partner"]
        )
        household_reporting_claimants = benunit.max(
            person.household.sum(person("jsa_income_reported", period) > 0)
        )
        household_claimants_and_partners = benunit.max(
            person.household.sum(person("is_claimant_or_partner", period))
        )
        fallback_divisor = max_(1, household_claimants_and_partners)
        claiming_proxy = where(claiming_jsa_income, household_capital, 0)
        fallback_proxy = (
            household_capital * benunit_claimants_and_partners / fallback_divisor
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in counted_person_sources(JSA.capital)
        )
        household_share = where(
            household_reporting_claimants > 0, claiming_proxy, fallback_proxy
        )
        return household_share + person_capital
