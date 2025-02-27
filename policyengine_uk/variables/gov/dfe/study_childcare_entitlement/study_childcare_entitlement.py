from policyengine_uk.model_api import *


class study_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "study childcare entitlement amount per year through Care to Learn scheme"
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    default_value = 0

    def formula(person, period, parameters):
        eligible = person("study_childcare_entitlement_eligible", period)

        # Get amounts from parameters
        region = person.household("region", period)
        p = parameters(
            period
        ).gov.dfe.study_childcare_entitlement.amount
        max_amount = where(
            region == region.possible_values.LONDON,
            p.in_london,
            p.outside_london,
        )

        return eligible * max_amount * WEEKS_IN_YEAR
