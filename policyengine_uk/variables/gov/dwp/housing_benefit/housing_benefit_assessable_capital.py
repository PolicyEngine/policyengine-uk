from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import valued_capital


class housing_benefit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit assessable capital"
    documentation = (
        "Housing Benefit capital counted from the configured capital sources, "
        "each valued at market value less 10% where a sale would incur "
        "expenses and less any debt secured on it (reg. 47 of SI 2006/213, "
        "reg. 45 of SI 2006/214). "
        "Household sources are allocated across benunits in proportion to their "
        "claimants and partners, a PolicyEngine convention because household "
        "capital data cannot identify ownership; children and young persons add "
        "no weight. Person-level sources, such as a Lifetime ISA, count only for "
        "the holder's own benunit, and only when the holder is its claimant or "
        "partner (is_claimant_or_partner): a dependant's capital is not the "
        "claimant's. Where the Pension Credit award is savings credit only, the "
        "Pension Credit assessment of capital is used instead. It is nil for a "
        "family on Universal Credit, Income Support, income-based Jobseeker's "
        "Allowance or income-related Employment and Support Allowance "
        "(housing_benefit_on_passporting_benefit), and for a pension-age "
        "family with a positive guarantee credit (the guarantee credit "
        "passport)."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/25",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7/paragraph/5",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
    )

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        household_capital = valued_capital(
            lambda variable: household(variable, period), p.sources, p.sale_expenses
        )
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
        # SI 2006/214 reg 27(6) (NI: SR 2006/406 reg 25(6)): where the award of
        # Pension Credit is savings credit only, the Secretary of State's
        # calculation of capital is used, and the £16,000 limit applies to it.
        # The recalculation when capital rises above £16,000 during an
        # assessed income period (reg 27(7) and (8)) is not modelled. That
        # regulation is in the pension-age regulations, so it applies only
        # where they do.
        savings_credit_only = pension_age_regulations & benunit(
            "in_receipt_of_savings_credit_only", period
        )
        capital = where(
            savings_credit_only,
            benunit("pension_credit_assessable_capital", period),
            household_capital_proxy + person_capital,
        )
        # Pension HB reg 26 disregards "the whole of his capital and income"
        # for guarantee-credit recipients within that regulation set.
        guarantee_credit = pension_age_regulations & (
            benunit("guarantee_credit", period) > 0
        )
        # SI 2006/213 Sch 6 para 5 (NI: SR 2006/405 Sch 7 para 5) disregards
        # "the whole of his capital" where a claimant is on universal credit,
        # income support, an income-based jobseeker's allowance or an
        # income-related employment and support allowance (para 6: a
        # joint-claim partner on income-based JSA). With no capital the tariff
        # income is nil and the capital limit is met. See
        # housing_benefit_applicable_income for the age and benefit cap points.
        on_passporting_benefit = benunit(
            "housing_benefit_on_passporting_benefit", period
        )
        return where(
            guarantee_credit | on_passporting_benefit,
            0,
            max_(0, capital),
        )
