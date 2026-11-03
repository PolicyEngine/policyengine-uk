"""Property tests for the September CPI benefit uprating.

Invariants, for every path of September CPI inputs:

1. The April rise is the previous September's CPI rounded to the published
   0.1 percentage points, and zero when that is negative: never a cut.
2. The rate never falls when September CPI rises, and a published figure
   passes through unchanged.
3. The index starts at 1 in the 2010 base, compounds each April's rise, and
   agrees with an independent Decimal compounding of the inputs.
4. The index never falls.
5. Raising any September's CPI never lowers the index, and changes it only
   from the following April on.
6. Building the series twice from the same inputs gives the same series.
"""

from decimal import ROUND_HALF_UP, Decimal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode

from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    BASE_YEAR,
    add_september_cpi_uprating,
    september_cpi_uprating_rate,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)

# September CPI since 1989 ranged from -0.1% (2015) to 10.1% (2022); draw
# wider, and off the published grid, to cover forecasts and scenarios.
any_rate = st.floats(min_value=-0.1, max_value=0.2, allow_nan=False)
published_rate = st.integers(min_value=-60, max_value=150).map(lambda n: n / 1000)
FIRST_SEPTEMBER = BASE_YEAR
# The index builder runs to 2039.
LAST_INDEX_YEAR = 2039
PROPERTIES = settings(
    max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)


def septembers(min_size=2, max_size=25):
    """September CPI for 2010 onward, one value per year."""
    return st.lists(any_rate, min_size=min_size, max_size=max_size).map(
        lambda rates: {FIRST_SEPTEMBER + i: rate for i, rate in enumerate(rates)}
    )


def build(cpi_by_september):
    """Run the model's builders on a tree holding only the inputs they read.

    The calendar-year series only bound the years covered: the inputs run
    to the last September given.
    """
    years = sorted(cpi_by_september)
    tree = ParameterNode(
        data={
            "gov": {
                "economic_assumptions": {
                    "statutory_uprating_inputs": {
                        "cpi_september": {
                            "values": {
                                f"{year}-09-01": rate
                                for year, rate in cpi_by_september.items()
                            }
                        }
                    },
                    "yoy_growth": {
                        "obr": {
                            series: {
                                "values": {f"{year}-01-01": 0.02 for year in years}
                            }
                            for series in ("consumer_price_index", "average_earnings")
                        }
                    },
                }
            }
        }
    )
    tree = create_economic_assumption_indices(add_september_cpi_uprating(tree))
    economic_assumptions = tree.gov.economic_assumptions
    rates = economic_assumptions.yoy_growth.september_cpi_uprating
    index = economic_assumptions.indices.september_cpi_uprating
    last_rate_year = max(years) + 1
    return (
        {year: rates(f"{year}-01-01") for year in range(BASE_YEAR, last_rate_year + 1)},
        {
            year: index(f"{year}-01-01")
            for year in range(BASE_YEAR, LAST_INDEX_YEAR + 1)
        },
    )


def published(rate):
    return Decimal(repr(float(rate))).quantize(Decimal("0.001"), ROUND_HALF_UP)


@PROPERTIES
@given(cpi=any_rate)
def test_rate_is_the_published_september_figure_and_never_a_cut(cpi):
    rate = september_cpi_uprating_rate(cpi)
    assert rate >= 0
    assert str(rate) != "-0.0"
    if published(cpi) > 0:
        assert rate == float(published(cpi))
        assert abs(rate - cpi) <= 0.0005 + 1e-12
    else:
        assert rate == 0


@PROPERTIES
@given(cpi=any_rate, rise=st.floats(min_value=0, max_value=0.1))
def test_rate_never_falls_when_september_cpi_rises(cpi, rise):
    assert september_cpi_uprating_rate(cpi + rise) >= september_cpi_uprating_rate(cpi)


@PROPERTIES
@given(cpi=published_rate)
def test_published_figures_pass_through(cpi):
    assert september_cpi_uprating_rate(cpi) == max(cpi, 0)
    assert september_cpi_uprating_rate(
        september_cpi_uprating_rate(cpi)
    ) == september_cpi_uprating_rate(cpi)


@PROPERTIES
@given(cpi=septembers())
def test_each_april_rises_by_the_previous_september(cpi):
    rates, _ = build(cpi)
    assert rates[BASE_YEAR] is None
    for year in range(BASE_YEAR + 1, max(cpi) + 2):
        assert rates[year] == september_cpi_uprating_rate(cpi[year - 1]), year


@PROPERTIES
@given(cpi=septembers())
def test_index_compounds_the_rises(cpi):
    """Against a Decimal compounding of the inputs: the builder rounds the
    index (never below 1) to 5 decimal places each year, so allow a relative
    5e-6 per year."""
    rates, index = build(cpi)
    last_rate_year = max(cpi) + 1
    reference = Decimal(1)
    assert index[BASE_YEAR] == 1
    for year in range(BASE_YEAR + 1, LAST_INDEX_YEAR + 1):
        # Past the inputs the last rise carries forward, as for every series.
        rise = max(published(cpi[min(year, last_rate_year) - 1]), Decimal(0))
        reference *= 1 + rise
        tolerance = 5e-6 * (year - BASE_YEAR)
        assert abs(index[year] / float(reference) - 1) <= tolerance, year
        assert index[year] == round(
            index[year - 1] * (1 + rates[min(year, last_rate_year)]), 5
        )


@PROPERTIES
@given(cpi=septembers())
def test_index_never_falls(cpi):
    _, index = build(cpi)
    for year in range(BASE_YEAR + 1, LAST_INDEX_YEAR + 1):
        assert index[year] >= index[year - 1], year


@PROPERTIES
@given(
    cpi=septembers(min_size=3),
    position=st.integers(min_value=0, max_value=24),
    rise=st.floats(min_value=0.0005, max_value=0.1),
)
def test_a_higher_september_raises_the_index_only_from_the_next_april(
    cpi, position, rise
):
    changed_september = FIRST_SEPTEMBER + position % len(cpi)
    higher = {**cpi, changed_september: cpi[changed_september] + rise}
    _, index = build(cpi)
    _, higher_index = build(higher)
    for year in range(BASE_YEAR, LAST_INDEX_YEAR + 1):
        assert higher_index[year] >= index[year], year
        if year <= changed_september:
            assert higher_index[year] == index[year], year


@PROPERTIES
@given(cpi=septembers())
def test_building_twice_gives_the_same_series(cpi):
    assert build(cpi) == build(dict(cpi))
