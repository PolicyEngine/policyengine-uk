from policyengine_uk.model_api import *


class tax_free_childcare_expected_declaration_period_income(Variable):
    value_type = float
    entity = Person
    label = "expected income in the Tax-Free Childcare declaration period"
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/9",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/10",
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare.income
        annual_countable_income = add(person, period, p.countable_sources)
        return annual_countable_income * p.declaration_period_weeks / WEEKS_IN_YEAR
