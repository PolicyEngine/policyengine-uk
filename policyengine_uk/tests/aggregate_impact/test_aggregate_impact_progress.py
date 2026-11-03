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
    monkeypatch.setattr(m, "withheld_reasons", lambda *args: [])
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
    assert step["with"]["path"].splitlines() == ["report", "measured/*/timing.jsonl"]
    measure = next(
        step for step in job["steps"] if step.get("name") == "Measure base, then head"
    )["run"]
    assert measure.index('measure base "$BASE_NAME"') < measure.index(
        'measure head "$HEAD_NAME"'
    )
