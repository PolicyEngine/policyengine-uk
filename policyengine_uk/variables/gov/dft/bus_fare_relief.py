from policyengine_uk.model_api import *


class bus_fare_relief(Variable):
    label = "young-person bus fare relief"
    documentation = (
        "Value of bus & coach fares met by government for eligible young "
        "people under the young-person fare policy (gov.dft.bus.young_person_fare). "
        "Treated as a transport subsidy: it counts as an in-kind household "
        "benefit and as government spending. Zero under baseline, where the "
        "age limit defaults to 0 (no one eligible)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        policy = parameters(period).gov.dft.bus.young_person_fare
        age = household.members("age", period)
        person_fare = household.members("person_bus_fare_spending", period)
        eligible = age < policy.age_limit
        relief = eligible * person_fare * (1 - policy.rate)
        return household.sum(relief)
