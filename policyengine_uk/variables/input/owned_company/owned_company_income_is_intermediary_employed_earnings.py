from policyengine_uk.model_api import *


class owned_company_income_is_intermediary_employed_earnings(Variable):
    value_type = bool
    entity = Person
    label = "owned company income is intermediary employed earnings"
    documentation = (
        "Whether the person derives income from the company that is employed "
        "earnings under Chapter 8 (workers under arrangements made by "
        "intermediaries), Chapter 9 (managed service companies) or Chapter 10 "
        "(workers' services provided through intermediaries) of Part 2 of the "
        "Income Tax (Earnings and Pensions) Act 2003, derived from activities "
        "that are the person's main employment (Chapter 10 from 28 November "
        "2018; before then only Chapters 8 and 9 excluded the person). Where "
        "this holds, Universal "
        "Credit does not treat the person as the company's sole owner or "
        "partner, and that income counts as employed earnings instead."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 Part 2 Chapters 8-10",
            href="https://www.legislation.gov.uk/ukpga/2003/1/part/2",
        ),
    ]
