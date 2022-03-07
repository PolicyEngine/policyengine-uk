from openfisca_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Housing Benefit means test"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        means_test = parameters(period).dwp.housing_benefit.means_test
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "JSA_income",
            "ESA_income",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "pension_income",
        ]
        bi = parameters(period).contrib.ubi_center.basic_income
        if bi.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(benunit, period, TAX_COMPONENTS)
        income += aggr(benunit, period, ["personal_benefits"])
        income += add(benunit, period, ["tax_credits"])
        income -= tax
        income -= aggr(benunit, period, ["pension_contributions"]) * 0.5
        income += benefits
        num_children = benunit.nb_persons(BenUnit.CHILD)
        childcare_amount_1 = (num_children == 1) * WTC.elements.childcare_1
        childcare_amount_2 = (num_children > 1) * WTC.elements.childcare_2
        max_weekly_childcare_amount = childcare_amount_1 + childcare_amount_2
        max_childcare_amount = max_weekly_childcare_amount * WEEKS_IN_YEAR
        childcare_element = min_(
            max_childcare_amount,
            aggr(benunit, period, ["childcare_expenses"]),
        )
        disregard = benunit("hb_income_disregards", period)
        return max_(0, income - disregard - childcare_element)
