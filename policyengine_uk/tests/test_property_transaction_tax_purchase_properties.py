"""Property-based tests for the purchases that property transaction taxes
are charged on (issue #2238).

Stamp Duty Land Tax, Land and Buildings Transaction Tax and Land Transaction
Tax are charged on a purchase's price. A household's stocks of other
residential and non-residential property are not purchases:
property_purchased sets only the main-residence purchase, and an
additional-dwelling or non-residential purchase is its own input.

Invariants, for any generated population of households across the four
nations, with or without a main-residence purchase:

1. Stocks are not purchases: zeroing a household's other residential and
   non-residential property never changes any transaction tax.
2. A main-residence purchase alone never pays the higher rates for
   additional dwellings: SDLT on residential property is the main-rates tax
   on the main-residence price.
3. An additional-dwelling purchase is charged on its own price at the higher
   rates (nil below the £40,000 minimum), on top of the main-residence tax,
   and the higher rates are never below the main rates.
4. Monotone: SDLT never falls as the additional-dwelling price rises.
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
YEARS = [2022, 2024, 2025, 2027]
REGIONS = ["LONDON", "NORTH_WEST", "NORTHERN_IRELAND", "SCOTLAND", "WALES"]
TAXES = [
    "stamp_duty_land_tax",
    "land_and_buildings_transaction_tax",
    "land_transaction_tax",
    "expected_sdlt",
    "expected_lbtt",
    "expected_ltt",
]
TOLERANCE = 0.01

household_strategy = st.fixed_dictionaries(
    {
        "region": st.sampled_from(REGIONS),
        "main_residence_value": st.integers(0, 3_000_000),
        "other_residential_property_value": st.integers(0, 5_000_000),
        "non_residential_property_value": st.integers(0, 2_000_000),
        "property_purchased": st.booleans(),
        "main_residential_property_purchased_is_first_home": st.booleans(),
        "additional_residential_property_purchased": st.integers(0, 3_000_000),
    }
)
population_strategy = st.lists(household_strategy, min_size=4, max_size=12)


def _situation(households, year):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, household in enumerate(households):
        person = f"p{i}"
        situation["people"][person] = {"age": {year: 40}}
        situation["benunits"][f"b{i}"] = {"members": [person]}
        situation["households"][f"h{i}"] = {
            "members": [person],
            **{key: {year: value} for key, value in household.items()},
        }
    return situation


def _calc(households, year, variables):
    sim = Simulation(situation=_situation(households, year))
    return sim, {v: np.array(sim.calculate(v, year), dtype=float) for v in variables}


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_property_stocks_are_never_purchases(households, year):
    _, with_stocks = _calc(households, year, TAXES)
    without = [
        {
            **h,
            "other_residential_property_value": 0,
            "non_residential_property_value": 0,
        }
        for h in households
    ]
    _, without_stocks = _calc(without, year, TAXES)
    for tax in TAXES:
        assert np.allclose(with_stocks[tax], without_stocks[tax], atol=TOLERANCE)


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_main_residence_purchase_never_pays_the_higher_rates(households, year):
    # Leave the additional-dwelling purchase unset, so a main-residence
    # purchase alone decides it.
    households = [
        {k: v for k, v in h.items() if k != "additional_residential_property_purchased"}
        for h in households
    ]
    sim, out = _calc(
        households,
        year,
        [
            "sdlt_on_residential_property_transactions",
            "main_residential_property_purchased",
            "additional_residential_property_purchased",
        ],
    )
    stamp_duty = sim.tax_benefit_system.parameters(year).gov.hmrc.stamp_duty
    main = stamp_duty.residential.purchase.main
    price = out["main_residential_property_purchased"]
    first_home = np.array(
        [h["main_residential_property_purchased_is_first_home"] for h in households]
    ) & (price < main.first.max)
    main_rates_tax = np.where(
        first_home, main.first.rate.calc(price), main.subsequent.calc(price)
    )
    assert np.all(out["additional_residential_property_purchased"] == 0)
    assert np.allclose(
        out["sdlt_on_residential_property_transactions"],
        main_rates_tax,
        atol=TOLERANCE,
    )


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS))
def test_additional_purchase_is_charged_on_its_own_price(households, year):
    sim, with_purchase = _calc(
        households, year, ["sdlt_on_residential_property_transactions"]
    )
    no_purchase = [
        {**h, "additional_residential_property_purchased": 0} for h in households
    ]
    _, without_purchase = _calc(
        no_purchase, year, ["sdlt_on_residential_property_transactions"]
    )
    purchase = sim.tax_benefit_system.parameters(year).gov.hmrc.stamp_duty.residential
    price = np.array(
        [h["additional_residential_property_purchased"] for h in households],
        dtype=float,
    )
    chargeable = np.where(price < purchase.purchase.additional.min, 0, price)
    higher_rates_tax = purchase.purchase.additional.rate.calc(chargeable)
    extra = (
        with_purchase["sdlt_on_residential_property_transactions"]
        - without_purchase["sdlt_on_residential_property_transactions"]
    )
    assert np.allclose(extra, higher_rates_tax, atol=TOLERANCE)
    # The higher rates are never below the main rates on the same price.
    assert np.all(
        higher_rates_tax
        >= purchase.purchase.main.subsequent.calc(chargeable) - TOLERANCE
    )


@PROPERTY_SETTINGS
@given(population_strategy, st.sampled_from(YEARS), st.integers(1, 1_000_000))
def test_stamp_duty_never_falls_as_the_additional_price_rises(
    households, year, increase
):
    _, before = _calc(households, year, ["stamp_duty_land_tax"])
    higher = [
        {
            **h,
            "additional_residential_property_purchased": h[
                "additional_residential_property_purchased"
            ]
            + increase,
        }
        for h in households
    ]
    _, after = _calc(higher, year, ["stamp_duty_land_tax"])
    assert np.all(
        after["stamp_duty_land_tax"] >= before["stamp_duty_land_tax"] - TOLERANCE
    )
