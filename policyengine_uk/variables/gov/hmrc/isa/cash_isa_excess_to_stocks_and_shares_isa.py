from policyengine_uk.model_api import *


class cash_isa_excess_to_stocks_and_shares_isa(Variable):
    value_type = float
    entity = Person
    label = "Cash ISA excess paid into stocks-and-shares ISAs"
    documentation = (
        "Cash ISA subscriptions above the cash limit that the person pays into "
        "stocks-and-shares ISAs instead: the stocks-and-shares ISA share in "
        "gov.contrib.behavioral_responses.cash_isa_excess, up to the room the "
        "annual subscription limit leaves after the cash kept in cash ISAs and "
        "the other ISA subscriptions. Zero unless a reform sets that share. "
        "It is not added to stocks_and_shares_isa_subscriptions."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        p = parameters(period).gov.contrib.behavioral_responses.cash_isa_excess
        shares = [p.stocks_and_shares_isa_share, p.taxable_savings_share]
        if min(shares) < 0 or sum(shares) > 1:
            raise ValueError(
                "The shares in gov.contrib.behavioral_responses.cash_isa_excess "
                "must be non-negative and sum to at most one"
            )
        excess = person("cash_isa_subscriptions_above_limit", period)
        kept = person("isa_subscriptions", period) - excess
        limit = parameters(period).gov.hmrc.isa.annual_subscription_limit
        room = max_(limit - kept, 0)
        return min_(excess * p.stocks_and_shares_isa_share, room)
