from policyengine_uk.model_api import *


class company_car_availability(Variable):
    value_type = float
    entity = Person
    label = "Share of the tax year the person's company car is available"
    documentation = (
        "The share of the tax year's days on which the company car is "
        "available to the person: 1 less the share of days on which it is "
        "unavailable, which are days before it is first available, after it "
        "is last available, and within a period of 30 days or more when it "
        "is not available (ITEPA 2003 s. 143(2)). The company car and car "
        "fuel benefits are reduced in proportion (ss. 143(3) and 152(1))."
    )
    definition_period = YEAR
    unit = "/1"
    default_value = 1
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 143",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/143",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 152",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/152",
        ),
    ]
