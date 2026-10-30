from policyengine_uk.model_api import *


class company_car_private_use_payments(Variable):
    value_type = float
    entity = Person
    label = "Payments for private use of the person's company car"
    documentation = (
        "Amounts the person is required to pay, and pays by 6 July after the "
        "tax year, as a condition of the company car being available for "
        "private use (ITEPA 2003 s. 144). Payments for fuel or insurance are "
        "not payments for private use."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    quantity_type = FLOW
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 s. 144",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/144",
    )
