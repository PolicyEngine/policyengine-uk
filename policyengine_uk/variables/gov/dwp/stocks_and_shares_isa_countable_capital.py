from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    bounded_person_holding,
)


class stocks_and_shares_isa_countable_capital(Variable):
    label = "Stocks and shares ISA value counted as means-tested capital"
    documentation = (
        "The person's stocks and shares ISA balance "
        "(stocks_and_shares_isa_balance) as the means tests count it, in the "
        "holder's own benefit unit. An ISA has one holder, who owns its "
        "investments beneficially, and a child holds their own junior ISA. "
        "The household's share_like_capital already counts the balance, "
        "through stocks_and_shares_isa within corporate_wealth or the "
        "itemised sum, so each means test takes it out of the household pool "
        "it shares between benefit units. Where the household's balances add "
        "up to more than the smaller of stocks_and_shares_isa and "
        "share_like_capital, each is scaled down by the same proportion, so "
        "no household counts more stocks and shares ISA than it holds. Where "
        "they add up to less, the rest stays in the pool. A household with no "
        "balances keeps all of share_like_capital in the pool."
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
        household_total = min_(
            person.household("stocks_and_shares_isa", period),
            person.household("share_like_capital", period),
        )
        return bounded_person_holding(
            person,
            person("stocks_and_shares_isa_balance", period),
            household_total,
        )
