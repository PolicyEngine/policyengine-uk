from policyengine_uk.model_api import *


class care_to_learn_amount(Variable):
    value_type = float
    entity = Person
    label = "care to learn childcare support amount"
    documentation = "Yearly childcare support amount for eligible young parents in education."
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    default_value = 0

    def formula(person, period, parameters):
        eligible = person("care_to_learn_eligible", period)

        # Get amounts from parameters
        region = person.household("region", period)
        p = parameters(
            period
        ).gov.dfe.study_childcare_entitlement.care_to_learn.amount
        max_amount = where(
            region == region.possible_values.LONDON,
            p.in_london,
            p.outside_london,
        )

        return eligible * max_amount * WEEKS_IN_YEAR
