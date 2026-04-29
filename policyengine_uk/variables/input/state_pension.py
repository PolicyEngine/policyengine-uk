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
        contrib = parameters.gov.contrib
        if contrib.abolish_state_pension(period):
            return 0
        uprating = 1 + contrib.cec.state_pension_increase(period)
        return (
            add(
                person,
                period,
                [
                    "basic_state_pension",
                    "additional_state_pension",
                    "new_state_pension",
                ],
            )
            * uprating
        )
