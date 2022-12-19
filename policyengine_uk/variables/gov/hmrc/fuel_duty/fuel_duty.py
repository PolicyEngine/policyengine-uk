from policyengine_uk.model_api import *


class fuel_duty(Variable):
    label = "Fuel duty (cars only)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        fd = parameters(period).gov.hmrc.fuel_duty
        petrol_litres = household("petrol_litres", period)
        diesel_litres = household("diesel_litres", period)
        return fd.petrol_and_diesel * (petrol_litres + diesel_litres)


class baseline_fuel_duty(Variable):
    label = "Baseline fuel duty (cars only)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class change_in_fuel_duty(Variable):
    label = "fuel duty"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(fuel_duty)
