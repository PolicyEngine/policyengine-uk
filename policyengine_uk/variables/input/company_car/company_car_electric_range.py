from policyengine_uk.model_api import *


class company_car_electric_range(Variable):
    value_type = float
    entity = Person
    label = "Electric range figure of the person's company car"
    documentation = (
        "The distance in miles the person's company car can be driven in "
        "electric mode without recharging, as on its certificate of "
        "conformity (ITEPA 2003 s. 139(5)). Only cars with a CO2 emissions "
        "figure of 1 to 50 g/km use it, and only to 2027-28."
    )
    definition_period = YEAR
    unit = "mile"
    quantity_type = STOCK
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 s. 139",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/139",
    )
