"""The economic assumption indices run as far as the growth series behind them.

Every index under ``gov.economic_assumptions.indices`` used to stop at 2039,
while the year-on-year growth series run to the 2070s. A parameter carries its
final value forward rather than raising, so everything uprated by an index,
the State Pension included, froze at its 2039 level with no error.

Invariants:

1. Horizon: every index ends in the last year any growth series covers, which
   is one year past the raw series because the lagged series run a year past
   their source.
2. Compounding: each index is 1 in its first year and, for every later year to
   the horizon, the previous year's value times one plus that year's growth,
   rounded to 5 decimal places. A series that ends sooner holds its final
   growth rate.
3. Uprating: every parameter uprated by an index that still moves after 2039
   moves with it, unless its value is zero.
"""

from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter, ParameterNode, get_parameter

from policyengine_uk import system
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.parameters.gov.economic_assumptions.horizon import (
    growth_horizon,
    last_year,
)

ECONOMIC_ASSUMPTIONS = system.parameters.gov.economic_assumptions
HORIZON = growth_horizon(ECONOMIC_ASSUMPTIONS.yoy_growth)
YOY_GROWTH_FILE = (
    Path(__file__).parents[1]
    / "parameters"
    / "gov"
    / "economic_assumptions"
    / "yoy_growth.yaml"
)
# The year the indices stopped at before they followed the growth series.
OLD_LAST_INDEX_YEAR = 2039


def _parameters(node: ParameterNode) -> list:
    return [p for p in node.get_descendants() if isinstance(p, Parameter)]


def _years_in_growth_file() -> dict:
    """First and last year of each series in yoy_growth.yaml, read from the file."""
    years = {}

    def visit(node, path):
        if "values" in node:
            dated = [int(str(key)[:4]) for key in node["values"]]
            years[path] = (min(dated), max(dated))
        for key, child in node.items():
            if key not in ("values", "metadata", "description"):
                visit(child, f"{path}.{key}")

    visit(yaml.safe_load(YOY_GROWTH_FILE.read_text()), "yoy_growth")
    return years


def test_the_horizon_is_a_year_past_the_growth_file():
    """The lagged series run one year past the last year in the file."""
    last_in_file = max(last for _, last in _years_in_growth_file().values())

    assert HORIZON == last_in_file + 1
    lagged_cpi = ECONOMIC_ASSUMPTIONS.yoy_growth.obr.lagged_cpi
    assert last_year(lagged_cpi) == HORIZON


def test_every_index_ends_where_the_growth_series_end():
    indices = _parameters(ECONOMIC_ASSUMPTIONS.indices)

    assert len(indices) == len(_parameters(ECONOMIC_ASSUMPTIONS.yoy_growth))
    for index in indices:
        assert last_year(index) == HORIZON, index.name


def test_every_index_compounds_its_growth_through_the_horizon():
    """Checked from 2030, after every series has started.

    Backdating fills each processed series and index back to 2015 with its
    first value, so the recursion only holds from the year a series starts.
    ``test_indices_end_where_any_growth_series_ends`` checks it from the
    start year on generated series.
    """
    first_checked = 2030
    assert all(first < first_checked for first, _ in _years_in_growth_file().values())
    for growth in _parameters(ECONOMIC_ASSUMPTIONS.yoy_growth):
        index = get_parameter(
            system.parameters, growth.name.replace("yoy_growth", "indices")
        )
        for year in range(first_checked, HORIZON + 1):
            expected = round(index(str(year - 1)) * (1 + growth(str(year))), 5)
            assert index(str(year)) == expected, (index.name, year)
        # Past the horizon an index holds its last value.
        assert index(str(HORIZON + 10)) == index(str(HORIZON)), index.name


def test_the_state_pension_keeps_rising_after_2039():
    """Both State Pension rates move with the triple lock index to the horizon."""
    triple_lock = ECONOMIC_ASSUMPTIONS.indices.triple_lock
    state_pension = system.parameters.gov.dwp.state_pension

    for amount in (
        state_pension.new_state_pension.amount,
        state_pension.basic_state_pension.amount,
    ):
        for year in range(OLD_LAST_INDEX_YEAR + 1, HORIZON + 1):
            assert amount(str(year)) > amount(str(year - 1)), (amount.name, year)
            assert amount(str(year)) / amount(str(year - 1)) == pytest.approx(
                triple_lock(str(year)) / triple_lock(str(year - 1)), rel=1e-12
            ), (amount.name, year)


def test_no_uprated_parameter_freezes_after_2039():
    """A parameter uprated by a series that moves after 2039 moves too."""
    checked = 0
    for parameter in _parameters(system.parameters.gov):
        uprating = (parameter.metadata or {}).get("uprating")
        if uprating is None:
            continue
        uprater_name = uprating if isinstance(uprating, str) else uprating["parameter"]
        if uprater_name == "self":
            continue
        uprater = get_parameter(system.parameters, uprater_name)
        before = parameter(str(OLD_LAST_INDEX_YEAR))
        if not isinstance(before, (int, float)) or before == 0:
            continue
        if uprater(str(OLD_LAST_INDEX_YEAR)) == uprater(str(HORIZON)):
            continue
        checked += 1
        assert parameter(str(HORIZON)) != before, parameter.name

    # The State Pension, benefit rates and tax thresholds are all in here.
    assert checked > 100


growth_rates = st.floats(min_value=-0.1, max_value=0.2, allow_nan=False)


@st.composite
def growth_trees(draw):
    """A yoy_growth node of Jan-1-dated series, some nested, of mixed lengths."""
    series = {}
    for number in range(draw(st.integers(min_value=1, max_value=5))):
        start = draw(st.integers(min_value=2000, max_value=2030))
        length = draw(st.integers(min_value=1, max_value=60))
        values = {
            f"{year}-01-01": draw(growth_rates) for year in range(start, start + length)
        }
        if draw(st.booleans()):
            series.setdefault("nested", {})[f"series_{number}"] = {"values": values}
        else:
            series[f"series_{number}"] = {"values": values}
    return ParameterNode(
        "",
        data={"gov": {"economic_assumptions": {"yoy_growth": series}}},
    )


@settings(max_examples=200, deadline=None)
@given(tree=growth_trees())
def test_indices_end_where_any_growth_series_ends(tree):
    growth = tree.gov.economic_assumptions.yoy_growth
    horizon = max(last_year(series) for series in _parameters(growth))

    create_economic_assumption_indices(tree)

    for series in _parameters(growth):
        index = get_parameter(tree, series.name.replace("yoy_growth", "indices"))
        start = int(series.values_list[-1].instant_str[:4])

        assert last_year(index) == horizon
        assert index(str(start)) == 1.0
        for year in range(start + 1, horizon + 1):
            # Past its last year a series holds its final growth rate.
            expected = round(index(str(year - 1)) * (1 + series(str(year))), 5)
            assert index(str(year)) == expected
