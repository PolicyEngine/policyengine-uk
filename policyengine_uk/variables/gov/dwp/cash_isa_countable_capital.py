from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    bounded_person_holding,
)


class cash_isa_countable_capital(Variable):
    label = "Cash ISA value counted as means-tested capital"
    documentation = (
        "The person's cash ISA balance (cash_isa_balance) as the means tests count it, "
        "in the holder's own benefit unit. The account investor beneficially owns an "
        "ordinary ISA's investments, and the named child owns a junior ISA's "
        "investments. The household's cash_isa already includes the balance, so each "
        "means test subtracts it from the household pool before allocating the pool "
        "between benefit units. The formula bounds the person's balance by cash_isa, "
        "the household total. When the household's stored balance sum exceeds that "
        "total, it scales the balances to sum to the total exactly, rounding each "
        "proportional share down or up to a whole float32 step of the total. When the "
        "balances sum to less, the rest of cash_isa stays in the pool, and a household "
        "with no balances keeps all of cash_isa there."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    reference = [
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/4",
        "https://www.legislation.gov.uk/uksi/1998/1870/regulation/2B",
    ]

    def formula(person, period, parameters):
        return bounded_person_holding(
            person,
            person("cash_isa_balance", period),
            person.household("cash_isa", period),
        )
