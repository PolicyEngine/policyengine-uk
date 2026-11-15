from policyengine_uk.model_api import *


class company_car_private_fuel_provided(Variable):
    value_type = bool
    entity = Person
    label = "Fuel provided for private use of the person's company car"
    documentation = (
        "Whether fuel is provided for the company car by reason of the "
        "person's employment and its cost for private use is not made good "
        "in full (ITEPA 2003 ss. 149 and 151). Electricity is not fuel "
        "(s. 149(4)). Part-year provision of fuel (s. 152(2)) is not "
        "modelled; the car fuel benefit is reduced only for days the car is "
        "unavailable."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 149",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/149",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 151",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/151",
        ),
    ]
