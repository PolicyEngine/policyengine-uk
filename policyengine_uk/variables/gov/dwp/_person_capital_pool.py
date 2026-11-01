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
    return benunit.max(amount)


def bounded_person_holding(person, balance, household_total):
    """A person's ``balance``, scaled so the household's never exceed its total.

    ``household_total`` is the household's total for each member. A negative
    or missing balance holds nothing, and an infinite one the whole total.
    Where the members' balances add up to more than the nonnegative total,
    each is scaled down by the same proportion, so the members together hold
    the total in proportion to their balances. Otherwise each holds its
    balance, and the rest of the total is held by no one the data name.
    """
    total = max_(0, household_total)
    finite = np.where(np.isfinite(balance), balance, np.where(balance > 0, total, 0))
    held = max_(0, finite)
    household_held = person.household.sum(held)
    over = household_held > total
    scale = where(over, total / where(over, household_held, 1), 1)
    return held * scale
