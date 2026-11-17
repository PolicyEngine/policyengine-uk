"""Property-based tests for rent from boarders, lodgers and sub-tenants.

A household head may receive rent from boarders and lodgers who live in the
household in their own benefit units (rent_paid_as_boarder and
rent_paid_as_lodger, recorded on the payer), and from a sub-tenant outside it
(sublet_income). A paying benefit unit may also hold a partner or an adult
who pays nothing; the generator supplies each person's role
(is_claimant_or_partner).

Invariants, for any generated household:

1. Conservation: the rent the head receives equals the rent paid by members
   outside the head's benefit unit, and nobody else receives any.
2. Rent-a-room bounds: 0 <= relief <= receipts; the limit is half the basic
   amount exactly when the person and someone else in the household both
   have receipts, and the basic amount otherwise; taxable rent-a-room income
   = max(0, receipts - limit).
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
7. Rent a programme does not count: UC earned income does not change with the
   rent. On the council tax reduction routes that do not count it (the
   Universal Credit route, and the Scottish working-age scheme), income does
   not change with the rent where the applicant and partner have no
   earnings; with earnings it falls by the extra tax earnings cause on the
   rent and by nothing else, so by no more than the top rate on the change in
   taxable rent-a-room income.
8. Tax: legacy_means_test_income_tax is between nil and income tax;
   rent_a_room_income_tax_after_reductions is between nil and
   rent_a_room_income_tax; the tax on income from capital left after
   reductions inside legacy_means_test_income_tax never goes negative; and
   for a person whose only counted income is rent-a-room income,
   rent_a_room_income_tax_after_reductions equals
   legacy_means_test_income_tax.

Person-level liability:

9. pays_rent_to_householder holds exactly for a person outside the household
   head's benefit unit who pays, or who is a claimant or partner in a benefit
   unit where a claimant or partner pays.
10. Moving a non-paying adult who is not a claimant or partner out of the
    payer's benefit unit into one of their own that claims no Universal Credit
    leaves the household head's Housing Benefit and council tax reduction
    non-dependant deductions unchanged.
11. Adding such an adult never lowers the household head's Housing Benefit
    non-dependant deductions, and never raises the head's Housing Benefit
    unless it raises the head's bedroom count under the size criteria.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.legacy_means_test_tax import legacy_means_test_tax_split

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
TOP_RATE = 0.48
KINDS = ("rent_paid_as_boarder", "rent_paid_as_lodger")
AWARDS = ["income_support", "housing_benefit", "pension_credit", "council_tax_benefit"]
rent = st.one_of(st.just(0.0), st.floats(100, 20_000))
positive_rent = st.floats(100, 20_000)


@st.composite
def member(draw, claimant_or_partner, pays=None):
    kind = draw(st.sampled_from(KINDS))
    amount = draw(rent) if pays is None else (draw(positive_rent) if pays else 0.0)
    return {
        "age": draw(st.integers(19, 60)),
        "is_claimant_or_partner": claimant_or_partner,
        "employment_income": draw(st.one_of(st.just(0.0), st.floats(0, 25_000))),
        kind: amount,
    }


@st.composite
def payer_units(draw):
    """A benefit unit outside the head's: one or two claimants or partners,
    and possibly an adult who is neither, each paying or not."""
    unit = [draw(member(True)) for _ in range(draw(st.integers(1, 2)))]
    if draw(st.booleans()):
        unit.append(draw(member(False)))
    return unit


@st.composite
def households(draw):
    pension_age = draw(st.booleans())
    age = st.integers(67, 90) if pension_age else st.integers(25, 60)
    head_unit = [
        dict(age=draw(age), employment_income=draw(st.floats(0, 25_000)))
        for _ in range(draw(st.integers(1, 2)))
    ]
    return dict(
        head_unit=head_unit,
        payers=[draw(payer_units()) for _ in range(draw(st.integers(0, 2)))],
        sublet=draw(st.one_of(st.just(0.0), st.floats(0, 8_000))),
        partner_sublet=draw(st.one_of(st.just(0.0), st.floats(100, 8_000))),
        tenure=draw(st.sampled_from(["RENT_PRIVATELY", "OWNED_OUTRIGHT"])),
        region=draw(st.sampled_from(["NORTH_WEST", "LONDON", "WALES", "SCOTLAND"])),
        claims_housing_benefit=draw(st.booleans()),
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
            "is_claimant_or_partner": {year: True},
            "sublet_income": {year: h["sublet"] if i == 0 else h["partner_sublet"]},
        }
        if h.get("claims_housing_benefit") and i == 0:
            people[name]["housing_benefit_reported"] = {year: 1.0}
        names.append(name)
    benunits["head_unit"] = {"members": list(names)}
    if h.get("claims_housing_benefit"):
        benunits["head_unit"]["would_claim_uc"] = {year: False}
    for j, unit in enumerate(h["payers"]):
        members = []
        for k, attrs in enumerate(unit):
            name = f"payer_{j}_{k}"
            person = {
                "age": {year: attrs["age"]},
                "is_household_head": {year: False},
                "is_claimant_or_partner": {year: attrs["is_claimant_or_partner"]},
                "employment_income": {year: attrs.get("employment_income", 0.0)},
            }
            for kind in KINDS:
                if kind in attrs:
                    target = as_kind or kind
                    person[target] = {year: attrs[kind] * scale}
            people[name] = person
            members.append(name)
        benunits[f"payer_{j}"] = {"members": members}
        if any(attrs.get("forgoes_universal_credit") for attrs in unit):
            benunits[f"payer_{j}"]["would_claim_uc"] = {year: False}
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


def per_week(annual):
    return annual / WEEKS


def paid(attrs, kind=None):
    if kind:
        return attrs.get(kind, 0.0)
    return sum(attrs.get(k, 0.0) for k in KINDS)


def payments(h, kind=None):
    return [[paid(a, kind) for a in unit] for unit in h["payers"]]


def expected_pays_rent_to_householder(h):
    """The person-level liability rule, from the inputs, in person order."""
    expected = [False] * len(h["head_unit"])
    for unit in h["payers"]:
        partner_pays = any(a["is_claimant_or_partner"] and paid(a) > 0 for a in unit)
        expected += [
            paid(a) > 0 or (a["is_claimant_or_partner"] and partner_pays) for a in unit
        ]
    return np.array(expected)


def head_taxable_rent_a_room(h, scale=1.0):
    """Taxable rent-a-room income of the head's benefit unit, from the inputs."""
    head = sum(sum(unit) for unit in payments(h)) * scale + h["sublet"]
    receipts = [head]
    if len(h["head_unit"]) > 1:
        receipts.append(h["partner_sublet"])
    shared = sum(r > 0 for r in receipts) > 1
    limit = BASIC_AMOUNT / 2 if shared else BASIC_AMOUNT
    return sum(max(0, r - limit) for r in receipts)


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_rent_is_received_by_the_head_and_conserved(h, year):
    v = calculate(h, year, ["rent_from_boarders_and_lodgers"])
    received = v["rent_from_boarders_and_lodgers"]
    total = sum(sum(unit) for unit in payments(h))
    np.testing.assert_allclose(received.sum(), total, rtol=1e-6, atol=0.01)
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
    receives = receipts > 0
    shared = receives & (receives.sum() - receives > 0)
    np.testing.assert_allclose(
        limit, np.where(shared, BASIC_AMOUNT / 2, BASIC_AMOUNT), atol=0.01
    )
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
    board = sum(
        0.5 * max(0, per_week(x) - DISREGARD)
        for unit in payments(h, "rent_paid_as_boarder")
        for x in unit
    )
    lodgers = payments(h, "rent_paid_as_lodger")
    if pension_age:
        lodging = sum(max(0, per_week(x) - DISREGARD) for unit in lodgers for x in unit)
    else:
        lodging = sum(max(0, per_week(sum(unit)) - DISREGARD) for unit in lodgers)
    sublet_received = h["sublet"] + (
        h["partner_sublet"] if len(h["head_unit"]) > 1 else 0.0
    )
    # #1995 sums the claimant's and partner's sublet income before one
    # disregard (one occupier assumed).
    sublet = max(0, per_week(sublet_received) - DISREGARD)
    expected = (board + lodging + sublet) * WEEKS
    np.testing.assert_allclose(counted[0], expected, rtol=1e-6, atol=0.01)
    assert np.all(counted[1:] == 0)
    received = sum(sum(unit) for unit in payments(h)) + sublet_received
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
def test_tax_bounds(h, year):
    sim = Simulation(situation=situation(h, year))
    v = {
        name: np.asarray(sim.calculate(name, year), dtype=float)
        for name in [
            "legacy_means_test_income_tax",
            "income_tax",
            "rent_a_room_income_tax",
            "rent_a_room_income_tax_after_reductions",
        ]
    }
    assert np.all(v["legacy_means_test_income_tax"] >= 0)
    assert np.all(v["legacy_means_test_income_tax"] <= v["income_tax"] + 0.01)
    after = v["rent_a_room_income_tax_after_reductions"]
    assert np.all(after >= -0.01)
    assert np.all(after <= v["rent_a_room_income_tax"] + 0.01)
    split = legacy_means_test_tax_split(sim.populations["person"], str(year))
    assert np.all(split["capital_after_reductions"] >= -0.01)


@st.composite
def rent_a_room_only(draw):
    """A household head whose only counted income is rent-a-room income, with
    income from capital, finance costs and a Step 6 reduction."""
    return dict(
        rent=draw(st.floats(0, 60_000)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        dividends=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        property=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        finance_costs=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
        other_tax_credits=draw(st.one_of(st.just(0.0), st.floats(0, 5_000))),
        region=draw(st.sampled_from(["LONDON", "SCOTLAND"])),
    )


@PROPERTY_SETTINGS
@given(rent_a_room_only(), st.sampled_from(YEARS))
def test_rent_a_room_tax_after_reductions_matches_the_counted_tax(h, year):
    situation = {
        "people": {
            "head": {
                "age": {year: 45},
                "is_household_head": {year: True},
                "savings_interest_income": {year: h["savings"]},
                "dividend_income": {year: h["dividends"]},
                "property_income": {year: h["property"]},
                "property_finance_costs": {year: h["finance_costs"]},
                "other_tax_credits": {year: h["other_tax_credits"]},
            },
            "lodger": {
                "age": {year: 30},
                "is_household_head": {year: False},
                "rent_paid_as_lodger": {year: h["rent"]},
            },
        },
        "benunits": {
            "head_unit": {"members": ["head"]},
            "lodger": {"members": ["lodger"]},
        },
        "households": {
            "household": {"members": ["head", "lodger"], "region": {year: h["region"]}}
        },
    }
    sim = Simulation(situation=situation)
    counted = sim.calculate("legacy_means_test_income_tax", year)[0]
    rent_a_room = sim.calculate("rent_a_room_income_tax_after_reductions", year)[0]
    np.testing.assert_allclose(rent_a_room, counted, rtol=1e-5, atol=0.01)


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS), st.floats(0.3, 0.9))
def test_programmes_that_exclude_the_rent_deduct_only_the_tax_earnings_cause(
    h, year, scale
):
    # Both runs keep every payment positive, so non-dependant status is fixed.
    variables = [
        "uc_earned_income",
        "council_tax_reduction_applicable_income",
        "council_tax_reduction_universal_credit_award",
        "council_tax_reduction_pensioner",
    ]
    full = calculate(h, year, variables)
    part = calculate(h, year, variables, scale=scale)
    np.testing.assert_allclose(
        full["uc_earned_income"], part["uc_earned_income"], atol=0.01
    )
    head_unit = 0
    working_age = not full["council_tax_reduction_pensioner"][head_unit]
    uc_route = working_age and bool(
        full["council_tax_reduction_universal_credit_award"][head_unit]
    )
    same_route = (
        full["council_tax_reduction_universal_credit_award"][head_unit]
        == part["council_tax_reduction_universal_credit_award"][head_unit]
    )
    excluded = uc_route or (h["region"] == "SCOTLAND" and working_age)
    if not (excluded and same_route):
        return
    fall = (
        part["council_tax_reduction_applicable_income"][head_unit]
        - full["council_tax_reduction_applicable_income"][head_unit]
    )
    earnings = sum(attrs["employment_income"] for attrs in h["head_unit"])
    if earnings == 0:
        np.testing.assert_allclose(fall, 0, atol=0.01)
    else:
        more_taxable = head_taxable_rent_a_room(h) - head_taxable_rent_a_room(h, scale)
        assert -0.01 <= fall <= TOP_RATE * more_taxable + 0.01


# Person-level liability.


@PROPERTY_SETTINGS
@given(households(), st.sampled_from(YEARS))
def test_pays_rent_to_householder_is_person_level(h, year):
    v = calculate(h, year, ["pays_rent_to_householder"])
    np.testing.assert_array_equal(
        v["pays_rent_to_householder"].astype(bool),
        expected_pays_rent_to_householder(h),
    )


@st.composite
def households_with_a_non_paying_adult(draw):
    """A household whose first paying unit has a payer who is a claimant, and
    an adult who is neither claimant nor partner and pays nothing."""
    h = draw(households())
    payer = draw(member(True, pays=True))
    adult = draw(member(False, pays=False))
    adult["employment_income"] = draw(st.floats(0, 40_000))
    h["payers"] = [[payer], *h["payers"]]
    h["tenure"] = "RENT_PRIVATELY"
    return h, adult


def with_adult(h, adult, own_unit):
    h = dict(h, payers=[list(unit) for unit in h["payers"]])
    if own_unit:
        # A family's own Universal Credit award with no earned income exempts
        # an adult from the national schemes' deductions (SI 2012/2885 Sch 1
        # para 8(8)(c) and equivalents), and one under 25 from Housing Benefit's
        # (HB Regs 2006 reg 74(8)). The model reads no award for an adult in
        # another family's unit, so this family doesn't claim.
        h["payers"].append(
            [dict(adult, is_claimant_or_partner=True, forgoes_universal_credit=True)]
        )
    else:
        h["payers"][0].append(adult)
    return h


@PROPERTY_SETTINGS
@given(households_with_a_non_paying_adult(), st.sampled_from(YEARS))
def test_a_non_paying_adult_counts_the_same_in_or_out_of_the_payers_unit(case, year):
    h, adult = case
    variables = [
        "housing_benefit_non_dep_deductions",
        "council_tax_reduction_non_dep_deductions",
    ]
    inside = calculate(with_adult(h, adult, own_unit=False), year, variables)
    outside = calculate(with_adult(h, adult, own_unit=True), year, variables)
    for v in variables:
        np.testing.assert_allclose(inside[v][0], outside[v][0], atol=0.01, err_msg=v)


@PROPERTY_SETTINGS
@given(households_with_a_non_paying_adult(), st.sampled_from(YEARS))
def test_adding_a_non_paying_adult_never_raises_housing_benefit(case, year):
    # A non-dependant also occupies a bedroom under the size criteria (HB
    # Regs 2006 reg 13D(12)), which can lift the maximum rent, for example
    # off the shared accommodation rate. So the property holds where the
    # household head's bedroom count does not change, and the non-dependant
    # deductions never fall.
    h, adult = case
    h = dict(h, claims_housing_benefit=True)
    variables = [
        "housing_benefit",
        "housing_benefit_LHA_allowed_bedrooms",
        "housing_benefit_non_dep_deductions",
    ]
    without = calculate(h, year, variables)
    with_them = calculate(with_adult(h, adult, own_unit=False), year, variables)
    assert (
        with_them["housing_benefit_non_dep_deductions"][0]
        >= without["housing_benefit_non_dep_deductions"][0] - 0.01
    )
    same_rooms = (
        with_them["housing_benefit_LHA_allowed_bedrooms"][0]
        == without["housing_benefit_LHA_allowed_bedrooms"][0]
    )
    if same_rooms:
        assert with_them["housing_benefit"][0] <= without["housing_benefit"][0] + 0.01
