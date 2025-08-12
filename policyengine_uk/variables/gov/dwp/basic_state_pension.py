from policyengine_uk.model_api import *


class basic_state_pension(Variable):
    label = "basic State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if simulation.dataset is None:
            return 0

        data_year = 2023
        reported = person("state_pension_reported", data_year) / WEEKS_IN_YEAR
        type = person("state_pension_type", period)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount
        amount_in_data_year = where(
            type == type.possible_values.BASIC,
            min_(reported, maximum_basic_sp),
            0,
        )
        triple_lock = parameters.gov.economic_assumptions.indices.triple_lock
        uprating_since_data_year = triple_lock(period) / triple_lock(data_year)
        return amount_in_data_year * uprating_since_data_year * WEEKS_IN_YEAR
