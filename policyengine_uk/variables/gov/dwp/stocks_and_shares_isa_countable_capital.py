from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    bounded_person_holding,
    household_sources,
)
from policyengine_uk.variables.household.wealth.share_like_capital_with_sale_expenses import (
    formula_split,
    holdings_with_sale_expenses,
    holdings_without_sale_expenses,
)


class stocks_and_shares_isa_countable_capital(Variable):
    label = "Stocks and shares ISA value counted as means-tested capital"
    documentation = (
        "The person's stocks and shares ISA balance (stocks_and_shares_isa_balance) as "
        "the six DWP capital assessments (Universal Credit, Pension Credit, Housing "
        "Benefit, Income Support, income-based JSA and income-related ESA) count it, in "
        "the holder's own benefit unit. Council Tax Reduction uses these valuations "
        "only through its Universal Credit and Pension Credit routes. The account "
        "investor beneficially owns an ordinary ISA's investments, and the named child "
        "owns a junior ISA's investments. The household's share_like_capital already "
        "includes the balance, through stocks_and_shares_isa within corporate_wealth "
        "or the itemised sum, in the part that holds the household's stocks and shares "
        "ISAs: share_like_capital_without_sale_expenses while "
        "gov.dwp.share_like_capital.without_sale_expenses lists stocks_and_shares_isa, "
        "and share_like_capital_with_sale_expenses under a reform that removes it. Each "
        "of the six assessments subtracts the balance from that part before allocating "
        "the pool between benefit units, and values it as it values that part: at face "
        "value, or less the sale-expense rate under such a reform. The formula bounds "
        "the person's balance by the smallest of stocks_and_shares_isa, "
        "share_like_capital and the holdings behind the part that holds the ISAs, so "
        "the household never counts more stocks and shares ISA than it holds. The "
        "holdings behind share_like_capital_without_sale_expenses are the float32 sum "
        "of the listed holdings, held between nil and share_like_capital where the "
        "itemised holdings sum to more than nil, and otherwise nil. The part itself is "
        "share_like_capital less the other part, and its float32 subtractions can "
        "leave it less than share_like_capital's float32 spacing either side of that "
        "sum. The holdings behind share_like_capital_with_sale_expenses are "
        "share_like_capital less the listed holdings, held between nil and "
        "share_like_capital where the itemised holdings sum to more than nil, and "
        "otherwise all of share_like_capital, computed in float64; the part itself "
        "rounds the listed sum and then the subtraction. For a list of two "
        "holdings, each of these holdings rounds at most once, to float32 (for the "
        "float64 complement, unless one amount is more than 2**29 times another), "
        "so bounding by them keeps the whole of a balance they cover, and the pool "
        "absorbs the part's "
        "rounding. While the list names at most two holdings, the parts' formulas "
        "stay within share_like_capital's float32 spacing of these holdings. The "
        "formula lets the balances exceed the stored part by no more than that "
        "spacing, and only where both stored parts equal the split the parts' own "
        "formulas give from share_like_capital and the itemised holdings; where "
        "that split falls further short, the stored part bounds the balances. "
        "Where a direct input, or a replaced or neutralised formula of either part, "
        "makes either stored part differ from that split, the stored part bounds "
        "the balances wherever it falls short of the holdings, however little, so "
        "the balances hold no more than the part and the pool keeps what the part "
        "holds. Inputs or formulas that give exactly the formulas' values leave "
        "every result as the formulas give it. "
        "Negative holdings beside the ISAs, itemised holdings that sum to nil or less, "
        "or a reform can leave these holdings short of the ISAs; the balances then "
        "share what the holdings hold. When the household's stored "
        "balance sum exceeds the bound, the formula scales the balances to sum to it "
        "exactly, rounding each proportional share down or up to a whole float32 step "
        "of the bound. When the balances sum to less, the rest stays in the pool, and "
        "a household with no balances keeps all of share_like_capital there."
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
        part = household_sources(parameters(period))[
            "stocks_and_shares_isa_countable_capital"
        ]
        # Bound the balances by the holdings behind the part that holds the
        # ISAs, formed with one rounding, so that a balance they cover keeps
        # its whole value. The part without sale expenses is
        # share_like_capital less the other part, so its subtractions can
        # round it below the listed holdings it stands for; their float32
        # sum, clamped as the part with sale expenses clamps it, has no such
        # rounding. The part with sale expenses subtracts that float32 sum
        # and rounds again; its complement in float64 rounds at most once.
        if part == "share_like_capital_without_sale_expenses":
            backing = holdings_without_sale_expenses(household, period, parameters)
        else:
            backing = holdings_with_sale_expenses(household, period, parameters)
        # The formulas net the balances out of the stored part. While the
        # list names at most two holdings, the parts' formulas stay within
        # share_like_capital's float32 spacing of these holdings, and that
        # rounding is all the bound lets the balances exceed the stored
        # part by. It allows it only where both stored parts are the split
        # the parts' own formulas give. Where a direct input or a replaced
        # or neutralised formula of either part changes either value, the
        # stored part bounds the balances wherever it falls short of the
        # holdings, by however little, so the pool keeps what the part
        # holds. Where the formulas' own split falls further short, the
        # stored part bounds the balances too.
        stored = household(part, period)
        with np.errstate(invalid="ignore"):
            short = where(
                formula_split(household, period, parameters),
                backing - stored > np.spacing(np.abs(share_like)),
                stored < backing,
            )
        backing = where(short, stored, backing)
        # A missing (NaN) backing leaves the bound unchanged.
        return bounded_person_holding(
            person,
            person("stocks_and_shares_isa_balance", period),
            where(backing < household_total, backing, household_total),
        )
