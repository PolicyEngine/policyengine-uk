"""Funded early years hours stop with the term a child starts school.

A reception place meets England's universal and working parent duties (DfE,
Early education and childcare: statutory guidance from 1 April 2026,
footnotes 7 and 17), and a child is entitled to that place "in the September
following their fourth birthday" (its legal annex, on the School Admissions
Code). In Scotland a child who has started primary school is not an eligible
pre-school child (Children and Young People (Scotland) Act 2014 s.47(2)(b)),
and primary 1 starts in August for children who turn five by the council's
latest date, the end of February (Education (Scotland) Act 1980 s.32). In
Northern Ireland primary 1 starts in September for children who are four by
1 July (Education and Libraries (Northern Ireland) Order 1986 art 46(2)).
Sources fetched on 2026-10-22:
https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026
https://www.legislation.gov.uk/asp/2014/8/section/47
https://www.legislation.gov.uk/ukpga/1980/44/section/32
https://www.legislation.gov.uk/nisi/1986/594/article/46

The year's terms begin on 1 April, 1 September and 1 January. For every date
of birth of a child aged 3 to 5 on 6 October, in each nation, the share of
those terms that begin before it starts school matches a reference written
with calendar dates.
"""

from datetime import date, timedelta

import pytest

from policyengine_uk import Simulation

YEAR = 2026


def birthday(born, age):
    # No child in these grids is born on 29 February.
    return date(born.year + age, born.month, born.day)


def first_school_term(born, country):
    """The first day of the autumn term in which the child starts school."""
    if country == "SCOTLAND":
        # The August whose cohort turns five from 1 March to the end of the
        # next February; it comes before the autumn term begins.
        five = birthday(born, 5)
        cohort_year = five.year if five >= date(five.year, 3, 1) else five.year - 1
        return date(cohort_year, 9, 1)
    four = birthday(born, 4)
    if country == "NORTHERN_IRELAND":
        # Four by 1 July: that September; otherwise the next.
        return date(four.year + (four > date(four.year, 7, 1)), 9, 1)
    # England and Wales: the September following the fourth birthday.
    return date(four.year + (four >= date(four.year, 9, 1)), 9, 1)


def expected_share(born, country):
    starts = (date(YEAR, 4, 1), date(YEAR, 9, 1), date(YEAR + 1, 1, 1))
    first_term = first_school_term(born, country)
    return sum(start < first_term for start in starts) / len(starts)


def age_on_6_october(born):
    return YEAR - born.year - ((10, 6) < (born.month, born.day))


@pytest.mark.parametrize(
    "country", ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
)
def test_the_share_before_school_follows_each_nations_school_start(country):
    first = date(YEAR - 6, 10, 7)
    births = [
        first + timedelta(days=d)
        for d in range((date(YEAR - 3, 10, 6) - first).days + 1)
    ]
    people = {
        f"child_{born:%Y%m%d}": {
            "age": {YEAR: age_on_6_october(born)},
            "date_of_birth": {YEAR: int(f"{born:%Y%m%d}")},
        }
        for born in births
    }
    sim = Simulation(
        situation={
            "people": people,
            "households": {
                "household": {"members": list(people), "country": {YEAR: country}}
            },
        }
    )
    shares = sim.calculate("early_years_term_share_before_school", YEAR)
    mismatches = [
        (born, float(share), expected_share(born, country))
        for born, share in zip(births, shares)
        if abs(share - expected_share(born, country)) > 1e-6
    ]
    assert not mismatches, mismatches[:10]
    # A child is at school all year, starts in September, or starts later.
    assert {round(3 * float(share)) for share in shares} == {0, 1, 3}


def test_a_deferred_start_keeps_the_year():
    people = {
        "deferred": {
            "age": {YEAR: 4},
            "date_of_birth": {YEAR: 20220831},
            "early_years_school_start_deferred": {YEAR: True},
        },
        "on_time": {"age": {YEAR: 4}, "date_of_birth": {YEAR: 20220831}},
    }
    sim = Simulation(
        situation={
            "people": people,
            "households": {
                "household": {"members": list(people), "country": {YEAR: "ENGLAND"}}
            },
        }
    )
    shares = sim.calculate("early_years_term_share_before_school", YEAR)
    assert list(shares) == pytest.approx([1, 1 / 3])
