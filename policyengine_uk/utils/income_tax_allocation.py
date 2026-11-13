"""Set Income Tax reliefs and allowances against the components of income.

At Steps 2 and 3 of the Income Tax calculation (ITA 2007 s. 23), the taxpayer
deducts reliefs and allowances "in the way which will result in the greatest
reduction in the taxpayer's liability to income tax" (s. 25(2)). From
2027-28, the taxpayer deducts them from income other than property, savings
and dividend income first (s. 25(3A), inserted by Finance Act 2026 s. 6(6)
with effect from 2027-28 under s. 6(8)), and then chooses between property,
savings and dividend income (s. 25(2)). Before 2027-28, the taxpayer chooses
between non-savings, savings and dividend income (s. 25(2)). In those years
Parliament taxes property income as non-savings income at the same rates, so
the model takes the deductions off the rest of non-savings income first, as
it always has.

The model deducts trade loss relief against general income at Step 2 and the
amounts in ``allowances`` (the personal and blind person's allowances, gifts
of investments to charity, covenanted payments, other deductions and pension
relief). The search shares their sum between the components. Each part of it
can come off any component, and the tax depends only on how much comes off
each, so the search shares out the sum.

Pension relief is the exception. The model takes employee contributions as a
net pay arrangement, which the employer deducts from employment income (FA
2004 s. 193(2)), and personal contributions as relief at source, under which
the payer keeps basic rate tax on the contribution (s. 192(1)). On a claim,
Parliament raises the basic and higher rate limits by the contribution where
higher or additional rate tax is chargeable (s. 192(4)), and for a Scottish
taxpayer the Scottish basic rate limit and the Scottish rate limits above it
where a Scottish rate above the Scottish basic rate is chargeable
(s. 192(4A)). Deducting the contribution from the bottom of non-savings
income moves every slice of income down against those limits, as raising
them does. Neither arrangement gives a Step 2 deduction the taxpayer can set
against savings or dividends, so the search holds
``min(pension relief, non-savings income)`` on non-savings income and shares
only the rest.

How the search finds the least tax
----------------------------------
Three components share what s. 25(3A) leaves: the first (non-savings income
before 2027-28, property income after), savings and dividends. Write ``x``
for the first component left after deductions, ``w`` for ``x`` plus the
savings left, and ``T - w`` for the dividends left, where ``T``, the three
together after deductions, stays the same in every share. Savings sit above
non-savings income and dividends above savings (ss. 16 and 16A), so with
``q`` the non-savings income below the savings (``x``, or property plus the
other non-savings income left before it from 2027-28):

- tax on the first component changes slope where ``x`` crosses a rate limit;
- the starting rate for savings (s. 12) and the savings nil rate (s. 12A)
  cover the savings from ``q`` up to ``max(q, L) + A``, where ``L`` stands
  for the starting rate limit and ``A`` for the personal savings allowance.
  That changes slope where ``q`` reaches ``L``, where ``max(q, L) + A``
  crosses a rate limit, and where ``w`` reaches the top of that band:
  ``w - x = A`` above ``L``, ``w`` constant below it;
- the rest of the savings change slope where their top, ``w``, crosses a rate
  limit;
- the dividend nil rate (s. 13A) covers the lowest dividend allowance ``DA``
  of the dividends, so their tax changes slope where ``w + DA`` crosses a
  dividend rate limit or reaches ``T``.

The limits on the components add ``x = 0`` and ``x`` equal to the whole first
component, savings left from nil to all (``w - x = 0`` and ``w - x`` equal to
the savings), and dividends left from nil to all (``w = T`` and ``w = T``
less the dividends). So the Step 5 tax runs continuous and linear on each
piece of the feasible polygon that vertical lines (``x`` constant),
horizontal lines (``w`` constant) and diagonal lines (``w - x`` constant)
cut. A linear function takes its least value on a polygon at a corner, so the
least tax lies where two of these lines cross. ``_candidates`` lists every
such crossing, and the search evaluates the tax at all of them for all people
at once.

Before 2027-28, a reform can add an exclusion ``E`` from earned income. With
property income ``P``, the savings then sit on ``q = x`` up to ``x = P``, on
``q = P`` up to ``x = P + E``, and on ``q = x - E`` beyond. ``_candidates``
adds the lines of each of those pieces: the two boundaries, the limits moved
by ``P`` and ``E``, and the diagonal lines that a fixed ``q = P`` gives.

That argument needs the starting rate limit at or below the basic rate limit,
a phase-out of one pound of starting rate band for each pound of non-savings
income (s. 12) and a first UK rate threshold at nil, as in every year
modelled. A reform that sets that threshold above nil leaves savings below it
untaxed and adds lines on which ``x + w`` stays constant, which the search
doesn't list, so the search can then miss the least tax. On 6,520 synthetic
people with that threshold at £2,000, a 101 x 101 grid found less tax than
the search for 32 in 2026-27 (by up to £181.70) and 38 in 2027-28 (by up to
£214.75). The fast path sends everyone to the search under such a reform.

The Marriage Allowance adds one term. Parliament gives it as a tax reduction
at Step 6 (ss. 23 and 55B(1)), and only to a person liable at the rates it
lists (s. 55B(2)(b)), with dividends tested as if the dividend nil rate were
omitted (s. 55B(2)(ba)). The share decides those rates, so the share can win
or lose the reduction. Section 25(2) asks for the greatest reduction in
liability, and s. 23 fixes liability at Step 7, so the search compares ``f``:
the Step 5 tax less the reduction ``M`` where the share meets the rate test.
No share moves the other Step 6 reductions ``R``, and all the reductions
together leave ``max(0, f - R)`` of Step 5 tax, so the share with the least
``f`` leaves the least liability. Where ``R`` takes the tax to nil under more
than one share, the search can still move the share for a saving no one
receives.

Where all the income left after the deductions exceeds the basic rate limit,
the rate test allows no dividends left, so the share lies on the line where
``w`` equals the Step 3 income, and the savings nil rate must cover any
savings above the limit. Under current rates that holds only with savings
left within the savings allowance (``w - x`` at most ``A``); a reform that
sets the basic rate limit below the starting rate limit plus the allowance
can make it hold all along that line. Otherwise only the limit on
non-savings income binds. So ``_candidates`` adds one vertical line, at that
limit, and the test's other edges already lie among the lines listed. On
each side of those edges ``f`` differs from the Step 5 tax by a constant, so
the least ``f`` again lies where two lines cross.

The rate test lets income reach each limit (s. 10(2)), and a share that leaves
non-savings income at a limit can be the only one that meets it. Incomes come
in whole pence, and the model holds them in float32, which carries a net income
under £65,536 to within a fifth of a penny. So the test counts income within
half a penny above a limit as at the limit (``RATE_TEST_SLACK``).

The model stores the deductions from savings and dividends in float32 too. The
search finds the least ``f`` in float64, then ``_stored_share`` rounds that
share's deductions to float32, down or up, and takes the rounding with the
least ``f`` that leaves the first component within its bounds. The search
moves a person only where that stored share leaves less ``f`` than the old
order as stored. ``share_meets_marriage_allowance_rate_test`` gives the
model's answer to the rate test from the stored deductions through the same
arithmetic, so the model applies the reduction wherever the search counted on
it, and nowhere else.

The search keeps the order non-savings, savings, dividends unless another
share lowers ``f``, so it never leaves more liability than that order.

Who cannot gain
---------------
Most people cannot gain from another share, and ``_old_order_is_least`` finds
them without a search, so the search runs only on the rest.

1. One share: with no deduction left for the taxpayer to place under
   s. 25(2), or no income left after the deductions, only one share exists,
   and the old order takes it.

Tests 2 and 3 need the rates to rise with income in every scale, as Parliament
has set them, and the old order to set every shared deduction against the
first component, so that any other share leaves more of it (``x`` rises).

2. Nothing taxed above the first component: if the old order leaves no savings
   and no dividends charged above the nil rates, any other share charges them
   at least nil, and tax on the first component rises with ``x``. So no share
   gives less tax.
3. Rates: moving a pound of the deductions to savings or dividends raises
   ``x`` by that pound and ``w`` by at most a pound. Write ``rho_n`` for the
   rate on the first component just above where the old order leaves it,
   ``rho_s`` for the savings rate just above the top of the savings, and
   ``sigma_s`` and ``sigma_v`` for the highest savings and dividend rates the
   moved pounds can reach above the nil rates. The tax then rises by at least
   ``(rho_n - sigma_s) dx + (rho_s - sigma_v) dw`` for any move with
   ``0 <= dw <= dx``, or ``rho_n dx - sigma_v dw`` where the old order charges
   no savings above the nil rates. Where that bound never falls below zero,
   the old order gives the least tax. The top of the nil rates moves by at
   most ``dx``, because the starting rate band shrinks by at most a pound for
   each pound of non-savings income (s. 12) and the savings and dividend nil
   rates cover fixed amounts (ss. 12A and 13A). Before 2027-28 the test also
   needs no property income or no exclusion from earned income that the
   search reads: with property income, such an exclusion breaks the rising
   rate on the first component.

Where any test holds, the search would keep the old order too, since it
changes the share only for a saving above ``TOLERANCE``. A Marriage Allowance
recipient the old order denies the reduction still goes to the search, unless
even the least non-savings income any share leaves exceeds the limit in the
rate test. So both paths give the same result, and
``test_income_tax_allocation.py`` checks it.
"""

from types import SimpleNamespace

import numpy as np
from policyengine_core import periods

from policyengine_uk.utils.income_tax import first_extended_scottish_threshold
from policyengine_uk.utils.marriage_allowance import (
    marriage_allowance_rate_limits,
    meets_marriage_allowance_rate_test,
)

# A share replaces the order non-savings, savings, dividends only where it
# saves more than this (in pounds), so rounding never moves a deduction.
TOLERANCE = 1e-3
# The search treats shares whose tax differs by less than this (in pounds)
# as equally good.
TIE = 1e-6
# Bound on people times candidates evaluated at once, to bound memory.
CHUNK = 2_000_000
# The Marriage Allowance rate test counts income within this much (in pounds)
# above a limit as at the limit: half a penny. Incomes come in whole pence, and
# float32 carries a net income under £65,536 to within a fifth of a penny, so
# the slack keeps income at a limit there and income a penny over it outside.
RATE_TEST_SLACK = 0.005
# Added to ``f`` for a float32 rounding that leaves the first component
# outside its bounds, so ``_stored_share`` takes one only where every rounding
# does.
OUT_OF_BOUNDS = 1e9
# The variables on earned_taxable_income_exclusions that the allocation sets
# rather than reads.
ALLOCATED_EXCLUSIONS = (
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_property_income",
    "received_allowances_earned_income",
)
# The search leaves these exclusions out. Parliament gives the Marriage
# Allowance as a tax reduction at Step 6 (s. 55B(1)), not a deduction at Step 3,
# so the search weighs the reduction and takes no exclusion for it. The baseline
# list leaves the allowance out too, so this matters only under a reform that
# lists it.
IGNORED_EXCLUSIONS = ("marriage_allowance",)


def _schedule(scale, gift, first=1, last=3):
    """Thresholds and rate steps of a marginal-rate scale, with the limits from
    index ``first`` up to ``last`` raised by the grossed-up Gift Aid gift (ITA
    2007 s. 414(2)(b)), as calc_income_tax_with_gift_aid applies it."""
    thresholds, steps, previous = [], [], 0
    stop = min(last, len(scale.thresholds))
    for index, (threshold, rate) in enumerate(zip(scale.thresholds, scale.rates)):
        thresholds.append(threshold + (gift if first <= index < stop else 0))
        steps.append(rate - previous)
        previous = rate
    return thresholds, steps


def _tax(income, schedule):
    thresholds, steps = schedule
    return sum(step * np.maximum(income - t, 0) for t, step in zip(thresholds, steps))


def _inputs(person, period, income_tax):
    """The amounts the tax on a share depends on, one float64 value a person."""

    def values(variable):
        return np.asarray(person(variable, period), dtype=np.float64)

    exclusions = [
        variable
        for variable in income_tax.earned_taxable_income_exclusions
        if variable not in ALLOCATED_EXCLUSIONS + IGNORED_EXCLUSIONS
    ]
    savings = values("taxable_savings_interest_income")
    limits = marriage_allowance_rate_limits(person, period, income_tax)
    return dict(
        savings=savings,
        dividends=values("taxable_dividend_income"),
        relief=values("trade_loss_relief_against_general_income"),
        net_income=values("net_income"),
        property=values("taxable_property_income"),
        allowances=values("allowances"),
        pension=values("pension_contributions_relief"),
        earned_exclusions=sum(
            (values(variable) for variable in exclusions), np.zeros_like(savings)
        ),
        gift=values("gift_aid_grossed_up"),
        scottish=np.asarray(person("pays_scottish_income_tax", period)),
        savings_allowance=values("savings_allowance"),
        marriage_allowance_reduction=values("marriage_allowance_reduction_at_stake"),
        rate_test_non_savings_limit=np.asarray(limits.non_savings, dtype=np.float64),
        rate_test_savings_allowance=np.broadcast_to(
            np.asarray(limits.savings_allowance, dtype=np.float64), savings.shape
        ),
    )


def _context(person, period, parameters):
    """Everything the tax on a share depends on, as float64 columns."""
    income_tax = parameters(period).gov.hmrc.income_tax
    return _build(_inputs(person, periods.period(period), income_tax), income_tax)


def _build(inputs, income_tax):
    """The context for the people in ``inputs`` (see ``_inputs``)."""
    rates = income_tax.rates
    columns = {name: values[:, None] for name, values in inputs.items()}
    savings = np.maximum(0, columns["savings"])
    dividends = np.maximum(0, columns["dividends"])
    relief = columns["relief"]
    # net_income, not its components, so the search follows a supplied adjusted
    # net income or a reform that sets net income, as the default order does.
    non_savings = np.maximum(0, columns["net_income"] + relief - savings - dividends)
    # Net pay comes off employment income (FA 2004 s. 193(2)); for relief at
    # source Parliament raises the basic and higher rate limits instead
    # (s. 192(4); for a Scottish taxpayer, the Scottish basic rate limit and
    # those above it, s. 192(4A)), which deducting the relief from the bottom
    # of non-savings income matches. So pension relief stays on non-savings
    # income as far as it reaches; the search shares the rest.
    # allowances includes the relief, so it never holds more than that.
    pension = np.clip(
        columns.get("pension", np.zeros_like(relief)),
        0,
        np.minimum(np.maximum(0, columns["allowances"]), non_savings),
    )
    non_savings = non_savings - pension
    property_income = np.minimum(np.maximum(0, columns["property"]), non_savings)
    deductions = relief + columns["allowances"] - pension
    used = np.minimum(deductions, non_savings + savings + dividends)
    gift = columns["gift"]
    uk_thresholds = rates.uk.thresholds
    savings_rates = rates.savings
    property_rates = rates.property
    c = SimpleNamespace(
        other_first=bool(income_tax.reliefs.other_income_first),
        savings=savings,
        dividends=dividends,
        non_savings=non_savings,
        property=property_income,
        used=used,
        earned_exclusions=columns["earned_exclusions"],
        gift=gift,
        scottish=columns["scottish"],
        uk=_schedule(rates.uk, gift),
        scotland=_schedule(
            rates.scotland.rates,
            gift,
            first_extended_scottish_threshold(rates.scotland.rates),
            len(rates.scotland.rates.thresholds),
        ),
        dividend_scale=_schedule(rates.dividends, gift),
        bands=(
            uk_thresholds[0],
            uk_thresholds[1] + gift,
            uk_thresholds[2] + gift,
        ),
        savings_rates=savings_rates,
        property_rates=property_rates,
        starting_limit=rates.savings_starter_rate.allowance,
        phase_out=rates.savings_starter_rate.phase_out,
        savings_allowance=columns["savings_allowance"],
        dividend_allowance=income_tax.allowances.dividend_allowance,
    )
    if c.other_first:
        # s. 25(3A): other non-savings income takes the deductions first.
        other = non_savings - property_income
        to_other = np.minimum(other, used)
        c.other_left = other - to_other
        c.first = property_income
        c.shared = used - to_other
        # The savings stack on the other non-savings income left, as earned
        # taxable income has it, plus the property income left.
        c.offset = np.maximum(0, c.other_left - c.earned_exclusions)
    else:
        c.first = non_savings
        c.shared = used
        c.offset = np.zeros_like(savings)
    c.step_3_income = c.first + savings + dividends - c.shared
    # The Marriage Allowance rate test. These columns stay nil for a caller
    # that passes no recipients.
    zero = np.zeros_like(savings)
    c.marriage_allowance_reduction = columns.get("marriage_allowance_reduction", zero)
    c.rate_test_savings_allowance = columns.get("rate_test_savings_allowance", zero)
    non_savings_limit = columns.get("rate_test_non_savings_limit", zero)
    basic_rate_limit = c.bands[1]
    # The rate test reads all the non-savings income, so it adds what s. 25(3A)
    # leaves below the first component.
    c.non_savings_below_first = c.other_left if c.other_first else zero
    # The statutory limit on non-savings income, where the tax changes slope.
    c.rate_test_non_savings_limit = non_savings_limit
    # The limits the test applies. Income can reach a limit (s. 10(2)), and a
    # share that leaves non-savings income at one can be the only share that
    # meets the test, so the test counts income within RATE_TEST_SLACK above a
    # limit as at it.
    c.rate_test_limits = SimpleNamespace(
        non_savings=non_savings_limit + RATE_TEST_SLACK,
        basic_rate=basic_rate_limit + RATE_TEST_SLACK,
        starting=c.starting_limit,
        savings_allowance=c.rate_test_savings_allowance + TIE,
    )
    return c


def _non_savings_tax(c, income):
    return np.where(c.scottish, _tax(income, c.scotland), _tax(income, c.uk))


def _split(c, x):
    """The other non-savings income and the property income left, and the
    earned taxable income, where the share leaves ``x`` of the first
    component."""
    if c.other_first:
        other, property_left = c.other_left, x
    else:
        property_left = np.minimum(x, c.property)
        other = x - property_left
    return other, property_left, np.maximum(0, other - c.earned_exclusions)


def _savings_band(c, below, s):
    """The top of the savings and the top of the part of them that the
    starting rate (s. 12) and the savings nil rate (s. 12A) cover, for ``s``
    of savings above ``below`` of non-savings income."""
    low, basic_limit, _ = c.bands
    top = below + s
    in_basic_band = np.clip(top, low, basic_limit) - np.clip(below, low, basic_limit)
    starting = np.clip(
        np.minimum(in_basic_band, s),
        0,
        np.maximum(0, c.starting_limit - np.maximum(0, below * c.phase_out)),
    )
    return top, below + np.minimum(s, starting + c.savings_allowance)


def step_5_tax(c, x, s, v):
    """Step 5 Income Tax on the share leaving ``x`` of the first component,
    ``s`` of savings and ``v`` of dividends, as the model's
    income_tax_pre_charges computes it from the variables the share sets."""
    other, property_left, earned = _split(c, x)
    earned_tax = _non_savings_tax(c, earned)
    if c.other_first:
        # property_income_tax.formula_2027: Scottish rates in Scotland,
        # property rates on the UK bands elsewhere.
        rates = c.property_rates
        _, basic_upper, higher_upper = c.bands
        in_basic = np.minimum(property_left, np.maximum(0, basic_upper - other))
        higher_space = np.maximum(0, higher_upper - np.maximum(other, basic_upper))
        in_higher = np.minimum(np.maximum(0, property_left - in_basic), higher_space)
        in_additional = np.maximum(0, property_left - in_basic - in_higher)
        ruk = (
            rates.basic * in_basic
            + rates.higher * in_higher
            + rates.additional * in_additional
        )
        scottish = _tax(other + property_left, c.scotland) - _tax(other, c.scotland)
        property_tax = np.where(c.scottish, scottish, ruk)
    else:
        property_tax = _non_savings_tax(c, other + property_left) - (
            _non_savings_tax(c, other)
        )
    # Savings and dividends sit on non_savings_taxable_income.
    top, start = _savings_band(c, earned + property_left, s)
    low, basic_limit, higher_limit = c.bands
    rates = c.savings_rates
    savings_tax = (
        rates.basic
        * np.maximum(
            0,
            np.clip(top, low, basic_limit) - np.clip(start, low, basic_limit),
        )
        + rates.higher
        * np.maximum(
            0,
            np.clip(top, basic_limit, higher_limit)
            - np.clip(start, basic_limit, higher_limit),
        )
        + rates.additional
        * np.maximum(0, np.maximum(top, higher_limit) - np.maximum(start, higher_limit))
    )
    nil_rate = np.minimum(c.dividend_allowance, v)
    dividend_tax = np.maximum(
        0,
        _tax(top + v, c.dividend_scale) - _tax(top + nil_rate, c.dividend_scale),
    )
    return earned_tax + property_tax + savings_tax + dividend_tax


def _meets_rate_test(c, x, s, v):
    """Whether the share meets the Marriage Allowance rate test, counting
    income within ``RATE_TEST_SLACK`` above a limit as at the limit. ``TIE``
    covers float64 rounding of a share that leaves savings at the savings
    allowance or no dividends."""
    return meets_marriage_allowance_rate_test(
        x + c.non_savings_below_first,
        s,
        np.maximum(0, v - TIE),
        c.rate_test_limits,
    )


def tax_after_marriage_allowance(c, x, s, v):
    """The Step 5 tax less the Marriage Allowance reduction the share wins:
    ``f`` in the module docstring."""
    tax = step_5_tax(c, x, s, v)
    if not np.any(c.marriage_allowance_reduction > 0):
        return tax
    return tax - c.marriage_allowance_reduction * _meets_rate_test(c, x, s, v)


def _candidates(c):
    """The points where two of the lines the module docstring lists cross."""
    zero = np.zeros_like(c.savings)
    low, basic_limit, higher_limit = c.bands
    band_limits = (basic_limit, higher_limit)
    allowance = c.savings_allowance
    dividend_allowance = c.dividend_allowance
    if c.other_first:
        first_limits = [
            np.where(c.scottish, scottish, ruk) - c.other_left
            for scottish, ruk in _paired_limits(
                c.scotland[0], [low, basic_limit, higher_limit], zero
            )
        ]
    else:
        first_limits = [
            np.where(c.scottish, scottish, ruk)
            for scottish, ruk in _paired_limits(c.scotland[0], c.uk[0], zero)
        ]
    total = c.step_3_income
    vertical = [zero, c.first] + first_limits
    horizontal = [total - c.dividends, total, total - dividend_allowance]
    diagonal = [zero, c.savings, allowance]
    # The non-savings income below the savings is x plus each offset.
    offsets = [c.offset]
    if not c.other_first and np.any(c.earned_exclusions > 0):
        # Before 2027-28 an exclusion E from earned income splits x into three
        # pieces: q = x up to the property income P, q = P up to P + E, and
        # q = x - E beyond. Tax on the property income changes slope where x
        # or x - P crosses a limit, and tax on earned income where x - P - E
        # does. With q fixed at P, the savings band and dividend lines run
        # diagonal, and the top of the dividends moves with x.
        property_income, exclusion = c.property, c.earned_exclusions
        offsets.append(-exclusion)
        vertical += [property_income, property_income + exclusion]
        vertical += [property_income + limit for limit in first_limits]
        vertical += [property_income + exclusion + limit for limit in first_limits]
        vertical += [property_income + total - limit for limit in c.dividend_scale[0]]
        starting = np.maximum(0, c.starting_limit - property_income * c.phase_out)
        diagonal += [limit - property_income for limit in band_limits]
        diagonal += [starting + allowance]
        diagonal += [
            limit - dividend_allowance - property_income
            for limit in c.dividend_scale[0]
        ]
    for offset in offsets:
        vertical += [c.starting_limit - offset + zero]
        vertical += [limit - allowance - offset for limit in band_limits]
        horizontal += [c.starting_limit + allowance - offset]
        horizontal += [limit - offset + zero for limit in band_limits]
        horizontal += [
            limit - dividend_allowance - offset + zero for limit in c.dividend_scale[0]
        ]
    if np.any(c.marriage_allowance_reduction > 0):
        # The Marriage Allowance rate test's limit on non-savings income. Its
        # other edges, no dividends left (w = total) and savings left at the
        # savings allowance (w - x = allowance), already have lines. Everyone
        # else repeats the line x = 0, so the search finds them the same share
        # whoever else it searches.
        recipient = c.marriage_allowance_reduction > 0
        # The statutory limit, and the limit with the slack the test allows.
        vertical += [
            np.where(recipient, limit - c.non_savings_below_first, zero)
            for limit in (
                c.rate_test_non_savings_limit,
                c.rate_test_limits.non_savings,
            )
        ]
    xs = np.concatenate([np.broadcast_to(v, zero.shape) for v in vertical], axis=1)
    ws = np.concatenate([np.broadcast_to(h, zero.shape) for h in horizontal], axis=1)
    ds = np.concatenate([np.broadcast_to(d, zero.shape) for d in diagonal], axis=1)
    n = len(zero)
    x = np.concatenate(
        [
            np.repeat(xs, ws.shape[1], axis=1),
            np.repeat(xs, ds.shape[1], axis=1),
            (ws[:, :, None] - ds[:, None, :]).reshape(n, -1),
        ],
        axis=1,
    )
    w = np.concatenate(
        [
            np.tile(ws, xs.shape[1]),
            (xs[:, :, None] + ds[:, None, :]).reshape(n, -1),
            np.repeat(ws, ds.shape[1], axis=1),
        ],
        axis=1,
    )
    return x, w


def _paired_limits(scottish, other, zero):
    """Pair two lists of limits by position, padding the shorter with +inf."""
    length = max(len(scottish), len(other))
    pad = zero + np.inf
    return [
        (
            scottish[i] + zero if i < len(scottish) else pad,
            other[i] + zero if i < len(other) else pad,
        )
        for i in range(length)
    ]


def _shares(c, x, w):
    """Project candidate points onto the feasible polygon and split them into
    the first component, savings and dividends left."""
    total = c.step_3_income
    x = np.clip(
        x, np.maximum(0, total - c.savings - c.dividends), np.minimum(c.first, total)
    )
    w = np.clip(w, np.maximum(x, total - c.dividends), np.minimum(x + c.savings, total))
    return x, w - x, total - w


def _least_tax_share(c):
    """The candidate share with the least ``f``, per person. Of shares within
    TIE of it, the one setting most against the first component, then most
    against savings: the nearest the least tax allows to the order non-savings,
    savings, dividends."""
    x, w = _candidates(c)
    n, count = x.shape
    tax = np.empty((n, count))
    width = max(1, CHUNK // max(n, 1))
    for start in range(0, count, width):
        part = slice(start, start + width)
        x[:, part], w[:, part], _ = _shares(c, x[:, part], w[:, part])
        tax[:, part] = tax_after_marriage_allowance(
            c, x[:, part], w[:, part], c.step_3_income - x[:, part] - w[:, part]
        )
    near = tax <= tax.min(axis=1, keepdims=True) + TIE
    x_near = np.where(near, x, np.inf)
    near &= x_near <= x_near.min(axis=1, keepdims=True) + TIE
    index = np.argmin(np.where(near, w, np.inf), axis=1)[:, None]
    x, s = (np.take_along_axis(part, index, axis=1) for part in (x, w))
    return x, s, c.step_3_income - x - s


def default_order_deductions(person, period):
    """The deductions from non-savings, savings and dividend income in the
    order non-savings, savings, dividends, computed as the model always has."""
    return old_order(
        person("allowances", period),
        person("taxable_savings_interest_income", period),
        person("taxable_dividend_income", period),
        person("net_income", period),
        person("trade_loss_relief_against_general_income", period),
        person("net_income_before_trade_loss_relief", period),
    )


def old_order(
    allowances, savings, dividends, net_income, relief, net_income_before_relief
):
    """``default_order_deductions`` from the amounts it reads."""
    non_savings = net_income - savings - dividends
    relief_left = np.maximum(
        0, relief - np.maximum(0, net_income_before_relief - savings - dividends)
    )
    to_non_savings = np.where(
        non_savings < allowances, np.maximum(0, non_savings), allowances
    )
    left = allowances + relief_left - to_non_savings
    to_savings = np.where(savings < left, np.maximum(0, savings), np.maximum(0, left))
    left = left - to_savings
    to_dividends = np.where(
        dividends < left, np.maximum(0, dividends), np.maximum(0, left)
    )
    return SimpleNamespace(
        earned=to_non_savings,
        savings=to_savings,
        dividends=to_dividends,
        relief_against_savings_and_dividends=relief_left,
    )


def _rate(schedule, income, above=True):
    """The rate ``_tax`` charges on a schedule just above ``income`` (or just
    below it): the sum of the steps passed, whatever order the thresholds
    take once a Gift Aid gift raises some of them."""
    thresholds, steps = schedule
    return sum(
        step * (income >= threshold if above else income > threshold)
        for threshold, step in zip(thresholds, steps)
    )


def _steps(rates):
    """The steps of a basic, higher and additional rate."""
    return [rates.basic, rates.higher - rates.basic, rates.additional - rates.higher]


def _old_order_is_least(c, to_savings, to_dividends):
    """People for whom no share gives less Step 5 tax than the old order, by
    the tests the module docstring sets out. ``to_savings`` and
    ``to_dividends`` are the old order's deductions from savings and
    dividends."""
    in_first = (to_savings == 0) & (to_dividends == 0)
    # Test 1: nothing to share, or nothing left after the deductions, so only
    # one share exists, and the old order takes it.
    nothing_to_share = (in_first & (c.shared <= 0)) | (
        (to_savings == c.savings)
        & (to_dividends == c.dividends)
        & (c.step_3_income <= TIE)
    )
    low, basic_limit, higher_limit = c.bands
    savings_scale = ((low, basic_limit, higher_limit), _steps(c.savings_rates))
    property_scale = ((-np.inf, basic_limit, higher_limit), _steps(c.property_rates))
    scales = (c.uk, c.scotland, c.dividend_scale, savings_scale, property_scale)
    # Rates that rise with income from nil: no step below nil.
    if not (
        all(step >= 0 for _, steps in scales for step in steps)
        and low <= 0
        and c.phase_out >= 0
    ):
        return nothing_to_share
    in_first &= c.shared <= c.first
    x = c.first - c.shared
    other, property_left, earned = _split(c, x)
    top, start = _savings_band(c, earned + property_left, c.savings)
    savings_taxed = top > start
    nil_rated = ~savings_taxed & (c.dividends <= c.dividend_allowance)
    # Test 3. The first component's rate just above x.
    if c.other_first:
        rho_n = np.where(
            c.scottish, _rate(c.scotland, other + x), _rate(property_scale, other + x)
        )
        in_reach = in_first
    else:
        # With no property income, an exclusion from earned income only moves
        # every band position down by its amount.
        position = x - c.earned_exclusions
        rho_n = np.where(c.scottish, _rate(c.scotland, position), _rate(c.uk, position))
        in_reach = in_first & ((c.earned_exclusions == 0) | (c.property == 0))
    # dx <= c.shared and dw <= min(dx, dividends). The top of the nil rates
    # moves up by at most dx and never passes the top of the savings.
    dw = np.minimum(c.shared, c.dividends)
    sigma_s = _rate(savings_scale, np.minimum(start + c.shared, top + dw), above=False)
    rho_s = _rate(savings_scale, top)
    # The dividends end at the top of income, which no share moves.
    sigma_v = np.where(
        c.dividends > c.dividend_allowance,
        _rate(
            c.dividend_scale,
            top + np.minimum(c.dividend_allowance + dw, c.dividends),
            above=False,
        ),
        0,
    )
    rates_hold = np.where(
        savings_taxed,
        (rho_n >= sigma_s) & (rho_n - sigma_s + rho_s - sigma_v >= 0),
        rho_n >= sigma_v,
    )
    return nothing_to_share | (in_first & nil_rated) | (in_reach & rates_hold)


def _marriage_allowance_in_reach(c, to_savings, to_dividends):
    """Recipients the old order (which sets ``to_savings`` and ``to_dividends``
    against savings and dividends) denies the Marriage Allowance reduction,
    where the least non-savings income any share leaves falls within the rate
    test's limit."""
    least_first = np.maximum(0, c.step_3_income - c.savings - c.dividends)
    old_order_meets = _meets_rate_test(c, *_share_left(c, to_savings, to_dividends))
    return (
        (c.marriage_allowance_reduction > 0)
        & ~old_order_meets
        & (least_first + c.non_savings_below_first <= c.rate_test_limits.non_savings)
    )


def _exact_where_the_rate_test_reads(c, s, v):
    """Savings and dividends left, with a recipient's savings at the savings
    allowance, or dividends at nil, set exactly, so that float32 rounding keeps
    them there."""
    recipient = c.marriage_allowance_reduction > 0
    allowance = c.rate_test_savings_allowance
    s = np.where(
        recipient & (np.abs(s - allowance) <= TIE),
        np.minimum(c.savings, allowance),
        s,
    )
    return s, np.where(recipient & (v <= TIE), 0, v)


def _share_left(c, to_savings, to_dividends):
    """The first component, savings and dividends left where the model holds
    ``to_savings`` and ``to_dividends`` as the deductions from savings and
    dividends, and sets the rest of the deductions against the first
    component."""
    s = np.maximum(0, c.savings - to_savings)
    v = np.maximum(0, c.dividends - to_dividends)
    return np.maximum(0, c.step_3_income - s - v), s, v


def _float32(values, toward):
    """``values`` rounded to float32 towards ``toward`` (-inf or +inf), as
    float64. A float32 amount stays as it is."""
    nearest = values.astype(np.float32)
    back = nearest.astype(np.float64)
    past = back < values if toward > 0 else back > values
    stepped = np.nextafter(nearest, np.float32(toward))
    return np.where(past, stepped, nearest).astype(np.float64)


def _stored_share(c, s, v):
    """The share the model can hold in place of the one that leaves ``s`` of
    savings and ``v`` of dividends. The model stores the deductions from
    savings and dividends in float32, so the function rounds each down or up
    to float32 and takes the pair with the least ``f``, among the pairs that
    leave the first component within its bounds. Deductions that are float32
    amounts already stay as they are. Returns the deductions and the first
    component, savings and dividends they leave."""
    s, v = _exact_where_the_rate_test_reads(c, s, v)
    exact_savings = np.clip(c.savings - s, 0, c.savings)
    exact_dividends = np.clip(c.dividends - v, 0, c.dividends)
    highest = np.minimum(c.first, c.step_3_income)
    best = None
    for toward_savings in (-np.inf, np.inf):
        for toward_dividends in (-np.inf, np.inf):
            to_savings = _float32(exact_savings, toward_savings)
            to_dividends = _float32(exact_dividends, toward_dividends)
            first = (
                c.step_3_income
                - (c.savings - to_savings)
                - (c.dividends - to_dividends)
            )
            share = _share_left(c, to_savings, to_dividends)
            tax = tax_after_marriage_allowance(c, *share) + OUT_OF_BOUNDS * (
                (first < -TIE) | (first > highest + TIE)
            )
            option = SimpleNamespace(
                tax=tax,
                to_savings=to_savings,
                to_dividends=to_dividends,
                x=share[0],
                s=share[1],
                v=share[2],
            )
            if best is None:
                best = option
                continue
            better = option.tax < best.tax - TIE
            best = SimpleNamespace(
                **{
                    name: np.where(better, values, vars(best)[name])
                    for name, values in vars(option).items()
                }
            )
    return best


def share_meets_marriage_allowance_rate_test(person, period, parameters):
    """Whether the share the model holds meets the Marriage Allowance rate test
    (ITA 2007 s. 55B(2)(b) and (ba)). The function reads the deductions from
    savings and dividends as the model stores them and works out the income
    they leave in float64, as the search does for the share it stores and for
    the old order. So the model gives the search's own answer."""
    c = _context(person, period, parameters)

    def stored(variable):
        return np.asarray(person(variable, period), dtype=np.float64)[:, None]

    share = _share_left(
        c,
        stored("received_allowances_savings_income"),
        stored("received_allowances_dividend_income"),
    )
    return _meets_rate_test(c, *share)[:, 0]


def allocate_deductions(person, period, parameters):
    """Deductions against savings and dividend income in the share that gives
    the least Income Tax after the Marriage Allowance (ITA 2007 s. 25(2) and
    (3A)). Where no share gives less tax than the order non-savings, savings,
    dividends, the function returns that order's deductions exactly."""
    default = default_order_deductions(person, period)
    income_tax = parameters(period).gov.hmrc.income_tax
    savings, dividends = least_tax_deductions(
        _inputs(person, period, income_tax),
        income_tax,
        default.savings,
        default.dividends,
    )
    return SimpleNamespace(savings=savings, dividends=dividends)


def least_tax_deductions(
    inputs, income_tax, to_savings, to_dividends, search_all=False
):
    """The deductions from savings and dividends: the old order's
    (``to_savings`` and ``to_dividends``) unless another share, as the model
    stores it, saves more than TOLERANCE. The search runs only on people the
    tests in ``_old_order_is_least`` leave and on Marriage Allowance
    recipients whom another share could win the reduction, or on everyone
    with ``search_all``."""
    to_savings = np.asarray(to_savings, dtype=np.float64)
    to_dividends = np.asarray(to_dividends, dtype=np.float64)
    if search_all:
        search = np.ones(len(to_savings), dtype=bool)
    else:
        everyone = _build(inputs, income_tax)
        old_order = to_savings[:, None], to_dividends[:, None]
        search = (
            ~_old_order_is_least(everyone, *old_order)
            | _marriage_allowance_in_reach(everyone, *old_order)
        )[:, 0]
    if not search.any():
        return to_savings, to_dividends
    c = _build({name: values[search] for name, values in inputs.items()}, income_tax)
    _, s, v = _least_tax_share(c)
    # Both sides as the model holds them: the share's deductions rounded to
    # float32, and the old order's as given. The model's answer to the rate
    # test comes from the same arithmetic, so it gives the reduction exactly
    # where this comparison counts it.
    stored = _stored_share(c, s, v)
    old_order = _share_left(
        c, to_savings[search][:, None], to_dividends[search][:, None]
    )
    old_order_tax = tax_after_marriage_allowance(c, *old_order)
    lower = (stored.tax < old_order_tax - TOLERANCE)[:, 0]
    moved = np.flatnonzero(search)[lower]
    to_savings, to_dividends = to_savings.copy(), to_dividends.copy()
    to_savings[moved] = stored.to_savings[lower, 0]
    to_dividends[moved] = stored.to_dividends[lower, 0]
    return to_savings, to_dividends


def _old_order_non_savings_left(person, period):
    """Non-savings income left under the old order: net income less savings,
    dividends and allowances, as the model has always computed it."""
    savings = np.maximum(0, person("taxable_savings_interest_income", period))
    dividends = np.maximum(0, person("taxable_dividend_income", period))
    return np.maximum(
        0,
        person("net_income", period)
        - savings
        - dividends
        - person("allowances", period),
    )


def non_savings_deductions(person, period):
    """Allowances against non-savings income beyond trade loss relief, the
    relief set against savings and dividends, and the non-savings income left
    after the deductions, once received_allowances_savings_income and
    received_allowances_dividend_income have taken their share.

    The relief comes off non-savings income first, as far as the share sets
    anything against it, then the allowances. Where the share keeps the order
    non-savings, savings, dividends, the function returns that order's
    amounts exactly. Elsewhere it takes the non-savings income left from the
    share's own arithmetic, in float64, so float32 rounding in a sum of
    net income and the relief added back leaves no residue above nil beyond
    the float32 rounding of the moved share, under a penny.
    """
    default = default_order_deductions(person, period)
    to_savings = person("received_allowances_savings_income", period)
    to_dividends = person("received_allowances_dividend_income", period)
    moved = (to_savings != default.savings) | (to_dividends != default.dividends)
    savings = np.maximum(0, person("taxable_savings_interest_income", period))
    dividends = np.maximum(0, person("taxable_dividend_income", period))
    relief = person("trade_loss_relief_against_general_income", period).astype(
        np.float64
    )
    net_income = person("net_income", period)
    allowances = person("allowances", period)
    non_savings = np.maximum(0, net_income + relief - savings - dividends)
    used = np.minimum(relief + allowances, non_savings + savings + dividends)
    to_non_savings = used - to_savings - to_dividends
    default_left = _old_order_non_savings_left(person, period)
    return SimpleNamespace(
        earned=np.where(moved, np.maximum(0, to_non_savings - relief), default.earned),
        relief_against_savings_and_dividends=np.where(
            moved,
            np.maximum(0, relief - to_non_savings),
            default.relief_against_savings_and_dividends,
        ),
        non_savings_left=np.where(
            moved, np.maximum(0, non_savings - to_non_savings), default_left
        ),
    )
