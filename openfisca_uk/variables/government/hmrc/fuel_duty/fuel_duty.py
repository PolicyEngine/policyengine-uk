from openfisca_uk.model_api import *


class fuel_duty(Variable):
    label = "Fuel duty"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        fd = parameters(period).hmrc.fuel_duty
        petrol_litres = household("petrol_litres", period)
        diesel_litres = household("diesel_litres", period)
        return fd.petrol_and_diesel * (petrol_litres + diesel_litres)
