from policyengine_uk.model_api import *


class legacy_means_test_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax deducted in the legacy means tests"
    documentation = (
        "Income Tax less the tax on savings interest, dividends and property "
        "income, floored at zero. The legacy means tests disregard tax only on "
        "income they take into account, and they treat income derived from "
        "capital as capital, not income, so tax on it is not deducted. Tax "
        "reductions are set against the remaining tax first."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
    ]

    def formula(person, period, parameters):
        tax_on_income_from_capital = add(
            person,
            period,
            ["savings_income_tax", "dividend_income_tax", "property_income_tax"],
        )
        return max_(0, person("income_tax", period) - tax_on_income_from_capital)
