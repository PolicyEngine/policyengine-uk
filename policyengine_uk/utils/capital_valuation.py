"""Value means-tested capital as the capital-valuation regulations require.

Universal Credit calculates capital "at its current market value or surrender
value less— (a) where there would be expenses attributable to sale, 10%; and
(b) the amount of any encumbrances secured on it" (UC Regs 2013 reg. 49(1)).
The legacy means tests have equivalent rules (HB Regs 2006 reg. 47, IS Regs
1987 reg. 49, JSA Regs 1996 reg. 111, ESA Regs 2008 reg. 113, SPC Regs 2002
reg. 19). Each programme sets its own rate and the capital sources whose sale
would incur expenses in a ``capital.sale_expenses`` parameter node, and how it
rounds a fraction of a penny in ``capital.round_down``: to the nearest penny
for Universal Credit and Housing Benefit, down for the others.
"""

import numpy as np
from policyengine_core.model_api import max_

# Household inputs holding the debt secured on each capital source, such as a
# mortgage on a second property. The debt is deducted from the source it is
# secured on and that source is floored at nil, so negative equity in one
# source never reduces another (ADM H1615-H1616). Each source is a category
# summed over the household's assets, so within a category the debts on one
# asset still offset equity in another.
SECURED_DEBT = {
    "other_residential_property_value": "other_residential_property_secured_debt",
    "non_residential_property_value": "non_residential_property_secured_debt",
    "owned_land": "owned_land_secured_debt",
}


def valued_capital(value_of, capital):
    """Sum ``capital.sources`` at market value less sale expenses and secured debt.

    ``value_of(variable)`` returns that household variable on the entity the
    caller is working with, and ``capital`` is the programme's capital
    parameter node. The sale-expense deduction is taken from the gross value
    before the encumbrance (ADM H1608), and each valuation is rounded to the
    penny under the programme's rule. A source carrying secured debt is never
    valued below nil. The total is in float64, unrounded: the caller rounds
    the capital it assesses at the last stage (``round_to_penny``).
    """
    total = 0
    for source in capital.sources:
        value = exact_amount(value_of(source))
        if source in capital.sale_expenses.sources:
            value = less_sale_expenses(
                value, capital.sale_expenses.rate, capital.round_down
            )
        if source in SECURED_DEBT:
            value = max_(0, value - exact_amount(value_of(SECURED_DEBT[source])))
        total = total + value
    return total


def counted_share(sale_expenses, source):
    """Share of a source's market value counted as capital: 90% where its
    sale would incur expenses (reg. 49(1)(a)), otherwise all of it."""
    return 1 - sale_expenses.rate if source in sale_expenses.sources else 1


def less_sale_expenses(value, rate, round_down):
    """Market value less the sale-expense ``rate`` (reg. 49(1)(a)), rounded to
    the penny under the programme's rule.

    The deduction is worked on the exact stored value: 250 shares at £4.1375
    are £1,034.375, and less 10% that is £930.9375, so £930.93 rounded down
    (ADM H1665) or £930.94 to the nearest penny (UC Regs 2013 reg. 6(1))."""
    return round_to_penny(
        exact_amount(value) * (1 - np.asarray(rate, dtype=np.float64)), round_down
    )


def exact_amount(amount):
    """``amount`` in float64, with float32 storage error removed.

    Inputs are stored in float32, which holds £1,000.10 as 1,000.0999756 and
    90% of £16,001 as 14,400.8994. A value is taken to be a whole penny when
    that penny is within half a unit of the value's own precision, so it is
    the penny the value was stored from; any other value (a share price to
    four decimal places, say) is kept exactly as stored. Above £131,072
    float32 cannot hold every penny, so a penny lost in storage there cannot
    be recovered."""
    stored = np.asarray(amount)
    wide = stored.astype(np.float64)
    pennies = np.round(wide, 2)
    # An infinite amount has no precision to compare against and passes through.
    with np.errstate(over="ignore", invalid="ignore"):
        stored_from_penny = np.abs(pennies - wide) <= np.spacing(np.abs(stored)) / 2
    return np.where(stored_from_penny, pennies, wide)


def round_to_penny(amount, round_down):
    """Round ``amount`` to the penny: down where ``round_down``, otherwise to
    the nearest penny with half a penny rounded up.

    Universal Credit treats a fraction of half a penny or more as a penny and
    disregards a smaller one (UC Regs 2013 reg. 6(1)), and Housing Benefit may
    do the same (HB Regs 2006 reg. 80). The legacy benefits treat a fraction
    as a penny only where that is to the claimant's advantage (IS Regs 1987
    reg. 27, JSA Regs 1996 reg. 92, ESA Regs 2008 reg. 3(a), SPC Regs 2002
    reg. 24A), which for capital means rounding down.

    Computed in float64, and rounded to a millionth of a penny first, so binary
    noise next to a whole or half penny (206.99999999999997 pence for 90% of
    £2.30) does not move it."""
    pence = np.round(np.asarray(amount, dtype=np.float64) * 100, 6)
    return np.where(round_down, np.floor(pence), np.floor(pence + 0.5)) / 100
