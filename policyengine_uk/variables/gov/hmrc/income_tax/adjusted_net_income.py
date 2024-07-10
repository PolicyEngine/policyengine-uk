from policyengine_uk.model_api import *


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"
    unit = GBP

    def formula(person, period, parameters):
        COMPONENTS = [
            "taxable_employment_income",
            "taxable_pension_income",
            "taxable_social_security_income",
            "taxable_self_employment_income",
            "taxable_property_income",
            "taxable_savings_interest_income",
            "taxable_dividend_income",
            "taxable_miscellaneous_income",
        ]
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
            COMPONENTS.append("basic_income")
        return max_(0, add(person, period, COMPONENTS))
