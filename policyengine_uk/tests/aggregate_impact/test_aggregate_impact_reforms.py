"""The standard reform set and the responsiveness rule."""

from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.aggregate_impact.reforms import (
    ReformSpecError,
    Responds,
    load_reforms,
    parameter_node,
    parse_reforms,
    reform_parameters,
    responsiveness,
)
from policyengine_uk.utils.aggregate_impact.spec import load_spec

TESTS = Path(__file__).resolve().parents[1]
YEARS = load_spec().years
STANDARD = load_reforms()


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def test_every_standard_reform_says_what_it_must_move(system):
    assert len(STANDARD) == 10
    assert len({r.id for r in STANDARD}) == len(STANDARD)
    for reform in STANDARD:
        assert reform.responds is not None, reform.id
        assert reform.responds.variable in system.variables, reform.id
        assert reform.responds.minimum > 0
        assert bool(reform.parameters) != bool(reform.scale), reform.id


def test_standard_set_contains_the_reform_cost_fixtures_unchanged():
    with open(TESTS / "microsimulation" / "reforms_config.yaml") as f:
        fixtures = yaml.safe_load(f)["reforms"]
    by_name = {r.name: r for r in STANDARD}
    for fixture in fixtures:
        assert dict(by_name[fixture["name"]].parameters) == fixture["parameters"]


def test_every_named_parameter_exists(system):
    for reform in STANDARD:
        for path in list(reform.parameters) + list(reform.scale):
            assert parameter_node(system.parameters, path) is not None, path


def test_bracket_paths_resolve(system):
    node = parameter_node(system.parameters, "gov.hmrc.income_tax.rates.uk[0].rate")
    assert node("2026-01-01") == pytest.approx(0.2)


def test_scaled_reforms_are_the_baseline_times_the_factor_in_every_year(system):
    for reform in STANDARD:
        changes = reform_parameters(reform, system.parameters, YEARS)
        for path, factor in reform.scale.items():
            assert set(changes[path]) == {str(y) for y in YEARS}
            node = parameter_node(system.parameters, path)
            for year in YEARS:
                assert changes[path][str(year)] == pytest.approx(
                    node(f"{year}-01-01") * factor
                )
        for path, value in reform.parameters.items():
            assert changes[path] == value


@pytest.mark.parametrize(
    "entry",
    [
        {"name": "no change"},
        {
            "name": "x",
            "parameters": {"a": 1},
            "responds": {"variable": "v", "direction": "sideways", "minimum": 1},
        },
        {
            "name": "x",
            "parameters": {"a": 1},
            "responds": {"variable": "v", "direction": "up", "minimum": 0},
        },
        {"name": "x", "scale": {"a": 0}},
    ],
)
def test_malformed_reforms_are_rejected(entry):
    with pytest.raises(ReformSpecError):
        parse_reforms({"reforms": [entry]})


def test_duplicate_ids_are_rejected():
    entry = {"name": "Same name", "parameters": {"a": 1}}
    with pytest.raises(ReformSpecError):
        parse_reforms({"reforms": [entry, dict(entry)]})


def test_fixture_schema_parses_without_responds():
    reforms = parse_reforms({"reforms": [{"name": "Raise X", "parameters": {"a": 1}}]})
    assert reforms[0].id == "raise_x" and reforms[0].responds is None


changes = st.dictionaries(
    st.integers(2025, 2035),
    st.floats(-1e11, 1e11, allow_nan=False),
    min_size=1,
    max_size=8,
)


@settings(max_examples=200, deadline=None)
@given(changes=changes, minimum=st.floats(1, 1e10))
def test_responsive_exactly_when_every_year_moves_enough_the_right_way(
    changes, minimum
):
    up, _ = responsiveness(Responds("v", "up", minimum), changes)
    assert up == all(c >= minimum for c in changes.values())
    # Mirror image: the same reform read as a fall of the negated changes.
    down, _ = responsiveness(
        Responds("v", "down", minimum), {y: -c for y, c in changes.items()}
    )
    assert down == up


@settings(max_examples=100, deadline=None)
@given(changes=changes, minimum=st.floats(1, 1e10), year=st.integers(2025, 2035))
def test_one_inert_or_wrong_signed_year_fails(changes, minimum, year):
    for bad in (0.0, -abs(minimum)):
        ok, detail = responsiveness(
            Responds("v", "up", minimum), {**changes, year: bad}
        )
        assert not ok and str(year)[2:] in detail


def test_no_measured_year_fails():
    ok, detail = responsiveness(Responds("v", "up", 1.0), {})
    assert not ok and "no year" in detail
