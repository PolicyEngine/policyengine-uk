from policyengine_uk.model_api import *


class isa_subscriptions_above_limit(Variable):
    value_type = float
    entity = Person
    label = "ISA subscriptions above the annual limit"
    documentation = (
        "ISA subscriptions above the annual subscription limit: an amount that "
        "cannot be held in any ISA in the year. It is zero for data that met "
        "the limits in force when it was collected. The model does not say "
        "which ISA type the excess comes from or where it goes. Cash above the "
        "cash limit counts in cash_isa_subscriptions_above_limit too, so the "
        "two overlap and must not be added."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA"

    def formula(person, period, parameters):
        limit = parameters(period).gov.hmrc.isa.annual_subscription_limit
        return max_(person("isa_subscriptions", period) - limit, 0)
