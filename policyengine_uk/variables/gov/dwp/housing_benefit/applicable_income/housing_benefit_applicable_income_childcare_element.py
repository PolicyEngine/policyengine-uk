from policyengine_uk.model_api import *


class housing_benefit_applicable_income_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit deductible childcare charges"
    documentation = "Qualifying per-child childcare, subject to the work condition, own statutory caps and the remaining-earnings plus actual-tax-credit restriction. It cannot reduce pensions, capital tariff or other unearned income. The pre-additional earnings disregard prevents a dependency cycle while preserving the additional-disregard coverage test."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/30",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/24",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.childcare.weekly_maximum
        count = benunit("num_relevant_children_for_housing_benefit_childcare", period)
        cap = (
            where(count == 1, p.one_child, where(count > 1, p.two_or_more_children, 0))
            * WEEKS_IN_YEAR
        )
        charges = benunit.sum(
            benunit.members("housing_benefit_qualifying_childcare_costs", period)
        )
        qualifying = min_(max_(charges, 0), cap)
        earnings = benunit("housing_benefit_net_earnings", period)
        base = benunit("housing_benefit_pre_additional_earnings_disregard", period)
        available_tax_credits = max_(
            add(benunit, period, ["working_tax_credit", "child_tax_credit"]), 0
        )
        deductible = min_(qualifying, max_(earnings - base, 0) + available_tax_credits)
        return where(
            benunit("housing_benefit_childcare_work_condition", period), deductible, 0
        )
