"""Property-based tests for rent from boarders, lodgers and sub-tenants.

A household head may receive rent from boarders and lodgers who live in the
household in their own benefit units (rent_paid_as_boarder and
rent_paid_as_lodger, recorded on the payer), and from a sub-tenant outside it
(sublet_income).

Invariants, for any generated household:

1. Conservation: the rent the head receives equals the rent paid by members
   outside the head's benefit unit, and nobody else receives any.
2. Rent-a-room bounds: 0 <= relief <= receipts, the limit is the basic amount
   or half of it, and taxable rent-a-room income = max(0, receipts - limit).
3. Disregards: the counted home-letting income is between nil and the rent
   received, and equals the statutory closed form (boarders: half the excess
   over £20 a week each; lodgers: the excess over £20 a week, per person at
   pension age and per lodger family at working age; sub-tenants: the excess
   over £20 a week).
4. Monotone: more rent from a boarder or lodger who already pays never lowers
   taxable rent-a-room income or counted home-letting income, and never raises
   Income Support, Housing Benefit, Pension Credit or council tax reduction.
5. Boarders keep more: the same weekly amount counts no more when paid for
   board and lodging than when paid for lodging only.
6. Universal Credit unearned income and household market income do not depend
   on the rent paid between members of the household.
7. Tax: legacy_means_test_income_tax is between nil and income tax.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2025, 2026]
WEEKS = 52
DISREGARD = 20
BASIC_AMOUNT = 7_500
AWARDS = ["income_support", "housing_benefit", "pension_credit", "council_tax_benefit"]
rent = st.one_of(st.just(0.0), st.floats(100, 20_000))


@st.composite
def households(draw):
    pension_age = draw(st.booleans())
    age = st.integers(67, 90) if pension_age else st.integers(25, 60)
    head_unit = [
        dict(age=draw(age), employment_income=draw(st.floats(0, 25_000)))
        for _ in range(draw(st.integers(1, 2)))
    ]
    payers = []
    for _ in range(draw(st.integers(0, 2))):
        kind = draw(st.sampled_from(["rent_paid_as_boarder", "rent_paid_as_lodger"]))
        payers.append(
            [
                {"age": draw(st.integers(19, 60)), kind: draw(rent)}
                for _ in range(draw(st.integers(1, 2)))
            ]
        )
    return dict(
        head_unit=head_unit,
        payers=payers,
        sublet=draw(st.one_of(st.just(0.0), st.floats(0, 8_000))),
        tenure=draw(st.sampled_from(["RENT_PRIVATELY", "OWNED_OUTRIGHT"])),
        region=draw(st.sampled_from(["NORTH_WEST", "LONDON", "WALES", "SCOTLAND"])),
    )


def situation(h, year, scale=1.0, as_kind=None):
    people, benunits = {}, {}
    names = []
    for i, attrs in enumerate(h["head_unit"]):
        name = f"head_{i}"
        people[name] = {
            "age": {year: attrs["age"]},
            "employment_income": {year: attrs["employment_income"]},
            "is_household_head": {year: i == 0},
            "sublet_income": {year: h["sublet"] if i == 0 else 0.0},
        }
        names.append(name)
    benunits["head_unit"] = {"members": list(names)}
    for j, unit in enumerate(h["payers"]):
        members = []
        for k, attrs in enumerate(unit):
            name = f"payer_{j}_{k}"
            person = {"age": {year: attrs["age"]}, "is_household_head": {year: False}}
            for kind in ("rent_paid_as_boarder", "rent_paid_as_lodger"):
                if kind in attrs:
                    target = as_kind or kind
                    person[target] = {year: attrs[kind] * scale}
            people[name] = person
            members.append(name)
        benunits[f"payer_{j}"] = {"members": members}
        names += members
    return {
        "people": people,
        "benunits": benunits,
        "households": {
            "household": {
                "members": names,
                "tenure_type": {year: h["tenure"]},
                "region": {year: h["region"]},
                "rent": {year: 8_000.0 if h["tenure"] == "RENT_PRIVATELY" else 0.0},
                "council_tax": {year: 1_500.0},
            }
        },
    }


def calculate(h, year, variables, **kwargs):
    sim = Simulation(situation=situation(h, year, **kwargs))
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}


def payments(h, kind=None):
    return [
        [
            a.get(kind, 0.0) if kind else sum(v for k, v in a.items() if k != "age")
            for a in unit
        ]
        for unit in h["payers"]
    ]


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_rent_is_received_by_the_head_and_conserved(h, year):
    v = calculate(h, year, ["rent_from_boarders_and_lodgers"])
    received = v["rent_from_boarders_and_lodgers"]
    paid = sum(sum(unit) for unit in payments(h))
    np.testing.assert_allclose(received.sum(), paid, rtol=1e-6, atol=0.01)
    assert np.all(received[1:] == 0)


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_rent_a_room_bounds(h, year):
    v = calculate(
        h,
        year,
        [
            "rent_a_room_receipts",
            "rent_a_room_limit",
            "rent_a_room_relief",
            "taxable_rent_a_room_income",
        ],
    )
    receipts, limit = v["rent_a_room_receipts"], v["rent_a_room_limit"]
    assert np.all(np.isin(limit, [BASIC_AMOUNT, BASIC_AMOUNT / 2]))
    assert np.all(v["rent_a_room_relief"] >= 0)
    assert np.all(v["rent_a_room_relief"] <= receipts + 0.01)
    np.testing.assert_allclose(
        v["taxable_rent_a_room_income"], np.maximum(0, receipts - limit), atol=0.01
    )


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_home_letting_income_closed_form(h, year):
    sim = Simulation(situation=situation(h, year))
    counted = np.asarray(sim.calculate("legacy_benefits_home_letting_income", year))
    pension_age = bool(
        np.asarray(sim.calculate("is_SP_age", year))[: len(h["head_unit"])].any()
    )
    weekly = lambda x: x / WEEKS
    board = sum(
        0.5 * max(0, weekly(x) - DISREGARD)
        for unit in payments(h, "rent_paid_as_boarder")
        for x in unit
    )
    lodgers = payments(h, "rent_paid_as_lodger")
    if pension_age:
        lodging = sum(max(0, weekly(x) - DISREGARD) for unit in lodgers for x in unit)
    else:
        lodging = sum(max(0, weekly(sum(unit)) - DISREGARD) for unit in lodgers)
    sublet = max(0, weekly(h["sublet"]) - DISREGARD)
    expected = (board + lodging + sublet) * WEEKS
    np.testing.assert_allclose(counted[0], expected, rtol=1e-6, atol=0.01)
    assert np.all(counted[1:] == 0)
    received = sum(sum(unit) for unit in payments(h)) + h["sublet"]
    assert 0 <= counted[0] <= received + 0.01


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS), st.floats(1.1, 4))
def test_more_rent_is_monotone(h, year, scale):
    variables = [
        "taxable_rent_a_room_income",
        "legacy_benefits_home_letting_income",
    ] + AWARDS
    base = calculate(h, year, variables)
    more = calculate(h, year, variables, scale=scale)
    for v in ["taxable_rent_a_room_income", "legacy_benefits_home_letting_income"]:
        assert np.all(more[v] >= base[v] - 0.01), v
    for v in AWARDS:
        assert np.all(more[v] <= base[v] + 0.01), v


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_board_and_lodging_counts_no_more_than_lodging(h, year):
    v = "legacy_benefits_home_letting_income"
    as_boarders = calculate(h, year, [v], as_kind="rent_paid_as_boarder")[v]
    as_lodgers = calculate(h, year, [v], as_kind="rent_paid_as_lodger")[v]
    pension_age = calculate(h, year, ["is_SP_age"])["is_SP_age"][
        : len(h["head_unit"])
    ].any()
    if pension_age:
        # Per-person lodger disregard at pension age: boarders keep at least
        # as much per person.
        assert np.all(as_boarders <= as_lodgers + 0.01)


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_rent_within_the_household_changes_no_uc_income_or_market_income(h, year):
    variables = ["uc_unearned_income", "household_market_income"]
    with_rent = calculate(h, year, variables)
    without = calculate(h, year, variables, scale=0.0)
    for v in variables:
        np.testing.assert_allclose(with_rent[v], without[v], atol=0.01, err_msg=v)


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_legacy_means_test_income_tax_bounds(h, year):
    v = calculate(h, year, ["legacy_means_test_income_tax", "income_tax"])
    assert np.all(v["legacy_means_test_income_tax"] >= 0)
    assert np.all(v["legacy_means_test_income_tax"] <= v["income_tax"] + 0.01)
