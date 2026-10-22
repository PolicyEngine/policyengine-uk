from policyengine_uk.model_api import *


class esa_income_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for income-related ESA"
    documentation = (
        "Household capital apportioned to the benefit unit for the income-related "
        "ESA capital test. Because the dataset only stores these stocks at "
        "household level, the model allocates full household capital to any "
        "benunit with a reported income-related ESA award and only falls back to "
        "a claimant-and-partner share when nobody in the household is on that "
        "reported claim path. This allocation is a PolicyEngine convention; "
        "the data cannot identify ownership of capital. "
        "Person-level sources, such as a Lifetime ISA, count only for the "
        "holder's own benunit, and only when the holder is its claimant or "
        "partner (is_claimant_or_partner): a dependant's capital is not the "
        "claimant's."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2008/794/regulation/83"

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        sources = ESA.capital.sources
        person = benunit.members
        claiming_esa_income = add(benunit, period, ["esa_income_reported"]) > 0

        household_capital = sum(
            benunit.max(person.household(source, period)) for source in sources
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
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in ESA.capital.person_sources
        )
        household_share = where(
            household_reporting_claimants > 0, claiming_proxy, fallback_proxy
        )
        return household_share + person_capital
