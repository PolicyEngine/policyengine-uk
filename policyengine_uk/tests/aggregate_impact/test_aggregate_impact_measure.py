"""Measurement bookkeeping: check scopes, reform costing checks, digests."""

import dataclasses
from types import SimpleNamespace

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.api import to_report
from policyengine_uk.utils.aggregate_impact.compare import classify_check
from policyengine_uk.utils.aggregate_impact.measure import (
    MIN_CELL,
    cell_detail,
    Recorder,
    _finite_metrics_check,
    _digest_tool_files,
    definitions_digest,
    measure_reforms,
    tool_digest,
)
from policyengine_uk.utils.aggregate_impact.reforms import load_reforms, parse_reforms
from policyengine_uk.utils.aggregate_impact.spec import load_spec

SPEC = load_spec()
YEARS = [2025, 2026]


class YearSim:
    """A simulation whose gov_balance per household depends on the year."""

    def __init__(self, balance_by_year):
        self.balance = balance_by_year
        entity = SimpleNamespace(key="household")
        self.tax_benefit_system = SimpleNamespace(
            variables={
                "gov_balance": SimpleNamespace(entity=entity),
                "household_weight": SimpleNamespace(entity=entity),
            }
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable == "household_weight":
            return np.ones(2)
        return np.full(2, self.balance[int(period)] / 2)


def test_checks_remember_which_years_failed():
    rec = Recorder()
    rec.scope = "2025"
    rec.check("identity:x", "x", True)
    rec.scope = "2026"
    rec.check("identity:x", "x", False, "broken")
    record = rec.checks["identity:x"]
    assert record["status"] == "fail" and record["failing"] == {"2026": "broken"}


def test_a_check_that_did_not_apply_is_skipped_not_passed():
    rec = Recorder()
    rec.check("counted_once:x", "x", None, "zero for every unit")
    assert rec.checks["counted_once:x"]["status"] == "skipped"
    rec.check("counted_once:x", "x", False, "broken")
    assert rec.checks["counted_once:x"]["status"] == "fail"


def test_a_rebuilt_baseline_must_match_in_every_year():
    rec = Recorder()
    baseline = {2025: 10.0, 2026: 20.0}
    drifting = YearSim({2025: 10.0, 2026: 20.5})
    measure_reforms(lambda reform=None: drifting, None, baseline, {}, [], YEARS, rec)
    record = rec.checks["determinism:rebuilt_baseline"]
    assert record["status"] == "fail" and list(record["failing"]) == ["2026"]

    rec = Recorder()
    measure_reforms(
        lambda reform=None: YearSim(baseline), None, baseline, {}, [], YEARS, rec
    )
    assert rec.checks["determinism:rebuilt_baseline"]["status"] == "pass"


def test_a_non_finite_reform_costing_fails_the_finiteness_check():
    rec = Recorder()
    baseline = {2025: 10.0, 2026: 20.0}
    reform = parse_reforms({"reforms": [{"name": "Break it", "parameters": {"a": 1}}]})

    def factory(reform=None):
        return YearSim({2025: 11.0, 2026: float("nan")} if reform else baseline)

    measure_reforms(factory, None, baseline, {}, reform, YEARS, rec)
    assert rec.checks.get("reform_runs:break_it") is None  # recorded by measure()
    _finite_metrics_check(rec)
    record = rec.checks["finite:metrics"]
    assert record["status"] == "fail" and "reforms.break_it" in record["details"][0]


def test_the_definitions_digest_follows_what_is_measured():
    reforms = load_reforms()
    digest = definitions_digest(SPEC, reforms)
    assert digest == definitions_digest(load_spec(), load_reforms())
    shorter = dataclasses.replace(SPEC, last_year=SPEC.last_year - 1)
    assert definitions_digest(shorter, reforms) != digest
    assert definitions_digest(SPEC, reforms[:-1]) != digest
    other_measures = dataclasses.replace(SPEC, raw={**SPEC.raw, "poverty": {}})
    assert definitions_digest(other_measures, reforms) != digest


@settings(max_examples=50, deadline=None)
@given(first=st.integers(2020, 2030), length=st.integers(1, 8), drop=st.integers(0, 9))
def test_the_digest_separates_different_horizons_and_reform_sets(first, length, drop):
    reforms = load_reforms()
    a = dataclasses.replace(SPEC, first_year=first, last_year=first + length - 1)
    b = dataclasses.replace(SPEC, first_year=first, last_year=first + length)
    assert definitions_digest(a, reforms) != definitions_digest(b, reforms)
    fewer = reforms[:drop] + reforms[drop + 1 :]
    assert definitions_digest(a, fewer) != definitions_digest(a, reforms)


def test_the_long_format_report_carries_each_checks_failing_years():
    rec = Recorder()
    rec.scope = "2025"
    rec.check("identity:x", "x", False, "broken in 2025")
    rec.scope = "2026"
    rec.check("identity:x", "x", False, "broken in 2026")
    rec.scope = ""
    rec.check("closure", "closure", True)
    rec.check("counted_once:y", "y", None, "zero for every unit")
    rec.metric("receipts.income_tax", "Income tax", "receipts", "gbp", 2025, 1.0)
    report = to_report(
        {
            "status": "ok",
            "years": [2025, 2026],
            "provenance": {"metrics_version": "v"},
            "partition": {"sha256": "p"},
            "metrics": list(rec.metrics.values()),
            "checks": list(rec.checks.values()),
        }
    )
    rows = {row["identity_id"]: row for row in report["identities"]}
    assert rows["identity:x"]["failing_scopes"] == ["2025", "2026"]
    assert rows["identity:x"]["status"] == "fail"
    assert rows["closure"]["failing_scopes"] == []
    assert rows["counted_once:y"]["status"] == "skipped"
    assert rows["counted_once:y"]["failing_scopes"] == []
    metric = report["metrics"][0]
    assert (
        metric["metric_id"] == "receipts.income_tax"
        and metric["partition"] == "income_tax"
    )
    assert metric["kind"] == "receipt" and metric["year"] == 2025


def test_the_tool_digest_is_taken_at_load_and_matches_the_files():
    assert tool_digest() == _digest_tool_files()
    assert len(tool_digest()) == 64


class TargetSim(YearSim):
    """gov_balance by year, plus a target variable whose change a reform sets."""

    def __init__(self, balance_by_year, target_by_year):
        super().__init__(balance_by_year)
        self.target = target_by_year
        self.tax_benefit_system.variables["universal_credit"] = SimpleNamespace(
            entity=SimpleNamespace(key="household")
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable == "universal_credit":
            return np.full(2, self.target[int(period)] / 2)
        return super().calculate(variable, period, map_to, unweighted)


def test_responsiveness_is_recorded_per_year():
    """A reform that goes inert in a second year is a regression, not old news."""
    reform = parse_reforms(
        {
            "reforms": [
                {
                    "name": "Raise UC",
                    "parameters": {"a": 1},
                    "responds": {
                        "variable": "universal_credit",
                        "direction": "up",
                        "minimum": 5.0,
                    },
                }
            ]
        }
    )
    baseline = {2025: 0.0, 2026: 0.0}
    targets = {2025: {"universal_credit": 100.0}, 2026: {"universal_credit": 100.0}}

    def run(reformed_uc):
        rec = Recorder()

        def factory(reform=None):
            uc = reformed_uc if reform else {2025: 100.0, 2026: 100.0}
            return TargetSim(baseline, uc)

        measure_reforms(factory, None, baseline, targets, reform, YEARS, rec)
        return rec.checks["responsive:raise_uc"]

    one_year = run({2025: 110.0, 2026: 100.0})
    both_years = run({2025: 100.0, 2026: 100.0})
    assert one_year["status"] == "fail" and set(one_year["failing"]) == {"2026"}
    assert set(both_years["failing"]) == {"2025", "2026"}
    verdict = classify_check(
        "fail", "fail", False, one_year["failing"], both_years["failing"]
    )
    assert verdict == "regression"


@settings(max_examples=100, deadline=None)
@given(count=st.integers(0, 10_000), amount=st.floats(-1e9, 1e9, allow_nan=False))
def test_a_small_cell_never_reveals_an_amount(count, amount):
    text = cell_detail(count, "households differ", f"by a weighted £{amount:,.0f}")
    if count < MIN_CELL:
        assert "£" not in text and str(count) not in text.replace(str(MIN_CELL), "")
    else:
        assert f"{count:,}" in text and "£" in text


def _protection_partition():
    from policyengine_uk.utils.aggregate_impact.partition import parse_partition

    def head(i, totals, kind="spending"):
        return {
            "id": i,
            "label": i,
            "variable": i,
            "totals": totals,
            "entity": "household",
        }

    return parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_tax": {}, "gov_spending": {}, "household_benefits": {}},
            "tax_heads": [head("tax", ["gov_tax"])],
            "spending_heads": [
                head("common", ["gov_spending", "household_benefits"]),
                head("rare", ["gov_spending", "household_benefits"]),
            ],
        }
    )


def _recorded(common, rare, tax=5e11):
    from policyengine_uk.utils.aggregate_impact.measure import Recorder

    rec = Recorder()
    rec.metric("receipts.tax", "Tax", "receipts", "gbp", 2026, tax, records=5000)
    rec.metric("spending.common", "C", "spending", "gbp", 2026, common, records=500)
    rec.metric("spending.rare", "R", "spending", "gbp", 2026, rare, records=1)
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        rec.metric(total, total, "model_totals", "gbp", 2026, common + rare)
    rec.metric("model.gov_tax", "gov_tax", "model_totals", "gbp", 2026, tax)
    rec.metric("balance.balance", "b", "balance", "gbp", 2026, tax - common - rare)
    return rec


def test_a_suppressed_head_cannot_be_recovered_from_a_total():
    """Sol review of #2425, P1: spending total less the common benefit gave the
    rare one back. Totals that contain it are rounded to £1bn."""
    from policyengine_uk.utils.aggregate_impact.measure import protect_totals

    rec = _recorded(common=7.3e10, rare=246.9)
    protect_totals(rec, _protection_partition(), set(), 2026)
    published = {m: r["values"]["2026"] for m, r in rec.metrics.items()}
    assert published["spending.rare"] is None
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        assert published[total] == 7.3e10  # 73.0000002469bn rounded
        assert rec.metrics[total]["rounded"] == ["2026"]
    assert published["balance.balance"] == round((5e11 - 7.3e10) / 1e9) * 1e9
    # A total with no suppressed head is exact.
    assert (
        published["model.gov_tax"] == 5e11
        and "rounded" not in rec.metrics["model.gov_tax"]
    )
    # The raw value is kept off the record.
    assert all(246.9 not in r["values"].values() for r in rec.metrics.values())


@settings(max_examples=200, deadline=None)
@given(common=st.floats(1e8, 5e11), rare=st.floats(1.0, 4.99e8))
def test_protected_totals_carry_nothing_below_a_billion(common, rare):
    from policyengine_uk.utils.aggregate_impact.measure import protect_totals

    rec = _recorded(common, rare)
    protect_totals(rec, _protection_partition(), set(), 2026)
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        value = rec.metrics[total]["values"]["2026"]
        assert value % 1e9 == 0
        # Two datasets whose rare head differs inside the same billion publish
        # the same total.
        other = _recorded(common, rare / 2)
        protect_totals(other, _protection_partition(), set(), 2026)
        if round((common + rare) / 1e9) == round((common + rare / 2) / 1e9):
            assert other.metrics[total]["values"]["2026"] == value


def test_a_large_suppressed_head_suppresses_its_totals():
    from policyengine_uk.utils.aggregate_impact.measure import protect_totals

    rec = _recorded(common=7.3e10, rare=6e8)
    protect_totals(rec, _protection_partition(), set(), 2026)
    assert rec.metrics["model.gov_spending"]["values"]["2026"] is None
    assert rec.metrics["model.gov_spending"]["suppressed"] == ["2026"]
