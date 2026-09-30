"""Value means-tested capital as the capital-valuation regulations require.

Universal Credit and each legacy means test value capital in the United
Kingdom "at its current market or surrender value less (a) where there would
be expenses attributable to sale, 10% [...]; and (b) the amount of any
encumbrances secured on it" (UC Regs 2013 reg. 49(1) and its legacy
equivalents). Each programme sets its own rate and the capital sources whose
sale would incur expenses in a ``capital.sale_expenses`` parameter node.
"""

from policyengine_core.model_api import max_

# Household inputs holding the debts secured on each capital source, such as
# a mortgage on a second property. The encumbrance is deducted only from the
# asset it is secured on, so negative equity in one asset never reduces the
# value of another (ADM H1615-H1616).
SECURED_DEBT = {
    "other_residential_property_value": "other_residential_property_secured_debt",
    "non_residential_property_value": "non_residential_property_secured_debt",
    "owned_land": "owned_land_secured_debt",
}


def valued_capital(value_of, sources, sale_expenses):
    """Sum ``sources`` at market value less sale expenses and secured debt.

    ``value_of(variable)`` returns that household variable on the entity the
    caller is working with. The sale-expense deduction comes first and the
    encumbrance second (ADM H1608), and an encumbered asset is never valued
    below nil.
    """
    total = 0
    for source in sources:
        value = value_of(source)
        if source in sale_expenses.sources:
            value = value * (1 - sale_expenses.rate)
        if source in SECURED_DEBT:
            value = max_(0, value - value_of(SECURED_DEBT[source]))
        total = total + value
    return total
