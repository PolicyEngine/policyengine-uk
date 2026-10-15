"""The standard reform set and the responsiveness rule."""

from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.aggregate_impact.reforms import (
    CALENDAR_DATED_METADATA,
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


def test_a_calendar_dated_parameter_cannot_be_scaled(system):
    dated = []

    def walk(node, path):
        for name, child in getattr(node, "children", {}).items():
            child_path = f"{path}.{name}" if path else name
            metadata = getattr(child, "metadata", None) or {}
            if any(metadata.get(k) for k in CALENDAR_DATED_METADATA) and hasattr(
                child, "values_list"
            ):
                dated.append(child_path)
            walk(child, child_path)

    walk(system.parameters, "")
    assert dated, "expected at least one calendar-dated parameter in the model"
    reform = parse_reforms(
        {"reforms": [{"name": "Scale it", "scale": {dated[0]: 1.1}}]}
    )[0]
    with pytest.raises(ReformSpecError):
        reform_parameters(reform, system.parameters, YEARS)


def test_a_scaled_reform_sets_exactly_the_horizon_years_in_the_model():
    """Build the reformed system the way a simulation does and read it back."""
    from policyengine_uk import Simulation

    reform = next(r for r in STANDARD if r.id == "uc_standard_allowance_plus_10pc")
    situation = {"people": {"a": {"age": 30}}}
    baseline = Simulation(situation=situation)
    changes = reform_parameters(reform, baseline.tax_benefit_system.parameters, YEARS)
    reformed = Simulation(situation=situation, reform=changes)
    for path, factor in reform.scale.items():
        before = parameter_node(baseline.tax_benefit_system.parameters, path)
        after = parameter_node(reformed.tax_benefit_system.parameters, path)
        for year in YEARS:
            assert after(f"{year}-06-01") == pytest.approx(
                before(f"{year}-06-01") * factor
            )
        outside = YEARS[-1] + 1
        assert after(f"{outside}-06-01") == pytest.approx(before(f"{outside}-06-01"))
        assert after(f"{YEARS[0] - 1}-06-01") == pytest.approx(
            before(f"{YEARS[0] - 1}-06-01")
        )
