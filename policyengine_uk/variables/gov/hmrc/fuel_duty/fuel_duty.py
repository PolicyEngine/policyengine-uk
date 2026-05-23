from policyengine_uk.model_api import *


class fuel_duty(Variable):
    label = "Fuel duty (cars only)"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        fd = parameters(period).gov.hmrc.fuel_duty
        petrol_litres = household("petrol_litres", period.this_year) / MONTHS_IN_YEAR
        diesel_litres = household("diesel_litres", period.this_year) / MONTHS_IN_YEAR
        in_relief_area = household("in_rural_fuel_duty_relief_area", period.this_year)
        effective_rate = (
            fd.petrol_and_diesel - in_relief_area * fd.rural_fuel_duty_relief
        )
        return effective_rate * (petrol_litres + diesel_litres)
