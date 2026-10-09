"""Property-based tests for the Child Tax Credit family element.

Law: Tax Credits Act 2002 s.9(2)(a); Child Tax Credit Regulations 2002
(SI 2002/2007) reg 7(2)(a) and (3).

- reg 7(3) set the family element at £545 from 6 April 2003, or £1,090 where
  any child was under one; from 6 April 2011 (SI 2011/1035 reg 2(2)) it is
  £545. No Up-rating Regulations changed it before tax credits ended on
  5 April 2025.
- reg 7(2)(a), from 6 April 2017 (SI 2017/387 reg 4(b)): the family element is
  included only where the claimant is responsible for a child or qualifying
  young person born before 6 April 2017.

Invariants:

1. The parameter is £545 on every day from 6 April 2003 to 2040, and with the
   baby addition never exceeds £1,090, nor £545 from 6 April 2011. In every
   converted fiscal year (2015 to 2040) the YEAR value is £545.
2. For any population of families and any tax year from 2015-16 to 2024-25:
   the family element is 0 or £545 (one per family, never per child), and it
   is £545 exactly when the family is eligible for Child Tax Credit and
   counts a child or qualifying young person born in 2016 or earlier. The
   oracle takes birth years from the generated ages and entered birth years,
   and the model's list of counted children; it does not call the formula or
   read birth_year (which is 0 for anyone left out when a situation enters it
   for some people).
3. Metamorphic: listing a family's members in a different order does not
   change the family element.
4. Metamorphic: from 2017-18, adding a newborn (born after 6 April 2017)
   never changes the family element.
5. Before 2011-12 (2004 to 2010, read at 1 January), the family element is
   £1,090 where an eligible family counts a child under one, otherwise £545.
"""

import datetime

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

FAMILY_ELEMENT = 545
BABY_FAMILY_ELEMENT = 1_090
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def test_family_element_is_545_every_day_from_2003(system):
    elements = system.parameters.gov.dwp.tax_credits.child_tax_credit.elements
    day = datetime.date(2003, 4, 6)
    while day <= datetime.date(2040, 12, 31):
        instant = day.isoformat()
        family = elements.family_element(instant)
        baby = elements.family_element_baby_addition(instant)
        assert family == FAMILY_ELEMENT, instant
        assert family + baby <= BABY_FAMILY_ELEMENT, instant
        if day >= datetime.date(2011, 4, 6):
            assert family + baby == FAMILY_ELEMENT, instant
        else:
            assert family + baby == BABY_FAMILY_ELEMENT, instant
        day += datetime.timedelta(days=1)


@pytest.mark.parametrize("year", range(2015, 2041))
def test_family_element_is_545_in_every_converted_fiscal_year(system, year):
    elements = system.parameters(str(year)).gov.dwp.tax_credits.child_tax_credit
    assert elements.elements.family_element == FAMILY_ELEMENT
    assert elements.elements.family_element_baby_addition == 0
    assert elements.eligibility.family_element_born_before == 20170406


# Ages 0 to 21 cover children, qualifying young persons (16 to 19 in
# non-advanced education) and dependants who no longer count.
member = st.fixed_dictionaries(
    {
        "age": st.integers(0, 21),
        "in_education": st.booleans(),
        # None: birth year is the period less age. Otherwise an entered birth
        # year consistent with the age (a birthday later in the year).
        "birth_year_offset": st.sampled_from([None, None, 0, 1]),
    }
)
family = st.fixed_dictionaries(
    {
        "adults": st.integers(1, 2),
        "children": st.lists(member, min_size=0, max_size=4),
        "reports_ctc": st.booleans(),
        "would_claim_uc": st.booleans(),
    }
)
population = st.lists(family, min_size=1, max_size=8)


def _situation(families, year, reverse=False, add_newborn=False, eligible=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(families):
        names = []
        for j in range(unit["adults"]):
            name = f"a{i}_{j}"
            adult = {"age": {year: 35 + j}}
            if j == 0 and unit["reports_ctc"]:
                adult["child_tax_credit_reported"] = {year: 1_000}
            people[name] = adult
            names.append(name)
        children = list(unit["children"])
        if add_newborn:
            children.append(
                {"age": 0, "in_education": False, "birth_year_offset": None}
            )
        for k, child in enumerate(children):
            name = f"c{i}_{k}"
            person = {"age": {year: child["age"]}}
            if child["in_education"]:
                person["current_education"] = {year: "UPPER_SECONDARY"}
            if child["birth_year_offset"] is not None:
                person["birth_year"] = {
                    year: year - child["age"] - child["birth_year_offset"]
                }
            people[name] = person
            names.append(name)
        if reverse:
            names = names[::-1]
        benunit = {"members": names}
        if eligible is None:
            benunit["would_claim_uc"] = {year: unit["would_claim_uc"]}
        else:
            benunit["is_CTC_eligible"] = {year: eligible}
        benunits[f"b{i}"] = benunit
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


def _calculate(families, year, **kwargs):
    simulation = Simulation(situation=_situation(families, year, **kwargs))
    return {
        variable: simulation.calculate(variable, year)
        for variable in [
            "CTC_family_element",
            "is_CTC_eligible",
            "is_child_or_qualifying_young_person_for_child_tax_credit",
            "birth_year",
            "age",
        ]
    }


def _oracle_people(families, year, add_newborn=False):
    """Each person's family index and birth year, in situation order, from the
    generated data alone."""
    benunit, birth_year = [], []
    for i, unit in enumerate(families):
        for j in range(unit["adults"]):
            benunit.append(i)
            birth_year.append(year - 35 - j)
        children = list(unit["children"])
        if add_newborn:
            children.append({"age": 0, "birth_year_offset": None})
        for child in children:
            benunit.append(i)
            birth_year.append(year - child["age"] - (child["birth_year_offset"] or 0))
    return np.array(benunit), np.array(birth_year)


def _any_by_family(families, benunit, mask):
    result = np.zeros(len(families), dtype=bool)
    np.logical_or.at(result, benunit, mask)
    return result


def _child(age, birth_year_offset=None):
    return {"age": age, "in_education": False, "birth_year_offset": birth_year_offset}


# Birth years entered for some people only: the others are left at 0.
PARTIAL_BIRTH_YEARS = [
    # Entered 2018 for one child; the sibling's birth year is 2021.
    {
        "adults": 1,
        "children": [_child(6, 0), _child(3)],
        "reports_ctc": True,
        "would_claim_uc": False,
    },
    # Entered 2019 for the younger child; the older child's is 2014.
    {
        "adults": 2,
        "children": [_child(10), _child(5, 0)],
        "reports_ctc": True,
        "would_claim_uc": False,
    },
]


@PROPERTY_SETTINGS
@given(population, st.integers(2015, 2024))
@example(PARTIAL_BIRTH_YEARS, 2024)
def test_family_element_is_one_flat_amount_for_a_child_born_before_the_cutoff(
    families, year
):
    result = _calculate(families, year)
    family_element = result["CTC_family_element"]
    assert np.all(np.isin(family_element, [0, FAMILY_ELEMENT]))

    # Oracle: a child or qualifying young person the model counts, born in
    # 2016 or earlier (birth year entered, or the period less age).
    counted = result["is_child_or_qualifying_young_person_for_child_tax_credit"]
    benunit, birth_year = _oracle_people(families, year)
    has_qualifying_child = _any_by_family(
        families, benunit, counted & (birth_year <= 2016)
    )
    expected = np.where(
        result["is_CTC_eligible"] & has_qualifying_child, FAMILY_ELEMENT, 0
    )
    np.testing.assert_array_equal(family_element, expected)


@PROPERTY_SETTINGS
@given(population, st.integers(2015, 2024))
def test_family_element_does_not_depend_on_member_order(families, year):
    forward = _calculate(families, year)["CTC_family_element"]
    reverse = _calculate(families, year, reverse=True)["CTC_family_element"]
    np.testing.assert_array_equal(forward, reverse)


@PROPERTY_SETTINGS
@given(population, st.integers(2017, 2024))
def test_a_newborn_after_the_cutoff_never_changes_the_family_element(families, year):
    # Hold eligibility fixed: a newborn can make a family with no other child
    # eligible, and the family element must still be nil.
    without = _calculate(families, year, eligible=True)["CTC_family_element"]
    with_newborn = _calculate(families, year, add_newborn=True, eligible=True)[
        "CTC_family_element"
    ]
    np.testing.assert_array_equal(without, with_newborn)


@PROPERTY_SETTINGS
@given(population, st.integers(2004, 2010))
def test_baby_rate_before_2011(families, year):
    result = _calculate(families, year, eligible=True)
    counted = result["is_child_or_qualifying_young_person_for_child_tax_credit"]
    benunit, _ = _oracle_people(families, year)
    has_child = _any_by_family(families, benunit, counted)
    has_baby = _any_by_family(families, benunit, counted & (result["age"] < 1))
    expected = np.where(
        has_child, np.where(has_baby, BABY_FAMILY_ELEMENT, FAMILY_ELEMENT), 0
    )
    np.testing.assert_array_equal(result["CTC_family_element"], expected)
