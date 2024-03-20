from policyengine_uk.model_api import *

class childcare(Variable): # rename to care_to_learn. also rename the file(.py) and move to a variables/dfe/care_to_learn.py location
    label = "Care-to-learn subsidy" # "Care-to-learn subsidy" - more specific because there are a few different childcare subsidies
    documentation = "Childcare support for parents under 20 taking publicly-funded courses in England." # all good!
    entity = Household # yep
    definition_period = WEEK # change to MONTH and just make sure the month amounts are 4x the amount of the weekly values
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/care-to-learn/what-youll-get" # all good!

    def formula(household, period, parameters):
        # MONTHLY example
        # if it's £180 per week, the monthly value is just 180 * 52 / 12
        live_in_london = household("live_in_london", period)
        # live_in_london = household("region", period).decode_to_str() == "LONDON"
        amount_per_child = parameters(period).gov.dwp.universal_credit.elements.childcare.childcare_amount_per_child
        # amount_per_child = parameters(period).gov.dfe.care_to_learn.amount_per_child
        if live_in_london:
            return amount_per_child.IN_LONDON # multiply to get monthly amount
        else:
            return amount_per_child.OUTSIDE_LONDON # also multiply