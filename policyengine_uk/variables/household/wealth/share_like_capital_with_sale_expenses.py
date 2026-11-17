from policyengine_uk.model_api import *

# The share-like holdings a dataset can itemise. The formula treats a
# household as itemising only when their sum is positive, so every name in
# gov.dwp.share_like_capital.without_sale_expenses must be in this list. A
# reform that adds a holding outside it would leave a household that itemises
# only that holding with all of its share-like capital under the deduction.
# share_like_capital sums the same three names, so such a reform must add
# the holding there too.
COMPONENTS = [
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
]


class share_like_capital_with_sale_expenses(Variable):
    label = "share-like capital with expenses of sale"
    documentation = (
        "The part of share_like_capital whose sale would incur expenses, so "
        "that the six DWP capital assessments value it less 10%. Where the "
        "itemised holdings sum to more than nil, it is share_like_capital less "
        "the itemised holdings listed in gov.dwp.share_like_capital."
        "without_sale_expenses (unit and investment trusts, stocks and shares "
        "ISAs), held between nil and share_like_capital, which is then "
        "nonnegative, so that the two parts add up to share_like_capital, to "
        "within float32 rounding, whatever the signs of the holdings. Where "
        "they sum to nil or less, it is all of share_like_capital, whatever "
        "its sign, so datasets that carry only corporate_wealth keep the flat "
        "10% on it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        return _formula_with_sale_expenses(household, period, parameters)


def _formula_with_sale_expenses(household, period, parameters):
    """share_like_capital_with_sale_expenses's formula."""
    share_like = household("share_like_capital", period)
    itemised, without = _itemised_and_listed(household, period, parameters)
    # share_like_capital is nonnegative wherever the itemised sum is
    # positive. Holding this part between nil and that total keeps the
    # other part, the difference, between nil and the total too, so
    # negative trusts beside positive shares can't push the two parts
    # apart.
    return where(
        itemised > 0,
        min_(share_like, max_(0, share_like - without)),
        share_like,
    )


def formula_split(household, period, parameters):
    """Whether each household's two stored parts are the split the parts'
    own formulas give.

    Recomputes share_like_capital_with_sale_expenses with its own formula,
    from the stored share_like_capital and itemised holdings and the law's
    exempt list, and stores it as the engine stores a formula result, in
    float32; the part without sale expenses is share_like_capital less that,
    as its formula subtracts it. The same float32 operations on the same
    values give the same result, so where both parts come from these
    formulas, the stored parts equal the recomputed ones exactly. A direct
    input, or a reform that replaces or neutralises either part's formula,
    gives a split that differs from it unless every value agrees, and a
    split whose values all agree gives every result the formulas give. A
    missing (NaN) part never equals its recomputation.
    """
    share_like = household("share_like_capital", period)
    with_expenses = np.asarray(
        _formula_with_sale_expenses(household, period, parameters), np.float32
    )
    return (
        household("share_like_capital_with_sale_expenses", period) == with_expenses
    ) & (
        household("share_like_capital_without_sale_expenses", period)
        == share_like - with_expenses
    )


def _itemised_and_listed(household, period, parameters):
    """share_like_capital's itemised sum, and the sum of the holdings
    gov.dwp.share_like_capital.without_sale_expenses lists, each added in
    float32 as the engine adds it: COMPONENTS left to right, and the listed
    holdings in list order from nil."""
    itemised = add(household, period, COMPONENTS)
    # Summed from a numeric zero so that an empty list (every holding taking
    # the deduction) still works.
    listed = 0 * household("share_like_capital", period)
    for variable in parameters(period).gov.dwp.share_like_capital.without_sale_expenses:
        listed = listed + household(variable, period)
    return itemised, listed


def holdings_without_sale_expenses(household, period, parameters):
    """The holdings share_like_capital_without_sale_expenses stands for.

    Where the itemised holdings sum to more than nil, the float32 sum of the
    holdings gov.dwp.share_like_capital.without_sale_expenses lists, held
    between nil and share_like_capital as share_like_capital_with_sale_expenses
    holds its complement; otherwise nil. It is the sum the other part
    subtracts, so it rounds once for a list of two holdings, as the baseline
    list is. The part itself is share_like_capital less
    share_like_capital_with_sale_expenses, whose float32 subtractions leave it
    less than share_like_capital's float32 spacing either side of this sum. No
    subtraction enters the sum: a balance it covers keeps its whole value,
    however the part rounds.
    """
    share_like = household("share_like_capital", period)
    itemised, listed = _itemised_and_listed(household, period, parameters)
    return where(itemised > 0, min_(share_like, max_(0, listed)), 0)


def holdings_with_sale_expenses(household, period, parameters):
    """The holdings share_like_capital_with_sale_expenses stands for.

    Where the itemised holdings sum to more than nil, share_like_capital less
    the holdings gov.dwp.share_like_capital.without_sale_expenses lists, held
    between nil and share_like_capital; otherwise all of share_like_capital.
    The part itself subtracts the listed holdings' float32 sum, which rounds
    once for a list of two holdings, and then rounds again. This complement
    runs in float64, which holds the sum and difference of float32 amounts
    exactly unless one is more than some 500 million (2**29) times another,
    so it rounds at most once, to float32, where it bounds a balance: a
    balance it covers keeps its whole value, however the part rounds.
    """
    share_like = np.asarray(household("share_like_capital", period), np.float64)
    itemised = add(household, period, COMPONENTS)
    listed = np.zeros_like(share_like)
    for variable in parameters(period).gov.dwp.share_like_capital.without_sale_expenses:
        listed = listed + np.asarray(household(variable, period), np.float64)
    with np.errstate(invalid="ignore"):
        complement = np.minimum(share_like, np.maximum(0, share_like - listed))
    return np.where(itemised > 0, complement, share_like)
