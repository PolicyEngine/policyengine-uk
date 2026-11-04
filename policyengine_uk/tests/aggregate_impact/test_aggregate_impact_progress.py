"""Phase receipts from the detached reporting tool, using no tax model."""

import builtins
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
import yaml


TOOL = Path(
    os.environ.get(
        "PE_AGGREGATE_PROGRESS_SOURCE",
        Path(__file__).resolve().parents[2] / "utils" / "aggregate_impact",
    )
)
PREFIX = "aggregate-impact-phase "


class FlushedStream(io.StringIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1
        super().flush()


@pytest.fixture
def tool(monkeypatch):
    """Load the copied CLI package without importing policyengine_uk/Core."""
    name = "_aggregate_progress_test_tool"
    for key in tuple(sys.modules):
        if key == name or key.startswith(name + "."):
            monkeypatch.delitem(sys.modules, key)
    fake_model = ModuleType("policyengine_uk")
    fake_model._progress_test_stub = True
    monkeypatch.setitem(sys.modules, "policyengine_uk", fake_model)
    original_import = builtins.__import__
    attempts = []

    def guarded_import(module, *args, **kwargs):
        if module == "policyengine_core" or module.startswith("policyengine_core."):
            attempts.append(module)
            raise AssertionError("A phase test must not import Core")
        if module.startswith("policyengine_uk."):
            attempts.append(module)
            raise AssertionError("A phase test must not import the tax model")
        return original_import(module, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    spec = importlib.util.spec_from_file_location(
        name, TOOL / "__init__.py", submodule_search_locations=[str(TOOL)]
    )
    package = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, package)
    spec.loader.exec_module(package)
    cli = importlib.import_module(name + ".__main__")
    measure = importlib.import_module(name + ".measure")
    dataset = importlib.import_module(name + ".dataset")
    partition = importlib.import_module(name + ".partition")
    specification = importlib.import_module(name + ".spec")
    reforms = importlib.import_module(name + ".reforms")
    yield SimpleNamespace(
        cli=cli,
        measure=measure,
        dataset=dataset,
        partition=partition,
        specification=specification,
        reforms=reforms,
        model=fake_model,
        blocked_imports=attempts,
    )
    assert attempts == []


def _stub_world(tool, monkeypatch, *, fail_reform=False, interrupt_year=False):
    trace = []
    parameters = object()
    partition = SimpleNamespace(
        component_variables=lambda: (),
        as_dict=lambda: {"name": "stub"},
    )
    spec = SimpleNamespace(years=[2025], guard_year=2025, counted_once_tolerance=0)
    reform = tool.reforms.StandardReform("stub_rate", "Stub policy", {"rate": 2})

    def world(name):
        return SimpleNamespace(
            name=name,
            dataset=object(),
            tax_benefit_system=SimpleNamespace(variables={}, parameters=parameters),
            _invalidate_all_caches=lambda: trace.append(("reset", name)),
        )

    def factory(reform=None):
        trace.append(("factory", reform))
        if reform is not None and fail_reform:
            raise RuntimeError("SECRET_FINANCIAL_MARKER_123")
        return world("rebuilt" if reform is None else "reformed")

    def year(sim, partition, spec, year, rec, households):
        trace.append(("measure_year", sim.name, year))
        if interrupt_year:
            raise KeyboardInterrupt
        rec.metric("stub.total", "Stub total", "stub", "gbp", year, 1)
        households[year] = {"stub": [1]}

    def total(sim, variable, year):
        trace.append(("weighted_total", sim.name, variable, year))
        return 2 if sim.name == "reformed" else 1

    def counted(*args, **kwargs):
        trace.append(("counted_once", args[2], args[3], args[4], kwargs))
        return {"status": "ran", "components": [], "double_counts": []}

    m = tool.measure
    monkeypatch.setattr(m, "read_model_lists", lambda _: ({}, []))
    monkeypatch.setattr(m, "closure_problems", lambda *args: [])
    monkeypatch.setattr(m, "snapshot_inputs", lambda *args: "snapshot")
    monkeypatch.setattr(m, "measure_year", year)
    monkeypatch.setattr(m, "weighted_total", total)
    monkeypatch.setattr(m, "baseline_records", lambda *args: {"stub": True})
    monkeypatch.setattr(m, "active_parameters", lambda *args: {})
    monkeypatch.setattr(m, "counted_once", counted)
    monkeypatch.setattr(m, "withheld_reasons", lambda *args, target=None: [])
    monkeypatch.setattr(m, "reform_parameters", lambda *args: {"rate": 2})
    monkeypatch.setattr(m, "stable_runtime", lambda *args: {"stub": True})
    monkeypatch.setattr(m, "tool_digest", lambda: "tool")
    monkeypatch.setattr(m, "definitions_digest", lambda *args: "definitions")
    return SimpleNamespace(
        sim=world("initial"),
        factory=factory,
        partition=partition,
        spec=spec,
        reforms=[reform],
        trace=trace,
    )


def _measure(tool, stub, **kwargs):
    return tool.measure.measure(
        stub.sim,
        stub.factory,
        stub.partition,
        stub.spec,
        label="head",
        reforms=stub.reforms,
        fingerprint_at_start="model",
        **kwargs,
    )


def _payload(result):
    return {key: value for key, value in result.items() if key != "timings"}


def _records(out):
    path = out / "timing.jsonl"
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.is_file()
        else []
    )


def _cli(tool, monkeypatch, tmp_path, *, fail_reform=False, interrupt_year=False):
    stub = _stub_world(
        tool, monkeypatch, fail_reform=fail_reform, interrupt_year=interrupt_year
    )
    source = tmp_path / "source.h5"
    source.write_bytes(b"public stub, never opened by a model")
    for name in ("spec.yaml", "reforms.yaml"):
        (tmp_path / name).write_text("stub: true\n")
    out = tmp_path / "out"
    stream = FlushedStream()
    seen = []
    writes = []

    def constructor(*, dataset, reform=None):
        seen.append((dataset, reform, _records(out), stream.flushes))
        return stub.sim if dataset == str(source) else stub.factory(reform=reform)

    monkeypatch.setattr(tool.model, "Microsimulation", constructor, raising=False)
    monkeypatch.setattr(tool.measure, "model_loaded", lambda: False)
    monkeypatch.setattr(tool.measure, "model_fingerprint", lambda: "model")
    monkeypatch.setattr(tool.measure, "write_result", lambda *args: writes.append(args))
    monkeypatch.setattr(tool.dataset, "sha256_file", lambda _: "dataset")
    monkeypatch.setattr(
        tool.specification, "load_spec", lambda *args, **kwargs: stub.spec
    )
    monkeypatch.setattr(tool.partition, "load_partition", lambda _: stub.partition)
    monkeypatch.setattr(tool.reforms, "load_reforms", lambda _: stub.reforms)
    monkeypatch.setattr(tool.cli.sys, "stderr", stream)
    args = SimpleNamespace(
        label="head",
        git_sha="stub-head",
        git_ref="stub-ref",
        spec=str(tmp_path / "spec.yaml"),
        years=None,
        pin=None,
        dataset_file=str(source),
        dataset_label="stub",
        partition="stub-partition",
        fallback_partition=None,
        no_reforms=False,
        reforms=str(tmp_path / "reforms.yaml"),
        no_guard=False,
        profile_first_year=False,
        out=str(out),
    )
    return SimpleNamespace(
        stub=stub, args=args, out=out, stream=stream, seen=seen, writes=writes
    )


def test_default_observer_preserves_the_stub_reference(tool, monkeypatch):
    stub = _stub_world(tool, monkeypatch)
    result, households = _measure(tool, stub)
    assert result["status"] == "ok"
    assert result["reforms"][0]["error"] is None
    assert result["metrics"][0]["values"] == {"2025": 1.0}
    assert households == {2025: {"stub": [1]}}
    assert [row[1] for row in stub.trace if row[0] == "factory"] == [None, {"rate": 2}]


def test_cli_flushes_phase_progress_before_initial_construction(
    tool, monkeypatch, tmp_path
):
    run = _cli(tool, monkeypatch, tmp_path)
    assert tool.cli.cmd_measure(run.args) == 0
    assert run.writes[0][1]["status"] == "ok"
    first = run.seen[0]
    assert any(
        r["phase"] == "initial_simulation" and r["event"] == "start" for r in first[2]
    )
    assert first[3] > 0
    records = _records(run.out)
    assert records and run.stream.flushes >= len(records)
    assert [
        json.loads(line[len(PREFIX) :])
        for line in run.stream.getvalue().splitlines()
        if line.startswith(PREFIX)
    ] == records
    allowed = {"event", "phase", "label", "utc", "elapsed_seconds", "year", "reform"}
    assert all(set(record) <= allowed for record in records)
    assert not (run.out / "result.json").exists()
    assert str(tmp_path) not in (run.out / "timing.jsonl").read_text()


def test_observation_preserves_calls_arguments_and_numeric_payload(tool, monkeypatch):
    original = _stub_world(tool, monkeypatch)
    expected, expected_households = _measure(tool, original)
    observed = _stub_world(tool, monkeypatch)
    events = []
    actual, actual_households = _measure(
        tool,
        observed,
        checkpoint=lambda event, phase, **scope: events.append((event, phase, scope)),
    )
    assert observed.trace == original.trace
    assert _payload(actual) == _payload(expected)
    assert actual_households == expected_households
    for phase in (
        "year",
        "counted_once",
        "rebuilt_factory",
        "rebuilt_year",
        "reform_parameters",
        "reform_factory",
        "reform_year",
    ):
        assert [event for event, name, _ in events if name == phase] == ["start", "end"]


def test_interruption_keeps_the_started_year_without_a_false_end(
    tool, monkeypatch, tmp_path
):
    run = _cli(tool, monkeypatch, tmp_path, interrupt_year=True)
    with pytest.raises(KeyboardInterrupt):
        tool.cli.cmd_measure(run.args)
    records = _records(run.out)
    assert [r["event"] for r in records if r["phase"] == "year"] == ["start"]
    assert not any(r["phase"] == "measure" and r["event"] == "end" for r in records)
    assert run.writes == []


def test_caught_reform_error_keeps_original_results_and_private_text_out_of_log(
    tool, monkeypatch, tmp_path
):
    run = _cli(tool, monkeypatch, tmp_path, fail_reform=True)
    assert tool.cli.cmd_measure(run.args) == 0
    result = run.writes[0][1]
    assert "SECRET_FINANCIAL_MARKER_123" in result["reforms"][0]["error"]
    records = _records(run.out)
    assert any(r["phase"] == "reform" and r["event"] == "error" for r in records)
    assert "SECRET_FINANCIAL_MARKER_123" not in (run.out / "timing.jsonl").read_text()


@pytest.mark.parametrize("sink", ["file", "stderr"])
def test_failed_diagnostic_sink_does_not_change_the_stub_measurement(
    tool, monkeypatch, tmp_path, sink
):
    run = _cli(tool, monkeypatch, tmp_path)
    if sink == "file":
        (run.out / "timing.jsonl").mkdir(parents=True)
    else:

        class BrokenStream:
            def write(self, text):
                raise OSError("closed diagnostic sink")

            def flush(self):
                raise OSError("closed diagnostic sink")

        monkeypatch.setattr(tool.cli.sys, "stderr", BrokenStream())
    assert tool.cli.cmd_measure(run.args) == 0
    assert run.writes[0][1]["status"] == "ok"
    assert run.writes[0][1]["reforms"][0]["error"] is None


def test_observer_exception_does_not_change_the_measurement(tool, monkeypatch):
    original = _stub_world(tool, monkeypatch)
    expected, expected_households = _measure(tool, original)
    observed = _stub_world(tool, monkeypatch)

    def broken(*args, **kwargs):
        raise OSError("diagnostics unavailable")

    actual, actual_households = _measure(tool, observed, checkpoint=broken)
    assert observed.trace == original.trace
    assert _payload(actual) == _payload(expected)
    assert actual_households == expected_households


def test_workflow_uploads_only_report_and_timing_sidecars():
    path = TOOL.parents[2] / ".github" / "workflows" / "aggregate-impact.yaml"
    workflow = yaml.safe_load(path.read_text())
    job = next(
        job
        for job in workflow["jobs"].values()
        if any(
            step.get("name") == "Measure base, then head"
            for step in job.get("steps", [])
        )
    )
    assert job["timeout-minutes"] == 120
    step = next(
        step
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert step["if"] == "always()"
    assert step["with"]["path"].splitlines() == [
        "report",
        "measured/*/timing.jsonl",
        "measured/*/infra-profile.json",
    ]
    measure = next(
        step for step in job["steps"] if step.get("name") == "Measure base, then head"
    )["run"]
    assert measure.index('measure base "$BASE_NAME"') < measure.index(
        'measure head "$HEAD_NAME"'
    )


def _infra(tool):
    return importlib.import_module(tool.measure.__package__ + ".infra_profile")


def _profile_code(filename, name="measure_year"):
    def observed():
        return None

    return observed.__code__.replace(co_filename=filename, co_qualname=name)


def _profile_entry(code, *, calls=4, recursive=1, own=0.25, total=0.5):
    return SimpleNamespace(
        code=code,
        callcount=calls,
        reccallcount=recursive,
        inlinetime=own,
        totaltime=total,
    )


def _fake_profiler(infra, monkeypatch, *, entries=(), fail=None):
    state = {"active": None, "created": 0, "enabled": 0, "disabled": 0}

    class Profile:
        def enable(self):
            state["enabled"] += 1
            state["active"] = self
            if fail == "enable":
                raise RuntimeError("PRIVATE_STARTUP_MESSAGE")

        def disable(self):
            state["disabled"] += 1
            if state["active"] is self:
                state["active"] = None

        def getstats(self):
            if fail == "statistics":
                raise RuntimeError("PRIVATE_STATISTICS_MESSAGE")
            return entries

    def factory():
        state["created"] += 1
        if fail == "construct":
            raise RuntimeError("PRIVATE_CONSTRUCTOR_MESSAGE")
        return Profile()

    monkeypatch.setattr(
        infra.FirstYearProfiler, "_monitoring_backend", staticmethod(lambda: None)
    )
    monkeypatch.setattr(infra.sys, "getprofile", lambda: state["active"])
    monkeypatch.setattr(infra.cProfile, "Profile", factory)
    return state


def test_year_profile_observes_only_the_first_year_through_reset_and_gc(
    tool, monkeypatch
):
    original = _stub_world(tool, monkeypatch)
    original.spec.years = [2025, 2026]
    monkeypatch.setattr(
        tool.measure.gc, "collect", lambda: original.trace.append(("gc",))
    )
    expected, expected_households = _measure(tool, original)
    observed = _stub_world(tool, monkeypatch)
    observed.spec.years = [2025, 2026]
    monkeypatch.setattr(
        tool.measure.gc, "collect", lambda: observed.trace.append(("gc",))
    )

    def profile(event, phase, **scope):
        observed.trace.append(("profile", event, phase, scope))

    actual, actual_households = _measure(tool, observed, year_profile=profile)
    assert [row for row in observed.trace if row[0] != "profile"] == original.trace
    assert _payload(actual) == _payload(expected)
    assert actual_households == expected_households
    assert [row for row in observed.trace if row[0] == "profile"] == [
        ("profile", "start", "first_ordinary_year", {"year": 2025}),
        ("profile", "stop", "first_ordinary_year", {"year": 2025, "completed": True}),
    ]
    start = next(
        i for i, row in enumerate(observed.trace) if row[:2] == ("profile", "start")
    )
    stop = next(
        i for i, row in enumerate(observed.trace) if row[:2] == ("profile", "stop")
    )
    assert observed.trace[start + 1] == ("measure_year", "initial", 2025)
    assert observed.trace[stop - 2 : stop] == [("reset", "initial"), ("gc",)]
    assert stop < observed.trace.index(("measure_year", "initial", 2026))


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_financial_exceptions_propagate_after_first_year_profile_stop(
    tool, monkeypatch, tmp_path, error_type
):
    infra = _infra(tool)
    state = _fake_profiler(infra, monkeypatch)
    records = []
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))
    stub = _stub_world(tool, monkeypatch)
    original_error = error_type("PRIVATE_FINANCIAL_MESSAGE")

    def failed_year(*args):
        raise original_error

    monkeypatch.setattr(tool.measure, "measure_year", failed_year)
    with pytest.raises(error_type) as caught:
        _measure(tool, stub, year_profile=infra.FirstYearProfiler(tmp_path, "head"))
    assert caught.value is original_error
    assert state["enabled"] == state["disabled"] == 1
    assert state["active"] is None
    assert len(records) == 1
    assert records[0]["status"] == "interrupted"
    assert records[0]["completed"] is False
    assert "PRIVATE_FINANCIAL_MESSAGE" not in json.dumps(records)


@pytest.mark.parametrize("enabled", [False, True])
def test_cli_first_year_profile_is_explicitly_opt_in(
    tool, monkeypatch, tmp_path, enabled
):
    infra = _infra(tool)
    run = _cli(tool, monkeypatch, tmp_path)
    run.args.profile_first_year = enabled
    created, events = [], []

    def factory(out, label):
        created.append((out, label))
        return lambda event, phase, **scope: events.append((event, phase, scope))

    monkeypatch.setattr(infra, "FirstYearProfiler", factory)
    assert tool.cli.cmd_measure(run.args) == 0
    assert run.writes[0][1]["status"] == "ok"
    assert run.writes[0][1]["metrics"][0]["values"] == {"2025": 1.0}
    assert created == ([(run.args.out, "head")] if enabled else [])
    assert events == (
        [
            ("start", "first_ordinary_year", {"year": 2025}),
            ("stop", "first_ordinary_year", {"year": 2025, "completed": True}),
        ]
        if enabled
        else []
    )


def test_year_profile_callback_error_preserves_the_reference(tool, monkeypatch):
    original = _stub_world(tool, monkeypatch)
    expected, expected_households = _measure(tool, original)
    observed = _stub_world(tool, monkeypatch)

    def unavailable(*args, **kwargs):
        raise OSError("PRIVATE_OBSERVER_MESSAGE")

    actual, actual_households = _measure(tool, observed, year_profile=unavailable)
    assert observed.trace == original.trace
    assert _payload(actual) == _payload(expected)
    assert actual_households == expected_households


@pytest.mark.parametrize("failure", ["construct", "enable", "statistics"])
def test_profiler_failure_preserves_financial_payload_and_uses_fixed_reason(
    tool, monkeypatch, tmp_path, failure
):
    infra = _infra(tool)
    original = _stub_world(tool, monkeypatch)
    expected, expected_households = _measure(tool, original)
    state = _fake_profiler(infra, monkeypatch, fail=failure)
    records = []
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))
    observed = _stub_world(tool, monkeypatch)
    actual, actual_households = _measure(
        tool, observed, year_profile=infra.FirstYearProfiler(tmp_path, "head")
    )
    assert observed.trace == original.trace
    assert _payload(actual) == _payload(expected)
    assert actual_households == expected_households
    assert state["active"] is None
    assert len(records) == 1
    assert records[0]["status"] == "unavailable"
    assert records[0]["reason"] == "observer_unavailable"
    assert records[0]["completed"] is True
    assert records[0]["functions"] == []
    assert "PRIVATE_" not in json.dumps(records)


def test_preexisting_profiler_is_never_replaced_or_disabled(
    tool, monkeypatch, tmp_path
):
    infra = _infra(tool)
    records = []
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))

    def forbidden_factory():
        raise AssertionError("the existing profiler owns this window")

    monkeypatch.setattr(infra.cProfile, "Profile", forbidden_factory)
    previous = sys.getprofile()

    def existing(frame, event, arg):
        return None

    try:
        sys.setprofile(existing)
        observer = infra.FirstYearProfiler(tmp_path, "base")
        observer("start", "first_ordinary_year", year=2026)
        assert sys.getprofile() is existing
        observer("stop", "first_ordinary_year", year=2026, completed=True)
        assert sys.getprofile() is existing
    finally:
        sys.setprofile(previous)
    assert len(records) == 1
    assert records[0]["status"] == "skipped"
    assert records[0]["reason"] == "preexisting_profiler"
    assert records[0]["functions"] == []


def _finish_real_profile(infra, observer, owned, previous):
    # Failed assertions must not leave the native cProfile slot occupied.
    try:
        sys.setprofile(None)
        if owned is not None:
            owned.disable()
        if getattr(infra, "_ORPHANED_PROFILE", None) is owned:
            infra._ORPHANED_PROFILE = None
        if observer is not None:
            observer._profile = None
    finally:
        sys.setprofile(previous)


def test_real_profiler_does_not_clear_a_midwindow_replacement(
    tool, monkeypatch, tmp_path
):
    import cProfile
    import weakref

    infra = _infra(tool)
    records = []
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))
    previous = sys.getprofile()
    observer = owned = owned_reference = None
    backend = infra.FirstYearProfiler._monitoring_backend()

    def replacement(frame, event, arg):
        return None

    try:
        sys.setprofile(None)
        observer = infra.FirstYearProfiler(tmp_path, "head")
        observer("start", "first_ordinary_year", year=2026)
        owned = observer._profile
        assert isinstance(owned, cProfile.Profile)
        owned_reference = weakref.ref(owned)
        if backend is None:
            assert sys.getprofile() is owned
        else:
            assert backend.get_tool(backend.PROFILER_ID) == "cProfile"
        sys.setprofile(replacement)
        observer("stop", "first_ordinary_year", year=2026, completed=True)
        assert observer._profile is None
        if backend is not None:
            assert backend.get_tool(backend.PROFILER_ID) is None
            # Observe cleanup too; a saved reference must not hide deallocation.
            owned = None
        assert sys.getprofile() is replacement
    finally:
        cleanup_owned = (
            owned
            if owned is not None
            else (owned_reference() if owned_reference else None)
        )
        _finish_real_profile(infra, observer, cleanup_owned, previous)
    assert len(records) == 1
    if backend is None:
        assert records[0]["reason"] == "observer_unavailable"
    else:
        assert records[0]["status"] == "ok"
        assert "reason" not in records[0]
    assert records[0]["functions"] == []


@pytest.mark.parametrize("sink", ["file", "stderr"])
def test_infra_profile_sinks_fail_independently_and_flush(
    tool, monkeypatch, tmp_path, sink
):
    infra = _infra(tool)
    _fake_profiler(infra, monkeypatch)
    stream = FlushedStream()
    monkeypatch.setattr(infra.sys, "stderr", stream)
    if sink == "file":
        (tmp_path / "infra-profile.json").mkdir()
    else:

        class BrokenStream:
            def write(self, text):
                raise OSError("PRIVATE_SINK_MESSAGE")

            def flush(self):
                raise OSError("PRIVATE_SINK_MESSAGE")

        monkeypatch.setattr(infra.sys, "stderr", BrokenStream())
    observer = infra.FirstYearProfiler(tmp_path, "PRIVATE_LABEL")
    observer("start", "first_ordinary_year", year=2026)
    observer("stop", "first_ordinary_year", year=2026, completed=True)
    if sink == "file":
        text = stream.getvalue()
        assert stream.flushes > 0
        assert text.startswith(infra.PREFIX)
        record = json.loads(text[len(infra.PREFIX) :])
    else:
        record = json.loads((tmp_path / "infra-profile.json").read_text())
    assert set(record) == {
        "schema",
        "status",
        "label",
        "year",
        "completed",
        "window_seconds",
        "functions",
    }
    assert record["schema"] == infra.SCHEMA
    assert record["status"] == "ok"
    assert record["label"] == "other"
    assert record["year"] == 2026
    assert record["completed"] is True
    assert record["functions"] == []
    assert "PRIVATE_" not in json.dumps(record)
    assert list(tmp_path.glob("*.pstats")) == []


@pytest.mark.parametrize(
    "filename",
    [
        "/private/SECRET/policyengine_uk/utils/aggregate_impact/measure.py",
        "/private/SECRET/pe_uk_aggregate_impact/measure.py",
    ],
)
def test_profile_maps_normal_and_copied_layout_to_the_same_literal_id(tool, filename):
    infra = _infra(tool)
    code = _profile_code(filename)
    expected_id = "aggregate_impact.measure.py:measure_year"
    assert infra._literal_id(code) == expected_id
    assert infra._safe_rows([_profile_entry(code)]) == [
        {
            "id": expected_id,
            "calls": 4,
            "primitive_calls": 3,
            "self_seconds": 0.25,
            "cumulative_seconds": 0.5,
        }
    ]


def test_profile_rejects_unknown_symbols_and_component_boundary_collisions(tool):
    infra = _infra(tool)
    invalid = [
        _profile_code("/SECRET/other/measure.py"),
        _profile_code("/SECRET/notpolicyengine_uk/utils/aggregate_impact/measure.py"),
        _profile_code("/SECRET/notpe_uk_aggregate_impact/measure.py"),
        _profile_code("/SECRET/policyengine_uk/utils/geography.py", "PRIVATE_FUNCTION"),
        "<PRIVATE_BUILTIN>",
    ]
    assert all(infra._literal_id(code) is None for code in invalid)
    assert infra._safe_rows([_profile_entry(code) for code in invalid]) == []
    valid = _profile_code("/SECRET/policyengine_uk/utils/geography.py", "input_facts")
    rows = infra._safe_rows(
        [_profile_entry(valid), *[_profile_entry(code) for code in invalid]]
    )
    assert len(rows) == 1
    assert rows[0]["id"] == "policyengine_uk.utils.geography.py:input_facts"
    assert len(rows) <= infra.MAX_ROWS == 50
    assert "SECRET" not in json.dumps(rows) and "PRIVATE" not in json.dumps(rows)


@pytest.mark.parametrize(
    "bad_stats",
    [
        {"calls": True},
        {"calls": -1},
        {"recursive": 5},
        {"recursive": -1},
        {"own": float("nan")},
        {"own": float("inf")},
        {"own": -0.1},
        {"total": float("-inf")},
        {"total": -0.1},
    ],
)
def test_profile_omits_nonfinite_negative_or_invalid_statistics(tool, bad_stats):
    infra = _infra(tool)
    code = _profile_code("/SECRET/pe_uk_aggregate_impact/measure.py")
    assert infra._safe_rows([_profile_entry(code, **bad_stats)]) == []


def test_profile_window_excludes_statistics_filtering_and_is_one_shot(
    tool, monkeypatch, tmp_path
):
    infra = _infra(tool)
    state = _fake_profiler(infra, monkeypatch)
    clock = [10.0]
    records = []
    monkeypatch.setattr(infra.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))
    observer = infra.FirstYearProfiler(tmp_path, "head")
    observer("start", "first_ordinary_year", year=2026)

    def expensive_filter(entries):
        clock[0] = 99.0
        return []

    monkeypatch.setattr(infra, "_safe_rows", expensive_filter)
    clock[0] = 11.0
    observer("stop", "first_ordinary_year", year=2026, completed=True)
    observer("start", "first_ordinary_year", year=2027)
    observer("stop", "first_ordinary_year", year=2027, completed=True)
    assert state["created"] == state["enabled"] == state["disabled"] == 1
    assert len(records) == 1 and records[0]["window_seconds"] == 1.0
    assert records[0]["year"] == 2026


def test_profile_transport_accepts_exact_prefixed_byte_limit_and_rejects_one_more(
    tool, monkeypatch, tmp_path
):
    infra = _infra(tool)
    stream = FlushedStream()
    monkeypatch.setattr(infra.sys, "stderr", stream)
    # Exercise the transport-size seam directly; real records use the fixed schema above.
    record = {"schema": infra.SCHEMA, "padding": ""}

    def encode(value):
        return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))

    overhead = len((infra.PREFIX + encode(record) + "\n").encode("utf-8"))
    record["padding"] = "x" * (infra.MAX_BYTES - overhead)
    infra._publish(tmp_path / "exact", record)
    assert len(stream.getvalue().encode("utf-8")) == infra.MAX_BYTES == 65_536
    assert json.loads((tmp_path / "exact" / "infra-profile.json").read_text()) == record
    assert stream.flushes == 1
    record["padding"] += "x"
    infra._publish(tmp_path / "too-large", record)
    assert not (tmp_path / "too-large" / "infra-profile.json").exists()
    assert len(stream.getvalue().encode("utf-8")) == infra.MAX_BYTES
    assert stream.flushes == 1


def test_real_profiler_exports_observed_allowlisted_calls_and_restores_hook(
    tool, monkeypatch, tmp_path
):
    from types import FunctionType

    infra = _infra(tool)
    stream = FlushedStream()
    monkeypatch.setattr(infra.sys, "stderr", stream)
    code = _profile_code("/PRIVATE/pe_uk_aggregate_impact/measure.py")
    observed = FunctionType(code, {})
    previous = sys.getprofile()
    observer = owned = None
    backend = infra.FirstYearProfiler._monitoring_backend()
    try:
        sys.setprofile(None)
        observer = infra.FirstYearProfiler(tmp_path, "base")
        observer("start", "first_ordinary_year", year=2026)
        owned = observer._profile
        assert owned is not None
        if backend is None:
            assert sys.getprofile() is owned
        else:
            assert backend.get_tool(backend.PROFILER_ID) == "cProfile"
        for _ in range(3):
            observed()
        observer("stop", "first_ordinary_year", year=2026, completed=True)
        assert sys.getprofile() is None
        assert observer._profile is None
        if backend is not None:
            assert backend.get_tool(backend.PROFILER_ID) is None
    finally:
        _finish_real_profile(infra, observer, owned, previous)
    record = json.loads((tmp_path / "infra-profile.json").read_text())
    assert record["status"] == "ok" and record["completed"] is True
    assert record["label"] == "base"
    assert record["functions"] == [
        {
            "id": "aggregate_impact.measure.py:measure_year",
            "calls": 3,
            "primitive_calls": 3,
            "self_seconds": record["functions"][0]["self_seconds"],
            "cumulative_seconds": record["functions"][0]["cumulative_seconds"],
        }
    ]
    assert record["functions"][0]["self_seconds"] >= 0
    assert record["functions"][0]["cumulative_seconds"] >= 0
    assert json.loads(stream.getvalue()[len(infra.PREFIX) :]) == record
    assert stream.flushes == 1
    assert "PRIVATE" not in json.dumps(record)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["infra-profile.json"]


def _backend_profile_spy(infra, monkeypatch, backend):
    import weakref

    state = {"hook": None, "native": None, "created": 0, "disabled": 0, "destroyed": 0}

    class Profile:
        def __init__(self):
            self.enabled = False

        def enable(self):
            self.enabled = True
            if backend == "legacy":
                state["hook"] = self
            else:
                state["native"] = "cProfile"

        def disable(self):
            self.enabled = False
            state["disabled"] += 1
            if backend == "legacy":
                state["hook"] = None
            else:
                state["native"] = None

        def getstats(self):
            return []

        def __del__(self):
            state["destroyed"] += 1
            # Model the documented danger of destroying an enabled lost owner.
            if self.enabled:
                state["hook" if backend == "legacy" else "native"] = None

    def factory():
        state["created"] += 1
        profile = Profile()
        state["weak_profile"] = weakref.ref(profile)
        return profile

    def get_tool(tool_id):
        assert tool_id == 2
        return state["native"]

    native = SimpleNamespace(PROFILER_ID=2, get_tool=get_tool)
    monkeypatch.setattr(
        infra.FirstYearProfiler,
        "_monitoring_backend",
        staticmethod(lambda: native if backend == "native" else None),
    )
    monkeypatch.setattr(infra.sys, "getprofile", lambda: state["hook"])
    monkeypatch.setattr(infra.cProfile, "Profile", factory)
    records = []
    monkeypatch.setattr(infra, "_publish", lambda out, record: records.append(record))
    return state, records


@pytest.mark.parametrize("backend", ["legacy", "native"])
def test_busy_profile_backend_is_skipped_without_allocation(
    tool, monkeypatch, tmp_path, backend
):
    infra = _infra(tool)
    state, records = _backend_profile_spy(infra, monkeypatch, backend)
    foreign_hook = object()
    if backend == "legacy":
        state["hook"] = foreign_hook
    else:
        state["native"] = "PRIVATE_FOREIGN_PROFILER"
    observer = infra.FirstYearProfiler(tmp_path, "head")
    observer("start", "first_ordinary_year", year=2026)
    observer("stop", "first_ordinary_year", year=2026, completed=True)
    assert state["created"] == state["disabled"] == state["destroyed"] == 0
    assert state["hook"] is (foreign_hook if backend == "legacy" else None)
    assert state["native"] == (
        "PRIVATE_FOREIGN_PROFILER" if backend == "native" else None
    )
    assert len(records) == 1
    assert records[0]["status"] == "skipped"
    assert records[0]["reason"] == "preexisting_profiler"
    assert records[0]["functions"] == []
    assert "PRIVATE" not in json.dumps(records)


@pytest.mark.parametrize("backend", ["legacy", "native"])
def test_owned_profile_backend_retires_without_touching_an_independent_hook(
    tool, monkeypatch, tmp_path, backend
):
    infra = _infra(tool)
    state, records = _backend_profile_spy(infra, monkeypatch, backend)
    observer = infra.FirstYearProfiler(tmp_path, "head")
    observer("start", "first_ordinary_year", year=2026)
    assert observer._profile is state["weak_profile"]()
    independent_hook = object()
    if backend == "native":
        state["hook"] = independent_hook
    observer("stop", "first_ordinary_year", year=2026, completed=True)
    assert state["created"] == state["disabled"] == 1
    assert state["destroyed"] == 1
    assert observer._profile is None
    assert infra._ORPHANED_PROFILE is None
    assert state["native"] is None
    assert state["hook"] is (independent_hook if backend == "native" else None)
    assert len(records) == 1 and records[0]["status"] == "ok"
    assert records[0]["completed"] is True and records[0]["functions"] == []


@pytest.mark.parametrize("backend", ["legacy", "native"])
def test_lost_profile_owner_is_quarantined_once_and_blocks_later_activation(
    tool, monkeypatch, tmp_path, backend
):
    infra = _infra(tool)
    state, records = _backend_profile_spy(infra, monkeypatch, backend)
    observer = infra.FirstYearProfiler(tmp_path, "head")
    foreign_hook = object()
    try:
        observer("start", "first_ordinary_year", year=2026)
        weak_profile = state["weak_profile"]
        if backend == "legacy":
            state["hook"] = foreign_hook
        else:
            state["native"] = "PRIVATE_FOREIGN_PROFILER"
        observer("stop", "first_ordinary_year", year=2026, completed=True)
        assert observer._profile is None
        assert infra._ORPHANED_PROFILE is weak_profile() is not None
        del observer
        assert weak_profile() is not None
        later = infra.FirstYearProfiler(tmp_path, "base")
        later("start", "first_ordinary_year", year=2027)
        later("stop", "first_ordinary_year", year=2027, completed=True)
        assert state["created"] == 1
        assert state["disabled"] == state["destroyed"] == 0
        assert infra._ORPHANED_PROFILE is weak_profile()
        assert state["hook"] is (foreign_hook if backend == "legacy" else None)
        assert state["native"] == (
            "PRIVATE_FOREIGN_PROFILER" if backend == "native" else None
        )
        assert len(records) == 2
        assert all(record["status"] == "unavailable" for record in records)
        assert all(record["reason"] == "observer_unavailable" for record in records)
        assert all(record["functions"] == [] for record in records)
        assert "PRIVATE" not in json.dumps(records)
    finally:
        # Teardown takes back only this fake owner's state before releasing it.
        orphan = infra._ORPHANED_PROFILE
        if orphan is not None:
            if backend == "legacy":
                state["hook"] = orphan
            else:
                state["native"] = "cProfile"
            orphan.disable()
            infra._ORPHANED_PROFILE = None


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_disable_interrupt_keeps_one_owned_profile_and_reraises_the_original(
    tool, monkeypatch, tmp_path, error_type
):
    infra = _infra(tool)
    state, records = _backend_profile_spy(infra, monkeypatch, "native")
    observer = infra.FirstYearProfiler(tmp_path, "head")
    observer("start", "first_ordinary_year", year=2026)
    weak_profile = state["weak_profile"]
    profile_type = type(observer._profile)
    normal_disable = profile_type.disable
    original_interrupt = error_type("PRIVATE_INTERRUPT_MESSAGE")
    state["disable_attempts"] = 0

    def interrupted_disable(self):
        state["disable_attempts"] += 1
        raise original_interrupt

    monkeypatch.setattr(profile_type, "disable", interrupted_disable)
    independent_hook = object()
    state["hook"] = independent_hook
    try:
        with pytest.raises(error_type) as caught:
            observer("stop", "first_ordinary_year", year=2026, completed=True)
        assert caught.value is original_interrupt
        assert observer._profile is None
        assert infra._ORPHANED_PROFILE is weak_profile() is not None
        del observer
        assert state["created"] == state["disable_attempts"] == 1
        assert state["disabled"] == state["destroyed"] == 0
        assert state["hook"] is independent_hook
        assert state["native"] == "cProfile"
        assert records == []
    finally:
        orphan = infra._ORPHANED_PROFILE
        if orphan is not None:
            normal_disable(orphan)
            infra._ORPHANED_PROFILE = None


@pytest.mark.parametrize("enabled", [False, True])
def test_cli_guard_profile_is_explicitly_opt_in(tool, monkeypatch, tmp_path, enabled):
    infra = _infra(tool)
    run = _cli(tool, monkeypatch, tmp_path)
    run.args.profile_first_guard_probe = enabled
    created, events = [], []
    original = tool.measure.counted_once

    def factory(out, label, *, window):
        created.append((out, label, window))
        return lambda event, phase, **scope: events.append((event, phase, scope))

    def counted(*args, **kwargs):
        observer = kwargs.pop("probe_profile", None)
        if observer is not None:
            observer("start", "first_counted_once_probe", year=args[2])
            observer("stop", "first_counted_once_probe", year=args[2], completed=True)
        return original(*args, **kwargs)

    monkeypatch.setattr(infra, "FirstYearProfiler", factory)
    monkeypatch.setattr(tool.measure, "counted_once", counted)
    assert tool.cli.cmd_measure(run.args) == 0
    assert created == (
        [(run.out / "first-guard-probe", "head", "first_counted_once_probe")]
        if enabled
        else []
    )
    assert events == (
        [
            ("start", "first_counted_once_probe", {"year": 2025}),
            ("stop", "first_counted_once_probe", {"year": 2025, "completed": True}),
        ]
        if enabled
        else []
    )
    assert run.writes[0][1]["metrics"][0]["values"] == {"2025": 1.0}


def test_guard_profile_uses_its_own_window_once_and_preserves_default_payload(
    tool, monkeypatch, tmp_path
):
    infra = _infra(tool)
    state = _fake_profiler(infra, monkeypatch)
    records = []
    monkeypatch.setattr(
        infra, "_publish", lambda out, record: records.append((out, record))
    )
    first = infra.FirstYearProfiler(tmp_path, "base")
    guarded = infra.FirstYearProfiler(
        tmp_path / "first-guard-probe", "base", window="first_counted_once_probe"
    )
    guarded("start", "first_ordinary_year", year=2026)
    assert state["created"] == 0
    first("start", "first_ordinary_year", year=2026)
    first("stop", "first_ordinary_year", year=2026, completed=True)
    for _ in range(2):
        guarded("start", "first_counted_once_probe", year=2026)
        guarded("stop", "first_counted_once_probe", year=2026, completed=True)
    assert state["created"] == state["enabled"] == state["disabled"] == 2
    assert state["active"] is None
    assert len(records) == 2
    assert "window" not in records[0][1]
    assert records[1][0] == tmp_path / "first-guard-probe"
    assert records[1][1]["window"] == "first_counted_once_probe"
    assert records[1][1]["completed"] is True


@pytest.mark.parametrize(
    "filename",
    [
        "/PRIVATE/policyengine_uk/utils/aggregate_impact/guard.py",
        "/PRIVATE/pe_uk_aggregate_impact/guard.py",
    ],
)
def test_guard_profile_allows_only_literal_infrastructure_ids(tool, filename):
    infra = _infra(tool)
    names = (
        "_perturb",
        "discard_formula_results",
        "_set_guard_value",
        "_head_arrays",
        "_raw",
        "_household",
    )
    entries = [_profile_entry(_profile_code(filename, name)) for name in names]
    entries.append(_profile_entry(_profile_code(filename, "counted_once")))
    entries.append(
        _profile_entry(_profile_code("/PRIVATE/household_secret.py", "_raw"))
    )
    assert infra._safe_rows(entries) == []
    rows = infra._safe_rows(entries, window="first_counted_once_probe")
    assert {row["id"] for row in rows} == {
        f"aggregate_impact.guard.py:{name}" for name in names
    }
    assert "PRIVATE" not in json.dumps(rows)
    assert len(rows) <= infra.MAX_ROWS


def test_guard_profile_native_backend_exports_calls_and_releases_ownership(
    tool, monkeypatch, tmp_path
):
    from types import FunctionType

    infra = _infra(tool)
    stream = FlushedStream()
    monkeypatch.setattr(infra.sys, "stderr", stream)
    observed = FunctionType(
        _profile_code("/PRIVATE/pe_uk_aggregate_impact/guard.py", "_head_arrays"), {}
    )
    previous = sys.getprofile()
    observer = owned = None
    backend = infra.FirstYearProfiler._monitoring_backend()
    try:
        sys.setprofile(None)
        observer = infra.FirstYearProfiler(
            tmp_path, "head", window="first_counted_once_probe"
        )
        observer("start", "first_counted_once_probe", year=2026)
        owned = observer._profile
        assert owned is not None
        for _ in range(3):
            observed()
        observer("stop", "first_counted_once_probe", year=2026, completed=True)
        assert sys.getprofile() is None
        assert observer._profile is None
        if backend is not None:
            assert backend.get_tool(backend.PROFILER_ID) is None
    finally:
        _finish_real_profile(infra, observer, owned, previous)
    record = json.loads((tmp_path / "infra-profile.json").read_text())
    assert record["window"] == "first_counted_once_probe"
    assert record["status"] == "ok" and record["completed"] is True
    assert [row["id"] for row in record["functions"]] == [
        "aggregate_impact.guard.py:_head_arrays"
    ]
    assert (
        record["functions"][0]["calls"]
        == record["functions"][0]["primitive_calls"]
        == 3
    )
    assert "PRIVATE" not in stream.getvalue()
    assert stream.flushes > 0
