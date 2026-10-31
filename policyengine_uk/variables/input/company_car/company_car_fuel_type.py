from policyengine_uk.model_api import *
from policyengine_uk.variables.input.vehicle.car_fuel_type import CarFuelType


class company_car_fuel_type(Variable):
    value_type = Enum
    possible_values = CarFuelType
    default_value = CarFuelType.PETROL
    entity = Person
    label = "Fuel type of the person's company car"
    documentation = (
        "A car propelled solely by diesel that does not meet the Euro 6d "
        "(RDE2) emissions standard takes the diesel supplement (ITEPA 2003 "
        "s. 141). A diesel hybrid is not propelled solely by diesel."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 s. 141",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/141",
    )
