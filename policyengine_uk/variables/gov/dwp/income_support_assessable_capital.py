from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    counted_person_sources,
    pooled_person_capital,
)


class income_support_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for Income Support"
    documentation = (
        "Household capital apportioned to the benefit unit for the Income Support "
        "capital test. Because the dataset only stores these stocks at household "
        "level, the model allocates full household capital to any benunit on the "
        "IS claim path and only falls back to a claimant-and-partner share when "
        "nobody in the household is on that path. This allocation is a "
        "PolicyEngine convention; the data cannot identify ownership of capital. "
        "Person-level sources, such as a Lifetime ISA, count only for the "
        "holder's own benunit, and only when the holder is its claimant or "
        "partner (is_claimant_or_partner): a dependant's capital is not the "
        "claimant's. A cash or stocks and shares ISA balance tied to a person "
        "counts the same way, and leaves the household capital the proxy shares "
        "out."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/1987/1967/regulation/23"

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        capital = IS.means_test.capital
        person = benunit.members
        would_claim_is = benunit("would_claim_IS", period)

        # The data model stores these capital stocks at household level. For the
        # live Income Support path, avoid diluting capital across separate claims:
        # any benunit on the IS claim path gets the full observed household total.
        # If nobody in the household is on that path, use claimant/partner
        # weights. Regulation 23 excludes children's and young persons' capital;
        # the household allocation itself is a modelling convention.
        household_capital = sum(
            benunit.max(person.household(source, period))
            - pooled_person_capital(benunit, source, period, capital)
            for source in capital.sources
        )
        benunit_claimants_and_partners = add(
            benunit, period, ["is_claimant_or_partner"]
        )
        household_claiming_members = benunit.max(
            person.household.sum(
                person("is_claimant_or_partner", period)
                & person.benunit("would_claim_IS", period)
            )
        )
        household_claimants_and_partners = benunit.max(
            person.household.sum(person("is_claimant_or_partner", period))
        )
        fallback_divisor = max_(1, household_claimants_and_partners)
        claiming_proxy = where(would_claim_is, household_capital, 0)
        fallback_proxy = (
            household_capital * benunit_claimants_and_partners / fallback_divisor
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in counted_person_sources(capital)
        )
        household_share = where(
            household_claiming_members > 0, claiming_proxy, fallback_proxy
        )
        return household_share + person_capital
