"""Measurement bookkeeping: check scopes, reform costing checks, digests."""

import dataclasses
from types import SimpleNamespace

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.utils.aggregate_impact.measure import (
    Recorder,
    _finite_metrics_check,
    definitions_digest,
    measure_reforms,
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
