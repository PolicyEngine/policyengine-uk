"""Comparison and rendering of two measurements, on synthetic results."""

import copy
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact import COMMENT_MARKER, TOOL_SCHEMA
from policyengine_uk.utils.aggregate_impact.compare import (
    classify_check,
    compare,
    decile_impacts,
)
from policyengine_uk.utils.aggregate_impact.measure import weighted_gini
from policyengine_uk.utils.aggregate_impact.render import fmt_change, fmt_level, render
from policyengine_uk.utils.aggregate_impact.spec import Threshold, load_spec

SPEC = load_spec()
YEARS = SPEC.years
SHA = "5" * 64

KINDS = {
    "receipts": "gbp",
    "caseloads": "count",
    "poverty": "rate",
    "inequality": "index",
}
finite = st.floats(-1e12, 1e12, allow_nan=False, allow_infinity=False)


def result(values, checks=(), sha=SHA, status="ok", partition_sha="p"):
    """A measurement with one metric per (section, name) and the given checks."""
    return {
        "schema": TOOL_SCHEMA,
        "status": status,
        "label": "x",
        "years": YEARS,
        "provenance": {
            "dataset": {"verified_sha256": sha, "path": "d.h5"},
            "git_sha": "abc",
        },
        "runtime": {
            "distributions": ["numpy==2.0"],
            "python": "3.13",
            "machine": "arm64",
        },
        "partition": {"sha256": partition_sha, "source": "s"},
        "metrics": [
            {
                "id": f"{section}.{name}",
                "label": name,
                "section": section,
                "group": None,
                "kind": KINDS[section],
                "unit": None,
                "values": {str(y): v for y, v in zip(YEARS, series)},
            }
            for (section, name), series in values.items()
        ],
        "checks": [
            {
                "id": cid,
                "label": cid,
                "section": "s",
                "severity": "fail",
                "status": s,
                "details": ["d"],
            }
            for cid, s in checks
        ],
        "guard": {"status": "skipped", "reason": "test"},
        "reforms": [],
        "timings": {"total": 1},
    }


metric_values = st.dictionaries(
    st.tuples(st.sampled_from(sorted(KINDS)), st.sampled_from(["a", "b", "c"])),
    st.lists(finite, min_size=len(YEARS), max_size=len(YEARS)),
    min_size=1,
    max_size=6,
)


@pytest.mark.parametrize(
    "base, head, blocking, expected",
    [
        ("pass", "pass", False, "pass"),
        ("fail", "pass", False, "fixed"),
        ("warn", "pass", False, "fixed"),
        (None, "pass", False, "pass"),
        ("pass", "fail", False, "regression"),
        (None, "fail", False, "regression"),
        ("fail", "fail", False, "pre_existing"),
        ("fail", "fail", True, "regression"),
        ("warn", "fail", False, "regression"),
        ("pass", "warn", False, "new_warning"),
        ("warn", "warn", False, "warning"),
        ("pass", None, False, "removed"),
    ],
)
def test_check_classification(base, head, blocking, expected):
    assert classify_check(base, head, blocking) == expected


@settings(max_examples=60, deadline=None)
@given(values=metric_values)
def test_identical_sides_change_nothing(values):
    side = result(values, checks=[("identity:x", "pass"), ("sign:y", "fail")])
    summary = compare(side, copy.deepcopy(side), SPEC)
    assert summary["status"] == "pass"
    assert summary["flags"] == []
    assert all(not row["changed"] for row in summary["rows"])
    assert {c["classification"] for c in summary["checks"]} == {"pass", "pre_existing"}


@settings(max_examples=60, deadline=None)
@given(base=metric_values, data=st.data())
def test_changes_are_antisymmetric(base, data):
    head = {k: [v + data.draw(finite) for v in series] for k, series in base.items()}
    forward = {r["id"]: r for r in compare(result(base), result(head), SPEC)["rows"]}
    backward = {r["id"]: r for r in compare(result(head), result(base), SPEC)["rows"]}
    for metric_id, row in forward.items():
        for year, cell in row["values"].items():
            assert cell["delta"] == pytest.approx(
                -backward[metric_id]["values"][year]["delta"], abs=1e-3
            )


@settings(max_examples=200, deadline=None)
@given(base=finite, head=finite, absolute=st.floats(0, 1e9), relative=st.floats(0, 0.5))
def test_a_move_is_flagged_exactly_when_it_exceeds_the_larger_bound(
    base, head, absolute, relative
):
    threshold = Threshold(absolute, relative)
    assert threshold.exceeded(base, head) == (
        abs(head - base) > max(absolute, relative * abs(base))
    )


def test_flags_follow_the_spec_thresholds():
    base = {("receipts", "a"): [100e9] * len(YEARS)}
    small = {("receipts", "a"): [100e9 + 50e6] * len(YEARS)}
    large = {("receipts", "a"): [100e9 + 200e6] * len(YEARS)}
    assert compare(result(base), result(small), SPEC)["flags"] == []
    assert len(compare(result(base), result(large), SPEC)["flags"]) == len(YEARS)


def test_a_crashed_or_missing_head_fails():
    base = result({("receipts", "a"): [1.0] * len(YEARS)})
    crashed = {
        "schema": TOOL_SCHEMA,
        "status": "crashed",
        "error": "Traceback\nValueError: boom",
    }
    summary = compare(base, crashed, SPEC)
    assert summary["status"] == "fail" and "boom" in summary["failures"][0]
    assert compare(base, None, SPEC)["status"] == "fail"


def test_without_a_base_the_heads_own_failing_checks_block():
    head = result(
        {("receipts", "a"): [1.0] * len(YEARS)}, checks=[("identity:x", "fail")]
    )
    summary = compare(None, head, SPEC)
    assert summary["status"] == "fail"
    assert any("identity:x" in f for f in summary["failures"])


def test_different_datasets_fail():
    values = {("receipts", "a"): [1.0] * len(YEARS)}
    summary = compare(result(values), result(values, sha="6" * 64), SPEC)
    assert summary["status"] == "fail"


def test_non_finite_head_figures_block_even_when_the_base_shares_them():
    values = {("receipts", "a"): [1.0] * len(YEARS)}
    checks = [("finite:metrics", "fail")]
    summary = compare(result(values, checks), result(values, checks), SPEC)
    assert summary["status"] == "fail"


def test_strict_mode_fails_pre_existing_failures():
    values = {("receipts", "a"): [1.0] * len(YEARS)}
    side = result(values, checks=[("sign:vat", "fail")])
    assert compare(side, copy.deepcopy(side), SPEC)["status"] == "pass"
    assert compare(side, copy.deepcopy(side), SPEC, strict=True)["status"] == "fail"


def test_a_partition_edit_is_noted():
    values = {("receipts", "a"): [1.0] * len(YEARS)}
    summary = compare(result(values), result(values, partition_sha="q"), SPEC)
    assert any("partition" in w for w in summary["warnings"])


def households(n, rng, decile=None, income=None, weight=None):
    return {
        str(y): {
            "household_id": np.arange(n),
            "household_weight": weight
            if weight is not None
            else rng.uniform(1, 1000, n),
            "household_count_people": rng.integers(1, 6, n).astype(float),
            "decile": decile if decile is not None else rng.integers(1, 11, n),
            "income": income if income is not None else rng.uniform(1e3, 1e5, n),
        }
        for y in YEARS
    }


@settings(max_examples=30, deadline=None)
@given(seed=st.integers(0, 2**32 - 1), n=st.integers(20, 400))
def test_decile_impacts_match_a_direct_grouped_calculation(seed, n):
    rng = np.random.default_rng(seed)
    base = households(n, rng)
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"] + rng.normal(0, 500, n)
    impacts, _ = decile_impacts(base, head, YEARS)
    year = str(YEARS[0])
    b, h = base[year], head[year]
    frame = pd.DataFrame(
        {
            "d": b["decile"],
            "w": b["household_weight"],
            "base": b["income"],
            "change": h["income"] - b["income"],
        }
    )
    for row in impacts[year][:-1]:
        group = frame[frame.d == row["decile"]]
        if group.empty:
            continue
        mean_change = (group.w * group.change).sum() / group.w.sum()
        relative = (group.w * group.change).sum() / (group.w * group.base).sum()
        assert row["mean_change"] == pytest.approx(mean_change)
        assert row["relative_change"] == pytest.approx(relative)


@settings(max_examples=30, deadline=None)
@given(seed=st.integers(0, 2**32 - 1), shift=st.floats(-1e4, 1e4))
def test_a_uniform_change_shows_in_every_decile(seed, shift):
    rng = np.random.default_rng(seed)
    base = households(200, rng, decile=np.repeat(np.arange(1, 11), 20))
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"] + shift
        columns["household_id"] = columns["household_id"][::-1].copy()
        for key in ("household_weight", "household_count_people", "decile", "income"):
            columns[key] = columns[key][::-1].copy()
    impacts, notes = decile_impacts(base, head, YEARS)
    assert not any("differ" in n for n in notes)
    for row in impacts[str(YEARS[0])]:
        assert row["mean_change"] == pytest.approx(shift, abs=1e-6)
        assert row["share_gaining"] == (1.0 if shift > 1 else 0.0)
        assert row["share_losing"] == (1.0 if shift < -1 else 0.0)


@settings(max_examples=50, deadline=None)
@given(seed=st.integers(0, 2**32 - 1), n=st.integers(2, 300))
def test_gini_matches_microdf(seed, n):
    from microdf import MicroSeries

    rng = np.random.default_rng(seed)
    income = rng.lognormal(10, 1, n)
    weights = rng.uniform(0.5, 50, n)
    assert weighted_gini(income, weights) == pytest.approx(
        float(MicroSeries(income, weights=weights).gini()), abs=1e-6
    )


def test_gini_bounds():
    assert weighted_gini(np.ones(10), np.ones(10)) == pytest.approx(0)
    assert weighted_gini(np.r_[np.zeros(99), 1.0], np.ones(100)) == pytest.approx(0.99)


@pytest.mark.parametrize(
    "value, kind, text",
    [
        (1.234e9, "gbp", "+£1.23bn"),
        (-5.5e6, "gbp", "-£5.5m"),
        (0, "gbp", "0"),
        (12_300, "count", "+12.3k"),
        (0.0012, "rate", "+0.12pp"),
        (None, "gbp", "n/a"),
    ],
)
def test_change_formatting(value, kind, text):
    assert fmt_change(value, kind) == text


def test_level_formatting():
    assert fmt_level(320.5e9, "gbp") == "£320.50bn"
    assert fmt_level(0.2335, "rate") == "23.4%"
    assert fmt_level(float("nan"), "gbp") == "n/a"


@settings(max_examples=20, deadline=None)
@given(values=metric_values, limit=st.integers(2000, 20000))
def test_the_comment_carries_the_marker_and_fits_its_limit(values, limit):
    head = {k: [v + 1e9 for v in series] for k, series in values.items()}
    summary = compare(result(values), result(head), SPEC)
    spec = SPEC.__class__(**{**SPEC.__dict__, "max_comment_characters": limit})
    text = render(summary, spec)
    assert text.startswith(COMMENT_MARKER)
    assert len(text) <= limit + 1
    assert render(summary, spec) == text


def test_a_skipped_head_passes_with_a_note():
    skipped = {"schema": TOOL_SCHEMA, "status": "skipped", "reason": "no data access"}
    summary = compare(None, skipped, SPEC)
    assert summary["status"] == "skipped" and summary["failures"] == []
    text = render(summary, SPEC)
    assert text.startswith(COMMENT_MARKER) and "no data access" in text
