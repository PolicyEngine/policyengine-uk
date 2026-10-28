from policyengine_uk.model_api import *


class cash_isa_subscriptions_above_limit(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA subscriptions above the cash limit"
    documentation = (
        "Cash ISA subscriptions above the cash limit that applies to the "
        "person. It is zero for data that met the limits in force when it was "
        "collected; under a lower limit it is cash that cannot go into a cash "
        "ISA. gov.contrib.behavioral_responses.cash_isa_excess sets where it "
        "goes, and by default none of it changes tax. Cash above the annual "
        "limit also counts in isa_subscriptions_above_limit, so the two "
        "overlap and must not be added."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA"

    def formula(person, period, parameters):
        subscriptions = person("cash_isa_subscriptions", period)
        limit = person("cash_isa_subscription_limit", period)
        return max_(subscriptions - limit, 0)
