from policyengine_uk.model_api import *


class cash_isa_excess_to_taxable_savings(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA excess held in taxable savings"
    documentation = (
        "Cash ISA subscriptions above the cash limit that the person holds in "
        "taxable savings instead: the taxable savings share in "
        "gov.contrib.behavioral_responses.cash_isa_excess, plus any cash meant "
        "for a stocks-and-shares ISA that the annual limit leaves no room for. "
        "Zero unless a reform sets those shares."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        p = parameters(period).gov.contrib.behavioral_responses.cash_isa_excess
        excess = person("cash_isa_subscriptions_above_limit", period)
        moved = person("cash_isa_excess_to_stocks_and_shares_isa", period)
        no_room = excess * p.stocks_and_shares_isa_share - moved
        return excess * p.taxable_savings_share + no_room
