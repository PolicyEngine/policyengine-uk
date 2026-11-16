"""Person-level capital that a household capital source already includes."""

from policyengine_uk.model_api import *


def household_sources(law) -> dict:
    """Each person source a household source includes, mapped to that source.

    The formulas subtract each such person source's stored household sum
    from its household source and allocate the remainder. No household
    source includes a person source missing here, such as a Lifetime ISA.
    ``law`` is the parameter tree at the period, as ``parameters(period)``
    gives it. cash_isa includes each cash ISA balance. share_like_capital
    includes each stocks and shares ISA balance, through stocks_and_shares_isa
    inside corporate_wealth or the itemised sum, and its part that holds the
    ISAs depends on the law: share_like_capital_without_sale_expenses while
    gov.dwp.share_like_capital.without_sale_expenses lists
    stocks_and_shares_isa, and share_like_capital_with_sale_expenses once a
    reform removes it. Every formula that subtracts, values or bounds a
    person source reads its household source here.
    """
    exempt = law.gov.dwp.share_like_capital.without_sale_expenses
    return {
        "cash_isa_countable_capital": "cash_isa",
        "stocks_and_shares_isa_countable_capital": (
            "share_like_capital_without_sale_expenses"
            if "stocks_and_shares_isa" in exempt
            else "share_like_capital_with_sale_expenses"
        ),
    }


def counted_person_sources(capital, law) -> list:
    """The person sources in ``capital.person_sources`` the formulas count.

    The formulas count a person source that a household source includes
    (``household_sources(law)``) only while ``capital.sources`` lists that
    household source. They move the part of the household source the data
    tie to a person into the holder's own benefit unit, so when the list
    drops the household source they count neither.
    """
    sources = set(capital.sources)
    held_in = household_sources(law)
    return [
        source
        for source in capital.person_sources
        if source not in held_in or held_in[source] in sources
    ]


def pooled_person_capital(
    benunit, source, period, parameters, capital, leaves_pool=None
):
    """The part of the household ``source`` that counted person sources make up.

    The household sum, for each benefit unit, of the counted person sources
    in ``capital.person_sources`` that ``source`` includes under the law at
    ``period`` (``household_sources``), over the members ``leaves_pool``
    selects (all members by default), as Core stores a total. The formulas
    subtract it from ``source`` before they allocate the remainder between
    benefit units, so they count each of those pounds only in its holder's
    own unit.
    """
    person = benunit.members
    law = parameters(period)
    held_in = household_sources(law)
    amount = 0
    for person_source in counted_person_sources(capital, law):
        if held_in.get(person_source) == source:
            held = person(person_source, period)
            if leaves_pool is not None:
                held = held * leaves_pool
            amount = amount + person.household.sum(held)
    if isinstance(amount, int):
        return 0
    return _as_stored(benunit.max(amount))


def bounded_person_holding(person, balance, household_total):
    """Each member's ``balance``, bounded by ``household_total``.

    ``household_total`` gives the household's total for each member. See
    ``bounded_holdings``, which this calls with Core's household sum and
    household rank.
    """
    return bounded_holdings(
        balance,
        household_total,
        person.household.sum,
        lambda criteria: person.get_rank(person.household, criteria),
    )


def bounded_holdings(balance, household_total, household_sum, household_rank):
    """Each member's holding: their ``balance``, bounded by the household total.

    ``household_total`` gives the household's total for each member.
    ``household_sum`` maps a member array to each member's household sum, as
    Core's ``person.household.sum`` does, and ``household_rank`` maps one to
    each member's rank in their household, lowest first and ties in member
    order, as Core's ``person.get_rank(person.household, ...)`` does.

    A negative or missing balance holds nothing, and an infinite one counts
    as the whole total before scaling. Where the household's balances, summed
    as Core stores a total, come to the nonnegative total or less, each member
    holds their balance exactly, and the formulas leave the rest of the total
    in the pool. Where they come to more, the function scales the balances to
    the total in whole steps of the total's float32 spacing, which it caps at
    2**104, the largest spacing of a finite float32. It rounds each
    proportional share down to a step, then gives the steps left over one
    each to the members whose shares lost the most in rounding, the first of
    them on a tie. Float32 represents every multiple of the step up to the
    total exactly, so the holdings sum to the total exactly. For every
    float32 balance and finite total:

    - no holding exceeds the household total, and none falls below zero;
    - where the balances' stored sum exceeds the total, the holdings' float64
      sum equals the total, so the pool keeps nothing of it;
    - where it doesn't, each holding equals the balance;
    - a sole holder whose balance reaches the total holds exactly the total;
    - each holding equals its proportional share, computed in float64, rounded
      down or up to a whole step, so it lies within one step of that share
      and passes a multiple of the step, such as a whole-pound capital
      limit, only where the share does;
    - a holding exceeds its balance by less than one step, and only where the
      balance falls between steps;
    - the same input gives the same output.
    """
    total = np.maximum(np.float32(0), np.asarray(household_total, np.float32))
    balance = np.asarray(balance, np.float32)
    finite = np.where(np.isfinite(balance), balance, np.where(balance > 0, total, 0))
    held = np.maximum(np.float32(0), finite).astype(np.float32)
    held_sum = np.asarray(household_sum(held), np.float64)
    over = _as_stored(held_sum) > total
    if not over.any():
        return held
    # A household that doesn't scale takes a total of 0 and a step of 1 here,
    # so an infinite total there stays quiet. Elsewhere the step equals the
    # total's own float32 spacing, as float64. At float32's largest value the
    # next float32 is infinite, so np.spacing gives infinity there and warns
    # of an overflow, which the formula silences. The cap at 2**104, the
    # spacing of every float32 from 2**127 up, keeps that step finite and
    # still divides the total.
    scaled = np.where(over, total, np.float32(0))
    with np.errstate(over="ignore"):
        step = np.minimum(
            np.spacing(np.where(over, total, np.float32(1))), np.float32(2.0**104)
        ).astype(np.float64)
    # Float64 holds the product of two float32 amounts exactly, so each share
    # rounds once, in the division, and never exceeds the total.
    share = held * scaled.astype(np.float64) / np.where(over, held_sum, 1)
    steps = np.floor(share / step)
    lost = share / step - steps
    # The total over its spacing gives a whole number, and the shares' whole
    # steps never sum above it, so the steps left over come to a whole number
    # at or above zero, and no more than the members whose shares lost part
    # of a step.
    left_over = scaled / step - household_sum(steps)
    takes_a_step = over & (household_rank(-lost) < left_over)
    return np.where(over, ((steps + takes_a_step) * step).astype(np.float32), held)


def _as_stored(amount):
    # Core holds float variables in float32 but sums and maximises members in
    # float64. Round the result as Core stores a household total such as
    # cash_isa, so balances that make up a total net it to exactly zero and
    # the pool keeps its float32 arithmetic.
    with np.errstate(over="ignore"):
        return np.asarray(amount).astype(np.float32)
