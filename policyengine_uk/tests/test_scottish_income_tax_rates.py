import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import statutory_parameters

# Each year's Scottish rate resolution, restated paragraph by paragraph from
# the motion at
# https://www.parliament.scot/chamber-and-committees/votes-and-motions/<motion>:
# the rate, and the limit of taxable income it is charged up to (None for the
# last rate, which has no limit). The limits are above the personal allowance.
SCOTTISH_RATE_RESOLUTIONS = {
    2017: ("S5M-03912", [(0.20, 31_500), (0.40, 150_000), (0.45, None)]),
    2018: (
        "S5M-10397",
        [(0.19, 2_000), (0.20, 12_150), (0.21, 31_580), (0.41, 150_000), (0.46, None)],
    ),
    2019: (
        "S5M-15879",
        [(0.19, 2_049), (0.20, 12_444), (0.21, 30_930), (0.41, 150_000), (0.46, None)],
    ),
    2020: (
        "S5M-21090",
        [(0.19, 2_085), (0.20, 12_658), (0.21, 30_930), (0.41, 150_000), (0.46, None)],
    ),
    2021: (
        "S5M-24225",
        [(0.19, 2_097), (0.20, 12_726), (0.21, 31_092), (0.41, 150_000), (0.46, None)],
    ),
    2022: (
        "S6M-03019",
        [(0.19, 2_162), (0.20, 13_118), (0.21, 31_092), (0.41, 150_000), (0.46, None)],
    ),
    2023: (
        "S6M-07853",
        [(0.19, 2_162), (0.20, 13_118), (0.21, 31_092), (0.42, 125_140), (0.47, None)],
    ),
    2024: (
        "S6M-12252",
        [
            (0.19, 2_306),
            (0.20, 13_991),
            (0.21, 31_092),
            (0.42, 62_430),
            (0.45, 125_140),
            (0.48, None),
        ],
    ),
    2025: (
        "S6M-16531",
        [
            (0.19, 2_827),
            (0.20, 14_921),
            (0.21, 31_092),
            (0.42, 62_430),
            (0.45, 125_140),
            (0.48, None),
        ],
    ),
    2026: (
        "S6M-20844",
        [
            (0.19, 3_967),
            (0.20, 16_956),
            (0.21, 31_092),
            (0.42, 62_430),
            (0.45, 125_140),
            (0.48, None),
        ],
    ),
}

# gov.scot's table for each year: the standard personal allowance it assumes
# and the top of each band but the last, as income including that allowance.
# 2017-18: https://www.gov.scot/news/income-tax-rates-set/
# 2018-19: https://www.gov.scot/publications/scottish-income-tax-2018-2019/
# 2019-20 to 2021-22: https://www.gov.scot/publications/scottish-income-tax-2019-2020/
# and the 2020-2021 and 2021-2022 pages, now in the National Records of
# Scotland web archive.
# 2022-23 onwards: https://www.gov.scot/publications/scottish-income-tax-rates-and-bands/
GOV_SCOT_TABLES = {
    2017: (11_500, [43_000, 150_000]),
    2018: (11_850, [13_850, 24_000, 43_430, 150_000]),
    2019: (12_500, [14_549, 24_944, 43_430, 150_000]),
    2020: (12_500, [14_585, 25_158, 43_430, 150_000]),
    2021: (12_570, [14_667, 25_296, 43_662, 150_000]),
    2022: (12_570, [14_732, 25_688, 43_662, 150_000]),
    2023: (12_570, [14_732, 25_688, 43_662, 125_140]),
    2024: (12_570, [14_876, 26_561, 43_662, 75_000, 125_140]),
    2025: (12_570, [15_397, 27_491, 43_662, 75_000, 125_140]),
    2026: (12_570, [16_537, 29_526, 43_662, 75_000, 125_140]),
}
# ITA 2007 s. 35(2): the allowance falls by half the income above £100,000.
ALLOWANCE_TAPER_START = 100_000

YEARS = sorted(SCOTTISH_RATE_RESOLUTIONS)


def resolution_scale(year):
    """The marginal rate schedule a resolution sets: thresholds and rates."""
    bands = SCOTTISH_RATE_RESOLUTIONS[year][1]
    thresholds = [0] + [limit for _, limit in bands[:-1]]
    return thresholds, [rate for rate, _ in bands]


@pytest.mark.parametrize(
    "year, thresholds",
    [
        # Scottish Rate Resolutions S6M-12252, S6M-16531 and S6M-20844.
        (2024, [0, 2306, 13991, 31092, 62430, 125140]),
        (2025, [0, 2827, 14921, 31092, 62430, 125140]),
        (2026, [0, 3967, 16956, 31092, 62430, 125140]),
    ],
)
def test_scottish_income_tax_thresholds_match_the_resolution(year, thresholds):
    rates = system.parameters.gov.hmrc.income_tax.rates.scotland.rates(f"{year}-04-06")

    assert rates.thresholds == thresholds


@pytest.mark.parametrize("year", [2026, 2027, 2028, 2029, 2030])
def test_scottish_announced_threshold_freeze_then_cpi_projection(year):
    # Scottish Budget 2026-27, Income Tax Policy: the higher, advanced and
    # top cash thresholds stay fixed through 2028-29. Future CPI uprating
    # is the model's existing projection, not a Budget commitment.
    # https://www.gov.scot/publications/scottish-budget-2026-2027/pages/4/
    rates = system.parameters.gov.hmrc.income_tax.rates.scotland.rates(year)
    cpi = system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index
    after_freeze = 1 if year <= 2028 else cpi(year) / cpi(2028)

    assert rates.thresholds[3:] == pytest.approx(
        [amount * after_freeze for amount in (31_092, 62_430, 125_140)], abs=1e-6
    )
    # Lower bands retain their pre-existing projection from the 2026 values.
    assert rates.thresholds[:3] == pytest.approx(
        [0, 3_967 * cpi(year) / cpi(2026), 16_956 * cpi(year) / cpi(2026)],
        abs=1e-6,
    )
    assert rates.rates == [0.19, 0.20, 0.21, 0.42, 0.45, 0.48]


@pytest.mark.parametrize("year", YEARS)
def test_scottish_rates_and_limits_match_each_resolution(year):
    """The model year's schedule is the one that year's resolution sets.

    The model reads each tax year's parameters at 30 April, so the year
    label 2019 carries the 2019-20 resolution.
    """
    thresholds, rates = resolution_scale(year)
    scale = system.parameters(year).gov.hmrc.income_tax.rates.scotland.rates

    assert list(scale.thresholds) == pytest.approx(thresholds, abs=0)
    assert list(scale.rates) == pytest.approx(rates, abs=0)


@pytest.fixture(scope="module")
def statutory_scottish_rates():
    return statutory_parameters().gov.hmrc.income_tax.rates.scotland.rates


@pytest.mark.parametrize("year", YEARS)
def test_each_resolution_holds_for_its_whole_tax_year(year, statutory_scottish_rates):
    """A resolution applies for the whole of one tax year (SA 1998 s. 80C(3))."""
    thresholds, rates = resolution_scale(year)
    for instant in (f"{year}-04-06", f"{year + 1}-04-05"):
        scale = statutory_scottish_rates(instant)
        assert list(scale.thresholds) == pytest.approx(thresholds, abs=0), instant
        assert list(scale.rates) == pytest.approx(rates, abs=0), instant


@pytest.mark.parametrize("year", YEARS)
def test_scottish_limits_plus_personal_allowance_match_gov_scot_tables(year):
    """The resolution's limits of taxable income are gov.scot's bands less the
    standard personal allowance. Above the point where the allowance is
    withdrawn in full, taxable income and income are the same."""
    allowance, band_tops = GOV_SCOT_TABLES[year]
    parameters = system.parameters(year).gov.hmrc.income_tax
    scale = parameters.rates.scotland.rates
    assert parameters.allowances.personal_allowance.amount == allowance

    assert len(scale.thresholds) == len(band_tops) + 1
    for limit, top in zip(scale.thresholds[1:], band_tops):
        if top <= ALLOWANCE_TAPER_START:
            assert limit + allowance == top
        else:
            assert top >= ALLOWANCE_TAPER_START + 2 * allowance
            assert limit == top


# Hand-built Scottish taxpayers with pay alone, in every year from 2017-18.
# Each example draws many people, as a calculation costs about the same for
# one person as for many.
PEOPLE = 48
PROPERTY_SETTINGS = settings(
    max_examples=4,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
# Above £100,000 the draws are even, so the allowance taper is in whole pounds.
pay = st.one_of(
    st.integers(0, 300_000),
    st.sampled_from(
        sorted(
            {
                top
                for allowance, tops in GOV_SCOT_TABLES.values()
                for top in [allowance, *tops]
            }
            | {ALLOWANCE_TAPER_START, 160_000}
        )
    ),
).map(lambda amount: amount - amount % 2 if amount > ALLOWANCE_TAPER_START else amount)
pays = st.lists(pay, min_size=PEOPLE // 2, max_size=PEOPLE // 2)
raises = st.lists(st.integers(0, 20_000), min_size=PEOPLE // 2, max_size=PEOPLE // 2)


def reference_tax(year, amount):
    """Income tax on pay alone, from the resolution and gov.scot's allowance."""
    allowance = max(
        0, GOV_SCOT_TABLES[year][0] - max(0, amount - ALLOWANCE_TAPER_START) / 2
    )
    taxable = max(0, amount - allowance)
    thresholds, rates = resolution_scale(year)
    tops = thresholds[1:] + [np.inf]
    return sum(
        rate * max(0, min(taxable, top) - bottom)
        for bottom, top, rate in zip(thresholds, tops, rates)
    )


@pytest.fixture(scope="module")
def scottish_sim():
    situation = {
        "people": {
            f"p{i}": {
                "age": {year: 40 for year in YEARS},
                "employment_income": {year: 0 for year in YEARS},
            }
            for i in range(PEOPLE)
        },
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(PEOPLE)},
        "households": {
            f"h{i}": {
                "members": [f"p{i}"],
                "region": {year: "SCOTLAND" for year in YEARS},
            }
            for i in range(PEOPLE)
        },
    }
    return Simulation(situation=situation)


def income_tax_by_year(sim, amounts):
    for year in YEARS:
        # The simulation moves pay to the source of its labour-supply formula.
        sim.set_input("employment_income_before_lsr", year, amounts)
    sim.reset_calculations()
    for year in YEARS:
        np.testing.assert_array_equal(sim.calculate("employment_income", year), amounts)
        assert sim.calculate("pays_scottish_income_tax", year).all()
    return {year: sim.calculate("income_tax", year).astype(float) for year in YEARS}


def tolerance(*amounts):
    """A penny plus rounding of the model's float32 monetary values."""
    return 0.01 + 4e-7 * sum(np.abs(amount) for amount in amounts)


@PROPERTY_SETTINGS
@given(pays, raises)
def test_scottish_pay_is_taxed_as_each_resolution_sets(scottish_sim, drawn, extra):
    """Every year's income tax on pay equals the resolution's bands applied to
    pay less the allowance, and it never falls as pay rises."""
    lower = np.array(drawn, dtype=float)
    upper = lower + np.array(extra) * 2
    upper = np.where(upper > ALLOWANCE_TAPER_START, upper - upper % 2, upper)
    amounts = np.concatenate([lower, upper])
    taxes = income_tax_by_year(scottish_sim, amounts)
    for year, tax in taxes.items():
        expected = np.array([reference_tax(year, amount) for amount in amounts])
        assert (np.abs(tax - expected) <= tolerance(tax, expected)).all(), year
        below, above = np.split(tax, 2)
        assert (above >= below - tolerance(below, above)).all(), year
