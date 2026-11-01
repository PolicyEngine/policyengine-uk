"""Set Income Tax reliefs and allowances against the components of income.

At Steps 2 and 3 of the Income Tax calculation (ITA 2007 s. 23), s. 25(2)
deducts reliefs and allowances "in the way which will result in the greatest
reduction in the taxpayer's liability to income tax". From 2027-28, s. 25(3A)
(Finance Act 2026 s. 6(6) and (8)) deducts them from income other than
property, savings and dividend income first, and s. 25(2) then chooses between
property, savings and dividend income. Before 2027-28, s. 25(2) chooses between
non-savings, savings and dividend income. Property income is non-savings income
taxed at the same rates in those years, so the deductions come off the rest of
non-savings income first, as they always have in the model.

The model deducts trade loss relief against general income at Step 2 and the
amounts in ``allowances`` (the personal and blind person's allowances, gifts of
investments to charity, covenanted payments, other deductions and pension
relief). Together they are one sum to share between the components. Each part
of it can come off any component, and the tax depends only on how much comes
off each, so the search shares out the sum.

How the search finds the least tax
----------------------------------
Three components share what s. 25(3A) leaves: the first (non-savings income
before 2027-28, property income after), savings and dividends. Write ``x`` for
the first component left after deductions, ``w`` for ``x`` plus the savings
left, and ``T`` for the three together after deductions, which the sharing
does not change. The dividends left are ``T - w``. Savings sit above
non-savings income and dividends above savings (ss. 16 and 16A), so with ``q``
the non-savings income below the savings (``x``, or property plus the other
non-savings income left before it from 2027-28):

- tax on the first component changes slope where ``x`` crosses a rate limit;
- the starting rate for savings (s. 12) and the savings nil rate (s. 12A) cover
  the savings from ``q`` up to ``max(q, L) + A``, where ``L`` is the starting
  rate limit and ``A`` the personal savings allowance. That changes slope where
  ``q`` reaches ``L``, where ``max(q, L) + A`` crosses a rate limit, and where
  ``w`` reaches the top of that band: ``w - x = A`` above ``L``, ``w`` constant
  below it;
- the rest of the savings change slope where their top, ``w``, crosses a rate
  limit;
- the dividend nil rate (s. 13A) covers the lowest dividend allowance ``DA`` of
  the dividends, so their tax changes slope where ``w + DA`` crosses a dividend
  rate limit or reaches ``T``.

The limits on the components add ``x = 0`` and ``x`` equal to the whole first
component, savings left from nil to all (``w - x = 0`` and ``w - x`` equal to
the savings), and dividends left from nil to all (``w = T`` and ``w = T`` less
the dividends). So the Step 5 tax is continuous and linear on each piece of the
feasible polygon cut out by vertical lines (``x`` constant), horizontal lines
(``w`` constant) and diagonal lines (``w - x`` constant). A linear function
takes its least value on a polygon at a corner, so the least tax is at a point
where two of these lines cross. ``_candidates`` lists every such crossing, and
the search evaluates the tax at all of them for all people at once.

That argument needs the starting rate limit at or below the basic rate limit
and a phase-out of one pound of starting rate band for each pound of
non-savings income (s. 12), as in every year modelled. Before 2027-28 it also
needs no Marriage Allowance: the model subtracts that allowance from earned
income (#1947) rather than giving the s. 55B tax reduction, which moves the
savings and dividends down by up to that amount. The search still evaluates
every candidate with the full tax, so with Marriage Allowance it takes the best
of them. In every case it keeps the order non-savings, savings, dividends
unless another share gives less tax, so it never charges more than that order.

Who cannot gain
---------------
Most people cannot gain from another share, and ``_old_order_is_least`` finds
them without a search, so the search runs only on the rest.

1. One share: with no deduction left for s. 25(2) to place, or no income left
   after the deductions, only one share exists, and the old order takes it.

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
   no savings above the nil rates. Where that is never negative, the old order
   gives the least tax. The top of the nil rates moves by at most ``dx``,
   because the starting rate band shrinks by at most a pound for each pound of
   non-savings income (s. 12) and the savings and dividend nil rates cover
   fixed amounts (ss. 12A and 13A). Before 2027-28 the test also needs no
   Marriage Allowance or no property income: with property income, the
   model's Marriage Allowance breaks the rising rate on the first component.

Where any test holds, the search would keep the old order too, since it
changes the share only for a saving above ``TOLERANCE``. So the result is the
same, and ``test_income_tax_allocation.py`` checks that it is.
"""

from types import SimpleNamespace

import numpy as np

from policyengine_uk.utils.income_tax import first_extended_scottish_threshold

# A share replaces the order non-savings, savings, dividends only where it
# saves more than this (in pounds), so rounding never moves a deduction.
TOLERANCE = 1e-3
# Shares whose tax differs by less than this (in pounds) are equally good.
TIE = 1e-6
# Bound on people times candidates evaluated at once, to bound memory.
CHUNK = 2_000_000
# The variables on earned_taxable_income_exclusions that the allocation sets
# rather than reads.
ALLOCATED_EXCLUSIONS = (
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_property_income",
    "received_allowances_earned_income",
)


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
        if variable not in ALLOCATED_EXCLUSIONS
    ]
    savings = values("taxable_savings_interest_income")
    return dict(
        savings=savings,
        dividends=values("taxable_dividend_income"),
        relief=values("trade_loss_relief_against_general_income"),
        net_income=values("net_income"),
        property=values("taxable_property_income"),
        allowances=values("allowances"),
        earned_exclusions=sum(
            (values(variable) for variable in exclusions), np.zeros_like(savings)
        ),
        gift=values("gift_aid_grossed_up"),
        scottish=np.asarray(person("pays_scottish_income_tax", period)),
        savings_allowance=values("savings_allowance"),
    )


def _context(person, period, parameters):
    """Everything the tax on a share depends on, as float64 columns."""
    income_tax = parameters(period).gov.hmrc.income_tax
    return _build(_inputs(person, period, income_tax), income_tax)


def _build(inputs, income_tax):
    """The context for the people in ``inputs`` (see ``_inputs``)."""
    rates = income_tax.rates
    columns = {name: values[:, None] for name, values in inputs.items()}
    savings = np.maximum(0, columns["savings"])
    dividends = np.maximum(0, columns["dividends"])
    relief = columns["relief"]
    # net_income, not its components, so a supplied adjusted net income or a
    # reform that sets net income is followed, as the default order does.
    non_savings = np.maximum(0, columns["net_income"] + relief - savings - dividends)
    property_income = np.minimum(np.maximum(0, columns["property"]), non_savings)
    deductions = relief + columns["allowances"]
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
        uk_rates=list(rates.uk.rates),
        scotland=_schedule(
            rates.scotland.rates,
            gift,
            first_extended_scottish_threshold(rates.scotland.rates),
            len(rates.scotland.rates.thresholds),
        ),
        scotland_rates=list(rates.scotland.rates.rates),
        dividend_scale=_schedule(rates.dividends, gift),
        dividend_rates=list(rates.dividends.rates),
        bands=(
            uk_thresholds[0],
            uk_thresholds[1] + gift,
            uk_thresholds[2] + gift,
        ),
        savings_rates=savings_rates,
        savings_rate_list=[
            savings_rates.basic,
            savings_rates.higher,
            savings_rates.additional,
        ],
        property_rates=property_rates,
        property_rate_list=[
            property_rates.basic,
            property_rates.higher,
            property_rates.additional,
        ],
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


def _candidates(c):
    """The points where two of the lines the module docstring lists cross."""
    zero = np.zeros_like(c.savings)
    offset = c.offset
    low, basic_limit, higher_limit = c.bands
    allowance = c.savings_allowance
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
    vertical = [zero, c.first, c.starting_limit - offset + zero]
    vertical += [limit - allowance - offset for limit in (basic_limit, higher_limit)]
    vertical += first_limits
    total = c.step_3_income
    horizontal = [
        total - c.dividends,
        total,
        total - c.dividend_allowance,
        c.starting_limit + allowance - offset,
        basic_limit - offset,
        higher_limit - offset,
    ]
    horizontal += [
        limit - c.dividend_allowance - offset + zero for limit in c.dividend_scale[0]
    ]
    diagonal = [zero, c.savings, allowance]
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
    """The candidate share with the least Step 5 tax, per person. Of shares
    within TIE of it, the one setting most against the first component, then
    most against savings: the nearest the least tax allows to the order
    non-savings, savings, dividends."""
    x, w = _candidates(c)
    n, count = x.shape
    tax = np.empty((n, count))
    width = max(1, CHUNK // max(n, 1))
    for start in range(0, count, width):
        part = slice(start, start + width)
        x[:, part], w[:, part], _ = _shares(c, x[:, part], w[:, part])
        tax[:, part] = step_5_tax(
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


def _rate(thresholds, rates, income, above=True):
    """The rate a scale charges just above ``income`` (or just below it)."""
    rate = np.zeros(np.shape(income))
    for threshold, value in zip(thresholds, rates):
        rate = np.where(
            income >= threshold if above else income > threshold, value, rate
        )
    return rate


def _rising(rates):
    return rates[0] >= 0 and all(b >= a for a, b in zip(rates, rates[1:]))


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
    if not (
        all(
            _rising(rates)
            for rates in (
                c.uk_rates,
                c.scotland_rates,
                c.dividend_rates,
                c.savings_rate_list,
                c.property_rate_list,
            )
        )
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
        _, basic_upper, higher_upper = c.bands
        rho_n = np.where(
            c.scottish,
            _rate(c.scotland[0], c.scotland_rates, other + x),
            _rate(
                (-np.inf, basic_upper, higher_upper), c.property_rate_list, other + x
            ),
        )
        in_reach = in_first
    else:
        # With no property income, Marriage Allowance only moves every band
        # position down by its amount.
        position = x - c.earned_exclusions
        rho_n = np.where(
            c.scottish,
            _rate(c.scotland[0], c.scotland_rates, position),
            _rate(c.uk[0], c.uk_rates, position),
        )
        in_reach = in_first & ((c.earned_exclusions == 0) | (c.property == 0))
    savings_scale = ((low, basic_limit, higher_limit), c.savings_rate_list)
    # dx <= c.shared and dw <= min(dx, dividends). The top of the nil rates
    # moves up by at most dx and never passes the top of the savings.
    dw = np.minimum(c.shared, c.dividends)
    sigma_s = _rate(*savings_scale, np.minimum(start + c.shared, top + dw), above=False)
    rho_s = _rate(*savings_scale, top)
    # The dividends end at the top of income, which no share moves.
    sigma_v = np.where(
        c.dividends > c.dividend_allowance,
        _rate(
            c.dividend_scale[0],
            c.dividend_rates,
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


def allocate_deductions(person, period, parameters):
    """Deductions against savings and dividend income in the share that gives
    the least Income Tax (ITA 2007 s. 25(2) and (3A)). Where no share gives less
    tax than the order non-savings, savings, dividends, these are that order's
    deductions exactly."""
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
    (``to_savings`` and ``to_dividends``) unless another share saves more than
    TOLERANCE. The search runs only on people the tests in
    ``_old_order_is_least`` leave, or on everyone with ``search_all``."""
    to_savings = np.asarray(to_savings, dtype=np.float64)
    to_dividends = np.asarray(to_dividends, dtype=np.float64)
    if search_all:
        search = np.ones(len(to_savings), dtype=bool)
    else:
        search = ~_old_order_is_least(
            _build(inputs, income_tax), to_savings[:, None], to_dividends[:, None]
        )[:, 0]
    if not search.any():
        return to_savings, to_dividends
    c = _build({name: values[search] for name, values in inputs.items()}, income_tax)
    x, s, v = _least_tax_share(c)
    default_s = c.savings - to_savings[search][:, None]
    default_v = c.dividends - to_dividends[search][:, None]
    default_x = c.step_3_income - default_s - default_v
    lower = (
        step_5_tax(c, x, s, v)
        < step_5_tax(c, default_x, default_s, default_v) - TOLERANCE
    )[:, 0]
    moved = np.flatnonzero(search)[lower]
    to_savings, to_dividends = to_savings.copy(), to_dividends.copy()
    to_savings[moved] = (c.savings - s)[lower, 0]
    to_dividends[moved] = (c.dividends - v)[lower, 0]
    return to_savings, to_dividends


def non_savings_deductions(person, period):
    """Allowances against non-savings income beyond trade loss relief, and the
    relief set against savings and dividends, once received_allowances_savings_income
    and received_allowances_dividend_income have taken their share.

    The relief comes off non-savings income first, as far as the share sets
    anything against it, then the allowances. Where the share is the order
    non-savings, savings, dividends, these are that order's amounts exactly.
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
    non_savings = np.maximum(
        0, person("net_income", period) + relief - savings - dividends
    )
    used = np.minimum(
        relief + person("allowances", period), non_savings + savings + dividends
    )
    to_non_savings = used - to_savings - to_dividends
    return SimpleNamespace(
        earned=np.where(moved, np.maximum(0, to_non_savings - relief), default.earned),
        relief_against_savings_and_dividends=np.where(
            moved,
            np.maximum(0, relief - to_non_savings),
            default.relief_against_savings_and_dividends,
        ),
    )
