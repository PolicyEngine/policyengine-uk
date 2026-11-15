from policyengine_uk.model_api import *


class stocks_and_shares_isa_subscriptions(Variable):
    value_type = float
    entity = Person
    label = "Stocks and shares ISA subscriptions"
    documentation = (
        "New money paid into stocks-and-shares ISAs in the tax year, summed "
        "over all the person's stocks-and-shares ISAs, including eligible shares "
        "subscribed by transfer, and net of current-year subscriptions withdrawn "
        "from a flexible ISA. It counts towards the annual subscription limit. "
        "Exclude transfers between ISAs, income and growth, and the "
        "subscriptions that regulation 5D disregards, such as replacement "
        "subscriptions to a flexible ISA, additional permitted subscriptions, "
        "defaulted subscriptions and transfers from a matured Child Trust Fund. "
        "Innovative finance ISAs are not included. Amounts are not uprated: "
        "growing them would put people who pay in exactly the annual limit above "
        "it in the baseline. As nominal subscriptions grow, flat amounts "
        "understate how much a lowered limit leaves out in later years; a "
        "producer can grow them instead and cap each person at the limit in "
        "force."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA",
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/5D",
    )
