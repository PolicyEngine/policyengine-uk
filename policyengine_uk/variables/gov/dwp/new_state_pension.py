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

        return where(
            person("state_pension_type", period) == StatePensionType.NEW,
            parameters(period).gov.dwp.state_pension.new_state_pension.amount
            * WEEKS_IN_YEAR,
            0,
        )
