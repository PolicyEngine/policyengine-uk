"""Housing Benefit WTC disregard within accommodation-disregard segments.

SI 2026/753 reg 1(1) brings the Sch 4 para 18 accommodation disregard into
force on 5 October 2026, and SI 2026/978 reg 2(2) adds it to the amounts
para 17(3)(a) counts. The model therefore settles para 17 separately before
and after that date, and Sch 5 para 56 disregards WTC "except in a case which
falls under" para 17(1), so each segment has its own WTC disregard. In law
the two disregards coexist only under a reform that keeps tax credits after
5 April 2025.

For every generated population in 2026-27, with or without tax credits, the
award equals the independent statutory calculation made within each
segment and combined by days, and no segment gives a benefit unit both the
additional earnings disregard and a positive WTC disregard. The annual WTC
disregard combines the segments' amounts. Where para 56 applies in no
segment, the award equals the previous path's, with the new disregard
neutralized; under current law that holds for every family. Outside
specified or temporary accommodation, a reform that replaces the childcare
deduction, its limit or the WTC disregard with a formula that only calls the
model's own changes no output.
"""

import numpy as np
import pytest
from hypothesis import example, given
from hypothesis import strategies as st
from policyengine_core.periods import period as period_
from policyengine_core.reforms import Reform

from policyengine_uk.system import system
from policyengine_uk.tests.test_housing_benefit_wtc_disregard import (
    FORWARDING_REFORMS,
    PROPERTY_SETTINGS,
    RENT,
    TOLERANCE,
    WITNESSES,
    assert_forwarding_changes_nothing,
    case,
    families,
    legal_components,
    results,
    same_supply,
    simulation,
    without_wtc_reservation,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_disregard import (
    hb_segment_deductions,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_childcare_earnings_limit import (
    hb_childcare_wtc_reserve,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
)


YEAR = 2026
# 6 April to 4 October 2026, then 5 October 2026 to 5 April 2027.
SEGMENT_DAYS = (182, 183)
# Sch 4 para 18(2)(a)(ii) and (b)(ii): a single claimant or lone parent
# aged 25 or over.
FULL_ACCOMMODATION = 77.73 * 52
# SSCBA 1992 s.130(3)(b) and SI 2006/213 reg 71.
WITHDRAWAL_RATE = 0.65


class keep_tax_credits(Reform):
    """Keep tax credits in 2026-27, so the two disregards coexist."""

    def apply(self):
        def modify(parameters):
            parameters.gov.dwp.tax_credits.active.update(
                period="year:2026:2", value=True
            )
            return parameters

        self.modify_parameters(modify)


TAX_CREDITS = keep_tax_credits(system)
SYSTEMS = {True: TAX_CREDITS, False: system}
PREVIOUS = {
    True: without_wtc_reservation(TAX_CREDITS),
    False: without_wtc_reservation(system),
}
FORWARDED = {name: reform(TAX_CREDITS) for name, reform in FORWARDING_REFORMS.items()}


def legal_segments(unit, active):
    """The statutory components in each segment of 2026-27."""
    segments = []
    for in_force in (False, True):
        applies = (
            in_force
            and unit["specified"]
            and unit["net"] > 0
            and not unit["pension_age"]
        )
        segment = {**unit, "accommodation": FULL_ACCOMMODATION if applies else 0}
        segments.append(legal_components(segment, YEAR, active))
    return segments


def legal_award(unit, active):
    """Reg 71 within each segment, then the awards combined by days."""
    awards = [
        max(
            0,
            RENT
            - WITHDRAWAL_RATE * max(0, segment["income"] - unit["applicable_amount"]),
        )
        for segment in legal_segments(unit, active)
    ]
    return sum(days * award for days, award in zip(SEGMENT_DAYS, awards)) / 365


def segmented(units, active, previous=False):
    systems = PREVIOUS if previous else SYSTEMS
    return simulation(
        units, YEAR, tax_benefit_system=systems[active], dated_accommodation=True
    )


def model_segments(sim):
    """Each segment's share of the year, additional earnings disregard, WTC
    disregard and the WTC its childcare limit keeps back, as the model
    applies them."""
    benunit = sim.populations["benunit"]
    year = period_(YEAR)
    parameters = sim.tax_benefit_system.parameters
    net = np.maximum(sim.calculate("housing_benefit_net_earnings", YEAR), 0)
    standard = sim.calculate(
        "housing_benefit_applied_standard_earnings_disregard", YEAR
    )
    result = []
    for accommodation, share in hb_accommodation_segments(benunit, year, parameters):
        disregard, reserve, _ = hb_segment_deductions(
            benunit, year, parameters, accommodation
        )
        capped = np.minimum(np.maximum(accommodation, 0), np.maximum(net - standard, 0))
        result.append(
            dict(
                share=share,
                additional=np.asarray(disregard - standard - capped, dtype=float),
                reserve=np.asarray(reserve, dtype=float),
                kept_back=np.asarray(
                    hb_childcare_wtc_reserve(benunit, year, parameters, accommodation),
                    dtype=float,
                ),
            )
        )
    return result


def specified_claimant(**overrides):
    """A single claimant aged 40 in specified accommodation with no
    childcare or other income, and a nil applicable amount."""
    return case(
        **{
            "net": 500,
            "standard": 260,
            "childcare": 0,
            "children": 0,
            "wtc": 2_000,
            "specified": True,
            **overrides,
        }
    )


@st.composite
def segment_families(draw, supplied=False, supplied_limit=False):
    return {
        **draw(families(supplied, supplied_limit)),
        "specified": draw(st.booleans()),
        "applicable_amount": draw(st.sampled_from([0, 2_000, 5_000])),
    }


@st.composite
def segment_populations(draw):
    supplied = draw(st.sampled_from([None, "deduction", "limit"]))
    return draw(
        st.lists(
            segment_families(supplied == "deduction", supplied == "limit"),
            min_size=1,
            max_size=8,
        )
    )


SEGMENT_EDGE_CASES = [
    specified_claimant(),
    specified_claimant(net=2_000),
    specified_claimant(net=4_000),
    specified_claimant(net=2_000, applicable_amount=2_000),
    specified_claimant(net=8_000),
    specified_claimant(net=2_000, specified=False),
    specified_claimant(net=2_000, worker=False),
    specified_claimant(net=2_000, pension_age=True),
    case(specified=True),
    case(specified=True, net=8_000, wtc=500),
    case(specified=True, net=8_000, wtc=2_000, other=3_000),
]
SUPPLIED_SEGMENT_EDGE_CASES = [
    {**unit, "supplied": value}
    for unit, value in zip(
        SEGMENT_EDGE_CASES, [0, 0, 100, 0, 1_000, 0, 0, 0, 0, 3_900, 3_000]
    )
]
SUPPLIED_LIMIT_SEGMENT_EDGE_CASES = [
    {**unit, "supplied_limit": value}
    for unit, value in zip(
        SEGMENT_EDGE_CASES, [0, 10_000, 100, 0, 1_000, 0, 0, 0, 10_000, 3_900, 3_000]
    )
]


def test_wtc_disregard_applies_before_and_after_5_october():
    sim = segmented([specified_claimant()], active=True)
    # 500 < 260 + 889.20 before 5 October, and 500 < 260 + 240 + 889.20
    # after it, so para 56 disregards 889.20 of WTC in both segments.
    # Income before deductions is 500 + 2,000 = 2,500.
    # Before: 10,400 - 0.65 * (2,500 - 260 - 889.20) = 9,521.98.
    # After: 10,400 - 0.65 * (2,500 - 500 - 889.20) = 9,677.98.
    # (182 * 9,521.98 + 183 * 9,677.98) / 365 = 9,600.19.
    assert sim.calculate("housing_benefit_wtc_disregard", YEAR)[0] == pytest.approx(
        889.20, abs=TOLERANCE
    )
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        9_600.19, abs=TOLERANCE
    )


@pytest.mark.parametrize(
    "net,applicable_amount,award",
    [
        # Before 5 October, 2,000 >= 260 + 889.20: para 17(1) applies and
        # para 56 does not, so income is 4,000 - 1,149.20 = 2,850.80 and the
        # award 8,546.98. After it, 2,000 < 260 + 1,740 + 889.20: para 56
        # disregards 889.20, income is 4,000 - 2,000 - 889.20 = 1,110.80 and
        # the award 9,677.98. (182 * 8,546.98 + 183 * 9,677.98) / 365.
        (2_000, 0, 9_114.03),
        # The same incomes against a 2,000 applicable amount: 10,400 - 0.65
        # * 850.80 = 9,846.98 before, and the full 10,400 after.
        (2_000, 2_000, 10_124.25),
        # Before: 6,000 - 1,149.20 = 4,850.80, award 7,246.98. After: 4,000
        # < 260 + 3,740 + 889.20, so 6,000 - 4,000 - 889.20 = 1,110.80 and
        # 9,677.98. (182 * 7,246.98 + 183 * 9,677.98) / 365.
        (4_000, 0, 8_465.81),
    ],
)
def test_each_segment_settles_paragraph_56_with_its_own_earnings_test(
    net, applicable_amount, award
):
    """A WTC disregard settled once for the year, from the annual
    accommodation amount, would give 9,402.23, 10,400 and 8,176.03: it
    grants both additional disregards before 5 October at 2,000, and none
    after it at 4,000."""
    unit = specified_claimant(net=net, applicable_amount=applicable_amount)
    sim = segmented([unit], active=True)
    before, after = model_segments(sim)
    assert before["reserve"][0] == 0
    assert before["additional"][0] == pytest.approx(889.20, abs=TOLERANCE)
    assert after["reserve"][0] == pytest.approx(889.20, abs=TOLERANCE)
    assert after["additional"][0] == pytest.approx(0, abs=TOLERANCE)
    # The annual amount combines the segments: 889.20 * 183 / 365.
    assert sim.calculate("housing_benefit_wtc_disregard", YEAR)[0] == pytest.approx(
        445.82, abs=TOLERANCE
    )
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        award, abs=TOLERANCE
    )


def test_each_segment_limits_childcare_with_its_own_wtc_disregard():
    """A lone parent aged 40 in specified accommodation earns £8,000, has
    £3,000 of other income and £2,000 of WTC, and pays £4,160 for
    childcare. Income before deductions is £13,000."""
    unit = case(specified=True, net=8_000, wtc=2_000, other=3_000)
    sim = segmented([unit], active=True)
    # Before 5 October, 8,000 >= 1,300 + 4,160 + 889.20, so para 17(1)
    # applies: income is 13,000 - 2,189.20 - 4,160 = 6,650.80, and the
    # award 10,400 - 0.65 * 6,650.80 = 6,076.98. After it, 8,000 < 1,300 +
    # 4,041.96 + 4,160 + 889.20, so para 56 disregards 889.20. Childcare
    # then draws on 8,000 - 1,300 - 4,041.96 = 2,658.04 of earnings and
    # 2,000 - 889.20 = 1,110.80 of WTC, 3,768.84 in all: income is 13,000 -
    # 5,341.96 - 889.20 - 3,768.84 = 3,000, and the award 8,450.
    # (182 * 6,076.98 + 183 * 8,450) / 365 = 7,266.74.
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        7_266.74, abs=TOLERANCE
    )


@pytest.mark.parametrize(
    "supplied,award",
    [
        # Before: 10,400 - 0.65 * 2,850.80 = 8,546.98. After: 10,400 - 0.65 *
        # (4,000 - 2,000) = 9,100. (182 * 8,546.98 + 183 * 9,100) / 365.
        (0, 8_824.25),
        # Before 5 October, 2,000 >= 260 + 889.20, so the additional earnings
        # disregard applies alongside the supplied 100: income 4,000 -
        # 1,149.20 - 100 = 2,750.80, and the award 10,400 - 0.65 * 2,750.80 =
        # 8,611.98. After it, income 4,000 - 2,000 - 100 = 1,900, and the
        # award 9,165. (182 * 8,611.98 + 183 * 9,165) / 365.
        (100, 8_889.25),
    ],
)
def test_supplied_annual_wtc_disregard_applies_in_every_segment(supplied, award):
    sim = segmented([specified_claimant(net=2_000)], active=True)
    sim.set_input("housing_benefit_wtc_disregard", YEAR, [supplied])
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        award, abs=TOLERANCE
    )


def test_supplied_wtc_disregard_reaches_each_segment_limit():
    """The lone parent of the childcare test above, with an annual WTC
    disregard of £500 supplied."""
    unit = case(specified=True, net=8_000, wtc=2_000, other=3_000)
    sim = segmented([unit], active=True)
    sim.set_input("housing_benefit_wtc_disregard", YEAR, [500])
    # Before 5 October the limit is 6,700 + 1,500 = 8,200, so childcare
    # takes the whole 4,160 charge, and 8,000 >= 1,300 + 4,160 + 889.20:
    # income is 13,000 - 2,189.20 - 500 - 4,160 = 6,150.80, and the award
    # 10,400 - 0.65 * 6,150.80 = 6,401.98. After it, childcare draws on
    # 8,000 - 1,300 - 4,041.96 = 2,658.04 of earnings and 2,000 - 500 =
    # 1,500 of WTC, 4,158.04 in all: income is 13,000 - 5,341.96 - 500 -
    # 4,158.04 = 3,000, and the award 8,450.
    # (182 * 6,401.98 + 183 * 8,450) / 365 = 7,428.80.
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        7_428.80, abs=TOLERANCE
    )


def segment_outputs(sim):
    return {
        **results(sim, YEAR),
        "award": np.asarray(
            sim.calculate("housing_benefit_entitlement", YEAR), dtype=float
        ),
    }


def outside_specified_accommodation(units):
    return [{**unit, "specified": False} for unit in units]


@PROPERTY_SETTINGS
@given(units=segment_populations().map(outside_specified_accommodation))
@example(units=WITNESSES)
@example(units=outside_specified_accommodation(SEGMENT_EDGE_CASES))
@example(units=outside_specified_accommodation(SUPPLIED_SEGMENT_EDGE_CASES))
def test_forwarding_reforms_change_nothing_with_tax_credits_kept(units):
    """In 2026-27, under a reform that keeps tax credits, a reform that
    replaces the childcare deduction, its limit or the WTC disregard with a
    formula that only calls the model's own changes no output, award
    included, for families outside specified or temporary accommodation."""
    assert_forwarding_changes_nothing(
        lambda tax_benefit_system: simulation(
            units, YEAR, tax_benefit_system=tax_benefit_system, dated_accommodation=True
        ),
        {None: TAX_CREDITS, **FORWARDED},
        segment_outputs,
    )


def test_replacement_wtc_disregard_applies_its_annual_amount_in_every_segment():
    """A replacement formula gives one annual amount, which every segment
    deducts, as a replacement for the childcare deduction, its limit or the
    earnings disregard does. That matches the
    model's segments while both stay on the taper, so even a formula that
    only calls the model's own can move the award once a segment leaves it.
    The model's segments give 10,124.25. With the annual 445.82 in each:
    before 5 October, income is 4,000 - 1,149.20 - 445.82 = 2,404.98, and
    the award 10,400 - 0.65 * 404.98 = 10,136.76. After it, income is 4,000
    - 2,000 - 445.82 = 1,554.18, below the 2,000 applicable amount, so the
    award is 10,400. (182 * 10,136.76 + 183 * 10,400) / 365 = 10,268.74."""
    unit = specified_claimant(net=2_000, applicable_amount=2_000)
    sim = simulation(
        [unit],
        YEAR,
        tax_benefit_system=FORWARDED["housing_benefit_wtc_disregard"],
        dated_accommodation=True,
    )
    assert sim.calculate("housing_benefit_wtc_disregard", YEAR)[0] == pytest.approx(
        445.82, abs=TOLERANCE
    )
    assert sim.calculate("housing_benefit_entitlement", YEAR)[0] == pytest.approx(
        10_268.74, abs=TOLERANCE
    )


@PROPERTY_SETTINGS
@given(units=segment_populations(), active=st.booleans())
@example(units=SEGMENT_EDGE_CASES, active=True)
@example(units=SEGMENT_EDGE_CASES, active=False)
@example(units=SUPPLIED_SEGMENT_EDGE_CASES, active=True)
@example(units=SUPPLIED_LIMIT_SEGMENT_EDGE_CASES, active=True)
def test_segmented_award_equals_the_regulations_with_one_additional_disregard(
    units, active
):
    sim = segmented(units, active)
    award = sim.calculate("housing_benefit_entitlement", YEAR)
    np.testing.assert_allclose(
        award, [legal_award(unit, active) for unit in units], rtol=0, atol=TOLERANCE
    )
    segments = model_segments(sim)
    calculated = units[0]["supplied"] is None and units[0]["supplied_limit"] is None
    for segment in segments:
        both = (segment["additional"] > TOLERANCE) & (segment["reserve"] > 0)
        assert not both.any(), [unit for unit, b in zip(units, both) if b]
        if calculated:
            # The whole-charge test and the test of the deduction in force
            # agree wherever the model calculates the deduction.
            np.testing.assert_allclose(
                segment["kept_back"], segment["reserve"], rtol=0, atol=TOLERANCE
            )
    np.testing.assert_allclose(
        sim.calculate("housing_benefit_wtc_disregard", YEAR),
        sum(segment["share"] * segment["reserve"] for segment in segments),
        rtol=0,
        atol=TOLERANCE,
    )


@PROPERTY_SETTINGS
@given(units=segment_populations(), active=st.booleans())
@example(units=SEGMENT_EDGE_CASES, active=True)
@example(units=SEGMENT_EDGE_CASES, active=False)
@example(units=SUPPLIED_SEGMENT_EDGE_CASES, active=False)
def test_segmented_previous_path_agrees_where_paragraph_56_does_not_apply(
    units, active
):
    unchanged = [
        unit
        for unit in units
        if all(segment["reserve"] == 0 for segment in legal_segments(unit, active))
    ]
    if not active:
        assert len(unchanged) == len(units)
    unchanged.append(specified_claimant(net=8_000, **same_supply(units, 0)))
    current = segmented(unchanged, active).calculate(
        "housing_benefit_entitlement", YEAR
    )
    previous = segmented(unchanged, active, previous=True).calculate(
        "housing_benefit_entitlement", YEAR
    )
    np.testing.assert_allclose(current, previous, rtol=0, atol=TOLERANCE)
