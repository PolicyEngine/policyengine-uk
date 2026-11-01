from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    bounded_person_holding,
)


class cash_isa_countable_capital(Variable):
    label = "Cash ISA value counted as means-tested capital"
    documentation = (
        "The person's cash ISA balance (cash_isa_balance) as the means tests "
        "count it, in the holder's own benefit unit. An ISA has one holder, "
        "who owns its investments beneficially, and a child holds their own "
        "junior ISA. The household's cash_isa already holds the balance, so "
        "each means test subtracts it from the household pool before sharing "
        "the pool between benefit units. Where the household's balances add up "
        "to more than cash_isa, the total the model holds for the household, "
        "the model scales each by cash_isa over their sum and rounds it down "
        "to float32, so the household never counts more cash ISA than "
        "cash_isa. Where they add up to less, the rest of cash_isa stays in "
        "the pool, and a household with no balances keeps all of cash_isa "
        "there."
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
