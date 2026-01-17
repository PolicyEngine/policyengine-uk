from policyengine_uk.model_api import *


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable income for Tax Credits"
    definition_period = YEAR
    unit = GBP
    reference = "The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3"

    def formula(benunit, period, parameters):
        TC = parameters(period).gov.dwp.tax_credits
        STEP_1_COMPONENTS = [
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "property_income",
        ]
        income = add(benunit, period, STEP_1_COMPONENTS)
        income = max_(income - TC.means_test.non_earned_disregard, 0)
        # Default behavior: Basic income not included in means tests.
        # Use basic_income_interactions reform to change this.
        STEP_2_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "social_security_income",
            "miscellaneous_income",
        ]
        income += add(benunit, period, STEP_2_COMPONENTS)
        EXEMPT_BENEFITS = ["income_support", "esa_income", "jsa_income"]
        on_exempt_benefits = add(benunit, period, EXEMPT_BENEFITS) > 0
        return income * ~on_exempt_benefits
