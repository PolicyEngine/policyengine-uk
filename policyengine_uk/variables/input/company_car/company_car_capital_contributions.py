from policyengine_uk.model_api import *


class company_car_capital_contributions(Variable):
    value_type = float
    entity = Person
    label = "Capital contributions to the person's company car"
    documentation = (
        "Capital sums the person has contributed, in this and earlier tax "
        "years, to the cost of their company car and its accessories. The "
        "company car benefit deducts them up to the cap "
        "(ITEPA 2003 s. 132(3))."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    quantity_type = STOCK
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 s. 132",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/132",
    )
