from policyengine_uk.model_api import *

class care_to_learn(Variable):
    label = "Care-to-learn subsidy"
    documentation = "Childcare support for parents under 20 taking publicly-funded courses in England." # all good!
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/care-to-learn/what-youll-get"

    def formula(household, period, parameters):
        live_in_london = household("region", period).decode_to_str() == "LONDON"
        amount_per_child = parameters(period).gov.dfe.care_to_learn.amount_per_child
        if live_in_london:
            return amount_per_child.IN_LONDON*4
        else:
            return amount_per_child.OUTSIDE_LONDON*4