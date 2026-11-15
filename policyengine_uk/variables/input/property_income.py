from policyengine_uk.model_api import *


class property_income(Variable):
    value_type = float
    entity = Person
    label = "property income"
    documentation = (
        "Profits of the person's UK and overseas property businesses: rents "
        "and other receipts less allowable expenses, before the property "
        "allowance and before any costs of dwelling-related loans (such as "
        "mortgage interest on let homes), which have not been deductible "
        "since 2020-21 and are relieved as a tax reduction instead "
        "(property_finance_costs). This is the profit concept of the SPI's "
        "net property income. Gross receipts are property_rental_income."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 268",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/268",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 272A",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/272A",
        ),
    ]
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
