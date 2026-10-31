from policyengine_uk.model_api import *


class company_car_list_price(Variable):
    value_type = float
    entity = Person
    label = "List price of the person's company car, with its accessories"
    documentation = (
        "The list price of a car made available to the person by reason of "
        "their employment and for their private use, on the day before its "
        "first registration, plus the price of its qualifying accessories "
        "(ITEPA 2003 s. 121(1) steps 1 and 2). Zero means the person has no "
        "company car. Set company_car_co2_emissions with it: a CO2 figure of "
        "0 means a car that cannot emit CO2. The benefits it gives must not "
        "also be in employment_income, or they are taxed twice; a dataset "
        "whose pay includes benefits in kind, as the SPI's EPB does, must take "
        "the car and car fuel benefits out of it. This is not car_list_price, "
        "which describes the person's own car for vehicle excise duty."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
    quantity_type = STOCK
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 121",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/121",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 123",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/123",
        ),
    ]
