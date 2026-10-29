from policyengine_uk.model_api import *


class isa_subscriptions(Variable):
    value_type = float
    entity = Person
    label = "ISA subscriptions"
    documentation = (
        "Subscriptions in the tax year that count towards the annual ISA "
        "subscription limit: cash, stocks-and-shares and Lifetime ISA. "
        "lifetime_isa_payments includes transfers into a Lifetime ISA from "
        "other ISAs, which count towards the Lifetime ISA limit but are not new "
        "subscriptions for the annual limit, so where that input includes them "
        "this total overstates subscriptions by the amount transferred. "
        "Innovative finance ISAs are not included."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    reference = (
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA",
        "https://www.gov.uk/guidance/manage-isa-subscriptions-for-your-investors",
    )
    adds = [
        "cash_isa_subscriptions",
        "stocks_and_shares_isa_subscriptions",
        "lifetime_isa_payments",
    ]
