"""Measurement bookkeeping: check scopes, reform costing checks, digests."""

import dataclasses
from types import SimpleNamespace

import numpy as np
import pytest
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


def _recorded(common, rare, tax=5e11, identities_ok=True):
    from policyengine_uk.utils.aggregate_impact.measure import Recorder

    rec = Recorder()
    rec.metric("receipts.tax", "Tax", "receipts", "gbp", 2026, tax, records=5000)
    rec.metric("spending.common", "C", "spending", "gbp", 2026, common, records=500)
    rec.metric("spending.rare", "R", "spending", "gbp", 2026, rare, records=1)
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        rec.metric(total, total, "model_totals", "gbp", 2026, common + rare)
    rec.metric("model.gov_tax", "gov_tax", "model_totals", "gbp", 2026, tax)
    rec.metric("balance.balance", "b", "balance", "gbp", 2026, tax - common - rare)
    _identities(rec, ok=identities_ok)
    return rec


IDENTITIES = (
    "identity:gov_tax",
    "identity:gov_spending",
    "identity:household_benefits",
    "identity:gov_balance",
    "identity:household_tax",
    "identity:household_net_income",
)


def _identities(rec, ok=True, year=2026):
    """The identity checks measure_year records: each total is its heads."""
    for check_id in IDENTITIES:
        rec.check(check_id, check_id, ok, "" if ok else "broken", scope=str(year))


def _excluded(rec, year=2026):
    from policyengine_uk.utils.aggregate_impact.measure import (
        exclude_suppressed,
        exclusion_signs,
        suppressed_heads,
    )

    partition = _protection_partition()
    exclude_suppressed(
        rec,
        exclusion_signs(partition, set()),
        suppressed_heads(rec, partition, year),
        year,
    )
    return {m: r["values"].get(str(year)) for m, r in rec.metrics.items()}


def test_a_total_leaves_out_a_suppressed_head():
    """Sol re-review 5 of #2335, P2: rounding the totals let repeated reports
    narrow the head down. Each total is now published without it."""
    rec = _recorded(common=7.3e10, rare=246.9)
    published = _excluded(rec)
    assert published["spending.rare"] is None
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        assert published[total] == 7.3e10
        assert rec.metrics[total]["excludes"] == {"2026": {"spending.rare": 1}}
    # The balance is receipts less spending: a spending head enters it negative.
    assert published["balance.balance"] == 5e11 - 7.3e10
    assert rec.metrics["balance.balance"]["excludes"] == {"2026": {"spending.rare": -1}}
    # A total with no suppressed head is unchanged and marked nothing.
    assert published["model.gov_tax"] == 5e11
    assert "excludes" not in rec.metrics["model.gov_tax"]
    # The raw value is kept off the record.
    assert all(246.9 not in r["values"].values() for r in rec.metrics.values())


@settings(max_examples=200, deadline=None)
@given(
    common=st.floats(1e8, 5e11),
    rare=st.floats(-1e10, 1e10),
    other=st.floats(-1e10, 1e10),
)
def test_no_published_figure_depends_on_a_suppressed_head(common, rare, other):
    """For all values: two datasets that differ only in a suppressed head
    publish the same figures, whatever its size or sign (to within a penny of
    floating-point rounding)."""
    first, second = (
        _excluded(_recorded(common, rare)),
        _excluded(_recorded(common, other)),
    )
    assert first.keys() == second.keys()
    for metric_id, value in first.items():
        if value is None:
            assert second[metric_id] is None
        else:
            assert second[metric_id] == pytest.approx(value, rel=0, abs=0.01)


@settings(max_examples=100, deadline=None)
@given(
    commons=st.lists(st.floats(1e8, 5e11), min_size=2, max_size=6),
    rare=st.floats(0, 4.99e8),
)
def test_repeated_reports_say_nothing_about_a_suppressed_head(commons, rare):
    """Each published total equals the published heads' sum in every report,
    so no sequence of reports narrows the suppressed head down."""
    for common in commons:
        published = _excluded(_recorded(common, rare))
        assert published["model.gov_spending"] == pytest.approx(
            published["spending.common"], rel=0, abs=0.01
        )
        assert published["balance.balance"] == pytest.approx(
            published["receipts.tax"] - published["spending.common"], rel=0, abs=0.01
        )


def test_income_for_deciles_leaves_out_suppressed_heads():
    from policyengine_uk.utils.aggregate_impact.measure import (
        exclusion_signs,
        income_without,
    )

    partition = _protection_partition()
    signs = exclusion_signs(partition, set())
    income = np.array([30_000.0, 40_000.0, 50_000.0])
    head_hh = {
        "rare": np.array([0.0, 900.0, 0.0]),
        "common": np.ones(3),
        "tax": np.ones(3),
    }
    hidden = {"rare": ("spending.rare", 900.0)}
    adjusted, excludes = income_without(
        income, signs["household.household_net_income"], hidden, partition, head_hh
    )
    np.testing.assert_allclose(adjusted, [30_000.0, 39_100.0, 50_000.0])
    assert excludes == {"spending.rare": 1}
    # Without suppressed heads, nothing changes.
    same, none = income_without(
        income, signs["household.household_net_income"], {}, partition, head_hh
    )
    assert same is income and none == {}
    # A suppressed head with an unknown income composition: no deciles.
    assert income_without(income, None, hidden, partition, head_hh) == (None, {})


def test_household_net_income_signs_follow_its_adds_and_subtracts():
    from policyengine_uk.utils.aggregate_impact.measure import exclusion_signs

    signs = exclusion_signs(_protection_partition(), set())
    # Benefits add to household net income; the partition's tax head is in
    # gov_tax only, not household_tax, so it doesn't enter it.
    assert signs["household.household_net_income"] == {"common": 1, "rare": 1}
    assert "household.household_market_income" not in signs


def test_no_head_is_part_of_household_market_income():
    """Market income holds no tax or benefit head, so it needs no exclusion."""
    from policyengine_uk.utils.aggregate_impact.partition import load_partition
    from policyengine_uk.variables.household.income.household_market_income import (
        HOUSEHOLD_MARKET_INCOME_VARIABLES,
    )

    from policyengine_uk.utils.aggregate_impact.partition import default_partition_path

    heads = {head.variable for head in load_partition(default_partition_path()).heads}
    assert not heads & set(HOUSEHOLD_MARKET_INCOME_VARIABLES)


def test_a_zero_weight_record_does_not_count_towards_a_published_figure():
    from policyengine_uk.utils.aggregate_impact.measure import _weighted_records

    values = np.array([5.0, 5.0, 5.0] + [5.0] * 7 + [0.0] * 5)
    weight = np.array([100.0] * 3 + [0.0] * 7 + [100.0] * 5)
    # Ten records have values, but only three carry weight: a small cell.
    assert _weighted_records(values != 0, weight) == 3


def test_identity_diagnostics_count_only_households_with_weight():
    """Sol re-review 4, finding 4: one weighted household and nine with no
    weight differing is a small cell, and its £100 is not published."""
    from policyengine_uk.utils.aggregate_impact.measure import _identity_check
    from policyengine_uk.utils.aggregate_impact.spec import load_spec

    rec = Recorder()
    components = np.zeros(20)
    components[:10] = 100.0
    weights = np.zeros(20)
    weights[0] = 1.0
    weights[10:] = 1.0
    _identity_check(
        rec, "identity:x", "x", components, np.zeros(20), 2026, load_spec(), weights
    )
    (detail,) = rec.checks["identity:x"]["failing"].values()
    assert "fewer than 10" in detail and "£" not in detail


def test_a_total_whose_identity_fails_is_suppressed_not_excluded():
    """Sol re-review 6 of #2335, P2 1: a formula that scales its components
    (benefit uprating, say) makes total less head reveal the head."""
    rec = _recorded(common=7.3e10, rare=246.9, identities_ok=False)
    published = _excluded(rec)
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        assert published[total] is None
        assert rec.metrics[total]["suppressed"] == ["2026"]
    # A total that holds no suppressed head is untouched.
    assert published["model.gov_tax"] == 5e11


class SuppressedHeadSim(TargetSim):
    """A reform that also moves a suppressed head (a state pension of £1,000)."""

    def __init__(self, balance_by_year, target_by_year, pension_by_year):
        super().__init__(balance_by_year, target_by_year)
        self.pension = pension_by_year
        self.tax_benefit_system.variables["state_pension"] = SimpleNamespace(
            entity=SimpleNamespace(key="household")
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable == "state_pension":
            return np.full(2, self.pension[int(period)] / 2)
        return super().calculate(variable, period, map_to, unweighted)


def test_a_reform_that_moves_a_suppressed_head_publishes_no_figure_that_year():
    """Sol re-review 6 of #2335, P2 2: a 10% uplift's £100 cost would give
    back a suppressed £1,000."""
    reform = parse_reforms(
        {
            "reforms": [
                {
                    "name": "Raise pensions",
                    "parameters": {"a": 1},
                    "responds": {
                        "variable": "universal_credit",
                        "direction": "up",
                        "minimum": 5_000.0,
                    },
                }
            ]
        }
    )
    baseline = {2025: 0.0, 2026: 0.0}
    targets = {2025: {"universal_credit": 100.0}, 2026: {"universal_credit": 100.0}}

    def factory(reform=None):
        if reform:
            return SuppressedHeadSim(
                {2025: -100.0, 2026: -100.0},
                {2025: 200.0, 2026: 200.0},
                {2025: 1000.0, 2026: 1100.0},  # moves the head in 2026 only
            )
        return SuppressedHeadSim(
            baseline, {2025: 100.0, 2026: 100.0}, {2025: 1000.0, 2026: 1000.0}
        )

    rec = Recorder()
    measure_reforms(
        factory,
        None,
        baseline,
        targets,
        reform,
        YEARS,
        rec,
        baseline_suppressed={2026: {"state_pension": 1000.0}},
    )
    costing = rec.metrics["reforms.raise_pensions"]
    target = rec.metrics["reform_targets.raise_pensions"]
    assert costing["values"]["2026"] is None and costing["suppressed"] == ["2026"]
    assert target["values"]["2026"] is None
    # A year in which the head isn't suppressed is published as usual.
    assert costing["values"]["2025"] == -100.0
    detail = rec.checks["responsive:raise_pensions"]["failing"]["2026"]
    assert "£" not in detail and "fewer than 10 records" in detail


def test_hbai_holds_a_head_only_when_it_is_one_of_its_components():
    from policyengine_uk.utils.aggregate_impact.measure import hbai_holds_any
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    partition = load_partition(default_partition_path())
    by_variable = {h.variable: h.id for h in partition.heads}
    assert not hbai_holds_any(
        partition, {by_variable["disabled_students_allowance"]: ("x", 1.0)}
    )
    assert hbai_holds_any(partition, {by_variable["child_benefit"]: ("x", 1.0)})


class HbaiSim:
    """Household-level HBAI pieces: employment income, child benefit and
    council tax, and the model's HBAI income before its reset."""

    def __init__(self, before):
        self.values = {
            "employment_income": np.array([20_000.0, 0.0]),
            "child_benefit": np.array([1_234.5, 100.0]),
            "council_tax": np.array([1_200.0, 0.0]),
            "hbai_household_net_income_before_reset_to_zero": before,
            "hbai_household_net_income": np.maximum(0.0, before),
        }
        self.tax_benefit_system = SimpleNamespace(variables=self.values)

    def calculate(self, variable, period, map_to=None, unweighted=True):
        return self.values.get(variable, np.zeros(2))


def test_hbai_is_recomputed_only_where_its_lists_reproduce_the_model():
    """Sol re-review 6 of #2335, P2 4: with council tax abolished the model
    leaves it out of HBAI, so adding it back would be wrong."""
    from policyengine_uk.utils.aggregate_impact.measure import _hbai_without
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    partition = load_partition(default_partition_path())
    cb = next(h for h in partition.heads if h.variable == "child_benefit")
    hidden = {cb.id: ("spending." + cb.id, 1_334.5)}
    head_hh = {"child_benefit": np.array([1_234.5, 100.0])}
    consistent = np.array([20_000.0 + 1_234.5 - 1_200.0, 100.0])
    values, excludes = _hbai_without(
        HbaiSim(consistent), 2026, hidden, partition, head_hh
    )
    np.testing.assert_allclose(values, [18_800.0, 0.0])
    assert excludes == {"spending." + cb.id: 1}
    # Council tax abolished: the model's income omits it, so the lists don't
    # reproduce it, and the total is suppressed rather than rebuilt.
    abolished = np.array([20_000.0 + 1_234.5, 100.0])
    assert _hbai_without(HbaiSim(abolished), 2026, hidden, partition, head_hh) == (
        None,
        None,
    )
