from policyengine_uk.model_api import *


class cash_isa_subscriptions(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA subscriptions"
    documentation = (
        "New money paid into cash ISAs in the tax year, summed over all the "
        "person's cash ISAs, as a person can pay into more than one in a year, "
        "and net of current-year subscriptions withdrawn from a flexible ISA. "
        "It counts towards the cash and annual subscription limits. Exclude "
        "transfers between ISAs, interest and growth, and the subscriptions "
        "that regulation 5D disregards, such as replacement subscriptions to a "
        "flexible ISA, additional permitted subscriptions, defaulted "
        "subscriptions and transfers from a matured Child Trust Fund. The model "
        "compares this amount with the limits in force and does not cap it: "
        "under a lower limit, such as a reform that brings in a £12,000 cash "
        "limit, cash_isa_subscriptions_above_limit reports the part that cannot "
        "be paid in. Amounts are not uprated: growing them would put people who "
        "pay in exactly the annual limit above it in the baseline. As nominal "
        "subscriptions grow, flat amounts understate how much a lowered limit "
        "leaves out in later years; a producer can grow them instead and cap "
        "each person at the limit in force."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA",
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/5D",
    )
