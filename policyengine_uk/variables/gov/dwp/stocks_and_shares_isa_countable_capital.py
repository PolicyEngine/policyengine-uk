from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    bounded_person_holding,
    household_sources,
)


class stocks_and_shares_isa_countable_capital(Variable):
    label = "Stocks and shares ISA value counted as means-tested capital"
    documentation = (
        "The person's stocks and shares ISA balance (stocks_and_shares_isa_balance) as "
        "the means tests count it, in the holder's own benefit unit. The account "
        "investor beneficially owns an ordinary ISA's investments, and the named child "
        "owns a junior ISA's investments. The household's share_like_capital already "
        "includes the balance, through stocks_and_shares_isa within corporate_wealth "
        "or the itemised sum, in the part that holds the household's stocks and shares "
        "ISAs: share_like_capital_without_sale_expenses while "
        "gov.dwp.share_like_capital.without_sale_expenses lists stocks_and_shares_isa, "
        "and share_like_capital_with_sale_expenses under a reform that removes it. Each "
        "means test subtracts the balance from that part before allocating the pool "
        "between benefit units, and values it as it values that part: at face value, "
        "or less the sale-expense rate under such a reform. The formula bounds the "
        "person's balance by the smaller of stocks_and_shares_isa and "
        "share_like_capital, so the household never counts more stocks and shares ISA "
        "than it holds. It bounds them instead by the part that holds the ISAs where "
        "that part falls short of this bound by more than share_like_capital's float32 "
        "spacing. Rounding in the subtraction that forms the part leaves it short by "
        "at most half that spacing, so the part takes over only where negative holdings "
        "beside the ISAs, itemised holdings that sum to nil or less, or a reform leave "
        "it short of the ISAs. When the household's stored balance sum exceeds the "
        "bound, the formula scales the balances to sum to it exactly, rounding each "
        "proportional share down or up to a whole float32 step of the bound. When the "
        "balances sum to less, the rest stays in the pool, and a household with no "
        "balances keeps all of share_like_capital there."
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
        household = person.household
        share_like = household("share_like_capital", period)
        household_total = min_(household("stocks_and_shares_isa", period), share_like)
        part = household(
            household_sources(parameters(period))[
                "stocks_and_shares_isa_countable_capital"
            ],
            period,
        )
        # The part without sale expenses is share_like_capital less the part
        # with them, so it can miss the holdings it stands for by half of
        # share_like_capital's float32 spacing. A larger shortfall means the
        # part holds less than the ISAs, and the balances can't take more out
        # of it than it holds. An infinite share_like_capital has no spacing,
        # and keeps the bound.
        with np.errstate(invalid="ignore"):
            slack = np.spacing(np.abs(share_like)).astype(np.float64)
            short = household_total.astype(np.float64) - part.astype(np.float64) > slack
        return bounded_person_holding(
            person,
            person("stocks_and_shares_isa_balance", period),
            where(short, part, household_total),
        )
