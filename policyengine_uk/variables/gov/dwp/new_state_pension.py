from policyengine_uk.model_api import *


class new_state_pension(Variable):
    label = "new State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        simulation = person.simulation
        if simulation.dataset is None:
            return 0

        type = person("state_pension_type", period)
        eligible = type == type.possible_values.NEW
        p = parameters(period).gov.dwp.state_pension.new_state_pension
        return eligible * p.amount * WEEKS_IN_YEAR
