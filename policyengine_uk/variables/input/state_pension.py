from policyengine_uk.model_api import *


class state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension"
    definition_period = YEAR
    unit = GBP
    documentation = "Gross State Pension payments"
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

    def formula(person, period, parameters):
        gov = parameters(period).gov
        if gov.contrib.abolish_state_pension:
            return 0
        relative_increase = gov.contrib.cec.state_pension_increase
        uprating = 1 + relative_increase
        sp = gov.dwp.state_pension
        gender = person("gender", period).decode_to_str()
        is_sp_age = person("is_SP_age", period)
        return add(
            person,
            period,
            [
                "basic_state_pension",
                "additional_state_pension",
                "new_state_pension",
            ],
        )
