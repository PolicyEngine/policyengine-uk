"""Working parent hours start with the term after the minimum age.

SI 2022/1134 reg 27(1)(a): a child is eligible for the period "beginning with
whichever of 1st January, 1st April or 1st September is the first date after
the day on which a declaration in respect of the child has effect". A
declaration made in advance has effect from the day the child meets the
description in reg 13 (regs 20(a) and 25(1)): it has attained the minimum
age, nine months from 1 September 2024 (SI 2023/1330 reg 2(5)(b)). Before
December 2022, SI 2016/1257 reg 35(3) set the same dates from the third
birthday. Sources fetched on 2026-10-22:
https://www.legislation.gov.uk/uksi/2022/1134/regulation/27
https://www.legislation.gov.uk/uksi/2022/1134/regulation/25
https://www.legislation.gov.uk/uksi/2022/1134/regulation/20
https://www.legislation.gov.uk/uksi/2016/1257/regulation/35/made

The model year runs from April, so its terms begin on 1 April and 1 September
of the year and 1 January of the next, a third of the year each. For every
date of birth of a child aged 0 to 4 on 6 October, the share of those terms
that begin after it attains the minimum age matches a reference written with
calendar dates.
"""

from datetime import date, timedelta

import pytest

from policyengine_uk import Simulation

# The minimum age in months the model reads for each year: the value on 30
# April (three as made, two from 1 April 2024, nine months from 1 September
# 2024).
MINIMUM_AGE_MONTHS = {2022: 36, 2023: 36, 2024: 24, 2025: 9, 2026: 9}


def attains(born, months):
    """The day a child born on ``born`` attains an age of ``months`` months:
    the same day of the month, or the month's last day if it has none."""
    year, month = divmod(born.year * 12 + born.month - 1 + months, 12)
    next_month = date(year + (month + 1) // 12, (month + 1) % 12 + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return date(year, month + 1, min(born.day, last_day))


def expected_share(born, year):
    reached = attains(born, MINIMUM_AGE_MONTHS[year])
    starts = (date(year, 4, 1), date(year, 9, 1), date(year + 1, 1, 1))
    return sum(reached < start for start in starts) / len(starts)


def age_on_6_october(born, year):
    return year - born.year - ((10, 6) < (born.month, born.day))


@pytest.mark.parametrize("year", sorted(MINIMUM_AGE_MONTHS))
def test_term_share_follows_the_date_of_birth(year):
    first = date(year - 5, 10, 7)
    births = [
        first + timedelta(days=d) for d in range((date(year, 10, 6) - first).days + 1)
    ]
    people = {
        f"child_{born:%Y%m%d}": {
            "age": {year: age_on_6_october(born, year)},
            "date_of_birth": {year: int(f"{born:%Y%m%d}")},
        }
        for born in births
    }
    sim = Simulation(situation={"people": people})
    shares = sim.calculate("extended_childcare_entitlement_term_share", year)
    mismatches = [
        (born, float(share), expected_share(born, year))
        for born, share in zip(births, shares)
        if abs(share - expected_share(born, year)) > 1e-6
    ]
    assert not mismatches, mismatches[:10]
    # Every share from none to all three terms occurs.
    assert {round(3 * float(share)) for share in shares} == {0, 1, 2, 3}
