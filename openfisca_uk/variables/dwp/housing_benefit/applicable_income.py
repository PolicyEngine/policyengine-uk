from openfisca_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Housing Benefit means test"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        means_test = parameters(period).benefit.housing_benefit.means_test
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
        hours = aggr(benunit, period, ["weekly_hours"])
        # Calculate single, couple, lone parent, and worker disregards.
        single = benunit("is_single_person", period)
        single_disregard = single * means_test.income_disregard_single
        couple = benunit("is_couple", period)
        couple_disregard = couple * means_test.income_disregard_couple
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_disregard = (
            lone_parent * means_test.income_disregard_lone_parent
        )
        hour_requirement = where(
            lone_parent, WTC.min_hours.lower, means_test.worker_hours
        )
        worker = hours > hour_requirement
        worker_disregard = worker * means_test.worker_income_disregard
        weekly_disregard = (
            single_disregard
            + couple_disregard
            + lone_parent_disregard
            + worker_disregard
        )
        disregard = weekly_disregard * WEEKS_IN_YEAR
        return max_(0, income - disregard - childcare_element)
