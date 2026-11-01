"""Property-based tests for the abolition of income-related ESA (#2562).

The abolition of income-related ESA (Welfare Reform Act 2012 s.33(1)(b))
came into force for every remaining old style ESA award on 1 July 2026 in
Great Britain (SI 2025/1148 art. 3A, inserted by SI 2026/409) and on 1
October 2026 in Northern Ireland (SR 2025/176 art. 3A, inserted by SR
2026/115). Art. 3A(2) saves an award for an appointee
(esa_income_appointee_saving); art. 3A(3) lets a Universal Credit claim end
a saved award. A contributory allowance continues as new style ESA.

Each generated population runs in one simulation three times over: with the
saving as drawn, with every award saved, and with none saved. Saving every
award pays it in full in every year, as the rule before the abolition did
(origin/main); a reform that keeps the parameter at 1 gives the same outputs
(test_keeping_awards_payable_is_saving_every_award).

Invariants, for any generated population of working-age families in
2025-26, 2026-27 and 2027-28:

1. Parameter: each fiscal year's gov.dwp.ESA.income.awards_payable value is
   the share of 6 April to 5 April falling before the statutory date, counted
   here from the two dates (1 before 2026-27, 0 after).
2. Bounds: 0 <= esa_income_payable_share <= 1, and it is 1 for every saved
   member in every year.
3. Abolition: from 2027-28, a benefit unit with no saved member pays no
   income-related ESA (esa_income and claimant_or_partner_esa_income are 0)
   and none of its members is on it; and in every benefit unit, a member who
   is neither the claimant nor the partner and has no saving is not on it.
4. Contributory ESA never changes: esa_contrib is the same with and without
   the saving, in every year.
5. Differential against the rule before the abolition: before 2026-27 every
   output is the same whatever is saved; in every year a benefit unit with no
   saved member gets exactly its jurisdiction's payable share of the award
   the rule before the abolition pays; and the abolition never raises
   anyone's income-related ESA.
6. Monotonic: turning the saving on for any members never lowers a benefit
   unit's esa_income or esa.
7. Status: a member who is neither the claimant nor the partner is on
   income-related ESA only while the award on their report is open.
"""

import datetime

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
REPORT = st.sampled_from([0.0, 2_000.0, 6_000.0])
BENUNIT_OUTPUTS = [
    "esa_income",
    "claimant_or_partner_esa_income",
    "esa_income_eligible",
    "esa",
    "claims_universal_credit",
]
PERSON_OUTPUTS = [
    "esa_contrib",
    "esa_income_payable_share",
    "esa_income_report_closed",
    "is_on_income_related_esa",
    "is_claimant_or_partner",
]
SAVING_MODES = ("drawn", "every", "none")


@st.composite
def families(draw):
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
                    if adult
                    else 0.0
                ),
                weekly_hours=draw(st.sampled_from([0, 10, 30])) if adult else 0,
                saved=draw(st.booleans()) if adult else False,
            )
        )
    return dict(
        members=members,
        region=draw(st.sampled_from(REGIONS)),
        # Around the £6,000 tariff threshold and £16,000 limit.
        savings=draw(st.sampled_from([0.0, 7_000.0, 20_000.0])),
        would_claim_uc=draw(st.booleans()),
    )


def every_year(value):
    return {year: value for year in YEARS}


def with_saving(units, mode):
    """The units with each member's saving as drawn, on for every adult, or
    off for everyone."""
    return [
        dict(
            unit,
            members=[
                dict(
                    member,
                    saved={
                        "drawn": member["saved"],
                        "every": member["role"] != "child",
                        "none": False,
                    }[mode],
                )
                for member in unit["members"]
            ],
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
                "is_claimant_or_partner": every_year(
                    member["role"] in ("claimant", "partner")
                ),
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


def calculate_each_saving(units):
    """Each output for the units under each saving mode, from one
    simulation holding all three copies of the population."""
    n = len(units)
    p = sum(len(unit["members"]) for unit in units)
    combined = [u for mode in SAVING_MODES for u in with_saving(units, mode)]
    values = calculate(combined)
    out = {mode: {year: {} for year in YEARS} for mode in SAVING_MODES}
    for year in YEARS:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            size = n if name in BENUNIT_OUTPUTS else p
            for k, mode in enumerate(SAVING_MODES):
                out[mode][year][name] = values[year][name][k * size : (k + 1) * size]
    return out


def members_of(units):
    """Each person's benefit unit index, in simulation order."""
    return np.array([i for i, unit in enumerate(units) for _ in unit["members"]])


def saved_people(units):
    return np.array([m["saved"] for unit in units for m in unit["members"]])


def saved_units(units):
    return np.array([any(m["saved"] for m in unit["members"]) for unit in units])


def fiscal_year_share_before(date, year):
    """Share of the fiscal year starting 6 April `year` falling before `date`."""
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    before = (min(max(date, start), end) - start).days
    return before / (end - start).days


def jurisdiction_share(units, year):
    return np.array(
        [
            fiscal_year_share_before(
                ABOLITION_DATES[
                    "northern_ireland"
                    if unit["region"] == "NORTHERN_IRELAND"
                    else "great_britain"
                ],
                year,
            )
            for unit in units
        ]
    )


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
        )
        for region in ["LONDON", "NORTHERN_IRELAND"]
    ] + [
        dict(
            members=[
                dict(adult, role="claimant", age=40, esa_income_reported=2_000.0),
                dict(adult, role="other", age=30, esa_income_reported=6_000.0),
            ],
            region="WALES",
            savings=0.0,
            would_claim_uc=True,
        )
    ]
    kept = calculate(units, reform=KEEP_AWARDS_PAYABLE)
    saved = calculate(with_saving(units, "every"))
    for year in YEARS:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            assert np.array_equal(kept[year][name], saved[year][name]), (year, name)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=8))
def test_abolition_invariants(units):
    values = calculate_each_saving(units)
    benunit = members_of(units)
    saved = saved_people(units)
    unsaved_unit = ~saved_units(units)
    for year in YEARS:
        # a: the saving as drawn; k: every award kept; w: no award saved.
        a, k, w = (values[mode][year] for mode in SAVING_MODES)
        # 2. Bounds.
        share = a["esa_income_payable_share"]
        assert np.all((share >= 0) & (share <= 1)), year
        assert np.all(share[saved] == 1), year
        # 4. Contributory ESA never changes.
        assert np.array_equal(a["esa_contrib"], k["esa_contrib"]), year
        assert np.array_equal(w["esa_contrib"], k["esa_contrib"]), year
        # 5. The abolition never raises income-related ESA, and without a
        # saving each award is the jurisdiction's share of the full award.
        assert np.all(a["esa_income"] <= k["esa_income"] + 1e-6), year
        assert np.all(
            a["claimant_or_partner_esa_income"]
            <= k["claimant_or_partner_esa_income"] + 1e-6
        ), year
        expected = jurisdiction_share(units, year) * k["esa_income"]
        assert np.allclose(w["esa_income"], expected, atol=0.01), year
        assert np.allclose(
            a["esa_income"][unsaved_unit], expected[unsaved_unit], atol=0.01
        ), year
        # 6. Turning the saving on never lowers ESA.
        for name in ["esa_income", "esa"]:
            assert np.all(a[name] >= w[name] - 1e-6), (year, name)
            assert np.all(k[name] >= a[name] - 1e-6), (year, name)
        # 7. An outside member is on it only while their award is open.
        for v in (a, k, w):
            outside = ~v["is_claimant_or_partner"].astype(bool)
            on = v["is_on_income_related_esa"].astype(bool)
            closed = v["esa_income_report_closed"].astype(bool)
            assert not np.any(outside & on & closed), year
    # 5. Before 2026-27 every output is the same whatever is saved.
    for year in BEFORE:
        for name in BENUNIT_OUTPUTS + PERSON_OUTPUTS:
            for mode in ("drawn", "none"):
                assert np.array_equal(
                    values[mode][year][name], values["every"][year][name]
                ), (year, name, mode)
    # 3. After both dates, nothing is paid outside the saving.
    for year in AFTER:
        a, w = values["drawn"][year], values["none"][year]
        assert np.all(a["esa_income"][unsaved_unit] == 0), year
        assert np.all(a["claimant_or_partner_esa_income"][unsaved_unit] == 0), year
        on = a["is_on_income_related_esa"].astype(bool)
        assert not np.any(on & unsaved_unit[benunit]), year
        outside = ~a["is_claimant_or_partner"].astype(bool)
        assert not np.any(on & outside & ~saved), year
        assert np.all(w["esa_income"] == 0), year
        assert not np.any(w["is_on_income_related_esa"].astype(bool)), year
