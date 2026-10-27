"""Projection contracts across forecasts, enacted history and combined reforms.

The differential reference below freezes the two builders merged in #2576
(main eb0b8087). It deliberately keeps their generation-after-uprating order.
For unreformed forecasts the reconciled builders must reproduce those
amounts, including main’s earnings and CPI floors. Reform independence and
the additional threshold residual floor have their own properties.
"""

from typing import Any, Callable

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import uprate_parameters
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant

from policyengine_uk.tests.test_pension_credit_uprating import (
    FIRST_PROJECTION_YEAR,
    HB_NAME,
    HB_RELATIONS,
    LAST_INDEX_YEAR,
    RAW_HB,
    RAW_SC,
    RAW_SMG,
    SC_NAME,
    SMG_NAME,
    growth,
    higher_allowances,
    paths,
    project_synthetic_parameters,
    synthetic_parameter_tree,
    synthetic_parameters,
)


PROJECTED_PATHS = (
    *(f"{SMG_NAME}.{relation}" for relation in ("SINGLE", "COUPLE")),
    *(
        f"{SC_NAME}.{kind}.{relation}"
        for kind in ("threshold", "maximum")
        for relation in ("SINGLE", "COUPLE")
    ),
    *(
        f"{HB_NAME}.{kind}.{cohort}"
        for kind in HB_RELATIONS
        for cohort in ("aged", "aged_from_cutoff")
    ),
)
REFORM_PATHS = (
    *(f"{SMG_NAME}.{relation}" for relation in ("SINGLE", "COUPLE")),
    *(f"{SC_NAME}.threshold.{relation}" for relation in ("SINGLE", "COUPLE")),
    f"{SC_NAME}.rate.phase_in",
    *(f"{HB_NAME}.{kind}.aged" for kind in HB_RELATIONS),
)
# Cover zeros, subnormal values and large monetary/rate reforms, without
# overflowing intermediate products of independently generated float64 values.
nonnegative_amount = st.floats(
    min_value=0, max_value=1e100, allow_nan=False, allow_infinity=False
)
nonnegative_rate = st.floats(
    min_value=0, max_value=100, allow_nan=False, allow_infinity=False
)


@st.composite
def combined_reforms(draw):
    """Change every independent component, including the lone parent's own base."""
    reforms = {}
    for path in REFORM_PATHS:
        year = draw(st.integers(FIRST_PROJECTION_YEAR - 1, LAST_INDEX_YEAR))
        value = draw(
            nonnegative_rate if path.endswith("phase_in") else nonnegative_amount
        )
        reforms[path] = (year, value)
    return reforms


def _apply_reforms(parameters, reforms):
    for path, (year, value) in reforms.items():
        parameters.get_child(path).update(start=f"{year}-04-01", value=value)


@settings(max_examples=60, deadline=None)
@given(path=paths, reforms=combined_reforms())
@example(
    path=[(0.039, 0.035)],
    reforms={path: (2026, 0.0) for path in REFORM_PATHS},
)
@example(
    path=[(0.039, -0.06), (-0.06, 0.15)],
    reforms={
        f"{SMG_NAME}.SINGLE": (2026, 300),
        f"{SMG_NAME}.COUPLE": (2026, 459),
        f"{SC_NAME}.threshold.SINGLE": (2026, 0),
        f"{SC_NAME}.threshold.COUPLE": (2026, 1),
        f"{SC_NAME}.rate.phase_in": (2026, 0),
        f"{HB_NAME}.single.aged": (2026, 220),
        f"{HB_NAME}.lone_parent.aged": (2026, 0),
        f"{HB_NAME}.couple.aged": (2026, 300),
    },
)
def test_combined_reforms_build_and_never_project_negative_amounts(path, reforms):
    """Building succeeds even for zero bases and allowances below guarantees.

    The enacted tree supplies the base year; future reform anchors must not
    turn into a mismatched set of supposedly enacted years.
    """
    parameters = synthetic_parameter_tree(path)
    unreformed = parameters.clone()
    _apply_reforms(parameters, reforms)
    projected = project_synthetic_parameters(parameters, unreformed)

    for name in PROJECTED_PATHS:
        parameter = projected.get_child(name)
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            assert parameter(f"{year}-04-30") >= 0, (name, year, reforms)


@pytest.mark.parametrize("first_year", [2026, 2028])
def test_maximum_reforms_reach_both_dependent_forecasts(first_year):
    parameters = synthetic_parameter_tree([(0.039, 0.035)])
    unreformed = parameters.clone()
    parameters.get_child(f"{SC_NAME}.maximum.SINGLE").update(
        start=f"{first_year}-04-01", value=0
    )
    projected = project_synthetic_parameters(parameters, unreformed)
    for year in range(max(first_year, FIRST_PROJECTION_YEAR), LAST_INDEX_YEAR + 1):
        at = f"{year}-04-30"
        guarantee = projected.get_child(f"{SMG_NAME}.SINGLE")(at)
        assert projected.get_child(f"{SC_NAME}.maximum.SINGLE")(at) == 0
        assert projected.get_child(f"{SC_NAME}.threshold.SINGLE")(at) == pytest.approx(
            guarantee
        )
        for kind in ("single", "lone_parent"):
            assert projected.get_child(f"{HB_NAME}.{kind}.aged")(at) == pytest.approx(
                guarantee
            )


@settings(max_examples=40, deadline=None)
@given(path=paths)
def test_unreformed_higher_allowances_equal_guarantee_plus_maximum_every_year(path):
    parameters = synthetic_parameters(path)
    for allowance, guarantee, maximum in higher_allowances(parameters):
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            at = f"{year}-04-30"
            assert allowance(at) == pytest.approx(
                guarantee(at) + maximum(at), abs=1e-9
            ), (allowance.name, year)


ENACTED_VALUES = (
    *(
        (f"{name}.{relation}", entry.instant_str, entry.value)
        for name, node in (
            (SMG_NAME, RAW_SMG),
            (f"{SC_NAME}.threshold", RAW_SC.threshold),
            (f"{SC_NAME}.maximum", RAW_SC.maximum),
        )
        for relation in ("SINGLE", "COUPLE")
        for entry in getattr(node, relation).values_list
    ),
    *(
        (f"{HB_NAME}.{kind}.{cohort}", entry.instant_str, entry.value)
        for kind in HB_RELATIONS
        for cohort in ("aged", "aged_from_cutoff")
        for entry in getattr(getattr(RAW_HB, kind), cohort).values_list
    ),
)


@settings(max_examples=60, deadline=None)
@given(path=paths, enacted=st.sampled_from(ENACTED_VALUES))
def test_forecasts_reproduce_each_enacted_value_exactly(path, enacted):
    name, instant, expected = enacted
    parameters = synthetic_parameters(path)
    assert parameters.get_child(name)(instant) == expected


def _main_last_projected_year(parameters: ParameterNode) -> int:
    """Frozen #2576 helper, eb0b8087: the earnings index's final year."""
    index = parameters.gov.economic_assumptions.indices.earnings_uprating
    return max(int(entry.instant_str[:4]) for entry in index.values_list)


def _main_extend_after_last_stated(
    parameter: Parameter,
    last_year: int,
    derive: Callable[[str, Any], Any],
) -> None:
    """Frozen #2576 value-generation algorithm; names are prefixed locally."""
    last = max(parameter.values_list, key=lambda entry: entry.instant_str)
    previous = last.value
    for year in range(int(last.instant_str[:4]) + 1, last_year + 1):
        previous = derive(f"{year}-04-30", previous)
        parameter.values_list.append(
            ParameterAtInstant(parameter.name, f"{year}-01-01", data=previous)
        )
    parameter.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    parameter.mark_as_modified()


def _main_project_savings_credit_threshold(parameters: ParameterNode) -> ParameterNode:
    """Frozen create_savings_credit_threshold.py from main eb0b8087."""
    pc = parameters.gov.dwp.pension_credit
    sc = pc.savings_credit
    last_year = _main_last_projected_year(parameters)
    for relation, threshold in sc.threshold.children.items():
        guarantee = pc.guarantee_credit.minimum_guarantee.children[relation]
        maximum = sc.maximum.children[relation]

        def derive(sample, previous):
            phase_in = sc.rate.phase_in(sample)
            if phase_in == 0:
                return previous
            return guarantee(sample) - maximum(sample) / phase_in

        _main_extend_after_last_stated(threshold, last_year, derive)
    sc.threshold.clear_parent_cache()
    return parameters


def _main_project_pension_age_allowances(parameters: ParameterNode) -> ParameterNode:
    """Frozen create_pension_age_allowances.py from main eb0b8087."""
    pc = parameters.gov.dwp.pension_credit
    allowances = parameters.gov.dwp.housing_benefit.allowances
    last_year = _main_last_projected_year(parameters)
    for kind, relation in HB_RELATIONS.items():
        guarantee = pc.guarantee_credit.minimum_guarantee.children[relation]
        maximum = pc.savings_credit.maximum.children[relation]

        def derive(sample, previous):
            return guarantee(sample) + maximum(sample)

        _main_extend_after_last_stated(
            allowances.children[kind].aged, last_year, derive
        )
    allowances.clear_parent_cache()
    return parameters


def _main_parameters(path):
    parameters = synthetic_parameter_tree(path)
    pc = parameters.gov.dwp.pension_credit
    # Main's thresholds and higher allowances were generated after uprating,
    # without metadata pointing at the reconciliation's new forecast indices.
    for node in (
        pc.savings_credit.threshold,
        *pc.savings_credit.threshold.children.values(),
    ):
        node.metadata.pop("uprating", None)
    for kind in HB_RELATIONS:
        getattr(parameters.gov.dwp.housing_benefit.allowances, kind).aged.metadata.pop(
            "uprating", None
        )
    pc.savings_credit.maximum.metadata["uprating"] = "gov.benefit_uprating_cpi"
    for maximum in pc.savings_credit.maximum.children.values():
        maximum.metadata["uprating"] = "gov.benefit_uprating_cpi"
    propagate_parameter_metadata(parameters)
    uprate_parameters(parameters)
    _main_project_savings_credit_threshold(parameters)
    _main_project_pension_age_allowances(parameters)
    return parameters


@settings(max_examples=40, deadline=None)
@given(path=paths)
@example(path=[(0.039, 0.035)])
def test_reconciled_builders_agree_with_main_where_its_behavior_is_retained(path):
    """Retain main’s unreformed amounts under positive and negative macro inputs."""
    main = _main_parameters(path)
    reconciled = synthetic_parameters(path)
    for name in PROJECTED_PATHS:
        for year in range(FIRST_PROJECTION_YEAR - 1, LAST_INDEX_YEAR + 1):
            at = f"{year}-04-30"
            assert reconciled.get_child(name)(at) == pytest.approx(
                main.get_child(name)(at), abs=1e-9
            ), (name, year, path)
