from policyengine_uk.model_api import *


class care_to_learn_amount(Variable):
    value_type = float
    entity = Person
    label = "Care to Learn childcare support amount"
    documentation = "Yearly childcare support amount for eligible young parents in education"
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    default_value = 0

    def formula(person, period, parameters):
        eligible = person("care_to_learn_eligible", period)

        # Check if in London using region
        household_region = person.household("region", period)
        region = household_region
        regions = household_region.possible_values
        in_london = region == regions.LONDON

        # Get amounts from parameters
        p = parameters(period).gov.hmrc.study_childcare_entitlement
        max_amount = where(
            in_london,
            p.care_to_learn_amount.in_london,
            p.care_to_learn_amount.outside_london,
        )

        return where(eligible, max_amount * 52, 0)
