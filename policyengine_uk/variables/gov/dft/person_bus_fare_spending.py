from policyengine_uk.model_api import *


class person_bus_fare_spending(Variable):
    label = "person bus and coach fare spending"
    documentation = (
        "Household bus_fare_spending apportioned to this person using an "
        "age-based bus usage profile (NTS-derived, concessionary-adjusted). "
        "This is a modelling allocation, not a direct measurement: LCFS "
        "records bus fares only at household level. Lets age-targeted fare "
        "reforms (e.g. free travel for under-22s) act on the relevant members."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        age = person("age", period)
        weight = parameters(period).gov.dft.bus.fare_allocation_weight_by_age.calc(age)
        total_weight = person.household("household_bus_fare_weight", period)
        household_fare = person.household("bus_fare_spending", period)
        share = where(total_weight > 0, weight / total_weight, 0)
        return household_fare * share
