from policyengine_uk.model_api import *


class council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "relevant income for Council Tax Reduction means test"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        benunit_means_tested_benefits = [
            "child_benefit",
            "income_support",
            "jsa_income",
            "esa_income",
            "universal_credit",
        ]
        personal_benefits = [
            "carers_allowance",
            "esa_contrib",
            "jsa_contrib",
            "state_pension",
            "maternity_allowance",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "ssmg",
        ]
        income_components = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        benefits = add(benunit, period, benunit_means_tested_benefits)
        income = add(benunit, period, income_components)
        personal_benefit_income = add(benunit, period, personal_benefits)
        credits = add(benunit, period, ["tax_credits"])
        increased_income = income + personal_benefit_income + credits + benefits

        if not bi.interactions.include_in_means_tests:
            increased_income -= add(benunit, period, ["basic_income"])

        pension_contributions = add(benunit, period, ["pension_contributions"]) * 0.5
        tax = add(benunit, period, ["income_tax", "national_insurance"])
        return max_(0, increased_income - tax - pension_contributions)
