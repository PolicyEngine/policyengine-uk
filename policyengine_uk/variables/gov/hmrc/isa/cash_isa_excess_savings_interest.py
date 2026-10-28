from policyengine_uk.model_api import *


class cash_isa_excess_savings_interest(Variable):
    value_type = float
    entity = Person
    label = "Interest on cash ISA excess held in taxable savings"
    documentation = (
        "Interest on the cash ISA subscriptions above the cash limit that the "
        "person holds in taxable savings, at the rate in "
        "gov.contrib.behavioral_responses.cash_isa_excess. It is taxed as "
        "savings interest but not added to income: the person earns it either "
        "way, tax-free in a cash ISA or taxed outside one, so a cash limit "
        "changes the tax and not the gross income. It is a full year's "
        "interest on the year's excess and leaves out cash moved out of ISAs "
        "in earlier years, which a static annual model does not hold. Zero "
        "unless a reform sets the response's shares."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        p = parameters(period).gov.contrib.behavioral_responses.cash_isa_excess
        responds = p.stocks_and_shares_isa_share > 0 or p.taxable_savings_share > 0
        if not responds or p.interest_rate == 0:
            return 0
        held = person("cash_isa_excess_to_taxable_savings", period)
        return held * p.interest_rate
