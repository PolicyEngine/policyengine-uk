from policyengine_uk.model_api import *


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Housing Benefit means test"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
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
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        TAX_COMPONENTS = ["income_tax", "national_insurance"]
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = add(benunit, period, INCOME_COMPONENTS)
        tax = add(benunit, period, TAX_COMPONENTS)
        income += add(benunit, period, ["personal_benefits"])
        if not bi.interactions.include_in_means_tests:
            # Basic income is already in personal benefits, deduct if needed
            income -= add(benunit, period, ["basic_income"])
        income += add(benunit, period, ["tax_credits"])
        income -= tax
        income -= add(benunit, period, ["pension_contributions"]) * 0.5
        income += benefits
        disregard = benunit(
            "housing_benefit_applicable_income_disregard", period
        )
        childcare_element = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        return max_(0, income - disregard - childcare_element)
