from policyengine_uk.model_api import *


class additional_state_pension(Variable):
    label = "additional State Pension"
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
        type = person("state_pension_type", data_year)
        maximum_basic_sp = parameters(
            data_year
        ).gov.dwp.state_pension.basic_state_pension.amount
        amount_in_data_year = where(
            type == type.possible_values.BASIC,
            max_(reported - maximum_basic_sp, 0),
            0,
        )
        return amount_in_data_year * WEEKS_IN_YEAR
