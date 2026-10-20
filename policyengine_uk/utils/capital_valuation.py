"""Value means-tested capital as the capital-valuation regulations require.

Universal Credit calculates capital "at its current market value or surrender
value less— (a) where there would be expenses attributable to sale, 10%; and
(b) the amount of any encumbrances secured on it" (UC Regs 2013 reg. 49(1)).
The legacy means tests have equivalent rules (HB Regs 2006 reg. 47, IS Regs
1987 reg. 49, JSA Regs 1996 reg. 111, ESA Regs 2008 reg. 113, SPC Regs 2002
reg. 19). Each programme sets its own rate and the capital sources whose sale
would incur expenses in a ``capital.sale_expenses`` parameter node.
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


def valued_capital(value_of, sources, sale_expenses):
    """Sum ``sources`` at market value less sale expenses and secured debt.

    ``value_of(variable)`` returns that household variable on the entity the
    caller is working with. The sale-expense deduction is taken from the gross
    value before the encumbrance (ADM H1608) and the result rounded down to the
    penny in the claimant's favour, as ADM H1665 does for quoted shares. A
    source carrying secured debt is never valued below nil.
    """
    total = 0
    for source in sources:
        value = value_of(source)
        if source in sale_expenses.sources:
            value = penny_floor(value * (1 - sale_expenses.rate))
        if source in SECURED_DEBT:
            value = max_(0, value - value_of(SECURED_DEBT[source]))
        total = total + value
    return total


def counted_share(sale_expenses, source):
    """Share of a source's market value counted as capital: 90% where its
    sale would incur expenses (reg. 49(1)(a)), otherwise all of it."""
    return 1 - sale_expenses.rate if source in sale_expenses.sources else 1


def penny_floor(amount):
    """Round down to the penny, in the claimant's favour (ADM H1665).

    Computed in float64, and rounded to a millionth of a penny first, so binary
    noise just under a whole penny (10,799.9999999 for 90% of 12,000) does not
    lose a penny."""
    pence = np.round(np.asarray(amount, dtype=np.float64) * 100, 6)
    return np.floor(pence) / 100
