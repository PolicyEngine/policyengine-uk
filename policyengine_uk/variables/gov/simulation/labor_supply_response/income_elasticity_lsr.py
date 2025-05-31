from policyengine_uk.model_api import *


class income_elasticity_lsr(Variable):
    value_type = float
    entity = Person
    label = "income elasticity of labor supply response"
    unit = GBP
    definition_period = YEAR
    requires_computation_after = "employment_income_behavioral_response"

    def formula(person, period, parameters):
        lsr = parameters(period).gov.simulation.labor_supply_responses
        employment_income = person("employment_income_before_lsr", period)
        income_change = person("relative_income_change", period)

        return employment_income * income_change * lsr.income_elasticity
