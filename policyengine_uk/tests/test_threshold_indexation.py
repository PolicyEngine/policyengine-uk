"""Tests for indexing the income tax and NICs thresholds after the freeze.

Income Tax Act 2007 s57(3) raises the personal allowance (PA) by the
September CPI increase, with the increase rounded up to a multiple of £10;
s21(3) raises the basic rate limit (BRL) by the same percentage, with the
result rounded up to a multiple of £100. Finance Act 2021 s5, as amended by
Finance Act 2023 s5 and Finance Act 2026 s10, fixes both and disapplies the
indexation to 2030-31. The government keeps the primary threshold (PT) and
lower profits limit (LPL) aligned with the PA, and the upper earnings and
profits limits (UEL, UPL) with the higher rate threshold, PA + BRL. After
2030-31 it says all of them will be uprated by September CPI (Explanatory
Memorandum to SI 2026/231 para 5.1). ``create_threshold_indexation`` writes
those paths; the secondary threshold (ST) rises by September CPI, unrounded.

Model year Y is the tax year starting 6 April Y. The model stores the PT and
UEL as the annual amount over 52, to the penny (241.73 and 966.73), so 52
weeks of them differ from the annual amount by at most 52 half-pennies.

Invariants:

1. Statutory steps, for any previous amount and any September CPI increase
   g: the PA rises by the smallest multiple of £10 at or above PA x g; the
   BRL becomes the smallest multiple of £100 at or above BRL x (1 + g);
   neither changes when g <= 0. Both never fall and are non-decreasing in g
   and in the previous amount. They agree with an independent exact-rational
   transcription of the statute (differential).
2. Outturn: from 2020-21's £12,500 and £37,500 and September 2020 CPI of
   0.5%, the steps give £12,570 and £37,700, the 2021-22 amounts in the
   Income Tax (Indexation) Order 2021 (SI 2021/111) arts 2 and 3(a).
3. Freeze: the model's PA is £12,570 and BRL £37,700 in 2022-2030.
4. Reference path: in 2031-2039 the model's PA and BRL equal the statute
   applied year by year, in exact rationals, to the model's own September
   CPI input; 2040 holds 2039, the last year of the economic assumptions.
5. Alignment in every year 2021-2040: UPL = PA + BRL and 52 x UEL is within
   £0.26 of the UPL. From 2023: LPL = PA and 52 x PT is within £0.26 of the
   LPL. Intended exceptions, as the law stood: in 2021-22 the PT and LPL
   were £9,568 a year, below the PA; in 2022-23 the PT rose to the PA only
   from 6 July 2022 and the LPL was £11,908 for the whole year. The model's
   2023-24 LPL (£11,908, not £12,570) is #1968.
6. Secondary threshold: from 2031, ST(Y) = ST(Y-1) x (1 + g_Y).
7. For any freeze end and September CPI path (function level): values up to
   each parameter's last stated year are unchanged; after it, each NICs
   threshold equals its income tax equivalent for that year (taking stated
   income tax values where the NICs freeze ends first). The PA, BRL and ST
   never fall, and an aligned NICs threshold never falls after its first
   indexed year. That first year can fall, by intent, when the stated NICs
   amount was above its income tax equivalent: it realigns. Running the
   indexation twice changes nothing. Indexed values are keyed to 1 January,
   so the unconverted ``parameters.baseline`` copy reads the same amounts.
8. Scenarios: a different September CPI moves the PA, BRL and NICs
   thresholds together by the statute; with September CPI <= 0, or with no
   economic assumptions, they stay at their frozen levels.
9. No double indexing: none of the seven parameters carries ``uprating``
   metadata, so core uprating does not extend them.
10. The September CPI series: each April's rise is the previous September's
    CPI to 0.1 percentage points (halves up), and zero unless positive; its
    index compounds those rises.
"""

import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    september_cpi_uprating_rate,
)
from policyengine_uk.parameters.gov.hmrc.create_threshold_indexation import (
    add_threshold_indexation,
    index_basic_rate_limit,
    index_personal_allowance,
    index_secondary_threshold,
    weekly_equivalent,
)
from policyengine_uk.scenarios import no_economic_assumptions

PARAMETER_DIR = Path(policyengine_uk.__file__).parent / "parameters"
FROZEN_YEARS = range(2022, 2031)
INDEXED_YEARS = range(2031, 2040)
ALIGNMENT_YEARS = range(2021, 2041)
# 52 weeks of an amount rounded to the nearest penny.
WEEKLY_ROUNDING = 52 * 0.005
# The model stores parameter values as Python floats; arrays are float32.
EXACT = 1e-6

PATHS = {
    "personal_allowance": "income_tax/allowances/personal_allowance/amount.yaml",
    "basic_rate_limit": "income_tax/rates/uk.yaml",
    "primary_threshold": "national_insurance/class_1/thresholds/primary_threshold.yaml",
    "upper_earnings_limit": "national_insurance/class_1/thresholds/upper_earnings_limit.yaml",
    "secondary_threshold": "national_insurance/class_1/thresholds/secondary_threshold.yaml",
    "lower_profits_limit": "national_insurance/class_4/thresholds/lower_profits_limit.yaml",
    "upper_profits_limit": "national_insurance/class_4/thresholds/upper_profits_limit.yaml",
}


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def threshold_parameters(root):
    """The seven parameters under a ``gov`` node."""
    hmrc = root.hmrc
    class_1 = hmrc.national_insurance.class_1.thresholds
    class_4 = hmrc.national_insurance.class_4.thresholds
    return {
        "personal_allowance": hmrc.income_tax.allowances.personal_allowance.amount,
        # Bracket 1 itself: a scale read at an instant sorts its thresholds,
        # so its thresholds[1] would be the £125,140 additional rate threshold
        # once the basic rate limit passed it.
        "basic_rate_limit": hmrc.income_tax.rates.uk.brackets[1].threshold,
        "primary_threshold": class_1.primary_threshold,
        "upper_earnings_limit": class_1.upper_earnings_limit,
        "secondary_threshold": class_1.secondary_threshold,
        "lower_profits_limit": class_4.lower_profits_limit,
        "upper_profits_limit": class_4.upper_profits_limit,
    }


def thresholds(system, year, root=None, instant=None):
    """Each threshold in tax year ``year`` (by default from the processed gov)."""
    root = system.parameters.gov if root is None else root
    at = str(year) if instant is None else instant
    return {
        name: float(parameter(at))
        for name, parameter in threshold_parameters(root).items()
    }


# Independent transcription of the statute in exact rationals: integers and
# Fractions only, no Decimal and no code from the module under test.


def reference_increase(september_cpi) -> Fraction:
    """September CPI as published (0.1pp, halves up); zero unless positive."""
    tenths = math.floor(Fraction(repr(float(september_cpi))) * 1000 + Fraction(1, 2))
    return Fraction(tenths, 1000) if tenths > 0 else Fraction(0)


def reference_personal_allowance(previous: Fraction, increase: Fraction) -> Fraction:
    """ITA 2007 s57(2)-(3) Steps 1-3."""
    if increase <= 0:
        return previous
    return previous + 10 * math.ceil(previous * increase / 10)


def reference_basic_rate_limit(previous: Fraction, increase: Fraction) -> Fraction:
    """ITA 2007 s21(1) and (3) Steps 1-2."""
    if increase <= 0:
        return previous
    return Fraction(100 * math.ceil(previous * (1 + increase) / 100))


# Invariant 1: statutory steps.

amount = st.decimals(min_value=0, max_value=1_000_000, places=2)
whole_pounds = st.integers(min_value=0, max_value=1_000_000).map(Decimal)
published_increase = st.integers(min_value=-60, max_value=250).map(
    lambda n: Decimal(n) / 1000
)
any_increase = st.decimals(min_value="-0.1", max_value="0.3", places=6)


@given(
    previous=st.one_of(amount, whole_pounds),
    g=st.one_of(published_increase, any_increase),
)
@example(previous=Decimal(12_570), g=Decimal("0.02"))  # rise 251.4 -> 260
@example(previous=Decimal(12_500), g=Decimal("0.0008"))  # rise 10 exactly
@example(previous=Decimal(0), g=Decimal("0.02"))
def test_personal_allowance_step(previous, g):
    new = index_personal_allowance(previous, g)
    rise = new - previous
    if g <= 0:
        assert new == previous
        return
    assert rise % 10 == 0
    assert previous * g <= rise < previous * g + 10
    assert Fraction(new) == reference_personal_allowance(
        Fraction(previous), Fraction(g)
    )


@given(
    previous=st.one_of(amount, whole_pounds),
    g=st.one_of(published_increase, any_increase),
)
@example(previous=Decimal(37_700), g=Decimal("0.02"))  # 38,454 -> 38,500
@example(previous=Decimal(37_500), g=Decimal("0.004"))  # 37,650 -> 37,700
def test_basic_rate_limit_step(previous, g):
    new = index_basic_rate_limit(previous, g)
    if g <= 0:
        assert new == previous
        return
    assert new % 100 == 0
    assert previous * (1 + g) <= new < previous * (1 + g) + 100
    assert Fraction(new) == reference_basic_rate_limit(Fraction(previous), Fraction(g))


@given(
    previous=amount,
    other=amount,
    g=st.one_of(published_increase, any_increase),
    h=st.one_of(published_increase, any_increase),
)
def test_steps_never_fall_and_are_monotone(previous, other, g, h):
    low, high = sorted([previous, other])
    g_low, g_high = sorted([g, h])
    for step in (
        index_personal_allowance,
        index_basic_rate_limit,
        index_secondary_threshold,
    ):
        assert step(previous, g) >= previous
        assert step(previous, g_low) <= step(previous, g_high)
        assert step(low, g) <= step(high, g)


@given(annual=amount)
def test_weekly_equivalent_is_annual_over_52_to_the_penny(annual):
    weekly = weekly_equivalent(annual)
    assert weekly == weekly.quantize(Decimal("0.01"))
    assert abs(52 * weekly - annual) <= Decimal("0.26")


def test_weekly_equivalents_reproduce_the_stored_convention():
    assert weekly_equivalent(Decimal(12_570)) == Decimal("241.73")
    assert weekly_equivalent(Decimal(50_270)) == Decimal("966.73")


# Invariant 2: outturn.


def test_steps_reproduce_the_income_tax_indexation_order_2021(system):
    # SI 2021/111 arts 2 and 3(a): BRL £37,700 and PA £12,570 for 2021-22,
    # indexed from 2020-21 by September 2020 CPI.
    cpi = system.parameters.gov.economic_assumptions.statutory_uprating_inputs
    september_2020 = Decimal(repr(float(cpi.cpi_september("2020-09-01"))))
    assert september_2020 == Decimal("0.005")
    assert index_personal_allowance(Decimal(12_500), september_2020) == 12_570
    assert index_basic_rate_limit(Decimal(37_500), september_2020) == 37_700
    previous, current = thresholds(system, 2020), thresholds(system, 2021)
    assert previous["personal_allowance"] == 12_500
    assert previous["basic_rate_limit"] == 37_500
    assert current["personal_allowance"] == 12_570
    assert current["basic_rate_limit"] == 37_700


# Invariant 3: freeze.


@pytest.mark.parametrize("year", FROZEN_YEARS)
def test_income_tax_thresholds_frozen_to_2030_31(system, year):
    values = thresholds(system, year)
    assert values["personal_allowance"] == 12_570
    assert values["basic_rate_limit"] == 37_700


# Invariant 4: reference path.


def reference_path(system):
    cpi = system.parameters.gov.economic_assumptions.statutory_uprating_inputs
    pa, brl = Fraction(12_570), Fraction(37_700)
    path = {}
    for year in INDEXED_YEARS:
        g = reference_increase(cpi.cpi_september(f"{year - 1}-09-01"))
        pa = reference_personal_allowance(pa, g)
        brl = reference_basic_rate_limit(brl, g)
        path[year] = (pa, brl, g)
    return path


def test_income_tax_thresholds_follow_the_statute_from_2031_32(system):
    path = reference_path(system)
    for year, (pa, brl, _) in path.items():
        values = thresholds(system, year)
        assert values["personal_allowance"] == pytest.approx(float(pa), abs=EXACT), year
        assert values["basic_rate_limit"] == pytest.approx(float(brl), abs=EXACT), year
    # Indexation resumes from the frozen level, with no catch-up.
    first_g = path[2031][2]
    assert thresholds(system, 2031)["personal_allowance"] == float(
        reference_personal_allowance(Fraction(12_570), first_g)
    )


def test_thresholds_hold_after_the_last_year_of_economic_assumptions(system):
    assert thresholds(system, 2040) == thresholds(system, 2039)


def test_indexed_amounts_are_statutory_multiples(system):
    for year in INDEXED_YEARS:
        values = thresholds(system, year)
        assert values["personal_allowance"] % 10 == 0, year
        assert values["basic_rate_limit"] % 100 == 0, year


# Invariant 5: alignment.


@pytest.mark.parametrize("year", ALIGNMENT_YEARS)
def test_upper_thresholds_align_with_the_higher_rate_threshold(system, year):
    values = thresholds(system, year)
    higher_rate_threshold = values["personal_allowance"] + values["basic_rate_limit"]
    assert values["upper_profits_limit"] == pytest.approx(
        higher_rate_threshold, abs=EXACT
    )
    assert abs(52 * values["upper_earnings_limit"] - values["upper_profits_limit"]) <= (
        WEEKLY_ROUNDING
    )


@pytest.mark.parametrize(
    "year",
    [
        pytest.param(
            2023,
            marks=pytest.mark.xfail(
                reason="#1968: the model's 2023-24 LPL is £11,908, not £12,570",
                strict=False,
            ),
        ),
        *range(2024, 2041),
    ],
)
def test_lower_thresholds_align_with_the_personal_allowance(system, year):
    values = thresholds(system, year)
    assert values["lower_profits_limit"] == pytest.approx(
        values["personal_allowance"], abs=EXACT
    )
    assert abs(52 * values["primary_threshold"] - values["lower_profits_limit"]) <= (
        WEEKLY_ROUNDING
    )


def test_lower_thresholds_before_alignment_are_intended(system):
    # 2021-22: PT £184 a week and LPL £9,568, below the £12,570 PA.
    values = thresholds(system, 2021)
    assert 52 * values["primary_threshold"] == values["lower_profits_limit"] == 9_568
    assert values["personal_allowance"] == 12_570
    # 2022-23: the PT was £190 a week until 5 July 2022 (the model reads the
    # April value) and the LPL £11,908 for the year (NICA 2022 s2).
    values = thresholds(system, 2022)
    assert values["primary_threshold"] == 190
    assert values["lower_profits_limit"] == 11_908
    assert values["personal_allowance"] == 12_570


# Invariant 6: secondary threshold.


def test_secondary_threshold_rises_by_september_cpi_from_2031_32(system):
    path = reference_path(system)
    st_ = Fraction(5_000, 52)
    assert thresholds(system, 2030)["secondary_threshold"] == pytest.approx(
        float(st_), abs=1e-6
    )
    for year in INDEXED_YEARS:
        st_ *= 1 + path[year][2]
        assert thresholds(system, year)["secondary_threshold"] == pytest.approx(
            float(st_), abs=1e-5
        ), year


# Invariant 7: the indexation function on any freeze end and CPI path.


def synthetic_parameters(last_years, rates, horizon, bases):
    def series(base, first, last, month_day="04-06"):
        return {
            "values": {
                f"{year}-{month_day}": float(base) for year in range(first, last + 1)
            }
        }

    data = {
        "gov": {
            "economic_assumptions": {
                "yoy_growth": {
                    "september_cpi_uprating": {
                        "values": {
                            "2010-01-01": None,
                            **{
                                f"{2011 + i}-01-01": float(rate)
                                for i, rate in enumerate(rates)
                            },
                        }
                    }
                },
                "indices": {
                    "september_cpi_uprating": {
                        "values": {
                            f"{year}-01-01": 1.0 for year in range(2010, horizon + 1)
                        }
                    }
                },
            },
            "hmrc": {
                "income_tax": {
                    "allowances": {
                        "personal_allowance": {
                            "amount": series(
                                bases["personal_allowance"],
                                2021,
                                last_years["personal_allowance"],
                            )
                        }
                    },
                    "rates": {
                        "uk": {
                            "brackets": [
                                {
                                    "rate": {"values": {"2015-04-06": 0.2}},
                                    "threshold": {"values": {"2015-04-06": 0}},
                                },
                                {
                                    "rate": {"values": {"2015-04-06": 0.4}},
                                    "threshold": series(
                                        bases["basic_rate_limit"],
                                        2021,
                                        last_years["basic_rate_limit"],
                                        "04-01",
                                    ),
                                },
                            ]
                        }
                    },
                },
                "national_insurance": {
                    "class_1": {
                        "thresholds": {
                            name: series(bases[name], 2021, last_years[name])
                            for name in (
                                "primary_threshold",
                                "upper_earnings_limit",
                                "secondary_threshold",
                            )
                        }
                    },
                    "class_4": {
                        "thresholds": {
                            name: series(bases[name], 2021, last_years[name])
                            for name in ("lower_profits_limit", "upper_profits_limit")
                        }
                    },
                },
            },
        }
    }
    return ParameterNode("", data=data)


def synthetic_values(root, year):
    hmrc = root.gov.hmrc
    instant = f"{year}-04-30"
    return {
        "personal_allowance": hmrc.income_tax.allowances.personal_allowance.amount(
            instant
        ),
        "basic_rate_limit": hmrc.income_tax.rates.uk.brackets[1].threshold(instant),
        "primary_threshold": hmrc.national_insurance.class_1.thresholds.primary_threshold(
            instant
        ),
        "upper_earnings_limit": hmrc.national_insurance.class_1.thresholds.upper_earnings_limit(
            instant
        ),
        "secondary_threshold": hmrc.national_insurance.class_1.thresholds.secondary_threshold(
            instant
        ),
        "lower_profits_limit": hmrc.national_insurance.class_4.thresholds.lower_profits_limit(
            instant
        ),
        "upper_profits_limit": hmrc.national_insurance.class_4.thresholds.upper_profits_limit(
            instant
        ),
    }


NAMES = list(PATHS)
# The amounts stated through 2030-31.
FROZEN_AMOUNTS = {
    "personal_allowance": 12_570,
    "basic_rate_limit": 37_700,
    "primary_threshold": 241.73,
    "upper_earnings_limit": 966.73,
    "secondary_threshold": 96.153846,
    "lower_profits_limit": 12_570,
    "upper_profits_limit": 50_270,
}
NICS_ALIGNED = {
    "lower_profits_limit": lambda pa, brl: pa,
    "upper_profits_limit": lambda pa, brl: pa + brl,
    "primary_threshold": lambda pa, brl: float(weekly_equivalent(Decimal(repr(pa)))),
    "upper_earnings_limit": lambda pa, brl: float(
        weekly_equivalent(Decimal(repr(pa + brl)))
    ),
}


@settings(
    max_examples=60,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    last_years=st.fixed_dictionaries(
        {name: st.integers(min_value=2024, max_value=2038) for name in NAMES}
    ),
    rates=st.lists(published_increase.map(float), min_size=64, max_size=64),
    horizon=st.integers(min_value=2030, max_value=2045),
    bases=st.fixed_dictionaries(
        {
            "personal_allowance": st.integers(1_000, 2_000).map(lambda n: 10 * n),
            "basic_rate_limit": st.integers(300, 450).map(lambda n: 100 * n),
            "primary_threshold": st.integers(15_000, 30_000).map(lambda n: n / 100),
            "upper_earnings_limit": st.integers(80_000, 120_000).map(lambda n: n / 100),
            "secondary_threshold": st.integers(5_000, 20_000).map(lambda n: n / 100),
            "lower_profits_limit": st.integers(5_000, 20_000),
            "upper_profits_limit": st.integers(40_000, 70_000),
        }
    ),
)
@example(
    # The current freeze: everything stated to 2030, 2% a year.
    last_years={name: 2030 for name in NAMES},
    rates=[0.02] * 64,
    horizon=2039,
    bases=FROZEN_AMOUNTS,
)
def test_indexation_function_on_any_freeze_and_cpi_path(
    last_years, rates, horizon, bases
):
    root = synthetic_parameters(last_years, rates, horizon, bases)
    add_threshold_indexation(root)
    years = range(2021, horizon + 3)
    values = {year: synthetic_values(root, year) for year in years}
    rate = {2011 + i: Decimal(repr(r)) for i, r in enumerate(rates)}

    for name in NAMES:
        last = last_years[name]
        for year in years:
            value = values[year][name]
            if year <= last:
                # Stated values are unchanged.
                assert value == pytest.approx(float(bases[name]), abs=EXACT), (
                    name,
                    year,
                )
            elif year <= horizon:
                previous = values[year - 1][name]
                if name in NICS_ALIGNED:
                    pa = values[year]["personal_allowance"]
                    brl = values[year]["basic_rate_limit"]
                    expected = NICS_ALIGNED[name](pa, brl)
                    assert value == pytest.approx(expected, abs=EXACT), (name, year)
                    if year - 1 > last:
                        assert value >= previous - EXACT, (name, year)
                else:
                    step = {
                        "personal_allowance": index_personal_allowance,
                        "basic_rate_limit": index_basic_rate_limit,
                        "secondary_threshold": index_secondary_threshold,
                    }[name]
                    expected = step(Decimal(repr(previous)), rate[year])
                    assert value == pytest.approx(float(expected), rel=1e-12), (
                        name,
                        year,
                    )
                    assert value >= previous, (name, year)
            else:
                # Past the horizon the last value holds.
                assert value == values[horizon][name], (name, year)

    # Running again changes nothing.
    before = {year: synthetic_values(root, year) for year in years}
    add_threshold_indexation(root)
    assert {year: synthetic_values(root, year) for year in years} == before


def test_a_nics_threshold_stated_above_its_equivalent_realigns():
    # Intended: an LPL stated at £12,571 to 2024-25 realigns to the £12,570
    # personal allowance in 2025-26, even with no CPI rise.
    last_years = {name: 2030 for name in NAMES} | {"lower_profits_limit": 2024}
    bases = FROZEN_AMOUNTS | {"lower_profits_limit": 12_571}
    root = synthetic_parameters(last_years, [0.0] * 64, 2039, bases)
    add_threshold_indexation(root)
    assert synthetic_values(root, 2024)["lower_profits_limit"] == 12_571
    for year in range(2025, 2041):
        assert synthetic_values(root, year)["lower_profits_limit"] == 12_570, year


@pytest.mark.parametrize("year", [2030, *INDEXED_YEARS, 2040])
def test_nested_baseline_reads_the_same_amounts(system, year):
    # parameters.baseline is cloned before fiscal-year conversion, so it is
    # read at 1 January; indexed values keyed to 1 January give it the same
    # amount as the converted gov tree.
    nested = thresholds(
        system, year, root=system.parameters.baseline.gov, instant=f"{year}-01-01"
    )
    assert nested == thresholds(system, year)


# Invariant 8: scenarios.


def system_with_september_cpi(values):
    system = CountryTaxBenefitSystem()
    system.reset_parameters()
    cpi_september = system.parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september
    for date, value in values.items():
        cpi_september.update(period=f"year:{date}:1", value=value)
    system.process_parameters()
    return system


def test_a_higher_september_cpi_moves_every_threshold_by_the_statute():
    system = system_with_september_cpi({"2030-09-01": 0.05})
    values = thresholds(system, 2031)
    # s57(3): 12,570 x 5% = 628.50, rounded up to 630. s21(3): 37,700 x 1.05
    # = 39,585, rounded up to 39,600.
    assert values["personal_allowance"] == 13_200
    assert values["basic_rate_limit"] == 39_600
    assert values["lower_profits_limit"] == 13_200
    assert values["upper_profits_limit"] == 52_800
    assert values["primary_threshold"] == pytest.approx(253.85)  # 13,200 / 52
    assert values["upper_earnings_limit"] == pytest.approx(1_015.38)  # 52,800 / 52
    assert values["secondary_threshold"] == pytest.approx(5_000 * 1.05 / 52)


def test_no_rise_when_september_cpi_falls():
    # s57(2) and s21(1): no indexation unless September CPI is higher.
    system = system_with_september_cpi({"2030-09-01": -0.005})
    assert thresholds(system, 2031) == thresholds(system, 2030)


def test_a_basic_rate_limit_above_the_additional_rate_threshold_is_kept():
    # 14.2% a year takes the BRL past the fixed £125,140 additional rate
    # threshold by 2039; the parameter still follows s21(3).
    system = system_with_september_cpi(
        {f"{year}-09-01": 0.142 for year in range(2030, 2039)}
    )
    for year, (pa, brl, _) in reference_path(system).items():
        values = thresholds(system, year)
        assert values["personal_allowance"] == float(pa), year
        assert values["basic_rate_limit"] == float(brl), year
        assert values["upper_profits_limit"] == float(pa + brl), year
    assert thresholds(system, 2039)["basic_rate_limit"] > 125_140


def test_thresholds_stay_frozen_without_economic_assumptions():
    situation = {
        "people": {"person": {"age": {2025: 40}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }
    simulation = Simulation(situation=situation, scenario=no_economic_assumptions)
    system = simulation.tax_benefit_system
    for year in (2031, 2035, 2040):
        assert thresholds(system, year) == thresholds(system, 2030), year


# Invariant 9: no double indexing.


@pytest.mark.parametrize("name", NAMES)
def test_indexed_parameters_carry_no_uprating(name):
    data = yaml.safe_load((PARAMETER_DIR / "gov/hmrc" / PATHS[name]).read_text())
    if name == "basic_rate_limit":
        metadata = data["brackets"][1]["threshold"]["metadata"]
    else:
        metadata = data["metadata"]
    assert "uprating" not in metadata


# Invariant 10: the September CPI series.


@given(raw=st.decimals(min_value="-1", max_value="10", places=6))
@example(raw=Decimal("0.00049"))  # rounds to 0.000: no rise
@example(raw=Decimal("0.0185"))  # 0.019
@example(raw=Decimal("0.0195"))  # 0.020
@example(raw=Decimal("-0.005"))  # a fall: no rise
def test_september_cpi_rise_is_the_published_rate_and_never_negative(raw):
    rise = september_cpi_uprating_rate(float(raw))
    assert Fraction(repr(rise)) == reference_increase(raw)


def test_september_cpi_series_and_index_follow_the_input(system):
    economic_assumptions = system.parameters.gov.economic_assumptions
    cpi_september = economic_assumptions.statutory_uprating_inputs.cpi_september
    rises = economic_assumptions.yoy_growth.september_cpi_uprating
    index = economic_assumptions.indices.september_cpi_uprating
    for year in range(2011, 2040):
        expected = reference_increase(cpi_september(f"{year - 1}-09-01"))
        assert Fraction(repr(float(rises(str(year))))) == expected, year
        # The index is stored to 5 decimal places.
        ratio = float(index(str(year))) / float(index(str(year - 1)))
        assert ratio == pytest.approx(1 + float(expected), abs=2e-5), year


# End to end: the indexed thresholds reach the tax and NICs calculations.


def test_income_tax_and_nics_use_the_indexed_thresholds_in_2031(system):
    values = thresholds(system, 2031)
    pa = values["personal_allowance"]
    hrt = pa + values["basic_rate_limit"]
    pt, uel = 52 * values["primary_threshold"], 52 * values["upper_earnings_limit"]
    incomes = [pa - 1, pa + 1, hrt - 1, hrt + 1, 60_000.0]
    people = {
        f"p{i}": {
            "age": {2031: 40},
            "employment_income": {2031: income},
            # From 2029 the salary sacrifice cap's broad-base haircut (a
            # behavioural assumption) trims employment income before tax.
            "salary_sacrifice_broad_base_haircut": {2031: 0},
            "ni_class_1_income": {2031: income},
            "employee_pension_contributions": {2031: 0},
            "employer_pension_contributions": {2031: 0},
        }
        for i, income in enumerate(incomes)
    }
    situation = {
        "people": people,
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(incomes))},
        "households": {
            f"h{i}": {"members": [f"p{i}"], "region": {2031: "LONDON"}}
            for i in range(len(incomes))
        },
    }
    simulation = Simulation(situation=situation)
    income_tax = simulation.calculate("income_tax", 2031)
    primary = simulation.calculate("ni_class_1_employee_primary", 2031)
    additional = simulation.calculate("ni_class_1_employee_additional", 2031)
    for i, income in enumerate(incomes):
        expected_tax = 0.2 * min(max(income - pa, 0), hrt - pa) + 0.4 * max(
            income - hrt, 0
        )
        expected_primary = 0.08 * min(max(income - pt, 0), uel - pt)
        expected_additional = 0.02 * max(income - uel, 0)
        assert income_tax[i] == pytest.approx(expected_tax, abs=0.02), income
        assert primary[i] == pytest.approx(expected_primary, abs=0.02), income
        assert additional[i] == pytest.approx(expected_additional, abs=0.02), income
    assert np.all(np.diff(income_tax) >= 0)
