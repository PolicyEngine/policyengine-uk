"""LBTT and LTT on lease rent.

Scotland: Table C of the Schedule to SSI 2015/126 bands the net present value
of lease rent at 0% to £150,000 and 1% above. SSI 2020/24 article 2 caps the
1% band at £2 million and adds 2% above it, for effective dates on or after 7
February 2020 (article 1(2)). Residential leases, other than qualifying long
leases, are exempt transactions: LBTT (Scotland) Act 2013 schedule 1
paragraph 3(1)(a).

Wales: Table 4 of the Schedule to SI 2018/128 bands the rent of
non-residential and mixed leases at 0% to £150,000, 1% to £2,000,000 and 2%
above; SI 2020/1618 regulation 6(4) raises the zero rate band to £225,000 for
effective dates on or after 22 December 2020. No tax is chargeable on
residential lease rent: Land Transaction Tax and Anti-avoidance of Devolved
Taxes (Wales) Act 2017 schedule 6 paragraph 27(1).

The model charges each year's rent as the increase in the banded tax when that
year's rent is added to the cumulative rent of earlier years, and reads each
parameter at 30 April of the model year (the fiscal year starting that April).

Invariants, for households in all four countries and model years 2019 to 2030:

1. Residential exemption: LBTT and LTT on residential lease rent are zero.
2. Differential: LBTT and LTT on non-residential lease rent equal a reference
   built here from the bands above, with the band in force at 30 April.
3. Bounds: 0 <= charge <= 2% of the year's rent.
4. Telescoping: charging rent over two years gives the same total as charging
   it in one year on the same earlier cumulative rent.
5. Country: rent is charged LBTT only in Scotland and LTT only in Wales.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

TOLERANCE = 0.01
TOP_RATE = 0.02
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
YEARS = [2019, 2020, 2021, 2025, 2030]
BOUNDARIES = [0, 150_000, 225_000, 2_000_000]


def banded(npv, bands):
    """Tax on npv under marginal (threshold, rate) bands."""
    tax = np.zeros_like(npv, dtype=float)
    for i, (threshold, rate) in enumerate(bands):
        upper = bands[i + 1][0] if i + 1 < len(bands) else np.inf
        tax += rate * np.clip(npv - threshold, 0, upper - threshold)
    return tax


def lbtt_rent_bands(year):
    # SSI 2020/24 is in force at 30 April from model year 2020.
    if year >= 2020:
        return [(0, 0), (150_000, 0.01), (2_000_000, 0.02)]
    return [(0, 0), (150_000, 0.01)]


def ltt_rent_bands(year):
    # SI 2020/1618 is in force at 30 April from model year 2021.
    zero_band = 225_000 if year >= 2021 else 150_000
    return [(0, 0), (zero_band, 0.01), (2_000_000, 0.02)]


def increment(bands, cumulative, rent):
    return banded(cumulative + rent, bands) - banded(cumulative, bands)


def simulate(households, year):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, household in enumerate(households):
        situation["people"][f"p{i}"] = {"age": {year: 40}}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {
            "members": [f"p{i}"],
            **{k: {year: v} for k, v in household.items()},
        }
    sim = Simulation(situation=situation)
    return lambda variable: np.asarray(sim.calculate(variable, year), dtype=float)


money = st.one_of(
    st.sampled_from(BOUNDARIES),
    st.integers(0, 3_000_000),
    st.integers(0, 20_000_000),
)
lease = st.fixed_dictionaries(
    {
        "country": st.sampled_from(COUNTRIES),
        "rent": money,
        "cumulative_residential_rent": money,
        "non_residential_rent": money,
        "cumulative_non_residential_rent": money,
    }
)
LEASES = st.lists(lease, min_size=1, max_size=6)


@PROPERTY_SETTINGS
@given(leases=LEASES, year=st.sampled_from(YEARS))
@example(
    leases=[
        {
            "country": "SCOTLAND",
            "rent": 200_000,
            "cumulative_residential_rent": 2_000_000,
            "non_residential_rent": 2_000_100,
            "cumulative_non_residential_rent": 0,
        }
    ],
    year=2025,
)
def test_lease_rent_matches_bands_and_exemptions(leases, year):
    calc = simulate(leases, year)
    non_residential_rent = np.array(
        [h["non_residential_rent"] for h in leases], dtype=float
    )
    cumulative = np.array(
        [h["cumulative_non_residential_rent"] for h in leases], dtype=float
    )
    country = np.array([h["country"] for h in leases])

    # 1. Residential exemption.
    assert np.all(calc("lbtt_on_residential_property_rent") == 0)
    assert np.all(calc("ltt_on_residential_property_rent") == 0)

    # 2. Differential against the statutory bands.
    lbtt = calc("lbtt_on_non_residential_property_rent")
    ltt = calc("ltt_on_non_residential_property_rent")
    expected_lbtt = increment(lbtt_rent_bands(year), cumulative, non_residential_rent)
    expected_ltt = increment(ltt_rent_bands(year), cumulative, non_residential_rent)
    np.testing.assert_allclose(lbtt, expected_lbtt, atol=TOLERANCE)
    np.testing.assert_allclose(ltt, expected_ltt, atol=TOLERANCE)
    np.testing.assert_allclose(calc("lbtt_on_rent"), lbtt, atol=TOLERANCE)
    np.testing.assert_allclose(calc("ltt_on_rent"), ltt, atol=TOLERANCE)

    # 3. Bounds.
    for charge in (lbtt, ltt):
        assert np.all(charge >= -TOLERANCE)
        assert np.all(charge <= TOP_RATE * non_residential_rent + TOLERANCE)

    # 5. Country.
    lbtt_total = calc("land_and_buildings_transaction_tax")
    ltt_total = calc("land_transaction_tax")
    np.testing.assert_allclose(
        lbtt_total, np.where(country == "SCOTLAND", lbtt, 0), atol=TOLERANCE
    )
    np.testing.assert_allclose(
        ltt_total, np.where(country == "WALES", ltt, 0), atol=TOLERANCE
    )


@PROPERTY_SETTINGS
@given(
    cumulative=money,
    first=money,
    second=money,
    year=st.sampled_from(YEARS),
)
def test_rent_charged_over_two_years_telescopes(cumulative, first, second, year):
    # 4. Year 1 on the earlier cumulative rent, year 2 on that plus year 1,
    # and both years at once on the earlier cumulative rent.
    households = [
        {"cumulative_non_residential_rent": c, "non_residential_rent": r}
        for c, r in [
            (cumulative, first),
            (cumulative + first, second),
            (cumulative, first + second),
        ]
    ]
    for country in ("SCOTLAND", "WALES"):
        calc = simulate([{"country": country, **h} for h in households], year)
        for variable in (
            "lbtt_on_non_residential_property_rent",
            "ltt_on_non_residential_property_rent",
        ):
            year_one, year_two, together = calc(variable)
            assert abs(year_one + year_two - together) <= TOLERANCE
