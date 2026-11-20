from policyengine_uk.model_api import *


class property_allowable_expenses(Variable):
    value_type = float
    entity = Person
    label = "property allowable expenses"
    documentation = (
        "Expenses already deducted in arriving at property_income, implied by "
        "gross receipts: property_rental_income less property_income. They do "
        "not include the costs of dwelling-related loans "
        "(property_finance_costs), which property_income is measured before. "
        "Zero when receipts are unknown, that is zero or below "
        "property_income."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 272",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/272",
    )

    def formula(person, period, parameters):
        profit = person("property_income", period)
        receipts = person("property_rental_income", period)
        receipts_known = (receipts > 0) & (receipts >= profit)
        return where(receipts_known, receipts - profit, 0)
