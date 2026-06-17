from policyengine_uk.model_api import *


class household_bus_fare_weight(Variable):
    label = "household bus fare allocation weight"
    documentation = (
        "Sum across household members of the age-based bus fare allocation "
        "weight, used as the denominator when apportioning household "
        "bus_fare_spending to people."
    )
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        age = household.members("age", period)
        weight = parameters(period).gov.dft.bus.fare_allocation_weight_by_age.calc(age)
        return household.sum(weight)
