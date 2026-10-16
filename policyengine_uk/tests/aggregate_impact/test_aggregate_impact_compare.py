"""Comparison and rendering of two measurements, on synthetic results."""

import copy
import json
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact import COMMENT_MARKER, TOOL_SCHEMA
from policyengine_uk.utils.aggregate_impact.compare import (
    REQUIRED_CHECKS,
    _match,
    classify_check,
    compare,
    decile_impacts,
)
from policyengine_uk.tests.aggregate_impact.test_aggregate_impact_measure import (
    _protection_partition,
    _recorded,
)
from policyengine_uk.utils.aggregate_impact.measure import (
    hidden_detail,
    protect_totals,
    weighted_gini,
)
from policyengine_uk.utils.aggregate_impact.privacy import HIDDEN_KEY
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


def check(check_id, status="pass", failing=()):
    return {
        "id": check_id,
        "label": check_id,
        "section": "s",
        "severity": "fail",
        "status": status,
        "details": ["d"] if status != "pass" else [],
        "failing": {
            scope: "d" for scope in (failing or ([""] if status == "fail" else []))
        },
    }


def result(values, checks=(), sha=SHA, status="ok", partition_sha="p", required=True):
    """A measurement with one metric per (section, name) and the given checks."""
    all_checks = [check(c) for c in REQUIRED_CHECKS] if required else []
    for entry in checks:
        all_checks.append(check(*entry) if isinstance(entry, tuple) else entry)
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
        "checks": all_checks,
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
        ("skipped", "fail", False, "regression"),
        ("fail", "fail", False, "pre_existing"),
        ("fail", "fail", True, "regression"),
        ("warn", "fail", False, "regression"),
        ("pass", "warn", False, "new_warning"),
        ("warn", "warn", False, "warning"),
        ("pass", "skipped", False, "skipped"),
        ("pass", None, False, "removed"),
    ],
)
def test_check_classification(base, head, blocking, expected):
    assert classify_check(base, head, blocking) == expected


@settings(max_examples=200, deadline=None)
@given(
    base=st.sets(st.sampled_from(["2025", "2026", "2027", ""])),
    head=st.sets(st.sampled_from(["2025", "2026", "2027", ""]), min_size=1),
)
def test_a_failure_is_pre_existing_only_if_the_base_fails_everywhere_the_head_does(
    base, head
):
    verdict = classify_check("fail" if base else "pass", "fail", False, base, head)
    assert verdict == ("pre_existing" if base and head <= base else "regression")


@settings(max_examples=60, deadline=None)
@given(values=metric_values)
def test_identical_sides_change_nothing(values):
    side = result(values, checks=[("identity:x", "pass"), ("sign:y", "fail")])
    summary = compare(side, copy.deepcopy(side), SPEC)
    assert summary["status"] == "pass", summary["failures"]
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


# The data axis: one model, two datasets (uk-data pull requests).


def _on(data_sha, **provenance):
    measured = result({("receipts", "a"): [1.0] * len(YEARS)}, sha=data_sha)
    measured["provenance"].update({"metrics_version": "m", **provenance})
    measured["runtime"].update(
        policyengine_uk="2.122.2",
        policyengine_uk_fingerprint="f" * 64,
        local_installs=["policyengine-uk-data"],
    )
    return measured


def test_the_data_axis_allows_two_datasets_but_the_model_axis_does_not():
    base, head = _on("1" * 64), _on("2" * 64)
    assert compare(base, head, SPEC)["status"] == "fail"
    summary = compare(base, head, SPEC, axis="data")
    assert summary["status"] == "pass", summary["failures"]
    assert summary["axis"] == "data"


@pytest.mark.parametrize(
    "change, message",
    [
        (
            lambda r: r["runtime"].update(policyengine_uk_fingerprint="e" * 64),
            "one policyengine-uk fingerprint",
        ),
        (
            lambda r: r["runtime"].update(policyengine_uk="9.9.9"),
            "one policyengine-uk version",
        ),
        (lambda r: r["runtime"].update(distributions=["numpy==9.0"]), "one runtime"),
        (lambda r: r["partition"].update(sha256="other"), "fiscal partition"),
        (
            lambda r: r["provenance"].update(metrics_version="other"),
            "metric definitions",
        ),
        (
            lambda r: r["provenance"]["dataset"].pop("verified_sha256"),
            "record the bytes",
        ),
    ],
)
def test_a_data_comparison_fails_unless_only_the_data_differs(change, message):
    base, head = _on("1" * 64), _on("2" * 64)
    change(head)
    summary = compare(base, head, SPEC, axis="data")
    assert summary["status"] == "fail"
    assert any(message in f for f in summary["failures"]), summary["failures"]


def test_the_data_axis_does_not_match_households_across_datasets():
    base, head = _on("1" * 64), _on("2" * 64)
    households = {"2025": {"household_id": np.arange(3)}}
    summary = compare(
        base,
        head,
        SPEC,
        base_households=households,
        head_households=households,
        axis="data",
    )
    assert summary["deciles"] == {}
    assert "not matched" in summary["decile_notes"][0]
    text = render(summary, SPEC)
    assert "## Aggregate impact of the data change: pass" in text
    assert "Base dataset" in text and "not matched" in text


@settings(max_examples=50, deadline=None)
@given(values=metric_values)
def test_a_data_comparison_with_itself_moves_nothing(values):
    side = result(values)
    side["provenance"]["metrics_version"] = "m"
    side["runtime"].update(
        policyengine_uk="2.122.2",
        policyengine_uk_fingerprint="f" * 64,
        local_installs=[],
    )
    summary = compare(side, side, SPEC, axis="data")
    assert summary["status"] == "pass"
    assert not any(row["changed"] for row in summary["rows"])
    assert summary["flags"] == []
    assert "Both sides measured the same dataset bytes." in summary["warnings"]


def test_an_unknown_axis_is_refused():
    with pytest.raises(ValueError, match="axis"):
        compare(_on("1" * 64), _on("1" * 64), SPEC, axis="sideways")


def test_measure_records_an_unpinned_dataset_by_its_bytes(tmp_path, monkeypatch):
    """With --dataset-file and no --pin, the measured bytes are the identity."""
    import json

    import policyengine_uk
    from policyengine_uk.utils.aggregate_impact import __main__ as cli
    from policyengine_uk.utils.aggregate_impact import measure as measure_module
    from policyengine_uk.utils.aggregate_impact.dataset import sha256_file

    built = tmp_path / "enhanced_frs_2024_25.h5"
    built.write_bytes(b"not really an h5 file")

    class StubSimulation:
        def __init__(self, dataset=None, reform=None):
            self.dataset = dataset

    def stub_measure(
        sim, factory, partition, spec, label, reforms, run_guard, provenance
    ):
        return {
            "schema": "x",
            "status": "ok",
            "provenance": provenance,
            "metrics": [],
            "timings": {"total": 0},
        }, None

    monkeypatch.setattr(policyengine_uk, "Microsimulation", StubSimulation)
    monkeypatch.setattr(measure_module, "measure", stub_measure)
    out = tmp_path / "out"
    code = cli.main(
        [
            "measure",
            "--label",
            "head",
            "--dataset-file",
            str(built),
            "--dataset-label",
            "uk-data #595 head build",
            "--no-reforms",
            "--no-guard",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    dataset = json.loads((out / "result.json").read_text())["provenance"]["dataset"]
    assert dataset == {
        "path": "enhanced_frs_2024_25.h5",
        "data_package": "unpinned build",
        "data_version": "uk-data #595 head build",
        "verified_sha256": sha256_file(built),
    }


def test_flags_follow_the_spec_thresholds():
    base = {("receipts", "a"): [100e9] * len(YEARS)}
    small = {("receipts", "a"): [100e9 + 50e6] * len(YEARS)}
    large = {("receipts", "a"): [100e9 + 200e6] * len(YEARS)}
    assert compare(result(base), result(small), SPEC)["flags"] == []
    assert len(compare(result(base), result(large), SPEC)["flags"]) == len(YEARS)


CRASHED = {
    "schema": TOOL_SCHEMA,
    "status": "crashed",
    "error": "Traceback\nValueError: boom",
}
ONE = {("receipts", "a"): [1.0] * len(YEARS)}


def test_a_crashed_or_missing_head_fails():
    summary = compare(result(ONE), CRASHED, SPEC)
    assert summary["status"] == "fail" and "boom" in summary["failures"][0]
    assert compare(result(ONE), None, SPEC)["status"] == "fail"


def test_a_crashed_or_missing_base_fails_unless_it_is_not_required():
    for base in (CRASHED, None):
        assert compare(base, result(ONE), SPEC)["status"] == "fail"
        relaxed = compare(base, result(ONE), SPEC, require_base=False)
        assert relaxed["status"] == "pass" and relaxed["warnings"]


def test_without_a_base_the_heads_own_failing_checks_block():
    head = result(ONE, checks=[("identity:x", "fail")])
    summary = compare(None, head, SPEC, require_base=False)
    assert summary["status"] == "fail"
    assert any("identity:x" in f for f in summary["failures"])


def test_different_datasets_fail():
    summary = compare(result(ONE), result(ONE, sha="6" * 64), SPEC)
    assert summary["status"] == "fail"


def test_non_finite_head_figures_block_even_when_the_base_shares_them():
    checks = [check("finite:x", "fail")]
    summary = compare(result(ONE, checks), result(ONE, checks), SPEC)
    assert summary["status"] == "fail"


def test_a_non_finite_head_figure_fails_even_if_no_check_caught_it():
    """Reform costings are measured after most checks; compare looks itself."""
    bad = {("receipts", "a"): [1.0] * (len(YEARS) - 1) + [float("nan")]}
    summary = compare(result(ONE), result(bad), SPEC)
    assert summary["status"] == "fail"
    assert any("not finite" in f for f in summary["failures"])


def test_a_newly_failing_year_is_a_regression_not_pre_existing():
    base = result(ONE, checks=[check("identity:x", "fail", ["2025"])])
    same = result(ONE, checks=[check("identity:x", "fail", ["2025"])])
    worse = result(ONE, checks=[check("identity:x", "fail", ["2025", "2026"])])
    assert compare(base, same, SPEC)["status"] == "pass"
    summary = compare(base, worse, SPEC)
    assert summary["status"] == "fail"
    assert any("identity:x" in f for f in summary["failures"])


def test_a_check_that_vanishes_fails_unless_the_partition_changed():
    base = result(ONE, checks=[("sign:vat", "pass")])
    summary = compare(base, result(ONE), SPEC)
    assert summary["status"] == "fail"
    assert any("sign:vat" in f for f in summary["failures"])
    edited = compare(base, result(ONE, partition_sha="q"), SPEC)
    assert edited["status"] == "pass"
    assert any("sign:vat" in w for w in edited["warnings"])


def test_a_head_without_the_required_checks_fails():
    summary = compare(result(ONE), result(ONE, required=False), SPEC)
    assert summary["status"] == "fail"
    assert any("finite:metrics" in f for f in summary["failures"])


def test_a_check_that_no_longer_applies_is_noted_not_failed():
    base = result(ONE, checks=[("counted_once:x", "pass")])
    head = result(ONE, checks=[check("counted_once:x", "skipped")])
    summary = compare(base, head, SPEC)
    assert summary["status"] == "pass"
    assert any("counted_once:x" in w for w in summary["warnings"])


def test_a_figure_on_one_side_only_is_a_change():
    two = {**ONE, ("receipts", "b"): [2.0] * len(YEARS)}
    removed = compare(result(two), result(ONE), SPEC)
    row = next(r for r in removed["rows"] if r["id"] == "receipts.b")
    assert row["changed"] and row["only_in"] == "base"
    text = render(removed, SPEC)
    assert "removed: base levels" in text
    assert "No change in any year:** receipts" not in text
    added = compare(result(ONE), result(two), SPEC)
    assert "new: head levels" in render(added, SPEC)


def test_strict_mode_fails_pre_existing_failures():
    side = result(ONE, checks=[("sign:vat", "fail")])
    assert compare(side, copy.deepcopy(side), SPEC)["status"] == "pass"
    assert compare(side, copy.deepcopy(side), SPEC, strict=True)["status"] == "fail"


def test_a_partition_edit_is_noted():
    summary = compare(result(ONE), result(ONE, partition_sha="q"), SPEC)
    assert any("partition" in w for w in summary["warnings"])


def test_households_match_only_one_to_one():
    assert _match(np.array([1, 2]), np.array([1, 2, 3])) is None
    assert _match(np.array([1, 2]), np.array([1, 1])) is None
    assert _match(np.array([1, 1]), np.array([1, 1])) is None
    assert np.array_equal(_match(np.array([1, 2, 3]), np.array([3, 1, 2])), [1, 2, 0])


@settings(max_examples=100, deadline=None)
@given(
    ids=st.lists(st.integers(0, 10_000), min_size=1, max_size=60, unique=True),
    data=st.data(),
)
def test_matching_recovers_any_permutation(ids, data):
    base = np.array(ids)
    head = np.array(data.draw(st.permutations(ids)))
    matched = _match(base, head)
    assert matched is not None and np.array_equal(head[matched], base)


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
        changed = int(((group.change.abs() > 0.005) & (group.w > 0)).sum())
        if 0 < changed < 10:
            assert row["suppressed"] and row["mean_change"] is None
            continue
        mean_change = (group.w * group.change).sum() / group.w.sum()
        relative = (group.w * group.change).sum() / (group.w * group.base).sum()
        # Published to what the comment shows: £1 and 0.1%.
        assert row["mean_change"] == round(mean_change)
        assert row["relative_change"] == round(relative, 3)
        assert "households" not in row and "base_mean" not in row


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
        assert row["mean_change"] == pytest.approx(shift, abs=0.5 + 1e-6)
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


def test_the_guard_section_lists_failures_and_mediated_responses():
    from policyengine_uk.utils.aggregate_impact.render import _guard

    guard = {
        "status": "ran",
        "year": 2026,
        "components": [
            {
                "variable": "incapacity_benefit",
                "status": "fail",
                "problems": [
                    {
                        "message": "household_benefits: pension_credit rises in 2 households"
                    }
                ],
                "mediated": [
                    {
                        "total": "household_benefits",
                        "head": "universal_credit",
                        "kind": "contains",
                        "households": 72,
                        "via": ["carers_allowance"],
                    }
                ],
            },
            {"variable": "vat", "status": "pass", "mediated": []},
        ],
        "double_counts": [],
    }
    text = _guard({"head": {"guard": guard}})
    assert "held at its baseline value" in text
    assert "1 failed; 0 were skipped" in text
    assert "pension_credit rises in 2 households" in text
    assert (
        "`universal_credit` responds only through other heads in 72 households "
        "(other heads that moved there: `carers_allowance`" in text
    )


def test_a_figure_from_too_few_records_is_suppressed_end_to_end():
    """Sol re-review 2, finding 1: a total and caseload from one recipient
    reveal the award and the weight, so neither is published."""
    from policyengine_uk.utils.aggregate_impact.api import to_report
    from policyengine_uk.utils.aggregate_impact.measure import (
        Recorder,
        _finite_metrics_check,
    )
    from policyengine_uk.utils.aggregate_impact.render import _levels_table

    rec = Recorder()
    rec.metric("spending.ben", "Ben", "spending", "gbp", 2025, 246.9, records=1)
    rec.metric("spending.ben", "Ben", "spending", "gbp", 2026, 9e9, records=500)
    rec.metric("spending.none", "None", "spending", "gbp", 2025, 0.0, records=0)
    ben = rec.metrics["spending.ben"]
    assert ben["values"] == {"2025": None, "2026": 9e9}
    assert ben["suppressed"] == ["2025"]
    # Zero records reveal nothing: an inert head stays at zero.
    assert rec.metrics["spending.none"]["values"] == {"2025": 0.0}
    _finite_metrics_check(rec)
    assert rec.checks["finite:metrics"]["status"] == "pass"

    base = result({("receipts", "ben"): [1.0] * len(YEARS)})
    head = result({("receipts", "ben"): [1.0] * len(YEARS)})
    metric = next(m for m in head["metrics"] if m["id"] == "receipts.ben")
    metric["values"][str(YEARS[0])] = None
    metric["suppressed"] = [str(YEARS[0])]
    summary = compare(base, head, SPEC)
    assert summary["status"] == "pass", summary["failures"]
    row = next(r for r in summary["rows"] if r["id"] == "receipts.ben")
    assert row["changed"] and row["values"][str(YEARS[0])]["head_suppressed"]
    assert summary["flags"] == []
    assert "suppressed" in _levels_table([row], YEARS)
    assert "suppressed" in render(summary, SPEC)
    report = to_report({**head, "partition": {"sha256": "p"}})
    first = next(
        m
        for m in report["metrics"]
        if m["metric_id"] == "receipts.ben" and m["year"] == YEARS[0]
    )
    assert first["value"] is None and first["suppressed"] is True


def test_published_guard_output_keeps_no_small_counts_or_shares():
    """Sol re-review 2, finding 3."""
    from policyengine_uk.utils.aggregate_impact.measure import publishable_guard

    guard = {
        "status": "ran",
        "components": [
            {
                "variable": "x",
                "units": 3,
                "problems": [
                    {
                        "households": 1,
                        "share": 0.125,
                        "message": "in fewer than 10 households",
                    },
                    {"households": 40, "share": 0.5, "message": "in 40 households"},
                ],
                "mediated": [{"households": 2, "head": "uc", "via": []}],
            }
        ],
    }
    guard["components"][0]["responses"] = {"gov_spending": {"uc": -0.55}}
    guard["components"][0]["coefficients"] = {"gov_spending": 1.0}
    out = publishable_guard(guard)
    row = out["components"][0]
    assert row["units"] is None
    assert (
        row["problems"][0]["households"] is None and "share" not in row["problems"][0]
    )
    # Sol re-review 3, finding 6: with only 3 perturbed units, no share and no
    # response survives, even for a problem in 40 households.
    assert row["problems"][1] == {"households": 40, "message": "in 40 households"}
    assert row["responses"] == {} and row["coefficients"] == {}
    assert row["mediated"][0]["households"] is None
    # The input is not changed.
    assert guard["components"][0]["units"] == 3
    # With enough perturbed units, a large problem keeps its share.
    guard["components"][0]["units"] = 300
    kept = publishable_guard(guard)["components"][0]
    assert kept["problems"][1]["share"] == 0.5
    assert kept["responses"] == {"gov_spending": {"uc": -0.55}}


# Sol re-review 3 of #2335: decile rows and protected totals' changes.


@pytest.mark.parametrize("changed", [1, 9, 10])
def test_a_decile_row_from_fewer_than_10_changed_households_publishes_no_change(
    changed,
):
    rng = np.random.default_rng(0)
    base = households(100, rng, decile=np.repeat(np.arange(1, 11), 10))
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"].copy()
        columns["income"][:changed] += 250.0  # all in decile 1
    impacts, _ = decile_impacts(base, head, YEARS)
    rows = {row["decile"]: row for row in impacts[str(YEARS[0])]}
    assert rows[1]["suppressed"] == (changed < 10)
    assert rows["all"]["suppressed"] == (changed < 10)
    if changed < 10:
        assert all(rows[1][k] is None for k in ("mean_change", "share_gaining"))
    # Deciles where nothing changed publish a zero change.
    assert rows[2]["mean_change"] == 0 and not rows[2]["suppressed"]


def test_a_zero_weight_household_does_not_count_as_changed():
    rng = np.random.default_rng(1)
    weight = rng.uniform(1, 1000, 100)
    weight[:10] = 0.0  # decile 1 carries no weight
    base = households(100, rng, decile=np.repeat(np.arange(1, 11), 10), weight=weight)
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"].copy()
        columns["income"][:12] += 250.0  # 10 zero-weight in decile 1, 2 weighted in 2
    impacts, _ = decile_impacts(base, head, YEARS)
    rows = {row["decile"]: row for row in impacts[str(YEARS[0])]}
    # Twelve households change, but only two carry weight: a small cell.
    assert rows[2]["suppressed"] and rows["all"]["suppressed"]
    assert not rows[1]["suppressed"]


@settings(max_examples=50, deadline=None)
@given(seed=st.integers(0, 2**32 - 1))
def test_published_decile_rows_cannot_rebuild_the_income_total(seed):
    """The "all" row's mean change over its relative change, times the
    household count, gave the exact base income total back."""
    rng = np.random.default_rng(seed)
    base = households(300, rng)
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"] + rng.normal(0, 500, 300)
    impacts, _ = decile_impacts(base, head, YEARS)
    for row in impacts[str(YEARS[0])]:
        assert "households" not in row and "base_mean" not in row
        if not row["suppressed"]:
            assert row["mean_change"] == round(row["mean_change"])
            assert row["relative_change"] == round(row["relative_change"], 3)
            assert row["share_gaining"] == round(row["share_gaining"], 3)


def _sides(rare_base, rare_head, common_head=7.4e10):
    out = []
    for common, rare in ((7.3e10, rare_base), (common_head, rare_head)):
        rec = _recorded(common=common, rare=rare)
        protect_totals(rec, _protection_partition(), set(), 2026)
        out.append(
            ({m["id"]: m for m in rec.metrics.values()}, hidden_detail(rec, 2026))
        )
    return out


def _cell(rows, metric_id):
    return next(r for r in rows if r["id"] == metric_id)["values"]["2026"]


def test_a_rounded_total_shows_its_exact_change_when_no_suppressed_head_moved():
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics

    (base, base_hidden), (head, head_hidden) = _sides(246.9, 246.9)
    rows, flags = compare_metrics(
        base, head, SPEC, [2026], base_hidden=base_hidden, head_hidden=head_hidden
    )
    total = _cell(rows, "model.gov_spending")
    # Levels stay rounded; the change is the common benefit's exact £1bn.
    assert total["base"] == 7.3e10 and total["head"] == 7.4e10
    assert total["delta"] == pytest.approx(1e9) and not total["rounded"]
    assert any(f["id"] == "model.gov_spending" for f in flags)
    # The suppressed head itself never shows a change.
    assert _cell(rows, "spending.rare")["delta"] is None


def test_a_rounded_total_withholds_its_change_when_a_suppressed_head_moved():
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics

    (base, base_hidden), (head, head_hidden) = _sides(246.9, 300.0, common_head=7.3e10)
    rows, flags = compare_metrics(
        base, head, SPEC, [2026], base_hidden=base_hidden, head_hidden=head_hidden
    )
    total = _cell(rows, "model.gov_spending")
    assert total["delta"] is None and total["rounded"]
    assert not any(f["id"] == "model.gov_spending" for f in flags)
    # The exact gov_tax change is unaffected: it holds no suppressed head.
    assert _cell(rows, "model.gov_tax")["delta"] == 0


def test_without_private_detail_a_rounded_total_withholds_its_change():
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics

    (base, _), (head, _) = _sides(246.9, 246.9)
    rows, flags = compare_metrics(base, head, SPEC, [2026])
    total = _cell(rows, "model.gov_spending")
    assert total["delta"] is None and total["rounded"]
    assert not any(f["id"] == "model.gov_spending" for f in flags)


@settings(max_examples=100, deadline=None)
@given(
    rare=st.floats(1.0, 4.9e8),
    moved=st.floats(-1e8, 1e8),
    common_change=st.floats(-1e10, 1e10),
)
def test_a_published_change_never_reveals_a_suppressed_heads_change(
    rare, moved, common_change
):
    """For all inputs: the published changes of every total, less the
    published changes of the heads, never give the suppressed head's change."""
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics

    (base, bh), (head, hh) = _sides(
        rare, rare + moved, common_head=7.3e10 + common_change
    )
    rows, _ = compare_metrics(base, head, SPEC, [2026], base_hidden=bh, head_hidden=hh)
    published = {r["id"]: r["values"]["2026"]["delta"] for r in rows}
    assert published["spending.rare"] is None
    if rare + moved != rare:  # the suppressed head really changed
        for total in (
            "model.gov_spending",
            "model.household_benefits",
            "balance.spending",
        ):
            assert published[total] is None


def test_hidden_detail_is_written_only_to_private_and_read_back(tmp_path):
    from policyengine_uk.utils.aggregate_impact.measure import read_result, write_result

    (base, hidden), _ = _sides(246.9, 246.9)
    households = {"2026": {"household_id": np.arange(3)}, HIDDEN_KEY: hidden}
    write_result(tmp_path, {"schema": "x", "metrics": list(base.values())}, households)
    published = (tmp_path / "result.json").read_text()
    assert "246.9" not in published and "hidden" not in published
    assert (tmp_path / "private" / "hidden.json").exists()
    _, loaded = read_result(tmp_path)
    assert loaded[HIDDEN_KEY] == json.loads(json.dumps(hidden))


def test_a_withheld_change_and_a_small_decile_row_render_as_such():
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics
    from policyengine_uk.utils.aggregate_impact.render import _change_cell, _deciles

    (base, bh), (head, hh) = _sides(246.9, 300.0, common_head=7.3e10)
    rows, _ = compare_metrics(base, head, SPEC, [2026], base_hidden=bh, head_hidden=hh)
    total = next(r for r in rows if r["id"] == "model.gov_spending")
    assert _change_cell(total, 2026) == "withheld (rounded total)"
    rare = next(r for r in rows if r["id"] == "spending.rare")
    assert _change_cell(rare, 2026) == "suppressed"
    row = {
        "decile": 1,
        "suppressed": True,
        "mean_change": None,
        "relative_change": None,
        "share_gaining": None,
        "share_losing": None,
    }
    text = _deciles({"deciles": {"2026": [row, dict(row, decile="all")]}}, [2026])
    assert "fewer than 10 households change" in text and "n/a" not in text


def test_the_data_axis_ignores_the_data_package_itself():
    """The data package is what a data comparison compares."""
    base, head = _on("1" * 64), _on("2" * 64)
    base["runtime"]["distributions"] = ["numpy==2.0", "policyengine-uk-data==1.58.1"]
    head["runtime"]["distributions"] = ["numpy==2.0", "policyengine-uk-data==1.59.0"]
    assert compare(base, head, SPEC, axis="data")["status"] == "pass"
    head["runtime"]["distributions"] = ["numpy==2.1", "policyengine-uk-data==1.59.0"]
    assert compare(base, head, SPEC, axis="data")["status"] == "fail"


@pytest.mark.parametrize(
    "path",
    [
        ("runtime", "policyengine_uk"),
        ("runtime", "policyengine_uk_fingerprint"),
        ("runtime", "distributions"),
        ("partition", "sha256"),
        ("provenance", "metrics_version"),
    ],
)
def test_a_data_comparison_fails_when_an_identity_field_is_missing(path):
    """Sol review of #2425, P1: blank or missing identities used to pass."""
    base, head = _on("1" * 64), _on("2" * 64)
    for side in (base, head):
        side[path[0]].pop(path[1])
    summary = compare(base, head, SPEC, axis="data")
    assert summary["status"] == "fail"
    assert any("does not record it" in f for f in summary["failures"])


def test_the_caller_commit_is_not_part_of_the_model_identity():
    """The same installed model measured from two checkouts is one model."""
    summary = compare(
        _on("1" * 64, git_sha="aaa"), _on("2" * 64, git_sha="bbb"), SPEC, axis="data"
    )
    assert summary["status"] == "pass", summary["failures"]


def test_data_axis_provenance_names_both_datasets():
    summary = compare(_on("1" * 64), _on("2" * 64), SPEC, axis="data")
    text = render(summary, SPEC)
    assert "Base dataset" in text and "Head dataset" in text
    assert "verified on both sides" not in text


def test_the_model_fingerprint_covers_the_model_and_nothing_else(tmp_path, monkeypatch):
    import importlib.util
    from types import SimpleNamespace

    from policyengine_uk.utils.aggregate_impact import measure

    package = tmp_path / "policyengine_uk"
    (package / "variables").mkdir(parents=True)
    (package / "tests").mkdir()
    (package / "__pycache__").mkdir()
    (package / "__init__.py").write_text("")
    (package / "variables" / "x.py").write_text("a = 1")
    (package / "tests" / "t.yaml").write_text("x")
    (package / "__pycache__" / "c.pyc").write_bytes(b"x")
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(package / "__init__.py")),
    )
    first = measure.model_fingerprint()
    assert first == measure.model_fingerprint()
    (package / "tests" / "t.yaml").write_text("changed")
    (package / "__pycache__" / "c.pyc").write_bytes(b"changed")
    assert measure.model_fingerprint() == first
    (package / "variables" / "x.py").write_text("a = 2")
    assert measure.model_fingerprint() != first


def test_a_suppression_transition_withholds_the_totals_exact_change():
    """Sol re-review 4, finding 1: 10 recipients on the base and 9 on the head,
    same total; an exact total change would show the 9 still add to £246.90."""
    from policyengine_uk.utils.aggregate_impact.compare import compare_metrics
    from policyengine_uk.utils.aggregate_impact.measure import Recorder

    sides = []
    for records, common in ((10, 7.3e10), (9, 7.4e10)):
        rec = Recorder()
        rec.metric("receipts.tax", "Tax", "receipts", "gbp", 2026, 5e11, records=5000)
        rec.metric("spending.common", "C", "spending", "gbp", 2026, common, records=500)
        rec.metric(
            "spending.rare", "R", "spending", "gbp", 2026, 246.9, records=records
        )
        for total in (
            "model.gov_spending",
            "model.household_benefits",
            "balance.spending",
        ):
            rec.metric(total, total, "model_totals", "gbp", 2026, common + 246.9)
        rec.metric("model.gov_tax", "gov_tax", "model_totals", "gbp", 2026, 5e11)
        rec.metric(
            "balance.balance", "b", "balance", "gbp", 2026, 5e11 - common - 246.9
        )
        protect_totals(rec, _protection_partition(), set(), 2026)
        sides.append(
            ({m["id"]: m for m in rec.metrics.values()}, hidden_detail(rec, 2026))
        )
    (base, bh), (head, hh) = sides
    rows, _ = compare_metrics(base, head, SPEC, [2026], base_hidden=bh, head_hidden=hh)
    assert _cell(rows, "model.gov_spending")["delta"] is None
    assert _cell(rows, "spending.rare")["delta"] is None
    assert _cell(rows, "spending.common")["delta"] == pytest.approx(1e9)


def test_decile_changes_that_round_to_zero_are_not_called_no_change():
    """Sol re-review 4, finding 6."""
    from policyengine_uk.utils.aggregate_impact.render import _deciles

    rng = np.random.default_rng(3)
    base = households(100, rng, decile=np.repeat(np.arange(1, 11), 10))
    head = copy.deepcopy(base)
    for columns in head.values():
        columns["income"] = columns["income"] + 0.25
    impacts, _ = decile_impacts(base, head, YEARS)
    assert all(
        r["mean_change"] == 0 and r["any_change"] for r in impacts[str(YEARS[0])]
    )
    text = _deciles({"deciles": {str(YEARS[0]): impacts[str(YEARS[0])]}}, [YEARS[0]])
    assert "rounds to £0" in text and "No household" not in text
    unchanged, _ = decile_impacts(base, copy.deepcopy(base), YEARS)
    text = _deciles({"deciles": {str(YEARS[0]): unchanged[str(YEARS[0])]}}, [YEARS[0]])
    assert "No household's net income changes" in text


def test_the_data_axis_refuses_a_locally_installed_dependency():
    """Sol review of #2425 at 7ca4ff2b, P2: an editable policyengine-core
    reports a released version whatever its files hold."""
    base, head = _on("1" * 64), _on("2" * 64)
    assert compare(base, head, SPEC, axis="data")["status"] == "pass"
    head["runtime"]["local_installs"] = ["policyengine-core", "policyengine-uk-data"]
    summary = compare(base, head, SPEC, axis="data")
    assert summary["status"] == "fail"
    assert any("policyengine-core" in f for f in summary["failures"])
    # The model and the data package are identified otherwise.
    head["runtime"]["local_installs"] = ["policyengine-uk", "policyengine-uk-data"]
    assert compare(base, head, SPEC, axis="data")["status"] == "pass"
    del head["runtime"]["local_installs"]
    assert compare(base, head, SPEC, axis="data")["status"] == "fail"


def test_local_installs_are_read_from_pep_610_metadata(monkeypatch):
    import json as json_

    from policyengine_uk.utils.aggregate_impact import measure

    class Dist:
        def __init__(self, name, direct_url):
            self.metadata = {"Name": name}
            self._direct = direct_url

        def read_text(self, filename):
            return None if self._direct is None else json_.dumps(self._direct)

    dists = [
        Dist("numpy", None),
        Dist(
            "policyengine_core",
            {"url": "file:///src/core", "dir_info": {"editable": True}},
        ),
        Dist("pandas", {"url": "file:///wheels/pandas.whl", "archive_info": {}}),
        Dist(
            "requests",
            {"url": "https://files.example/requests.whl", "archive_info": {}},
        ),
    ]
    monkeypatch.setattr(measure.metadata, "distributions", lambda: dists)
    assert measure._local_installs() == ["pandas", "policyengine-core"]


def test_a_model_that_changes_during_a_measurement_has_no_fingerprint(monkeypatch):
    """Sol review of #2425 at 7ca4ff2b, P2: a branch switched in a shared
    checkout mid-run would stamp the base with the head's files."""
    from policyengine_uk.utils.aggregate_impact import measure

    monkeypatch.setattr(measure, "model_fingerprint", lambda: "after")
    rec = measure.Recorder()
    runtime = measure.stable_runtime(rec, "before")
    assert runtime["policyengine_uk_fingerprint"] is None
    assert rec.checks["model:unchanged"]["status"] == "fail"
    rec = measure.Recorder()
    runtime = measure.stable_runtime(rec, "after")
    assert runtime["policyengine_uk_fingerprint"] == "after"
    assert rec.checks["model:unchanged"]["status"] == "pass"


def test_an_unpinned_dataset_is_described_by_its_label():
    from policyengine_uk.utils.aggregate_impact.render import render

    base, head = _on("1" * 64), _on("2" * 64)
    for side, label in (
        (base, "the base's build"),
        (head, "this pull request's build"),
    ):
        side["provenance"]["dataset"].update(
            data_package="unpinned build", data_version=label
        )
    text = render(compare(base, head, SPEC, axis="data"), SPEC)
    assert "(the base's build, sha256" in text
    assert "(this pull request's build, sha256" in text
    assert "unpinned build the" not in text
