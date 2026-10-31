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

from policyengine_uk.utils.supplied_inputs import supplied_input

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


def valued_person_capital(benunit, period, parameters, capital, counted):
    """Sum ``capital.person_sources`` over the benefit unit's members for whom
    ``counted`` is true (its claimant and partner), in float64.

    A source whose formula can give a fraction of a penny
    (``CALCULATED_PERSON_SOURCES``) is valued to the penny under the
    programme's rule, like any other valuation. The baseline formula is
    worked again in float64, so float32 cannot move the rounding, and only
    where the variable's ``defined_for`` mask applies it, as Core does. Like
    Core, it runs no formula when the mask applies to nobody.
    Explicit inputs for this period and branch, and values from a reformed
    formula, are kept as stored: matching a baseline value in float32 does
    not prove where a value came from. Any other source is a stored
    amount."""
    person = benunit.members
    total = 0
    for source in capital.person_sources:
        stored = person(source, period)
        value = exact_amount(stored)
        if source in CALCULATED_PERSON_SOURCES:
            calculate = CALCULATED_PERSON_SOURCES[source]
            # A holder can predate a reform; the system owns the active formula.
            variable = person.simulation.tax_benefit_system.get_variable(source)
            if (
                not variable.is_neutralized
                and variable.get_formula(period) is calculate
                and supplied_input(person, source, period) is None
            ):
                applicable = None
                if variable.defined_for is not None:
                    # Core keeps the formula's result only where the
                    # defined_for variable is above zero and stores the
                    # default elsewhere, and runs no formula when it is
                    # above zero for nobody; do the same.
                    applicable = (
                        person.simulation.calculate(
                            variable.defined_for, period, map_to=variable.entity.key
                        )
                        > 0
                    )
                if applicable is None or applicable.any():
                    exact = calculate(person, period, parameters)
                    if applicable is not None:
                        exact = np.where(applicable, exact, value)
                    value = exact
            value = round_to_penny(value, capital.round_down)
        total = total + benunit.sum(value * counted)
    return total


def lifetime_isa_surrender_value(person, period, parameters):
    """Surrender value of each person's Lifetime ISAs, in float64: the balance
    less the withdrawal charge below the charge-free age, and the whole balance
    from that age.

    75% of a whole-penny balance can end in a quarter or half penny (75% of
    £0.26 is £0.195), which float32 would store as 0.19499999 and so move a
    nearest-penny rounding; 75% of £1,000.04 is £750.03."""
    p = parameters(period).gov.hmrc.isa.lifetime
    balance = exact_amount(person("lifetime_isa_balance", period))
    charge_free = person("age", period) >= p.charge_free_age
    return np.where(charge_free, balance, balance * (1 - p.withdrawal_charge))


# Person-level capital sources the means tests value from their inputs, each
# mapped to the float64 calculation of its value.
CALCULATED_PERSON_SOURCES = {
    "lifetime_isa_countable_capital": lifetime_isa_surrender_value,
}


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
    90% of £16,001 as 14,400.8994. A float32 value, or one widened from
    float32 to float64, is taken to be a whole penny when that penny is within
    half its float32 spacing: it is then the penny the value was stored from.
    Below £131,072 float32 holds every penny, so at most one penny is that
    close. From £131,072 its spacing is wider than a penny, the penny cannot
    be identified, and the value is kept as stored. A capital figure built
    from it can then be a penny either way: £140,000.01 and £140,000.02 are
    both stored as 140,000.015625, and 90% of that rounds down to
    £126,000.01, a penny above the £126,000.00 that £140,000.01 gives. The
    same holds for any stored value from £262,144, where the spacing exceeds
    two pennies. A value in whole pounds below £16,777,216 is stored exactly
    and is unaffected. Any other value (a share price to four decimal places,
    or a float64 that is not a float32) is kept exactly."""
    wide = np.asarray(amount).astype(np.float64)
    pennies = np.round(wide, 2)
    # Zero and subnormal values underflow in np.spacing and in the cast to
    # float32, and an infinite one overflows; neither is a penny that needs
    # recovering.
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        narrow = wide.astype(np.float32)
        precision = np.where(
            narrow == wide,
            np.spacing(np.abs(narrow)).astype(np.float64),
            np.spacing(np.abs(wide)),
        )
        stored_from_penny = (2 * np.abs(pennies - wide) <= precision) & (
            precision < 0.01
        )
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
    £2.30) does not move it. That tolerance is intended: an amount within a
    millionth of a penny below a whole penny, which only a value that is not
    a whole penny can produce, rounds to that penny."""
    pence = np.round(np.asarray(amount, dtype=np.float64) * 100, 6)
    return np.where(round_down, np.floor(pence), np.floor(pence + 0.5)) / 100
