from policyengine_uk.model_api import *


class housing_benefit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit assessable capital"
    documentation = (
        "Housing Benefit capital counted from the configured capital sources. "
        "Household sources are allocated across benunits in proportion to their "
        "claimants and partners, a PolicyEngine convention because household "
        "capital data cannot identify ownership; children and young persons add "
        "no weight. Person-level sources, such as a Lifetime ISA, count only for "
        "the holder's own benunit, and only when the holder is its claimant or "
        "partner (is_claimant_or_partner): a dependant's capital is not the "
        "claimant's."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/25"

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        household_capital = sum(household(source, period) for source in p.sources)
        claimant_or_partner = person("is_claimant_or_partner", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in p.person_sources
        )
        benunit_claimants_and_partners = add(
            benunit, period, ["is_claimant_or_partner"]
        )
        household_claimants_and_partners = benunit.max(
            person.household.sum(person("is_claimant_or_partner", period))
        )
        claimant_partner_divisor = max_(1, household_claimants_and_partners)
        household_capital_proxy = where(
            household_claimants_and_partners > 0,
            household_capital
            * benunit_claimants_and_partners
            / claimant_partner_divisor,
            0,
        )
        # Pension HB reg 26 disregards "the whole of his capital and income"
        # for guarantee-credit recipients within that regulation set.
        guarantee_credit = pension_age_regulations & (
            benunit("guarantee_credit", period) > 0
        )
        return where(
            guarantee_credit,
            0,
            max_(0, household_capital_proxy + person_capital),
        )
