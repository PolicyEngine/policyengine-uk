from policyengine_uk.model_api import *


STATUTORY_CONSUMER_INCIDENCE = 0.5
ECONOMIC_CONSUMER_INCIDENCE = 1


class fuel_duty(Variable):
    label = "Fuel duty (cars only)"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        fd = parameters(period).gov.hmrc.fuel_duty
        petrol_litres = (
            household("petrol_litres", period.this_year) / MONTHS_IN_YEAR
        )
        diesel_litres = (
            household("diesel_litres", period.this_year) / MONTHS_IN_YEAR
        )
        return (
            fd.petrol_and_diesel
            * (petrol_litres + diesel_litres)
            / STATUTORY_CONSUMER_INCIDENCE
            * ECONOMIC_CONSUMER_INCIDENCE
        )
