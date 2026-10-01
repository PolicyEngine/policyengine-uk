from policyengine_uk.model_api import *


class housing_benefit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit assessable capital"
    documentation = (
        "Housing Benefit capital counted from the configured capital sources. "
        "Household sources are allocated across benunits using a household "
        "adult-share proxy; person-level sources, such as a Lifetime ISA, "
        "count only for the holder's own benunit, and only when the holder is "
        "its claimant or partner (is_uc_claimant): a dependant's capital is "
        "not the claimant's. It is nil for a family in receipt of Income "
        "Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance, and for a pension-age family in "
        "receipt of the Pension Credit guarantee credit."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7/paragraph/5",
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
        claimant_or_partner = person("is_uc_claimant", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in p.person_sources
        )
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
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        # SI 2006/213 Sch 6 para 5 (NI: SR 2006/405 Sch 7 para 5) disregards
        # "the whole of his capital" where a claimant is on income support, an
        # income-based jobseeker's allowance or an income-related employment
        # and support allowance (para 6: a joint-claim partner on income-based
        # JSA). With no capital the tariff income is nil and the capital limit
        # is met. See housing_benefit_applicable_income for the age and
        # universal credit points.
        on_income_related_benefit = benunit(
            "in_receipt_of_income_support_jsa_ib_or_esa_ir", period
        )
        return where(
            guarantee_credit | on_income_related_benefit,
            0,
            max_(0, household_capital_proxy + person_capital),
        )
