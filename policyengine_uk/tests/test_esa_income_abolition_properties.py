"""Property-based tests for the abolition of income-related ESA (#2562).

The Secretary of State appointed 1 July 2026 for the abolition of
income-related ESA (Welfare Reform Act 2012 s.33(1)(b)) to reach every
remaining old style ESA award in Great Britain (SI 2025/1148 art. 3A,
inserted by SI 2026/409), and the Department appointed 1 October 2026 in
Northern Ireland (SR 2025/176 art. 3A, inserted by SR 2026/115). Art. 3A(2)
saves an award for an appointee (esa_income_appointee_saving); a couple's
award is one award, saved when either member who reports it is saved.
Art. 3A(3) lets a Universal Credit claim end a saved award. A contributory
allowance continues as new style ESA.

When the abolition reaches the claimant's or partner's award
(esa_income_abolition_reached, from 2026-27), the family claims Universal
Credit if would_claim_uc_at_legacy_closure. From 2027-28 the award has ended
and the family is moved off its legacy benefits (legacy_benefits_closed).

Each generated population runs in one simulation five times over: with the
saving and claim flag as drawn; with every award saved; with none saved;
with the saving of every member who reports nothing flipped; and with
nobody claiming when moved. Saving every award pays it in full in every
year, as the rule before the abolition did; a reform that keeps the
parameter at 1 gives the same outputs
(test_keeping_awards_payable_is_saving_every_award).

Invariants, for any generated population of working-age families in
2025-26, 2026-27 and 2027-28:

1. Parameter: each fiscal year's gov.dwp.ESA.income.awards_payable value is
   the share of 6 April to 5 April falling before the statutory date, counted
   here from the two dates (1 before 2026-27, 0 after).
2. Bounds: 0 <= esa_income_payable_share <= 1; the claimant and partner
   share one value; and it is 1 for every member of a saved claim.
3. Abolition: from 2027-28 an unsaved claim pays nothing: a family whose
   couple claim is unsaved has no claimant_or_partner_esa_income, a member
   outside the couple whose claim is unsaved is not on income-related ESA,
   and with no saving nobody gets any.
4. Contributory ESA never changes, whatever is saved or claimed.
5. Before 2026-27 every output is the same whatever is saved or claimed;
   the abolition never raises anyone's income-related ESA; and a family
   that claims nothing and saves nothing gets exactly its jurisdiction's
   share of the award before the abolition.
6. Monotonic: turning the saving on for any members never lowers a benefit
   unit's esa_income or esa.
7. Status: a member outside the couple is on income-related ESA only while
   the award on their report is open.
8. Saving a member who reports nothing changes no output.
9. The claim path never gives a family income-related ESA: turning
   would_claim_uc_at_legacy_closure on never raises esa_income, and a family
   that claims when the abolition reaches its award has no
   claimant_or_partner_esa_income that year.
10. A saved claim never prompts the claim or the closure: a family whose
    couple claim is saved is neither reached nor moved, and a member outside
    the couple with a saved claim keeps their legacy benefits open.
11. Independent reading: for families with no work, esa_income,
    claims_universal_credit and each outside member's status equal amounts
    worked here from the regulations (the £6,000 tariff threshold, £1 a week
    for each £250 or part above it and the £16,000 limit, ESA Regs 2008 regs
    110 and 118), the dates and the saving, without the model's code. This
    bounds a couple's claim by one share and keeps a saved claim whole.
"""

import datetime
import math

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ABOLITION_DATES = {
    "great_britain": datetime.date(2026, 7, 1),
    "northern_ireland": datetime.date(2026, 10, 1),
}
PARAMETER = "gov.dwp.ESA.income.awards_payable"
KEEP_AWARDS_PAYABLE = {
    f"{PARAMETER}.{jurisdiction}": {"2015-01-01.2040-12-31": 1}
    for jurisdiction in ABOLITION_DATES
}
# 2025-26 is before both dates, 2026-27 holds both, 2027-28 is after both.
YEARS = (2025, 2026, 2027)
BEFORE = (2025,)
AFTER = (2027,)
REGIONS = ["LONDON", "NORTH_EAST", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
WORKING_AGE = st.integers(25, 60)
# "other" is an adult who is neither the claimant, the partner nor a young
# person they are responsible for, so they claim in their own right.
SHAPES = {
    "single": ["claimant"],
    "couple": ["claimant", "partner"],
    "lone_parent": ["claimant", "child"],
    "single_with_other": ["claimant", "other"],
    "couple_with_other": ["claimant", "partner", "other"],
}
COUPLE = ("claimant", "partner")
REPORT = st.sampled_from([0.0, 2_000.0, 3_000.0, 6_000.0])
BENUNIT_OUTPUTS = [
    "esa_income",
    "claimant_or_partner_esa_income",
    "esa_income_eligible",
    "esa",
    "claims_universal_credit",
    "claims_uc_at_legacy_closure",
    "esa_income_abolition_reached",
    "legacy_benefits_closed",
]
PERSON_OUTPUTS = [
    "esa_contrib",
    "esa_income_payable_share",
    "esa_income_report_closed",
    "is_on_income_related_esa",
    "is_claimant_or_partner",
    "person_legacy_benefits_closed",
]
MODES = ("drawn", "every", "none", "flipped", "no_claim")
# Statutory amounts for the independent reading: ESA Regs 2008 reg 110 (the
# £16,000 limit) and reg 118 (£1 a week for each £250, or part of £250,
# above £6,000), annualised over 52 weeks as the model does.
CAPITAL_LIMIT = 16_000
TARIFF_THRESHOLD = 6_000
TARIFF_STEP = 250
WEEKS = 52


@st.composite
def families(draw, work=True):
    roles = SHAPES[draw(st.sampled_from(sorted(SHAPES)))]
    members = []
    for role in roles:
        adult = role != "child"
        members.append(
            dict(
                role=role,
                age=draw(WORKING_AGE if adult else st.integers(0, 15)),
                esa_income_reported=draw(REPORT) if adult else 0.0,
                esa_contrib_reported=(
                    draw(st.sampled_from([0.0, 0.0, 4_000.0])) if adult else 0.0
                ),
                employment_income=(
                    draw(st.sampled_from([0.0, 0.0, 4_000.0, 20_000.0]))
                    if adult and work
                    else 0.0
                ),
                weekly_hours=(
                    draw(st.sampled_from([0, 10, 30])) if adult and work else 0
                ),
                saved=draw(st.booleans()) if adult else False,
            )
        )
    return dict(
        members=members,
        region=draw(st.sampled_from(REGIONS)),
        # Around the £6,000 tariff threshold and £16,000 limit.
        savings=draw(
            st.sampled_from([0.0, 6_000.0, 6_100.0, 7_000.0, 16_000.0, 20_000.0])
        ),
        would_claim_uc=draw(st.booleans()),
        claims_when_moved=draw(st.booleans()),
    )


def every_year(value):
    return {year: value for year in YEARS}


def in_mode(units, mode):
    """The units under a saving and claim mode (see MODES)."""

    def saved(member, unit):
        if mode == "every":
            return member["role"] != "child"
        if mode == "none":
            return False
        if mode == "flipped" and member["esa_income_reported"] == 0:
            return member["role"] != "child" and not member["saved"]
        return member["saved"]

    return [
        dict(
            unit,
            claims_when_moved=unit["claims_when_moved"] and mode != "no_claim",
            members=[dict(m, saved=saved(m, unit)) for m in unit["members"]],
        )
        for unit in units
    ]


def situation(units):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, member in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            # Set every input for every member, or it stops being an input
            # for the rest of the simulation.
            people[name] = {
                "age": every_year(member["age"]),
                "is_claimant_or_partner": every_year(member["role"] in COUPLE),
                "current_education": every_year("NOT_IN_EDUCATION"),
                "esa_income_reported": every_year(member["esa_income_reported"]),
                "esa_contrib_reported": every_year(member["esa_contrib_reported"]),
                "employment_income": every_year(member["employment_income"]),
                "weekly_hours": every_year(member["weekly_hours"]),
                "esa_income_appointee_saving": every_year(member["saved"]),
            }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": every_year(unit["would_claim_uc"]),
            "would_claim_uc_at_legacy_closure": every_year(unit["claims_when_moved"]),
            "claims_all_entitled_benefits": every_year(False),
        }
        households[f"h{i}"] = {
            "members": names,
            "region": every_year(unit["region"]),
            "savings": every_year(unit["savings"]),
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, reform=None):
    sim = Simulation(situation=situation(units), reform=reform)
    return {
        year: {
            v: np.asarray(sim.calculate(v, year))
            for v in BENUNIT_OUTPUTS + PERSON_OUTPUTS
        }
        for year in YEARS
    }


def calculate_each_mode(units, modes=MODES):
    """Each output for the units under each mode, from one simulation
    holding a copy of the population for each."""
    n = len(units)
    p = sum(len(unit["members"]) for unit in units)
    combined = [u for mode in modes for u in in_mode(units, mode)]
    values = calculate(combined)
    out = {mode: {year: {} for year in YEARS} for mode in modes}
    for year in YEARS:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            size = n if name in BENUNIT_OUTPUTS else p
            for k, mode in enumerate(modes):
                out[mode][year][name] = values[year][name][k * size : (k + 1) * size]
    return out


def members_of(units):
    """Each person's benefit unit index, in simulation order."""
    return np.array([i for i, unit in enumerate(units) for _ in unit["members"]])


def couple_claim_saved(unit):
    return any(
        m["role"] in COUPLE and m["esa_income_reported"] > 0 and m["saved"]
        for m in unit["members"]
    )


def claim_saved(member, unit):
    """Whether the claim this member belongs to is saved."""
    if member["role"] in COUPLE:
        return couple_claim_saved(unit)
    return member["esa_income_reported"] > 0 and member["saved"]


def saved_claim_people(units):
    return np.array([claim_saved(m, u) for u in units for m in u["members"]])


def fiscal_year_share_before(date, year):
    """Share of the fiscal year starting 6 April `year` falling before `date`."""
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    before = (min(max(date, start), end) - start).days
    return before / (end - start).days


def unit_share(unit, year):
    jurisdiction = (
        "northern_ireland" if unit["region"] == "NORTHERN_IRELAND" else "great_britain"
    )
    return fiscal_year_share_before(ABOLITION_DATES[jurisdiction], year)


def jurisdiction_share(units, year):
    return np.array([unit_share(unit, year) for unit in units])


def tariff_income(capital):
    """ESA Regs 2008 reg 118, annualised."""
    excess = max(0.0, capital - TARIFF_THRESHOLD)
    return math.ceil(excess / TARIFF_STEP) * WEEKS


def independent_reading(unit, year):
    """esa_income, the Universal Credit claim and each member outside the
    couple's status, for a family nobody in which works, worked from the
    regulations, the dates and the saving alone."""
    share = unit_share(unit, year)
    capital = unit["savings"]
    tariff = tariff_income(capital)
    within_limit = capital <= CAPITAL_LIMIT
    couple = [m for m in unit["members"] if m["role"] in COUPLE]
    couple_reported = sum(m["esa_income_reported"] for m in couple)
    couple_saved = couple_claim_saved(unit)
    couple_share = 1.0 if couple_saved else share
    # The abolition reaches an unsaved couple claim from the year less than
    # all of it is payable; from the year none is, the family is moved.
    reached = couple_reported > 0 and not couple_saved and share < 1
    claims = unit["would_claim_uc"] or (reached and unit["claims_when_moved"])
    # A claim ends the couple's reports; the abolition pays the rest for
    # the claim's share of the year.
    couple_award = 0.0
    if couple_reported > 0 and within_limit and not claims:
        couple_award = max(0.0, couple_reported - tariff) * couple_share
    outside_awards, outside_on = [], []
    for m in unit["members"]:
        if m["role"] in COUPLE:
            continue
        own_share = 1.0 if claim_saved(m, unit) else share
        own = within_limit and m["esa_income_reported"] > tariff
        outside_awards.append(
            max(0.0, m["esa_income_reported"] - tariff) * own_share if own else 0.0
        )
        outside_on.append(bool(own and own_share > 0))
    return couple_award + sum(outside_awards), claims, outside_on


@pytest.fixture(scope="module")
def baseline_tax_benefit_system():
    """Share immutable baseline parameters across the annual-value checks."""
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize("year", range(2015, 2041))
def test_awards_payable_is_the_day_share_before_the_statutory_date(
    year, baseline_tax_benefit_system
):
    parameter = baseline_tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.ESA.income.awards_payable
    for name, date in ABOLITION_DATES.items():
        expected = fiscal_year_share_before(date, year)
        assert getattr(parameter, name) == pytest.approx(expected, abs=1e-12)


def test_day_shares_match_the_hand_counted_days():
    # 6 April to 30 June 2026 is 25 + 31 + 30 = 86 days; to 30 September,
    # 86 + 31 + 31 + 30 = 178; 2026-27 has 365 days.
    assert fiscal_year_share_before(ABOLITION_DATES["great_britain"], 2026) == (
        86 / 365
    )
    assert fiscal_year_share_before(ABOLITION_DATES["northern_ireland"], 2026) == (
        178 / 365
    )


def test_tariff_income_matches_the_hand_counted_steps():
    # £7,000 is four £250 steps above £6,000; £6,100 is part of one.
    assert tariff_income(7_000) == 4 * 52
    assert tariff_income(6_100) == 52
    assert tariff_income(6_000) == 0
    assert tariff_income(16_000) == 40 * 52


def test_keeping_awards_payable_is_saving_every_award():
    """The parameter and the saving are two routes to a payable award: a
    reform keeping awards_payable at 1 gives what saving every award gives."""
    adult = dict(
        esa_contrib_reported=0.0, employment_income=0.0, weekly_hours=0, saved=False
    )
    units = [
        dict(
            members=[dict(adult, role="claimant", age=40, esa_income_reported=5_000.0)],
            region=region,
            savings=7_000.0,
            would_claim_uc=False,
            claims_when_moved=True,
        )
        for region in ["LONDON", "NORTHERN_IRELAND"]
    ] + [
        dict(
            members=[
                dict(adult, role="claimant", age=40, esa_income_reported=2_000.0),
                dict(adult, role="partner", age=38, esa_income_reported=3_000.0),
                dict(adult, role="other", age=30, esa_income_reported=6_000.0),
            ],
            region="WALES",
            savings=0.0,
            would_claim_uc=False,
            claims_when_moved=True,
        )
    ]
    kept = calculate(units, reform=KEEP_AWARDS_PAYABLE)
    saved = calculate(in_mode(units, "every"))
    for year in YEARS:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            assert np.array_equal(kept[year][name], saved[year][name]), (year, name)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=8))
def test_abolition_invariants(units):
    values = calculate_each_mode(units)
    benunit = members_of(units)
    saved_claim = saved_claim_people(units)
    couple_saved = np.array([couple_claim_saved(unit) for unit in units])
    unsaved_unit = np.array(
        [
            not any(claim_saved(m, unit) for m in unit["members"])
            and not any(m["saved"] for m in unit["members"])
            for unit in units
        ]
    )
    for year in YEARS:
        a, k, w, f, n = (values[mode][year] for mode in MODES)
        couple = a["is_claimant_or_partner"].astype(bool)
        outside = ~couple
        # 2. Bounds, one share per couple, and 1 for a saved claim.
        share = a["esa_income_payable_share"]
        assert np.all((share >= 0) & (share <= 1)), year
        assert np.all(share[saved_claim] == 1), year
        for i in range(len(units)):
            shares = share[(benunit == i) & couple]
            assert np.all(shares == shares[0]), (year, units[i])
        # 4. Contributory ESA never changes.
        for v in (a, w, f, n):
            assert np.array_equal(v["esa_contrib"], k["esa_contrib"]), year
        # 5. The abolition never raises income-related ESA.
        for v in (a, w, f, n):
            assert np.all(v["esa_income"] <= k["esa_income"] + 1e-6), year
            assert np.all(
                v["claimant_or_partner_esa_income"]
                <= k["claimant_or_partner_esa_income"] + 1e-6
            ), year
        # 5. With no claim and no saving, each award is the jurisdiction's
        # share of the award before the abolition. (The no-claim copy keeps
        # the drawn saving, so this reads families with nothing saved.)
        expected = jurisdiction_share(units, year) * k["esa_income"]
        claims_anyway = np.array([unit["would_claim_uc"] for unit in units])
        plain = unsaved_unit & ~claims_anyway
        assert np.allclose(n["esa_income"][plain], expected[plain], atol=0.01), year
        # 6. Turning the saving on never lowers ESA.
        for name in ["esa_income", "esa"]:
            assert np.all(a[name] >= w[name] - 1e-6), (year, name)
            assert np.all(k[name] >= a[name] - 1e-6), (year, name)
        # 7. An outside member is on it only while their award is open.
        for v in (a, k, w, f, n):
            on = v["is_on_income_related_esa"].astype(bool)
            closed = v["esa_income_report_closed"].astype(bool)
            assert not np.any(outside & on & closed), year
        # 8. Saving a member who reports nothing changes nothing.
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            assert np.array_equal(f[name], a[name]), (year, name)
        # 9. The claim path never gives income-related ESA, and a family
        # that claims when the abolition reaches its award has none.
        assert np.all(a["esa_income"] <= n["esa_income"] + 1e-6), year
        claimed_when_reached = a["claims_uc_at_legacy_closure"].astype(bool) & a[
            "esa_income_abolition_reached"
        ].astype(bool)
        assert np.all(a["claimant_or_partner_esa_income"][claimed_when_reached] == 0)
        # 10. A saved claim prompts neither the claim nor the closure. No
        # generated family reports another legacy benefit.
        for v in (a, k, f, n):
            assert not np.any(
                v["esa_income_abolition_reached"].astype(bool) & couple_saved
            ), year
            assert not np.any(v["legacy_benefits_closed"].astype(bool) & couple_saved)
            assert not np.any(
                v["person_legacy_benefits_closed"].astype(bool) & outside & saved_claim
            ), year
        assert not np.any(k["esa_income_abolition_reached"]), year
        assert not np.any(k["legacy_benefits_closed"]), year
    # 5. Before 2026-27 every output is the same whatever is saved or claimed.
    for year in BEFORE:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            for mode in ("drawn", "none", "flipped", "no_claim"):
                assert np.array_equal(
                    values[mode][year][name], values["every"][year][name]
                ), (year, name, mode)
    # 3. After both dates, nothing is paid outside the saving.
    for year in AFTER:
        a, w = values["drawn"][year], values["none"][year]
        couple = a["is_claimant_or_partner"].astype(bool)
        assert np.all(a["claimant_or_partner_esa_income"][~couple_saved] == 0), year
        on = a["is_on_income_related_esa"].astype(bool)
        assert not np.any(on & ~couple & ~saved_claim), year
        assert np.all(w["esa_income"] == 0), year
        assert not np.any(w["is_on_income_related_esa"].astype(bool)), year


@PROPERTY_SETTINGS
@given(st.lists(families(work=False), min_size=1, max_size=8))
def test_awards_match_an_independent_reading(units):
    values = calculate_each_mode(units, modes=("drawn",))["drawn"]
    benunit = members_of(units)
    for year in YEARS:
        v = values[year]
        outside = ~v["is_claimant_or_partner"].astype(bool)
        on = v["is_on_income_related_esa"].astype(bool)
        for i, unit in enumerate(units):
            award, claims, outside_on = independent_reading(unit, year)
            assert abs(float(v["esa_income"][i]) - award) < 0.01, (year, unit)
            assert bool(v["claims_universal_credit"][i]) == claims, (year, unit)
            assert on[(benunit == i) & outside].tolist() == outside_on, (year, unit)
