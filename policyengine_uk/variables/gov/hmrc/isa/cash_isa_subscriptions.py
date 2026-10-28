from policyengine_uk.model_api import *


class cash_isa_subscriptions(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA subscriptions"
    documentation = (
        "New money paid into cash ISAs in the tax year, summed over all the "
        "person's cash ISAs, as a person can pay into more than one in a year. "
        "It counts towards the cash and annual subscription limits. Exclude "
        "transfers between ISAs, interest and growth, and replacements of cash "
        "withdrawn from a flexible ISA earlier in the same tax year, which do "
        "not count towards the limits. The model compares this amount with the limits in force "
        "and does not cap it: under a lower limit, such as a reform that "
        "brings in a £12,000 cash limit, cash_isa_subscriptions_above_limit "
        "reports the part that cannot be paid in. Amounts are not uprated, as "
        "the limits are fixed in cash terms."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4ZA"
