from policyengine_uk.model_api import *


class property_rental_income(Variable):
    value_type = float
    entity = Person
    label = "gross property rental receipts"
    documentation = (
        "Gross rents and other receipts of the person's UK and overseas "
        "property businesses, before any expenses. Rent-a-room receipts are "
        "not included. Optional: used only to apply the property allowance, "
        "which is measured against gross receipts and replaces actual "
        "expenses. It does not replace property_income, the profit that is "
        "taxed: set both. Must be at least property_income; leave at zero "
        "when unknown, and receipts below property_income are treated as "
        "unknown."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BB",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BB",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BC",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BC",
        ),
    ]
    quantity_type = FLOW
    # The same index as property_income, so that uprated receipts never fall
    # below uprated profit and the implied expenses keep their share.
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
