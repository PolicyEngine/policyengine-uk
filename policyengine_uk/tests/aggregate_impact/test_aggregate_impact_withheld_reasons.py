"""Why the tool withholds a reform year (#2654): one reason per condition.

``measure.withheld_reasons`` names each condition of reform withholding that
holds, and the component or variable it holds for. These tests pin one case
per condition, two conditions together, and, for all small worlds, that the
tool withholds a year exactly when it records a reason, that the reasons
match a direct computation, and that the years withheld and the figures
published match the yes-or-no rule frozen at da31e8698 (the oracle in
``reform_withheld_main_reference.py``).
"""

import re
from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.tests.aggregate_impact import (
    reform_withheld_main_reference as main_reference,
)
from policyengine_uk.utils.aggregate_impact.api import to_report
from policyengine_uk.utils.aggregate_impact.compare import compare
from policyengine_uk.utils.aggregate_impact.measure import (
    CHANGE_GBP,
    Recorder,
    _weighted_records,
    baseline_records,
    component_metric_ids,
    measure_reforms,
    reform_withheld,
    weighted_total,
    withheld_reasons,
)
from policyengine_uk.utils.aggregate_impact.partition import (
    default_partition_path,
    load_partition,
    parse_partition,
)
from policyengine_uk.utils.aggregate_impact.privacy import (
    MIN_CELL,
    NO_BASELINE,
    SMALL_BALANCE_CHANGE,
    SMALL_COMPONENT_LEFT,
    SMALL_TARGET_CHANGE,
    SUPPRESSED_COMPONENT_CHANGED,
    WITHHELD_CONDITIONS,
    withheld_reason,
    withheld_text,
)
from policyengine_uk.utils.aggregate_impact.reforms import load_reforms, parse_reforms
from policyengine_uk.utils.aggregate_impact.render import _withheld_notes, render
from policyengine_uk.utils.aggregate_impact.spec import load_spec

SPEC = load_spec()
N = 20
YEAR = 2026
HEADS = ("income_tax", "dividend_tax", "state_pension")
METRIC_IDS = {
    "income_tax": "receipts.income_tax",
    "dividend_tax": "receipts.dividend_tax",
    "state_pension": "spending.state_pension",
}


class WorldSim:
    """Household arrays by year and variable, with household weights.

    gov_balance is income tax plus dividend tax less the state pension.
    """

    def __init__(self, values_by_year, weight):
        self.values = values_by_year
        self.weight = np.asarray(weight, dtype=float)
        entity = SimpleNamespace(key="household")
        names = {v for values in values_by_year.values() for v in values}
        self.tax_benefit_system = SimpleNamespace(
            variables={
                v: SimpleNamespace(entity=entity)
                for v in names | {"gov_balance", "household_weight"}
            }
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable == "household_weight":
            return self.weight
        values = self.values[int(period)]
        if variable == "gov_balance":
            return _balance(values)
        return np.asarray(values.get(variable, np.zeros(N)), dtype=float)


class BenunitWorldSim(WorldSim):
    """A WorldSim whose Child Benefit falls on 40 benefit units, two in each
    household, each weighted as its household."""

    HOUSEHOLD = np.repeat(np.arange(N), 2)

    def __init__(self, values_by_year, weight):
        super().__init__(values_by_year, weight)
        self.tax_benefit_system.variables["child_benefit"] = SimpleNamespace(
            entity=SimpleNamespace(key="benunit")
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable == "benunit_weight":
            return self.weight[self.HOUSEHOLD]
        return super().calculate(variable, period, map_to, unweighted)

    def map_result(self, values, source, target):
        assert (source, target) == ("benunit", "household")
        return np.bincount(self.HOUSEHOLD, weights=values, minlength=N)


def _balance(values) -> np.ndarray:
    zero = np.zeros(N)
    return (
        np.asarray(values.get("income_tax", zero), dtype=float)
        + np.asarray(values.get("dividend_tax", zero), dtype=float)
        - np.asarray(values.get("state_pension", zero), dtype=float)
    )


def _partition(double_counts=()):
    """Three heads, and any double counts named, each inside the state
    pension."""

    def head(i, totals):
        return {"id": i, "label": i, "variable": i, "totals": totals}

    return parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_tax": {}, "gov_spending": {}},
            "tax_heads": [
                head("income_tax", ["gov_tax"]),
                head("dividend_tax", ["gov_tax"]),
            ],
            "spending_heads": [head("state_pension", ["gov_spending"])],
            "model_double_counts": [
                {
                    "variable": variable,
                    "contained_in": "state_pension",
                    "totals": ["gov_spending"],
                }
                for variable in double_counts
            ],
        }
    )


def _reform(target="income_tax", name="Change it"):
    return parse_reforms(
        {
            "reforms": [
                {
                    "name": name,
                    "parameters": {"a": 1},
                    "responds": {
                        "variable": target,
                        "direction": "up",
                        "minimum": 1e12,
                    },
                }
            ]
        }
    )


def _measure(
    base,
    reformed,
    weight=None,
    target="income_tax",
    years=(YEAR,),
    others=(),
    double_counts=(),
    sim=WorldSim,
):
    """Measure one reform as measure() does: record the baseline's heads,
    with their suppression, then cost the reform against the baseline.

    ``base`` and ``reformed`` map variable to household values, or year to
    such a mapping. ``others`` are other reforms' targets, which measure()
    checks too."""
    if not isinstance(next(iter(base)), int):
        base = {year: base for year in years}
        reformed = {year: reformed for year in years}
    weight = np.ones(N) if weight is None else np.asarray(weight, dtype=float)
    partition = _partition(double_counts)
    targets = [target, *others]
    base_sim = sim(base, weight)
    rec = Recorder()
    for year in years:
        for head in partition.heads:
            section = "receipts" if head.kind == "tax" else "spending"
            values = np.asarray(base[year].get(head.variable, np.zeros(N)))
            rec.metric(
                f"{section}.{head.id}",
                head.label,
                section,
                "gbp",
                year,
                float(np.sum(weight * values)),
                records=_weighted_records(values != 0, weight),
            )
    reform = _reform(target)
    measure_reforms(
        lambda reform=None: sim(reformed if reform else base, weight),
        None,
        {y: weighted_total(base_sim, "gov_balance", y) for y in years},
        {y: {t: weighted_total(base_sim, t, y) for t in targets} for y in years},
        reform,
        list(years),
        rec,
        baseline={
            y: baseline_records(base_sim, partition, rec, y, targets) for y in years
        },
        components=partition.component_variables(),
    )
    return rec


def _reasons(rec, year=YEAR, metric="reforms.change_it"):
    return rec.metrics[metric]["withheld_because"].get(str(year), [])


def _conditions(reasons):
    return [(r["condition"], r["variable"], r["metric_id"]) for r in reasons]


def _world(income_tax, state_pension, dividend_tax=None, **others):
    values = {
        "income_tax": np.asarray(income_tax, dtype=float),
        "state_pension": np.asarray(state_pension, dtype=float),
        "dividend_tax": np.full(N, 50.0)
        if dividend_tax is None
        else np.asarray(dividend_tax, dtype=float),
    }
    values.update({k: np.asarray(v, dtype=float) for k, v in others.items()})
    return values


def _first(n, value, otherwise=0.0):
    return np.r_[np.full(n, value), np.full(N - n, otherwise)]


# One case per condition. Each world fires exactly one condition.


def test_a_reform_that_changes_a_suppressed_component_names_it():
    """Two pensions (suppressed); the reform raises one and every income tax
    bill, so 20 balances and 20 target records change."""
    base = _world(np.full(N, 100.0), _first(2, 1_000.0))
    reformed = _world(np.full(N, 110.0), np.r_[1_100.0, 1_000.0, np.zeros(N - 2)])
    rec = _measure(base, reformed)
    assert _conditions(_reasons(rec)) == [
        (SUPPRESSED_COMPONENT_CHANGED, "state_pension", "spending.state_pension")
    ]
    assert rec.metrics["reforms.change_it"]["values"][str(YEAR)] is None


def test_a_reform_that_leaves_a_small_component_names_it():
    """Dividend tax falls from 20 payers to 5: a new small cell."""
    base = _world(np.full(N, 100.0), np.full(N, 100.0))
    reformed = _world(np.full(N, 110.0), np.full(N, 100.0), _first(5, 50.0))
    rec = _measure(base, reformed)
    assert _conditions(_reasons(rec)) == [
        (SMALL_COMPONENT_LEFT, "dividend_tax", "receipts.dividend_tax")
    ]


def test_a_reform_that_changes_few_balances_says_so():
    """Three households' income tax rises; the target, the state pension,
    doesn't move."""
    base = _world(np.full(N, 100.0), np.full(N, 100.0))
    reformed = _world(_first(3, 110.0, 100.0), np.full(N, 100.0))
    rec = _measure(base, reformed, target="state_pension")
    assert _conditions(_reasons(rec)) == [(SMALL_BALANCE_CHANGE, "gov_balance", None)]


def test_a_reform_that_changes_few_target_records_names_the_target():
    """Pension Credit, outside gov_balance here, rises for three households;
    every household's income tax rises too."""
    base = _world(np.full(N, 100.0), np.full(N, 100.0), pension_credit=np.zeros(N))
    reformed = _world(
        np.full(N, 110.0), np.full(N, 100.0), pension_credit=_first(3, 25.0)
    )
    rec = _measure(base, reformed, target="pension_credit")
    assert _conditions(_reasons(rec)) == [(SMALL_TARGET_CHANGE, "pension_credit", None)]
    target = rec.metrics["reform_targets.change_it"]
    assert target["values"][str(YEAR)] is None
    assert (
        target["withheld_because"]
        == rec.metrics["reforms.change_it"]["withheld_because"]
    )


def test_a_small_change_in_another_reforms_target_names_that_target():
    """measure() checks every costed reform's target: the tool withholds a
    reform aimed at income tax when it moves Pension Credit, another
    reform's target, in three records."""
    world = _world(np.full(N, 100.0), np.full(N, 100.0), pension_credit=np.zeros(N))
    reformed = _world(
        np.full(N, 110.0), np.full(N, 100.0), pension_credit=_first(3, 25.0)
    )
    base_sim = WorldSim({YEAR: world}, np.ones(N))
    targets = ["income_tax", "pension_credit"]
    rec = Recorder()
    measure_reforms(
        lambda reform=None: WorldSim({YEAR: reformed if reform else world}, np.ones(N)),
        None,
        {YEAR: weighted_total(base_sim, "gov_balance", YEAR)},
        {YEAR: {t: weighted_total(base_sim, t, YEAR) for t in targets}},
        _reform("income_tax", name="Raise income tax"),
        [YEAR],
        rec,
        baseline={YEAR: baseline_records(base_sim, _partition(), rec, YEAR, targets)},
        components=_partition().component_variables(),
    )
    reasons = rec.metrics["reforms.raise_income_tax"]["withheld_because"]
    assert _conditions(reasons[str(YEAR)]) == [
        (SMALL_TARGET_CHANGE, "pension_credit", None)
    ]


def test_a_year_without_baseline_records_says_so():
    rec = Recorder()
    reform = parse_reforms({"reforms": [{"name": "Any", "parameters": {"a": 1}}]})
    world = {y: _world(np.full(N, 1.0), np.full(N, 1.0)) for y in (2025, 2026)}
    measure_reforms(
        lambda reform=None: WorldSim(world, np.ones(N)),
        None,
        {2025: 0.0, 2026: 0.0},
        {},
        reform,
        [2025, 2026],
        rec,
    )
    assert rec.metrics["reforms.any"]["withheld_because"] == {
        "2025": [{"condition": NO_BASELINE, "variable": None, "metric_id": None}],
        "2026": [{"condition": NO_BASELINE, "variable": None, "metric_id": None}],
    }


def test_two_conditions_together_are_both_recorded():
    """The reform raises one suppressed pension and leaves dividend tax with
    five payers; every income tax bill changes, so neither the balance nor
    the target is a small change. The tool records both conditions."""
    base = _world(np.full(N, 100.0), _first(2, 1_000.0))
    reformed = _world(
        np.full(N, 110.0),
        np.r_[1_100.0, 1_000.0, np.zeros(N - 2)],
        _first(5, 50.0),
    )
    rec = _measure(base, reformed)
    assert _conditions(_reasons(rec)) == [
        (SUPPRESSED_COMPONENT_CHANGED, "state_pension", "spending.state_pension"),
        (SMALL_COMPONENT_LEFT, "dividend_tax", "receipts.dividend_tax"),
    ]
    detail = rec.checks["responsive:change_it"]["failing"][str(YEAR)]
    assert (
        "the reform changes a record of spending.state_pension, which the "
        "baseline suppresses; the reform leaves receipts.dividend_tax with "
        "fewer than 10 records" in detail
    )


def test_every_condition_at_once():
    """A 10% rise in one suppressed £4 pension, and dividend tax falls from
    12 payers to 5: eight balances and one target record change."""
    base = _world(np.full(N, 100.0), _first(1, 4.0), _first(12, 50.0))
    reformed = _world(np.full(N, 100.0), _first(1, 4.4), _first(5, 50.0))
    rec = _measure(base, reformed, target="state_pension")
    assert [c for c, _, _ in _conditions(_reasons(rec))] == [
        SUPPRESSED_COMPONENT_CHANGED,
        SMALL_COMPONENT_LEFT,
        SMALL_BALANCE_CHANGE,
        SMALL_TARGET_CHANGE,
    ]


def test_a_published_year_records_no_reason():
    base = _world(np.full(N, 100.0), np.full(N, 100.0))
    reformed = _world(np.full(N, 110.0), np.full(N, 100.0))
    rec = _measure(base, reformed)
    record = rec.metrics["reforms.change_it"]
    assert record["values"][str(YEAR)] == pytest.approx(200.0)
    assert record["withheld_because"] == {} and "suppressed" not in record


def test_component_metric_ids_name_heads_and_double_counts():
    partition = SimpleNamespace(
        heads=(
            SimpleNamespace(variable="income_tax", id="income_tax", kind="tax"),
            SimpleNamespace(variable="dla", id="disability", kind="spending"),
        ),
        double_counts=(SimpleNamespace(variable="sdlt_corporate"),),
    )
    assert component_metric_ids(partition) == {
        "income_tax": "receipts.income_tax",
        "dla": "spending.disability",
        "sdlt_corporate": "double_counts.sdlt_corporate",
    }


def test_two_small_targets_are_both_named():
    """The reform moves Pension Credit and Child Benefit, two other reforms'
    targets, in three records each; every income tax bill rises too."""
    zero = np.zeros(N)
    base = _world(
        np.full(N, 100.0), np.full(N, 100.0), pension_credit=zero, child_benefit=zero
    )
    reformed = _world(
        np.full(N, 110.0),
        np.full(N, 100.0),
        pension_credit=_first(3, 25.0),
        child_benefit=_first(3, 10.0),
    )
    rec = _measure(base, reformed, others=("pension_credit", "child_benefit"))
    assert _conditions(_reasons(rec)) == [
        (SMALL_TARGET_CHANGE, "pension_credit", None),
        (SMALL_TARGET_CHANGE, "child_benefit", None),
    ]


def test_a_change_of_exactly_half_a_penny_changes_no_record():
    """Three households hold nothing until the reform pays each of them a
    state pension of exactly CHANGE_GBP, which moves neither their balance
    nor the target by more than CHANGE_GBP; a penny does."""
    base = _world(_first(3, 0.0, 100.0), _first(3, 0.0, 100.0), _first(3, 0.0, 50.0))
    reformed = dict(base, state_pension=_first(3, CHANGE_GBP, 100.0))
    rec = _measure(base, reformed, target="state_pension")
    assert _reasons(rec) == []
    target = rec.metrics["reform_targets.change_it"]["values"][str(YEAR)]
    assert target == pytest.approx(3 * CHANGE_GBP)
    penny = dict(base, state_pension=_first(3, 0.01, 100.0))
    assert _conditions(_reasons(_measure(base, penny, target="state_pension"))) == [
        (SMALL_BALANCE_CHANGE, "gov_balance", None),
        (SMALL_TARGET_CHANGE, "state_pension", None),
    ]


def test_a_reform_that_leaves_a_small_double_count_names_it():
    """A double count, counted inside the state pension, falls from 20
    records to 4: a new small cell, named by its published id."""
    base = _world(np.full(N, 100.0), np.full(N, 100.0), pension_top_up=np.full(N, 5.0))
    reformed = _world(
        np.full(N, 110.0), np.full(N, 100.0), pension_top_up=_first(4, 5.0)
    )
    rec = _measure(base, reformed, double_counts=("pension_top_up",))
    assert _conditions(_reasons(rec)) == [
        (SMALL_COMPONENT_LEFT, "pension_top_up", "double_counts.pension_top_up")
    ]


@pytest.mark.parametrize(
    "households, withheld",
    [
        # Ten weighted benefit units in five households: not a small cell.
        (6, False),
        # Four weighted benefit units in two households.
        (3, True),
    ],
)
def test_a_benefit_unit_target_counts_benefit_units(households, withheld):
    """Child Benefit falls on 40 benefit units in 20 households, and the
    first household carries no weight. The reform raises Child Benefit for
    both benefit units in the first few households and every income tax
    bill, so the tool counts the target's records with benefit unit
    weights."""
    weight = _first(1, 0.0, 1.0)
    base = _world(np.full(N, 100.0), np.full(N, 100.0), child_benefit=np.zeros(2 * N))
    reformed = _world(
        np.full(N, 110.0),
        np.full(N, 100.0),
        child_benefit=np.r_[
            np.full(2 * households, 10.0), np.zeros(2 * (N - households))
        ],
    )
    rec = _measure(base, reformed, weight, "child_benefit", sim=BenunitWorldSim)
    reasons = _conditions(_reasons(rec))
    target = rec.metrics["reform_targets.change_it"]["values"][str(YEAR)]
    if withheld:
        assert reasons == [(SMALL_TARGET_CHANGE, "child_benefit", None)]
        assert target is None
    else:
        assert reasons == []
        assert target == pytest.approx(10.0 * 2 * (households - 1))


def test_reason_words_add_no_digit_to_the_names_they_quote():
    """Some component names hold digits, such as bursary_fund_16_to_19's age
    range; a name counts no records. Around the names, a reason's words add
    no digit but the 10 in "fewer than 10"."""
    ids = component_metric_ids(load_partition(default_partition_path()))
    assert "bursary_fund_16_to_19" in ids
    for name in {*ids, *ids.values()}:
        for condition in WITHHELD_CONDITIONS:
            text = withheld_text([withheld_reason(condition, name)])
            words = text.replace(name, "").replace(f"fewer than {MIN_CELL}", "")
            assert not re.search(r"\d", words), text


def test_privacy_py_covers_the_stock_reform_rows():
    """privacy.py's exception for reasons across reform rows rests on the
    reform list in the repository: a change to that list revisits it."""
    assert " ".join(r.id for r in load_reforms()) == (
        "basic_rate_plus_1pp higher_rate_plus_1pp personal_allowance_13000 "
        "child_benefit_additional_25 uc_taper_20pc employee_nics_main_10pc "
        "vat_standard_plus_2pp additional_rate_plus_3pp "
        "uc_standard_allowance_plus_10pc state_pension_plus_10pc"
    )


# The issue's example: two heads suppressed in every year, a reform withheld
# in 2027-28 to 2030-31 only.

ISSUE_YEARS = tuple(range(2025, 2032))
WITHHELD_YEARS = (2027, 2028, 2029, 2030)


def _issue_example():
    base = {y: _world(np.full(N, 100.0), _first(2, 1_000.0)) for y in ISSUE_YEARS}
    reformed = {
        y: _world(
            np.full(N, 103.0),
            _first(2, 1_000.0),
            _first(4, 50.0) if y in WITHHELD_YEARS else np.full(N, 50.0),
        )
        for y in ISSUE_YEARS
    }
    return _measure(base, reformed, years=ISSUE_YEARS)


def test_the_issue_example_says_why_only_some_years_are_withheld():
    rec = _issue_example()
    record = rec.metrics["reforms.change_it"]
    assert record["suppressed"] == [str(y) for y in WITHHELD_YEARS]
    assert set(record["withheld_because"]) == set(record["suppressed"])
    for year in WITHHELD_YEARS:
        assert _conditions(_reasons(rec, year)) == [
            (SMALL_COMPONENT_LEFT, "dividend_tax", "receipts.dividend_tax")
        ]
    for year in set(ISSUE_YEARS) - set(WITHHELD_YEARS):
        assert record["values"][str(year)] == pytest.approx(60.0)


def test_the_long_format_report_carries_the_reasons_on_reform_rows_only():
    rec = _issue_example()
    report = to_report(
        {
            "status": "ok",
            "provenance": {},
            "partition": {"sha256": "p"},
            "years": list(ISSUE_YEARS),
            "metrics": list(rec.metrics.values()),
            "checks": list(rec.checks.values()),
        }
    )
    rows = report["metrics"]
    reform_rows = [r for r in rows if r["metric_id"].startswith("reform")]
    assert {r["metric_id"] for r in reform_rows} == {
        "reforms.change_it",
        "reform_targets.change_it",
    }
    for row in reform_rows:
        assert row["suppressed"] == bool(row["withheld_because"])
        assert row["suppressed"] == (row["year"] in WITHHELD_YEARS)
    assert all("withheld_because" not in r for r in rows if r not in reform_rows)
    target_2027 = next(
        r
        for r in reform_rows
        if r["metric_id"] == "reform_targets.change_it" and r["year"] == 2027
    )
    assert target_2027["value"] is None
    assert target_2027["withheld_because"] == [
        {
            "condition": SMALL_COMPONENT_LEFT,
            "variable": "dividend_tax",
            "metric_id": "receipts.dividend_tax",
        }
    ]


def _side(rec):
    from policyengine_uk.tests.aggregate_impact.test_aggregate_impact_compare import (
        result,
    )

    side = result({})
    side["metrics"] = list(rec.metrics.values())
    return side


def test_the_comment_says_why_each_reform_year_is_suppressed():
    rec = _issue_example()
    summary = compare(_side(rec), _side(rec), SPEC)
    assert summary["status"] == "pass", summary["failures"]
    row = next(r for r in summary["rows"] if r["id"] == "reforms.change_it")
    reason = [
        {
            "condition": SMALL_COMPONENT_LEFT,
            "variable": "dividend_tax",
            "metric_id": "receipts.dividend_tax",
        }
    ]
    assert row["values"]["2027"]["withheld_because"] == {
        "base": reason,
        "head": reason,
    }
    assert "withheld_because" not in row["values"]["2025"]
    text = render(summary, SPEC)
    line = (
        "- Change it, 2027-28 to 2030-31 (base and head): the reform leaves "
        "receipts.dividend_tax with fewer than 10 records."
    )
    assert line in text
    # Once, under the costings, though the tool withholds the targets too.
    assert text.count("receipts.dividend_tax with fewer than 10") == 1
    assert text.index(line) > text.index("### Standard reform costings")


def test_the_comment_tells_the_sides_apart():
    base_rec = _issue_example()
    world = {y: _world(np.full(N, 100.0), _first(2, 1_000.0)) for y in ISSUE_YEARS}
    head_rec = _measure(
        world,
        {
            y: _world(
                np.full(N, 103.0),
                np.r_[1_001.0, 1_000.0, np.zeros(N - 2)]
                if y == 2026
                else w["state_pension"],
            )
            for y, w in world.items()
        },
        years=ISSUE_YEARS,
    )
    summary = compare(_side(base_rec), _side(head_rec), SPEC)
    notes = _withheld_notes(
        [r for r in summary["rows"] if r["section"] == "reforms"], ISSUE_YEARS
    )
    assert notes == [
        "- Change it, 2027-28 to 2030-31 (base): the reform leaves "
        "receipts.dividend_tax with fewer than 10 records.",
        "- Change it, 2026-27 (head): the reform changes a record of "
        "spending.state_pension, which the baseline suppresses.",
    ]


def test_the_comment_caps_the_reasons_it_lists():
    """25 reforms, each withheld in a different year on each side, give 50
    lines: the comment shows 40 and points to the artifact for the rest."""
    from policyengine_uk.utils.aggregate_impact.render import MAX_WITHHELD_ROWS

    def side(year, variable):
        reason = [
            {
                "condition": SMALL_COMPONENT_LEFT,
                "variable": variable,
                "metric_id": f"receipts.{variable}",
            }
        ]
        measured = _side(Recorder())
        measured["metrics"] = [
            {
                "id": f"reforms.reform_{i}",
                "label": f"Reform {i}",
                "section": "reforms",
                "group": None,
                "kind": "gbp",
                "unit": None,
                "values": {str(y): None if y == year else 1.0 for y in SPEC.years},
                "suppressed": [str(year)],
                "withheld_because": {str(year): reason},
            }
            for i in range(25)
        ]
        return measured

    summary = compare(side(2025, "income_tax"), side(2026, "dividend_tax"), SPEC)
    text = render(summary, SPEC)
    listed = [line for line in text.splitlines() if line.startswith("- Reform ")]
    assert len(listed) == MAX_WITHHELD_ROWS
    assert (
        "- 10 more left out here; the report artifact's `summary.json` gives "
        "every reason under `withheld_because`." in text
    )


# For all small worlds.

values = st.floats(1.0, 1e4, allow_nan=False)
deltas = st.sampled_from([0.0, 0.004, CHANGE_GBP, 0.006, 1.0, -250.0, 1e3])


@st.composite
def worlds(draw):
    """A baseline and a reformed world of N households, with each variable's
    number of non-zero records and of changed records drawn from 0 to N, so
    small cells come up often; some households carry no weight."""
    weight = np.asarray(
        draw(st.lists(st.sampled_from([0.0, 1.0, 2.5]), min_size=N, max_size=N))
    )
    base, reformed = {}, {}
    for variable in HEADS + ("pension_credit",):
        support = draw(st.integers(0, N))
        level = np.asarray(draw(st.lists(values, min_size=N, max_size=N)))
        before = np.where(np.arange(N) < support, level, 0.0)
        start = draw(st.integers(0, N - 1))
        changed = draw(st.integers(0, N))
        delta = draw(deltas)
        moved = (np.arange(N) - start) % N < changed
        after = np.where(moved, before + delta, before)
        if draw(st.booleans()):
            # Some reforms take a component away from most of its records.
            after = np.where(np.arange(N) < draw(st.integers(0, N)), after, 0.0)
        base[variable], reformed[variable] = before, after
    target = draw(st.sampled_from(HEADS + ("pension_credit",)))
    return base, reformed, weight, target


def _direct_reasons(base, reformed, weight, target):
    """The conditions computed straight from the arrays: a second
    implementation of the rule."""

    def records(mask):
        return int(np.count_nonzero(mask & (weight > 0)))

    def small(count):
        return 0 < count < MIN_CELL

    hidden = [v for v in HEADS if small(records(base[v] != 0))]
    out = [
        (SUPPRESSED_COMPONENT_CHANGED, v, METRIC_IDS[v])
        for v in hidden
        if not np.array_equal(reformed[v], base[v])
    ]
    out += [
        (SMALL_COMPONENT_LEFT, v, METRIC_IDS[v])
        for v in HEADS
        if v not in hidden and small(records(reformed[v] != 0))
    ]
    if small(records(np.abs(_balance(reformed) - _balance(base)) > 0.005)):
        out.append((SMALL_BALANCE_CHANGE, "gov_balance", None))
    if small(records(np.abs(reformed[target] - base[target]) > 0.005)):
        out.append((SMALL_TARGET_CHANGE, target, None))
    return out


@settings(max_examples=300, deadline=None)
@given(world=worlds())
def test_a_year_is_withheld_exactly_when_it_has_a_reason(world):
    """For every world: the tool withholds the figures exactly when it
    records a reason; the reasons match the conditions computed directly;
    the years withheld match the frozen rule; and the published
    figures equal the direct weighted changes."""
    base, reformed, weight, target = world
    rec = _measure(base, reformed, weight, target)
    reasons = _reasons(rec)
    for metric_id in ("reforms.change_it", "reform_targets.change_it"):
        record = rec.metrics[metric_id]
        withheld = record["values"][str(YEAR)] is None
        assert withheld == bool(reasons)
        assert set(record.get("suppressed", [])) == set(record["withheld_because"])
        assert record["withheld_because"].get(str(YEAR), []) == reasons
    assert _conditions(reasons) == _direct_reasons(base, reformed, weight, target)
    assert all(r["condition"] in WITHHELD_CONDITIONS for r in reasons)

    partition = _partition()
    base_sim, reformed_sim = (
        WorldSim({YEAR: base}, weight),
        WorldSim({YEAR: reformed}, weight),
    )
    records = baseline_records(base_sim, partition, rec, YEAR, [target])
    components = partition.component_variables()
    frozen = main_reference.reform_withheld(reformed_sim, YEAR, records, components)
    assert frozen == bool(reasons)
    assert reform_withheld(reformed_sim, YEAR, records, components) == frozen
    assert withheld_reasons(reformed_sim, YEAR, records, components) == reasons

    costing = float(np.sum(weight * (_balance(reformed) - _balance(base))))
    change = float(np.sum(weight * (reformed[target] - base[target])))
    published = rec.metrics["reforms.change_it"]["values"][str(YEAR)]
    target_change = rec.metrics["reform_targets.change_it"]["values"][str(YEAR)]
    if frozen:
        assert published is None and target_change is None
    else:
        assert published == pytest.approx(costing, abs=1e-6)
        assert target_change == pytest.approx(change, abs=1e-6)


@settings(max_examples=300, deadline=None)
@given(world=worlds())
def test_a_reason_never_gives_a_count_or_an_amount(world):
    """A reason holds only names; around them, its words say "fewer than
    10" at most, whatever the counts and amounts behind it."""
    base, reformed, weight, target = world
    rec = _measure(base, reformed, weight, target)
    reasons = _reasons(rec)
    text = withheld_text(reasons)
    words = text.replace(f"fewer than {MIN_CELL}", "")
    for reason in reasons:
        assert set(reason) == {"condition", "variable", "metric_id"}
        assert all(value is None or isinstance(value, str) for value in reason.values())
        words = words.replace(reason["metric_id"] or reason["variable"] or "", "")
    assert not re.search(r"\d", words)
    assert "£" not in text
    detail = rec.checks["responsive:change_it"]["failing"].get(str(YEAR), "")
    if reasons:
        assert text in detail and "£" not in detail
