from policyengine_uk.model_api import *


class property_finance_costs(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs"
    documentation = (
        "The person's share of the year's costs of dwelling-related loans of "
        "their property businesses: interest (and returns economically "
        "equivalent to interest) on money borrowed for letting homes, such "
        "as buy-to-let mortgages, and the incidental costs of obtaining that "
        "finance. ITTOIA 2005 s. 272A stops them being deducted from property "
        "profits (in full from 2020-21) and ss. 274A-274AA give a tax "
        "reduction instead. property_income is measured before these costs."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 272A",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/272A",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 272B",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/272B",
        ),
    ]
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.mortgage_interest"
