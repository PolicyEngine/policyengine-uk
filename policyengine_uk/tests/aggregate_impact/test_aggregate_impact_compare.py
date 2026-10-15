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
    REQUIRED_CHECKS,
    _match,
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


# The data axis: one model, two datasets (uk-data pull requests).


def _on(data_sha, **provenance):
    measured = result({("receipts", "a"): [1.0] * len(YEARS)}, sha=data_sha)
    measured["provenance"].update(provenance)
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
        (lambda r: r["provenance"].update(git_sha="def"), "commits"),
        (lambda r: r["runtime"].update(policyengine_uk="9.9.9"), "ran policyengine-uk"),
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
    out = publishable_guard(guard)
    row = out["components"][0]
    assert row["units"] is None
    assert (
        row["problems"][0]["households"] is None and "share" not in row["problems"][0]
    )
    assert row["problems"][1] == {
        "households": 40,
        "share": 0.5,
        "message": "in 40 households",
    }
    assert row["mediated"][0]["households"] is None
    # The input is not changed.
    assert guard["components"][0]["units"] == 3
