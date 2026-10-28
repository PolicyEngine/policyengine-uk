from policyengine_uk.model_api import *


class stocks_and_shares_isa_subscriptions(Variable):
    value_type = float
    entity = Person
    label = "Stocks and shares ISA subscriptions"
    documentation = (
        "New money paid into stocks-and-shares ISAs in the tax year, summed "
        "over all the person's stocks-and-shares ISAs and including eligible "
        "shares subscribed by transfer. It counts towards the annual "
        "subscription limit. Exclude transfers between ISAs, income and growth, "
        "and replacements of cash withdrawn from a flexible ISA earlier in the "
        "same tax year. Innovative finance ISAs are not included. Amounts are "
        "not uprated, as the limit is fixed in cash terms."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA"
