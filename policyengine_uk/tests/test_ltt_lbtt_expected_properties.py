"""Property-based tests: LTT and LBTT enter the tax totals once, at full value.

``land_transaction_tax`` (Wales) and ``land_and_buildings_transaction_tax``
(Scotland) are already annual: they charge the prices of properties bought
in the year and the tax on each year's addition to cumulative rent. Their
expected values, ``expected_ltt`` and ``expected_lbtt``, are what
``household_tax``, ``gov_tax`` and ``pre_budget_change_household_tax`` sum,
so the expected value must be the liability itself. Issue 2246: both used to
be multiplied by a 4.5% property sale rate, discounting the purchase draw a
second time.

Each example builds a population of three to five households and simulates
it twice:

- B: the baseline;
- Z: every LTT and LBTT rate (residential, first-time buyer, additional
  dwelling, non-residential and rent schedules) set to zero.

The population varies the year (2022 to 2030), each household's region
(all four nations), purchases of main, additional and non-residential
property (or none), first-home status, residential and non-residential
rent with cumulative rent, earnings and positive weights. "Equal" means
equal up to the float32 rounding of the totals (32 float32 ulps of the
largest value compared, per household); "exactly" means bit-equal.

1. Expected is realised: ``expected_ltt`` is exactly ``land_transaction_tax``
   and ``expected_lbtt`` is exactly ``land_and_buildings_transaction_tax``,
   for every household, and so also in weighted total.
2. Geography: LTT is zero outside Wales and LBTT is zero outside Scotland,
   and both are non-negative.
3. Once, at full value: for each total T, T(B) - T(Z) equals the
   liabilities ``land_transaction_tax + land_and_buildings_transaction_tax``
   in B, independently of 1. The old 4.5% scaling made the gap 0.045 times
   that; counting either twice would double it.
4. Zeroing the rates removes them: ``expected_ltt`` and ``expected_lbtt``
   are exactly 0 in Z, and SDLT is unchanged, so with 3 nothing else in the
   totals moves.

``test_lbtt_and_ltt_match_the_rate_tables`` compares expected LBTT and LTT
with an independent marginal-band calculation from the statutory tables.
It covers both historical Welsh schedules and the current schedules,
including the rate updates from issues 1795 and 1796.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter

from policyengine_uk import Simulation
from policyengine_uk.system import system

ALWAYS = "2000-01-01.2100-12-31"
RATE_ROOTS = ("gov.revenue_scotland.lbtt", "gov.wra.land_transaction_tax")


def zero_rate_reform() -> dict:
    """Every LTT and LBTT rate, and the additional dwelling supplement, at 0."""
    reform = {}
    for root in RATE_ROOTS:
        for parameter in system.parameters.get_child(root).get_descendants():
            if not isinstance(parameter, Parameter):
                continue
            name = parameter.name
            if name.endswith(".rate") or name.endswith(
                "additional_residence_surcharge"
            ):
                reform[name] = {ALWAYS: 0}
    return reform


NO_LTT_OR_LBTT = zero_rate_reform()
TOTALS = ["household_tax", "gov_tax", "pre_budget_change_household_tax"]
VARIABLES = TOTALS + [
    "land_transaction_tax",
    "expected_ltt",
    "land_and_buildings_transaction_tax",
    "expected_lbtt",
    "expected_sdlt",
    "household_weight",
]
REGIONS = ["LONDON", "NORTH_WEST", "NORTHERN_IRELAND", "SCOTLAND", "WALES"]
ULPS = 32

purchase = st.one_of(st.just(0.0), st.floats(40_000, 5_000_000))
rent = st.one_of(st.just(0.0), st.floats(1_000, 400_000))
cumulative_rent = st.one_of(st.just(0.0), st.floats(1_000, 3_000_000))

household = st.fixed_dictionaries(
    {
        "region": st.sampled_from(REGIONS),
        "main_residential_property_purchased": purchase,
        "main_residential_property_purchased_is_first_home": st.booleans(),
        "additional_residential_property_purchased": purchase,
        "non_residential_property_purchased": purchase,
        "rent": rent,
        "cumulative_residential_rent": cumulative_rent,
        "non_residential_rent": rent,
        "cumulative_non_residential_rent": cumulative_rent,
        "household_weight": st.floats(1, 10_000),
        "employment_income": st.floats(0, 200_000),
    }
)


def situation(households: list, year: int) -> dict:
    people, benunits, hh = {}, {}, {}
    for i, inputs in enumerate(households):
        person, benunit = f"person_{i}", f"benunit_{i}"
        people[person] = {
            "age": {year: 30 + 10 * i},
            "employment_income": {year: inputs["employment_income"]},
        }
        benunits[benunit] = {"members": [person]}
        hh[f"household_{i}"] = {
            "members": [person],
            **{
                name: {year: value}
                for name, value in inputs.items()
                if name != "employment_income"
            },
        }
    return {"people": people, "benunits": benunits, "households": hh}


def simulate(households: list, year: int, reform=None) -> dict:
    sim = Simulation(situation=situation(households, year), reform=reform)
    return {
        name: np.asarray(sim.calculate(name, year), dtype=np.float64)
        for name in VARIABLES
    }


def tolerance(*arrays) -> np.ndarray:
    """Per-household rounding allowance for float32 totals."""
    magnitude = np.max(np.abs(np.stack(arrays)), axis=0)
    return ULPS * np.spacing(magnitude.astype(np.float32)).astype(np.float64)


def test_zero_rate_reform_covers_every_schedule():
    # A schedule left out of the reform would leave tax in Z and weaken 3.
    names = set(NO_LTT_OR_LBTT)
    for schedule in (
        "gov.revenue_scotland.lbtt.residential.rate",
        "gov.revenue_scotland.lbtt.residential.first_time_buyer_rate",
        "gov.revenue_scotland.lbtt.non_residential",
        "gov.revenue_scotland.lbtt.rent",
        "gov.wra.land_transaction_tax.residential.primary",
        "gov.wra.land_transaction_tax.residential.higher_rate",
        "gov.wra.land_transaction_tax.non_residential",
        "gov.wra.land_transaction_tax.rent",
    ):
        brackets = system.parameters.get_child(schedule).brackets
        assert brackets, schedule
        for i in range(len(brackets)):
            assert f"{schedule}[{i}].rate" in names
    assert "gov.revenue_scotland.lbtt.residential.additional_residence_surcharge" in (
        names
    )


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    households=st.lists(household, min_size=3, max_size=5),
    year=st.integers(2022, 2030),
)
def test_ltt_and_lbtt_enter_the_totals_once_at_full_value(households, year):
    b = simulate(households, year)
    z = simulate(households, year, NO_LTT_OR_LBTT)
    regions = np.array([h["region"] for h in households])

    ltt, lbtt = b["land_transaction_tax"], b["land_and_buildings_transaction_tax"]

    event(f"LTT charged: {bool((ltt > 0).any())}")
    event(f"LBTT charged: {bool((lbtt > 0).any())}")

    # 1. Expected is realised, per household and in weighted total.
    np.testing.assert_array_equal(b["expected_ltt"], ltt)
    np.testing.assert_array_equal(b["expected_lbtt"], lbtt)
    weight = b["household_weight"]
    assert (b["expected_ltt"] * weight).sum() == (ltt * weight).sum()
    assert (b["expected_lbtt"] * weight).sum() == (lbtt * weight).sum()

    # 2. Geography and sign.
    np.testing.assert_array_equal(ltt[regions != "WALES"], 0)
    np.testing.assert_array_equal(lbtt[regions != "SCOTLAND"], 0)
    assert (ltt >= 0).all() and (lbtt >= 0).all()

    # 3. Once, at full value, in every total.
    transaction_taxes = ltt + lbtt
    for total in TOTALS:
        np.testing.assert_array_less(
            np.abs(b[total] - z[total] - transaction_taxes),
            tolerance(b[total], z[total], transaction_taxes) + 1e-9,
            err_msg=f"{total}: LTT and LBTT not counted once at full value",
        )

    # 4. Zeroing the rates removes them and nothing else.
    np.testing.assert_array_equal(z["expected_ltt"], 0)
    np.testing.assert_array_equal(z["expected_lbtt"], 0)
    np.testing.assert_array_equal(z["expected_sdlt"], b["expected_sdlt"])


# Differential: an independent calculation from the statutory rate tables.
#
# LBTT: SSI 2015/126 schedule, Table A (residential, in force from 1 April
# 2021 after SSI 2020/215's temporary nil band ended) and Table B
# (non-residential, as substituted by SSI 2018/372); first-time buyer relief
# takes the first £175,000 out of charge (LBTT(S)A 2013 schedule 4A para 3);
# the additional dwelling supplement is 8% of the relevant consideration from
# 5 December 2024 (LBTT(S)A 2013 schedule 2A para 4(2), as amended by SSI
# 2024/367).
# LTT: WSI 2018/128 schedule. Table 1 (main rates) as at 2022, before WSI
# 2022/1027 substituted it from 10 October 2022, and as substituted; Table 2
# (higher rates) as substituted by WSI 2020/1618, and by WSI 2024/1311 from
# 11 December 2024; Table 3 (non-residential) as substituted by WSI
# 2020/1618, still in force.
LBTT_RESIDENTIAL = [(0, 0), (145_000, 0.02), (250_000, 0.05), (325_000, 0.10)]
LBTT_RESIDENTIAL += [(750_000, 0.12)]
LBTT_FIRST_TIME_BUYER = [(0, 0), (175_000, 0.02), (250_000, 0.05)]
LBTT_FIRST_TIME_BUYER += [(325_000, 0.10), (750_000, 0.12)]
LBTT_NON_RESIDENTIAL = [(0, 0), (150_000, 0.01), (250_000, 0.05)]
LBTT_SUPPLEMENT_FROM_2024_12_05 = 0.08
LTT_MAIN_2022 = [(0, 0), (180_000, 0.035), (250_000, 0.05), (400_000, 0.075)]
LTT_MAIN_2022 += [(750_000, 0.10), (1_500_000, 0.12)]
LTT_MAIN_FROM_2022_10_10 = [(0, 0), (225_000, 0.06), (400_000, 0.075)]
LTT_MAIN_FROM_2022_10_10 += [(750_000, 0.10), (1_500_000, 0.12)]
LTT_HIGHER_2022 = [(0, 0.04), (180_000, 0.075), (250_000, 0.09)]
LTT_HIGHER_2022 += [(400_000, 0.115), (750_000, 0.14), (1_500_000, 0.16)]
LTT_HIGHER_FROM_2024_12_11 = [(0, 0.05), (180_000, 0.085), (250_000, 0.10)]
LTT_HIGHER_FROM_2024_12_11 += [(400_000, 0.125), (750_000, 0.15), (1_500_000, 0.17)]
LTT_NON_RESIDENTIAL = [(0, 0), (225_000, 0.01), (250_000, 0.05)]
LTT_NON_RESIDENTIAL += [(1_000_000, 0.06)]

PRICES = [0, 40_000, 145_000, 150_000, 175_000, 180_000, 225_000, 250_000]
PRICES += [251_000, 325_000, 400_000, 612_345, 750_000, 1_000_000, 1_500_000]
PRICES += [2_750_000]
# The higher rates and the supplement are compared only at £145,000 and over:
# the rate tables say nothing about the minimum consideration below which a
# transaction is not a higher-rates or supplement transaction.
HIGHER_RATE_PRICES = [price for price in PRICES if price >= 145_000]


def marginal_tax(bands: list, price: float) -> float:
    tax = 0.0
    for i, (threshold, rate) in enumerate(bands):
        top = bands[i + 1][0] if i + 1 < len(bands) else np.inf
        tax += rate * max(0.0, min(price, top) - threshold)
    return tax


def lbtt_with_supplement(price: float) -> float:
    return marginal_tax(LBTT_RESIDENTIAL, price) + (
        LBTT_SUPPLEMENT_FROM_2024_12_05 * price
    )


def modelled_expected_tax(region, year, price_input, first_home, prices):
    n = len(prices)
    sim = Simulation(
        situation={
            "people": {f"person_{i}": {"age": {year: 40}} for i in range(n)},
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(n)
            },
            "households": {
                f"household_{i}": {
                    "members": [f"person_{i}"],
                    "region": {year: region},
                    price_input: {year: price},
                    "main_residential_property_purchased_is_first_home": {
                        year: first_home
                    },
                }
                for i, price in enumerate(prices)
            },
        }
    )
    expected = "expected_lbtt" if region == "SCOTLAND" else "expected_ltt"
    return np.asarray(sim.calculate(expected, year), dtype=np.float64)


MAIN = "main_residential_property_purchased"
ADDITIONAL = "additional_residential_property_purchased"
NON_RESIDENTIAL = "non_residential_property_purchased"


def bands(table):
    return lambda price: marginal_tax(table, price)


# (region, year, input, first home, prices, statutory tax)
DIFFERENTIAL_CASES = {
    "lbtt_main_2026": ("SCOTLAND", 2026, MAIN, False, PRICES, bands(LBTT_RESIDENTIAL)),
    "lbtt_first_home_2026": (
        "SCOTLAND",
        2026,
        MAIN,
        True,
        PRICES,
        bands(LBTT_FIRST_TIME_BUYER),
    ),
    "lbtt_non_residential_2026": (
        "SCOTLAND",
        2026,
        NON_RESIDENTIAL,
        False,
        PRICES,
        bands(LBTT_NON_RESIDENTIAL),
    ),
    "ltt_main_2022": ("WALES", 2022, MAIN, False, PRICES, bands(LTT_MAIN_2022)),
    "ltt_higher_2022": (
        "WALES",
        2022,
        ADDITIONAL,
        False,
        HIGHER_RATE_PRICES,
        bands(LTT_HIGHER_2022),
    ),
    "ltt_non_residential_2026": (
        "WALES",
        2026,
        NON_RESIDENTIAL,
        False,
        PRICES,
        bands(LTT_NON_RESIDENTIAL),
    ),
    "ltt_main_2026": (
        "WALES",
        2026,
        MAIN,
        False,
        PRICES,
        bands(LTT_MAIN_FROM_2022_10_10),
    ),
    "ltt_higher_2026": (
        "WALES",
        2026,
        ADDITIONAL,
        False,
        HIGHER_RATE_PRICES,
        bands(LTT_HIGHER_FROM_2024_12_11),
    ),
    "lbtt_supplement_2026": (
        "SCOTLAND",
        2026,
        ADDITIONAL,
        False,
        HIGHER_RATE_PRICES,
        lbtt_with_supplement,
    ),
}


def assert_matches_statute(region, year, price_input, first_home, prices, statute):
    modelled = modelled_expected_tax(region, year, price_input, first_home, prices)
    reference = np.array([statute(price) for price in prices])
    np.testing.assert_allclose(modelled, reference, rtol=0, atol=0.01)


@pytest.mark.parametrize("case", sorted(DIFFERENTIAL_CASES))
def test_lbtt_and_ltt_match_the_rate_tables(case):
    assert_matches_statute(*DIFFERENTIAL_CASES[case])
