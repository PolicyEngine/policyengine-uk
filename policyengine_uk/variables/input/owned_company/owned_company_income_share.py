from policyengine_uk.model_api import *


class owned_company_income_share(Variable):
    value_type = float
    entity = Person
    label = "share of owned company income"
    documentation = (
        "The income of the company in which the person stands as sole owner "
        "or partner, or the person's share of that income, calculated as "
        "self-employed earnings would be: the company's actual receipts less "
        "its permitted expenses, on a cash basis. Pay the company gives the "
        "person as a director or employee is a company expense here and is "
        "recorded in employment_income instead. Corporation tax is not "
        "deducted: the self-employed earnings calculation deducts only "
        "income tax and National Insurance the person pays, and neither the "
        "regulations nor DWP guidance provide for corporation tax. Dividends "
        "the person receives from the company are paid out of this income, "
        "so they are not added to it."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.mixed_income"
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(3)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="The Universal Credit Regulations 2013 reg. 57",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
    ]
