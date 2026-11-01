"""Person-level capital that a household capital source already holds."""

from policyengine_uk.model_api import *

# Each person-level capital source whose holdings sit inside a household
# capital source, with that source. A cash ISA balance is part of cash_isa,
# and a stocks and shares ISA balance part of share_like_capital (through
# stocks_and_shares_isa, inside corporate_wealth or the itemised sum). A
# person source with no entry here, such as a Lifetime ISA, sits in none.
HOUSEHOLD_SOURCE_OF = {
    "cash_isa_countable_capital": "cash_isa",
    "stocks_and_shares_isa_countable_capital": "share_like_capital",
}


def counted_person_sources(capital) -> list:
    """The person sources in ``capital.person_sources`` that count.

    A person source that sits inside a household source counts only while
    ``capital.sources`` lists that household source: it moves the part of the
    source the data tie to a person into the holder's own benefit unit, so a
    list without the household source counts neither.
    """
    sources = set(capital.sources)
    return [
        source
        for source in capital.person_sources
        if source not in HOUSEHOLD_SOURCE_OF or HOUSEHOLD_SOURCE_OF[source] in sources
    ]


def pooled_person_capital(benunit, source, period, capital, leaves_pool=None):
    """The part of the household ``source`` that counted person sources hold.

    The household sum, for each benefit unit, of the counted person sources
    in ``capital.person_sources`` that sit inside ``source``, over the
    members ``leaves_pool`` selects (all members by default). The household
    pool takes it out of ``source`` before sharing the rest between benefit
    units, so each of those pounds counts only in its holder's own unit.
    """
    person = benunit.members
    amount = 0
    for person_source in counted_person_sources(capital):
        if HOUSEHOLD_SOURCE_OF.get(person_source) == source:
            held = person(person_source, period)
            if leaves_pool is not None:
                held = held * leaves_pool
            amount = amount + person.household.sum(held)
    if isinstance(amount, int):
        return 0
    return _as_stored(benunit.max(amount))


def bounded_person_holding(person, balance, household_total):
    """Each member's ``balance``, bounded by ``household_total``.

    ``household_total`` is the household's total for each member. See
    ``bounded_holdings``, which this calls with Core's household sum.
    """
    return bounded_holdings(balance, household_total, person.household.sum)


def bounded_holdings(balance, household_total, household_sum):
    """Each member's holding: their ``balance``, bounded by the household total.

    ``household_total`` gives the household's total for each member, and
    ``household_sum`` maps a member array to each member's household sum, as
    Core's ``person.household.sum`` does. A negative or missing balance holds
    nothing, and an infinite one the whole total. Where the household's
    balances add up, stored as Core stores a total, to the nonnegative total
    or less, each member holds their balance exactly, and no one the data
    name holds the rest. Where they add up to more, the function scales each
    balance by the total over their sum and rounds it down to float32, as
    Core stores the result. For every float32 balance and finite total:

    - no holding exceeds the household total;
    - the household's stored sum of holdings never exceeds the total, so the
      pool's remainder stays at or above zero;
    - a sole holder whose balance reaches the total holds exactly the total;
    - each holding lies within float32 spacing of its proportional share;
    - the same input gives the same output.
    """
    total = np.maximum(np.float32(0), np.asarray(household_total, np.float32))
    balance = np.asarray(balance, np.float32)
    finite = np.where(np.isfinite(balance), balance, np.where(balance > 0, total, 0))
    held = np.maximum(np.float32(0), finite).astype(np.float32)
    held_sum = np.asarray(household_sum(held), np.float64)
    over = _as_stored(held_sum) > total
    # Float64 holds the product of two float32 amounts exactly, so each share
    # rounds once, in the division. A sole holder's share is then the total
    # itself, and rounding every share down keeps their sum within the total.
    share = held * total.astype(np.float64) / np.where(over, held_sum, 1)
    return np.where(over, _round_down_to_float32(share), held)


def _as_stored(amount):
    # Core holds float variables in float32 but sums and maximises members in
    # float64. Round the result as Core stores a household total such as
    # cash_isa, so balances that make up a total net it to exactly zero and
    # the pool keeps its float32 arithmetic.
    with np.errstate(over="ignore"):
        return np.asarray(amount).astype(np.float32)


def _round_down_to_float32(amount):
    # The largest float32 at or below each nonnegative float64 amount.
    rounded = amount.astype(np.float32)
    return np.where(rounded > amount, np.nextafter(rounded, np.float32(0)), rounded)
