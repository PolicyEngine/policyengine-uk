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

The rate test lets income reach each limit (s. 10(2)): income at a limit
passes, and income above it fails. A share that leaves non-savings income at
the limit can be the only one that meets the test, so the search keeps no room
below the limit for a person whose amounts float32 holds closely enough (see
below). The test reads the income the model holds. The model holds incomes in
float32 and sums net income and allowances in float32, so the income it holds
can sit either side of the sum of the amounts entered. A household entered at
a limit can then sit just above it and fail, as at the model's other limits.

One entered a penny over a limit can also sit on it, where the amounts are
large enough or many enough. Each amount the model holds, and each float32
sum, sits within half a float32 step of the true amount. Under £65,536 the
step is 0.39p or less, and it takes more than five roundings the same way to
hide a penny. From £65,536 the step is 0.78p, and three can. Pay of
£53,360.11, savings of £23,554.02 and dividends of £714.91 come to £77,629.04,
and after a trade loss of £26,859.03 the model holds net income of £50,770.00,
a penny under the £50,770.01 entered. From £131,072 the step is 1.56p, and two
whole-pence amounts can store as one: the model holds pay of £190,529.99 and
of £190,529.98 both as £190,529.984375.

So the test in float64 keeps room below each limit, as ``main``'s search does
for everyone, unless the model can show that float32 hid less than the entries
can sit over a limit. The room is ``RATE_TEST_ROOM`` plus
``RATE_TEST_ROOM_FRACTION`` of the limits and of the income after the
deductions, 3.9p at £37,700 and 13.9p at £138,255. Two rules keep it
(``c.low_precision``):

- An amount the test reads reaches £65,536 (``LOW_PRECISION``;
  ``_low_precision`` lists the amounts).
- A bound on the float32 error in net income, the allowances and the gift
  reaches the least amount the entries can sit over a limit
  (``_can_hide_an_excess``). That amount is a penny for entries in whole
  pence. A Gift Aid gift raises the limits by five quarters of the gift
  (s. 414(2)(b)), which can leave a limit between two pence, and the least
  excess is then a quarter, a half or three quarters of a penny.

The second rule reads the amounts behind the income the test reads.
``_held_error`` works the bound from the entries up. An entry under £131,072
sits within 0.39p of the whole-pence amount entered, so its distance from
whole pence is its error; from £131,072 the function gives no bound. For each
sum the model makes on the way to net income and the allowances, it adds the
distance between the amount held and the float64 sum of the parts as held,
which is the float32 rounding in that sum. So pay of £148,609.46 less
£108,409.45 of expenses, which the model holds as £40,200.00, gets no bound,
though no amount the test reads reaches £65,536. An amount the function
cannot follow gets no bound either: a formula it does not list, such as the
State Pension or a company car benefit, a relief the law caps, or a formula a
reform replaces, whose amount stops matching the parts listed here. The
function assumes entries in whole pence. An entry in fractions of a penny
reads as an error and adds to the bound.

An entry is an amount with no formula, or any amount supplied as an input for
the year: in a situation, a dataset or a YAML test, or through
``Simulation.set_input``. The model reads a supplied amount in place of the
variable's formula, so ``_held_error`` bounds it as an entry and reads none of
the amounts the formula would. Pay set through ``Simulation.set_input`` sits
in employment_income itself, with nothing in the amounts that variable adds
up. It gets the same bound as pay the constructor moves into
employment_income_before_lsr. A value the model stored itself
(``set_model_value``) is not an entry and keeps its variable's rule. Where
``_held_error`` stops at a supplied net income or supplied allowances,
``_can_hide_an_excess`` bounds on their own the other amounts the test reads:
savings, dividends, property income, the trade loss relief and pension
relief. A grossed-up gift supplied as an input is an entry too.

For a recipient the test holds to room, the search does what ``main``'s does
(``_moves_with_room``). It counts on the reduction only where the exact share
meets the test with the room, and it stores the float32 values nearest that
share's deductions. So the search never moves such a recipient to win the
reduction at a limit itself. A recipient entered at a limit is then denied
the reduction where ``main`` denies it: the model cannot tell that recipient
from one entered over the limit. Both pay amounts above, with savings of
£9,000.02, dividends of £1,570, a trade loss of £50,275 and a Gift Aid gift of
£80,044, leave the model £138,255 of income after the allowances, the raised
limit plus the £500 savings allowance. The law gives the reduction for
£190,529.98 and not for £190,529.99, and the model denies both.

The model has always applied the test in float32, to non-savings income,
savings and dividends each held in float32. Float32 rounding there can land
income entered over a limit back on it, where a float64 sum of the same
float32 amounts sits over; and a float64 sum can sit at a limit where float32
rounding of the limit or of the amounts carries them apart. So a share meets
the test where it does in either arithmetic (``_rate_test_on_stored``): in
float32 as before, which for the old order is ``_old_order_meets_rate_test``
and for a moved share ``_float32_meets_rate_test``, or in float64 from the
amounts the model holds (``_meets_rate_test``), with the room for a person the
test holds to it. The float64 test adds the grossed-up gift, as the model holds
it in float32, to the basic rate limit.
The vertex search scores each candidate in float64 only, so it can miss a
share that passes only in float32, as at a limit a Gift Aid gift raises. It
rounds only the share with the least ``f``, so it can also miss a share that
meets the test only once its deductions are rounded to float32. ``main``
misses both kinds too. The float32 test rounds each limit to float32 after it
adds the gift, where ``main`` rounds the limit first. The two agree where the
statutory limit is a float32 amount, as every limit up to 2028-29 is. The
model then never denies the reduction where ``main``'s float32 test gave it
for the same share. From 2029-30 the uprated Scottish higher rate threshold is
not a float32 amount, so for a Scottish taxpayer with a Gift Aid gift the two
limits can sit a float32 step apart. The model grants the reduction over a
limit only where float32 rounding of the amounts it holds carries income onto
the limit, as the float32 test always could. For a recipient the test holds to
room, the search decides and stores as ``main``'s does, so the float32 test
reads the share ``main`` stores.

The model stores the deductions from savings and dividends in float32 too. The
search finds the least ``f`` in float64, then ``_stored_share`` rounds that
share's deductions to float32, down or up, and takes the rounding with the
least ``f``. Among roundings within ``TOLERANCE`` of each other it prefers one
that leaves the first component within its bounds, but a rounding outside them
still wins where it leaves less ``f``. A first component can have no room: a
person may have no non-savings income, or from 2027-28 no property income. The
two deductions then have to add up to the shared amount exactly, which float32
rarely allows, and at a limit only one rounding may meet the rate test. The
model then sets up to a float32 step more than the shared amount against
savings and dividends, which leaves that much non-savings income beyond the
first component, or it leaves up to a step of the shared amount unset.

A rounding that sets more than half a penny beyond the shared amount
(``OVER_DEDUCTION``) ranks below every other, since the rate test would then
read that much of the savings or dividends as non-savings income the person
does not have. So does a rounding that meets the rate test only in float32,
for a recipient. Otherwise the search could pick a rounding for the slack in
the float32 test alone, and give the reduction to a recipient entered a penny
over a limit, whom ``main`` denies. And for a recipient the test holds to
room, every rounding but the nearest ranks last, so the model stores the
nearest, as ``main`` does.

None of these rules applies to the rounding nearest the exact deductions,
which storing them in float32 gives and the model has always held. It sits up
to half a float32 step of each deduction beyond the shared amount: 0.39p for a
deduction from £65,536 to £131,072, 0.78p up to £262,144, and twice as much in
each range above. Storing the savings or dividends that take the deduction,
which are at least as large, can move them by as much. So a household entered
at a limit can hold the same amounts as one entered just over it, and the
model gives both the same answer. Where the nearest rounding meets the test
only in float32, the slack grows with the float32 step of the income, as for
the old order. A recipient entered a few pence over a limit can then get the
reduction, as on ``main``. Any other rounding that sets more than half a penny
beyond the shared amount ranks last, and the nearest never does, so the model
stores no other rounding more than half a penny beyond it.

The search prices the stored share and the old order each with
``_rate_test_on_stored``, and moves a person only where the stored share leaves
less ``f``.
``share_meets_marriage_allowance_rate_test`` gives the model's answer from the
stored deductions through the same function, so the model applies the
reduction wherever the search counted on it. For a person the test does not
hold to room it applies the reduction nowhere else. A recipient it holds to
room can also get it where the search did not count on it, as on ``main``:
where the search moves the share for the Step 5 tax alone and the float32 test
passes at a limit.

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
from policyengine_uk.utils.supplied_inputs import is_supplied_input

# A share replaces the order non-savings, savings, dividends only where it
# saves more than this (in pounds). So float32 rounding moves a deduction only
# where one float32 step of it saves more, and then by that step. The step
# saves tax at the person's rates. For a Marriage Allowance recipient it can
# also carry the share across a limit of the rate test and win the reduction.
TOLERANCE = 1e-3
# The search treats shares whose tax differs by less than this (in pounds)
# as equally good.
TIE = 1e-6
# Bound on people times candidates evaluated at once, to bound memory.
CHUNK = 2_000_000
# A float32 rounding of a share can set more than the shared allowances against
# savings and dividends, by up to a float32 step of each deduction (over a
# penny once a deduction passes £131,072). ``_stored_share`` ranks a rounding
# that sets more than this (in pounds) beyond them below every other, unless it
# is the rounding to the nearest float32 values, which storing the deductions
# gives.
OVER_DEDUCTION = 0.005
# From this amount (in pounds, 2**16) the float32 step is 1/128 of a pound,
# 0.78p, or more. Each amount the model holds, and each float32 sum of them,
# can then sit 0.39p or more from the amount entered, so three such roundings
# can move income a whole penny, and a person entered a penny over a limit of
# the Marriage Allowance rate test can hold income at the limit. Where any
# amount the test reads reaches this, the search counts a share as meeting the
# test only with the room below (``_low_precision``). The amounts behind
# those, such as pay before expenses, fall to ``_can_hide_an_excess``.
LOW_PRECISION = 65_536.0
# The room below each limit of the rate test for a person with such an amount:
# pounds, plus a fraction of the limits and of the income after the deductions.
RATE_TEST_ROOM = 1e-3
RATE_TEST_ROOM_FRACTION = 1e-6
# From this amount (in pounds, 2**17) the float32 step is 1/64 of a pound,
# 1.56p, and two whole-pence amounts can store as one. Below it a float32
# amount sits within 0.39p of the whole-pence amount entered, so rounding the
# amount held to whole pence recovers the entry.
INDISTINCT = 131_072.0
# ``_held_error`` rounds an input to whole pence to recover the amount entered.
PENNY = 0.01
# The variables below are an amount less other amounts, floored at nil where
# the third item says so, plus the amounts in the last item. Unless the amount
# is supplied as an input, when it is an entry, ``_held_error`` checks the
# amount the model holds against that sum, so a formula that stops matching
# its entry here leaves an error no rounding explains, and the person keeps
# the room.
SUMS = {
    "net_income": (
        ("net_income_before_trade_loss_relief",),
        ("trade_loss_relief_against_general_income",),
        True,
        (),
    ),
    "taxable_employment_income": (
        ("employment_income", "employment_benefits", "benefits_in_kind"),
        ("employment_deductions",),
        True,
        (),
    ),
    "taxable_property_income": (
        ("property_income",),
        ("deductible_property_finance_costs", "property_allowance_deduction"),
        True,
        ("taxable_rent_a_room_income",),
    ),
    "taxable_savings_interest_income": (
        ("savings_interest_income", "other_investment_income"),
        (),
        True,
        (),
    ),
    "taxable_dividend_income": (
        ("dividend_income",),
        ("deficiency_relief",),
        True,
        (),
    ),
    "taxable_miscellaneous_income": (
        ("miscellaneous_income_before_trading_allowance",),
        ("miscellaneous_income_trading_allowance_deduction",),
        False,
        (),
    ),
}
# The Personal Allowance is a whole number of pounds (``np.ceil`` in its
# formula), which float32 holds exactly. Float32 rounding of adjusted net
# income could move it by a pound only in the taper, above £100,000 of net
# income, where ``_low_precision`` keeps the room anyway.
EXACT = ("personal_allowance",)
# The amounts the rate test reads beside net income and the allowances, which
# hold them as parts: savings, dividends and property income in net income
# with the trade loss relief taken off it, and pension relief in the
# allowances. ``_can_hide_an_excess`` bounds each on its own where the walk
# from net income and the allowances does not reach it.
READ_WITH_NET_INCOME = (
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_property_income",
    "trade_loss_relief_against_general_income",
    "pension_contributions_relief",
)
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
    earned_exclusions = sum(
        (values(variable) for variable in exclusions), np.zeros_like(savings)
    )
    return dict(
        savings=savings,
        dividends=values("taxable_dividend_income"),
        relief=values("trade_loss_relief_against_general_income"),
        net_income=values("net_income"),
        property=values("taxable_property_income"),
        allowances=values("allowances"),
        pension=values("pension_contributions_relief"),
        earned_exclusions=earned_exclusions,
        gift=values("gift_aid_grossed_up"),
        scottish=np.asarray(person("pays_scottish_income_tax", period)),
        savings_allowance=values("savings_allowance"),
        marriage_allowance_reduction=values("marriage_allowance_reduction_at_stake"),
        rate_test_non_savings_limit=np.asarray(limits.non_savings, dtype=np.float64),
        rate_test_savings_allowance=np.broadcast_to(
            np.asarray(limits.savings_allowance, dtype=np.float64), savings.shape
        ),
        old_order_meets_rate_test=_old_order_meets_rate_test(person, period, limits),
        can_hide_an_excess=_can_hide_an_excess(
            person, period, income_tax, limits, earned_exclusions
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
    # The model's own answer to the test for the old order, which it gives a
    # person the search leaves there (``_old_order_meets_rate_test``).
    c.old_order_meets_rate_test = columns.get("old_order_meets_rate_test", zero > 0)
    non_savings_limit = columns.get("rate_test_non_savings_limit", zero)
    basic_rate_limit = c.bands[1]
    # The rate test reads all the non-savings income, so it adds what s. 25(3A)
    # leaves below the first component.
    c.non_savings_below_first = c.other_left if c.other_first else zero
    # The statutory limit on non-savings income.
    c.rate_test_non_savings_limit = non_savings_limit
    c.low_precision = _low_precision(
        columns, non_savings_limit, basic_rate_limit
    ) | columns.get("can_hide_an_excess", zero > 0)
    # The limits the test applies. Income can reach a limit (s. 10(2)), and a
    # share that leaves non-savings income at one can be the only share that
    # meets the test. TIE covers float64 rounding of a share the search puts
    # at a limit. For a person with an amount at or above ``LOW_PRECISION``,
    # or whose float32 error the model cannot bound under the least excess
    # (``_can_hide_an_excess``), the test keeps room below each limit, as
    # ``main``'s search does for everyone: income held at a limit may have
    # been entered over it.
    room = RATE_TEST_ROOM + RATE_TEST_ROOM_FRACTION * np.maximum(
        np.maximum(np.abs(non_savings_limit), np.abs(basic_rate_limit)),
        np.abs(c.non_savings_below_first + c.step_3_income),
    )
    c.rate_test_limits = SimpleNamespace(
        non_savings=np.where(
            c.low_precision, non_savings_limit - room, non_savings_limit + TIE
        ),
        basic_rate=np.where(
            c.low_precision, basic_rate_limit - room, basic_rate_limit + TIE
        ),
        starting=np.where(c.low_precision, c.starting_limit - room, c.starting_limit),
        savings_allowance=c.rate_test_savings_allowance + TIE,
    )
    return c


def _low_precision(columns, non_savings_limit, basic_rate_limit):
    """People with an amount the Marriage Allowance rate test reads at or
    above ``LOW_PRECISION``: net income, net income before the trade loss
    relief, that relief, the allowances, savings, dividends, an exclusion from
    earned income, the grossed-up gift or a limit the gift raises. Net income
    before the relief counts because the relief can take net income below
    ``LOW_PRECISION`` where the float32 sum it comes off sits above. These are
    the amounts the test reads, not the amounts behind them: pay and the
    expenses the model takes off it can each sit above ``LOW_PRECISION`` and
    leave net income below it. ``_can_hide_an_excess`` covers those."""
    relief = columns["relief"]
    largest = np.maximum.reduce(
        [
            np.abs(amount) + np.zeros_like(relief)
            for amount in (
                columns["net_income"],
                columns["net_income"] + relief,
                relief,
                columns["allowances"],
                columns["savings"],
                columns["dividends"],
                columns["earned_exclusions"],
                columns["gift"],
                non_savings_limit,
                basic_rate_limit,
            )
        ]
    )
    return largest >= LOW_PRECISION


def _whole_pence(amount):
    return np.round(amount / PENNY) * PENNY


def _entry_error(amount):
    """How far an entry the model holds as ``amount`` can sit from the amount
    entered: its distance from whole pence under ``INDISTINCT``, and no bound
    from there."""
    return np.where(
        np.abs(amount) < INDISTINCT, np.abs(amount - _whole_pence(amount)), np.inf
    )


def _listed(person, period, variables):
    """The variables an ``adds`` or ``subtracts`` attribute names, which can
    be a list or the path of a parameter that holds one."""
    if isinstance(variables, str):
        node = person.simulation.tax_benefit_system.parameters(period.start)
        for part in variables.split("."):
            node = getattr(node, part)
        variables = node
    return tuple(variables or ())


def _held_error(person, period, income_tax, name, known):
    """A bound, in pounds, on how far the float32 amount the model holds for
    ``name`` can sit from the amount the entries give, or infinity where the
    function cannot give one.

    - An entry: the distance from the amount held to the nearest whole penny,
      which is the amount entered where the entry is in whole pence and under
      ``INDISTINCT``. From ``INDISTINCT`` two entries can store as one, so the
      function gives no bound. An entry is a variable with no formula, or any
      amount supplied as an input for the year (``is_supplied_input``): from
      a situation, a dataset or ``Simulation.set_input``. The model reads a
      supplied amount in place of the variable's formula or sum, so the
      function applies this rule before the rules below and reads none of the
      amounts that formula or sum would. A value the model stored itself
      (``set_model_value``) is not supplied.
    - A sum of other variables (``adds`` and ``subtracts``, or an entry in
      ``SUMS``): the bounds of its parts, plus the distance from the amount
      held to the float64 sum of the parts as held. That distance is the
      float32 rounding inside the sum. It is also large where the model did
      not work the amount from those parts, as for a formula a reform
      replaces.
    - The trade loss relief: the bound of the loss, where the relief is the
      whole loss. Pension relief: the bound of the contributions, where the
      relief is all of them. A capped relief gets no bound.
    - A variable in ``EXACT``: nil.
    - Any other formula: nil where the amount is nil, and no bound elsewhere,
      as for the State Pension or a company car benefit.

    ``known`` holds the bounds already worked out, by variable."""
    if name in known:
        return known[name]

    def values(variable):
        return np.asarray(person(variable, period), dtype=np.float64)

    def error(variable):
        return _held_error(person, period, income_tax, variable, known)

    def unless_nil(amount, bound):
        return np.where(amount == 0, 0.0, bound)

    variable = person.simulation.tax_benefit_system.variables[name]
    held = values(name)
    if is_supplied_input(person, name, period, held):
        # The model reads this amount as supplied and never works out its
        # parts, so neither does this function: a part can be a formula the
        # tax calculation would not otherwise run.
        known[name] = _entry_error(held)
        return known[name]
    plus, minus, floored, after = (), (), False, ()
    if name == "net_income_before_trade_loss_relief":
        plus = tuple(income_tax.adjusted_net_income_components)
    elif name == "taxable_self_employment_income":
        plus, floored = ("self_employment_income",), True
        minus = tuple(income_tax.bases.taxable_self_employment_income_deductions)
    elif name in SUMS:
        plus, minus, floored, after = SUMS[name]
    elif variable.adds or variable.subtracts:
        plus, minus = (
            _listed(person, period, listed)
            for listed in (variable.adds, variable.subtracts)
        )
    if name in EXACT:
        bound = np.zeros_like(held)
    elif name == "trade_loss_relief_against_general_income":
        loss = values("trading_loss")
        bound = unless_nil(held, np.where(held == loss, _entry_error(loss), np.inf))
    elif name == "pension_contributions_relief":
        contributions = values("pension_contributions")
        bound = unless_nil(
            held,
            np.where(held == contributions, error("pension_contributions"), np.inf),
        )
    elif plus or minus:
        total = sum(values(part) for part in plus) - sum(
            (values(part) for part in minus), np.zeros_like(held)
        )
        if floored:
            total = np.maximum(0, total)
        total = total + sum((values(part) for part in after), np.zeros_like(held))
        bound = np.abs(held - total) + sum(error(part) for part in plus + minus + after)
    elif variable.is_input_variable():
        bound = _entry_error(held)
    else:
        bound = unless_nil(held, np.inf)
    known[name] = bound
    return bound


def _can_hide_an_excess(person, period, income_tax, limits, earned_exclusions):
    """People for whom float32 can have moved the amounts the Marriage
    Allowance rate test reads by as much as the least amount the entries can
    sit over a limit. For them income the model holds at a limit may have been
    entered over it, so the test keeps room below each limit.

    The test compares sums and differences of net income, the allowances,
    savings and dividends with the limits. ``_held_error`` bounds how far the
    model's net income and allowances sit from the entries. Savings,
    dividends, property income and the trade loss relief are parts of net
    income, and pension relief is part of the allowances, so their rounding
    counts there. Where ``_held_error`` does not reach one of them, the
    function adds its bound (``READ_WITH_NET_INCOME``). That happens where it
    stops at an amount supplied as an input above them, or a reform takes
    them out of the parts of net income. A Gift Aid gift raises the limits by
    its gross amount (s. 414(2)(b)), five quarters of the gift, which float32
    also rounds. A gross amount supplied as an input is an entry: its bound
    is its distance from whole pence.

    Amounts entered in whole pence sit at least a penny over a whole-pence
    limit they exceed. A gift whose gross amount is not in whole pence leaves
    the limit between two pence, and income can then sit a quarter, a half or
    three quarters of a penny over it. So the function asks for the bound to
    stay below that least excess. An exclusion from earned income, which only
    a reform gives, gets no bound."""
    known = {}
    bound = sum(
        _held_error(person, period, income_tax, name, known)
        for name in ("net_income", "allowances")
    )
    # The walk reaches the other amounts the test reads, unless it stopped at
    # a supplied amount above them or a reform took them out of the parts of
    # net income. Then each gets its own bound.
    for name in READ_WITH_NET_INCOME:
        if name not in known:
            bound = bound + _held_error(person, period, income_tax, name, known)
    held_gross = np.asarray(person("gift_aid_grossed_up", period), dtype=np.float64)
    if is_supplied_input(person, "gift_aid_grossed_up", period, held_gross):
        # A gross gift supplied in place of its formula is an entry.
        gross = _whole_pence(held_gross)
        bound = bound + _entry_error(held_gross)
    else:
        gift = np.asarray(person("gift_aid", period), dtype=np.float64)
        gross = _whole_pence(gift) / (1 - income_tax.rates.uk.rates[0])
        bound = bound + np.where(
            np.abs(gift) < INDISTINCT, np.abs(held_gross - gross), np.inf
        )
    bound = bound + np.where(earned_exclusions == 0, 0.0, np.inf)
    least_excess = PENNY
    for limit in (limits.non_savings, limits.basic_rate):
        pence = (np.asarray(limit, dtype=np.float64) - held_gross + gross) / PENNY
        # The distance from the limit to the next whole penny above it.
        least_excess = np.minimum(
            least_excess, (np.floor(pence + 1e-6) + 1 - pence) * PENNY
        )
    # TIE keeps the comparison clear of the slack the float64 test allows.
    return bound > least_excess - 10 * TIE


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
    """Whether the share meets the Marriage Allowance rate test. Income at a
    limit meets it (s. 10(2)), except for a person the test holds to room
    (``c.low_precision``), whose limits carry it (``c.rate_test_limits``).
    ``TIE`` covers float64 rounding of a share that leaves income at a limit,
    savings at the savings allowance or no dividends."""
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
        # With room for a person the test holds below the limit.
        limit = np.where(
            c.low_precision,
            c.rate_test_limits.non_savings,
            c.rate_test_non_savings_limit,
        )
        vertical.append(np.where(recipient, limit - c.non_savings_below_first, zero))
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


def _marriage_allowance_in_reach(c):
    """Recipients the old order denies the Marriage Allowance reduction, where
    the least non-savings income any share leaves falls within the rate test's
    limit."""
    least_first = np.maximum(0, c.step_3_income - c.savings - c.dividends)
    return (
        (c.marriage_allowance_reduction > 0)
        & ~c.old_order_meets_rate_test
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


def _float32_meets_rate_test(c, to_savings, to_dividends):
    """Whether the share the model holds as ``to_savings`` and
    ``to_dividends`` meets the rate test in the arithmetic the model has
    always applied: on non-savings income left, savings and dividends each
    held in float32, against the limits rounded to float32."""
    single = np.float32
    x, _, _ = _share_left(c, to_savings, to_dividends)
    savings = np.maximum(
        single(0),
        c.savings.astype(single) - np.asarray(to_savings).astype(single),
    )
    dividends = np.maximum(
        single(0),
        c.dividends.astype(single) - np.asarray(to_dividends).astype(single),
    )
    return meets_marriage_allowance_rate_test(
        (x + c.non_savings_below_first).astype(single),
        savings,
        dividends,
        SimpleNamespace(
            non_savings=np.asarray(c.rate_test_non_savings_limit).astype(single),
            basic_rate=np.asarray(c.bands[1]).astype(single),
            starting=c.starting_limit,
            savings_allowance=np.asarray(c.rate_test_savings_allowance).astype(single),
        ),
    )


def _rate_test_on_stored(c, to_savings, to_dividends, moved):
    """Whether the share the model holds as ``to_savings`` and
    ``to_dividends`` meets the rate test, in float64 from the amounts held
    (``_meets_rate_test``, with room for a person the test holds to it,
    ``c.low_precision``) or in float32 as the model has always applied it:
    ``_float32_meets_rate_test`` where ``moved``, and the old order's own
    answer (``_old_order_meets_rate_test``) elsewhere."""
    single = np.where(
        moved,
        _float32_meets_rate_test(c, to_savings, to_dividends),
        c.old_order_meets_rate_test,
    )
    return _meets_rate_test(c, *_share_left(c, to_savings, to_dividends)) | single


def _with_room(c):
    """Marriage Allowance recipients whom the rate test holds to room below
    each limit (``c.low_precision``). For them the search decides and stores
    as ``main``'s does (``_moves_with_room``)."""
    return c.low_precision & (c.marriage_allowance_reduction > 0)


def _moves_with_room(c, x, s, v, to_savings, to_dividends):
    """Whether the search moves a recipient the rate test holds to room below
    each limit (``_with_room``) from the old order's deductions
    (``to_savings`` and ``to_dividends``) to the share that leaves ``x``,
    ``s`` and ``v``. The search decides as ``main``'s does. It counts on the
    reduction for the share only where the exact share meets the test with the
    room, and for the old order only where the old order meets it in float32
    (``_old_order_meets_rate_test``). It prices both in float64, and reads the
    first component the old order leaves without a floor at nil. So the search
    never moves such a person to win the reduction at a limit itself, where
    the amounts held may hide a penny."""
    old_s = c.savings - to_savings
    old_v = c.dividends - to_dividends
    old_order_tax = step_5_tax(c, c.step_3_income - old_s - old_v, old_s, old_v) - (
        c.marriage_allowance_reduction * c.old_order_meets_rate_test
    )
    return tax_after_marriage_allowance(c, x, s, v) < old_order_tax - TOLERANCE


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
    to float32 and takes the pair with the least ``f`` under the rate test the
    model applies to a stored share (``_rate_test_on_stored``). Among pairs
    within ``TOLERANCE`` of each other, it prefers one that leaves the first
    component within its bounds. A pair can leave the first component outside
    its bounds by less than a float32 step of the deductions, and the model
    then reads it as ``_share_left`` does, at nil where it would fall below
    nil. Such a pair still wins where it gives less ``f``, for example where
    only its rounding meets the rate test. Three kinds of pair rank below
    every other: one that sets more than ``OVER_DEDUCTION`` beyond the shared
    allowances; for a recipient, one that meets the rate test only in float32;
    and, for a recipient the rate test holds to room (``_with_room``), every
    pair. None of that applies to the pair nearest the exact deductions,
    which storing the deductions in float32 gives, as the model always has.
    So a recipient the test holds to room gets the nearest pair. Deductions
    that are float32 amounts already stay as they are. Returns the
    deductions, the first component, savings and dividends they leave, and
    their ``f``."""
    s, v = _exact_where_the_rate_test_reads(c, s, v)
    exact_savings = np.clip(c.savings - s, 0, c.savings)
    exact_dividends = np.clip(c.dividends - v, 0, c.dividends)
    recipient = c.marriage_allowance_reduction > 0
    with_room = _with_room(c)
    nearest_savings = exact_savings.astype(np.float32).astype(np.float64)
    nearest_dividends = exact_dividends.astype(np.float32).astype(np.float64)
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
            meets = _rate_test_on_stored(c, to_savings, to_dividends, True)
            tax = step_5_tax(c, *share) - c.marriage_allowance_reduction * meets
            outside = (first < -TIE) | (first > highest + TIE)
            nearest = (to_savings == nearest_savings) & (
                to_dividends == nearest_dividends
            )
            float32_only = meets & ~_meets_rate_test(c, *share)
            option = SimpleNamespace(
                last=(
                    (first > highest + OVER_DEDUCTION)
                    | (float32_only & recipient)
                    | with_room
                )
                & ~nearest,
                outside=outside,
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
            level = np.abs(option.tax - best.tax) <= TOLERANCE
            lower = (option.tax < best.tax - TOLERANCE) | (
                level
                & (
                    (best.outside & ~option.outside)
                    | ((best.outside == option.outside) & (option.tax < best.tax - TIE))
                )
            )
            better = (best.last & ~option.last) | ((best.last == option.last) & lower)
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
    savings and dividends as the model stores them and applies
    ``_rate_test_on_stored``, as the search does to the share it stores and to
    the old order, so the model gives the answer the search counted on."""
    c = _context(person, period, parameters)
    default = default_order_deductions(person, period)

    def stored(variable):
        return np.asarray(person(variable, period), dtype=np.float64)

    to_savings = stored("received_allowances_savings_income")
    to_dividends = stored("received_allowances_dividend_income")
    moved = (to_savings != default.savings) | (to_dividends != default.dividends)
    return _rate_test_on_stored(
        c, to_savings[:, None], to_dividends[:, None], moved[:, None]
    )[:, 0]


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
            | _marriage_allowance_in_reach(everyone)
        )[:, 0]
    if not search.any():
        return to_savings, to_dividends
    c = _build({name: values[search] for name, values in inputs.items()}, income_tax)
    x, s, v = _least_tax_share(c)
    # Both sides as the model holds them: the share's deductions rounded to
    # float32, and the old order's as given, each with the model's own answer
    # to the rate test (``_rate_test_on_stored``, which
    # ``share_meets_marriage_allowance_rate_test`` applies). So the model gives
    # the reduction wherever this comparison counts it.
    stored = _stored_share(c, s, v)
    old_savings = to_savings[search][:, None]
    old_dividends = to_dividends[search][:, None]
    old_order = _share_left(c, old_savings, old_dividends)
    old_order_tax = step_5_tax(c, *old_order) - c.marriage_allowance_reduction * (
        _rate_test_on_stored(c, old_savings, old_dividends, False)
    )
    lower = stored.tax < old_order_tax - TOLERANCE
    # A recipient the rate test holds to room below each limit moves as on
    # ``main``, to the nearest rounding of the exact share.
    lower = np.where(
        _with_room(c),
        _moves_with_room(c, x, s, v, old_savings, old_dividends),
        lower,
    )
    # A stored share with the old order's deductions is the old order.
    same = (stored.to_savings == old_savings) & (stored.to_dividends == old_dividends)
    lower = (lower & ~same)[:, 0]
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


def _old_order_meets_rate_test(person, period, limits):
    """Whether the old order meets the Marriage Allowance rate test, in the
    arithmetic the model has always applied to that order: in float32, on net
    income less savings, dividends and allowances, against ``limits`` rounded
    to float32. Where the statutory limit is a float32 amount, that is the
    float32 sum of the limit and the gift, as on ``main``. The Scottish higher
    rate threshold is not one from 2029-30, and with a gift the rounded limit
    can then sit a float32 step from that sum."""
    default = default_order_deductions(person, period)
    savings = person("taxable_savings_interest_income", period)
    dividends = person("taxable_dividend_income", period)
    return meets_marriage_allowance_rate_test(
        _old_order_non_savings_left(person, period),
        np.maximum(0, savings - default.savings),
        np.maximum(0, dividends - default.dividends),
        SimpleNamespace(
            non_savings=np.asarray(limits.non_savings).astype(np.float32),
            basic_rate=np.asarray(limits.basic_rate).astype(np.float32),
            starting=limits.starting,
            savings_allowance=limits.savings_allowance,
        ),
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
