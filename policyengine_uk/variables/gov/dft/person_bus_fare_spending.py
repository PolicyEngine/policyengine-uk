from policyengine_uk.model_api import *


class person_bus_fare_spending(Variable):
    label = "personal bus and coach fare spending"
    documentation = (
        "Share of the household's bus and coach fare spending attributed to "
        "this person. The LCFS records fares at household level only, so the "
        "split uses a National Travel Survey age profile of local bus use, "
        "adjusted for concessionary travel. Members' values sum to the "
        "household's bus_fare_spending."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        weight = parameters(period).gov.dft.bus.fare_allocation_weight_by_age.calc(
            person("age", period)
        )
        household_weight = person.household("household_bus_fare_age_weight", period)
        share = where(household_weight > 0, weight / household_weight, 0)
        return person.household("bus_fare_spending", period) * share


class household_bus_fare_age_weight(Variable):
    label = "household bus fare age weight"
    documentation = (
        "Sum of members' bus fare allocation weights, the denominator that "
        "makes person_bus_fare_spending sum to household bus_fare_spending."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        weight = parameters(period).gov.dft.bus.fare_allocation_weight_by_age.calc(
            household.members("age", period)
        )
        return household.sum(weight)
