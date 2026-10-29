from policyengine_uk.model_api import *


class company_car_co2_emissions(Variable):
    value_type = float
    entity = Person
    label = "CO2 emissions figure of the person's company car"
    documentation = (
        "The CO2 emissions figure of the person's company car in grams per "
        "kilometre, as on its certificate of conformity: 0 for a car that "
        "cannot emit CO2 by being driven. For a car first registered on or "
        "after 6 April 2020 it is the WLTP figure (ITEPA 2003 s. 136(2B)). "
        "The model treats every company car as having a CO2 emissions "
        "figure; cars without one (s. 140) and cars first registered before "
        "1 January 1998 (s. 142) are not modelled."
    )
    definition_period = YEAR
    unit = "g/km"
    quantity_type = STOCK
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 136",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/136",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 139",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/139",
        ),
    ]
