from policyengine_uk.model_api import *


class self_employment_gross_receipts(Variable):
    value_type = float
    entity = Person
    label = "self-employment gross receipts"
    documentation = (
        "Gross receipts (turnover) of the person's trades before expenses. "
        "Optional: used only to apply the trading allowance, which is measured "
        "against gross receipts and replaces actual expenses. Leave at zero "
        "when unknown; self_employment_income remains the profit used "
        "everywhere else."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 783AC",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AC",
    )
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.mixed_income"
