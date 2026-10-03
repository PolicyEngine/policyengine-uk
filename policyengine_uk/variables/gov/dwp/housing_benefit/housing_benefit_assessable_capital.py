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
        any_over_SP_age = benunit.any(person("is_SP_age", period))
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
        # Guarantee Credit passport: SI 2006/214 reg 26 (NI: SR 2006/406
        # reg 24) disregards the whole of the capital and income of a
        # claimant "in receipt, or whose partner is in receipt, of a
        # guarantee credit". By reg 2(5) (NI: reg 2(5)), that includes a
        # person who would be in receipt but for SPC Regs 2002 reg 13 (NI:
        # SPC Regs (NI) 2003 reg 13), the small-amounts rule, which
        # PolicyEngine does not model.
        passported = any_over_SP_age & benunit("in_receipt_of_guarantee_credit", period)
        return where(
            passported,
            0,
            max_(0, household_capital_proxy + person_capital),
        )
