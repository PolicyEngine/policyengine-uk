from policyengine_uk.model_api import *


class care_to_learn(Variable):
    value_type = float
    entity = Person
    label = "Care to Learn scheme amount"
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    default_value = 0
    defined_for = "care_to_learn_eligible"

    def formula(person, period, parameters):
        # Get amounts from parameters
        region = person.household("region", period)
        p = parameters(period).gov.dfe.care_to_learn
        max_amount = where(
            region == region.possible_values.LONDON,
            p.amount.in_london,
            p.amount.outside_london,
        )

        return max_amount * WEEKS_IN_YEAR
