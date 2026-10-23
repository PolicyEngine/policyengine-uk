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


# Households in the stub worlds: a change in fewer than 10 is a small cell.
N = 20
NO_HEADS = SimpleNamespace(heads=(), double_counts=())


def _baseline(sim, years, targets=()):
    """The baseline records a reform is checked against, with nothing
    suppressed."""
    from policyengine_uk.utils.aggregate_impact.measure import baseline_records

    return {y: baseline_records(sim, NO_HEADS, Recorder(), y, targets) for y in years}


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
            return np.ones(N)
        return np.full(N, self.balance[int(period)] / N)


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

    measure_reforms(
        factory,
        None,
        baseline,
        {},
        reform,
        YEARS,
        rec,
        baseline=_baseline(factory(), YEARS),
    )
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
            return np.full(N, self.target[int(period)] / N)
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

        measure_reforms(
            factory,
            None,
            baseline,
            targets,
            reform,
            YEARS,
            rec,
            baseline=_baseline(factory(), YEARS, ["universal_credit"]),
        )
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


HW = np.ones(2)
MARKET = np.array([30_000.0, 20_000.0])


def _rebuilt(common, rare, tax=5e11, records=1, scale=1.0, year=2026, market=MARKET):
    """A two-household year as measure_year records it, then rebuilt.

    Household 1 has the common benefit and the tax, household 2 the rare
    benefit, from ``records`` records. The model's own totals scale their
    heads by ``scale``, as a formula that uprates its components would (Sol
    re-review 7 of #2335). Returns the recorder and the rebuilt household
    net income and what it leaves out.
    """
    from policyengine_uk.utils.aggregate_impact.measure import (
        rebuild_protected,
        suppressed_components,
    )

    partition = _protection_partition()
    component_hh = {
        "common": np.array([common, 0.0]),
        "rare": np.array([0.0, rare]),
        "tax": np.array([tax, 0.0]),
    }
    rec = Recorder()
    rec.metric("receipts.tax", "Tax", "receipts", "gbp", year, tax, records=5000)
    rec.metric("spending.common", "C", "spending", "gbp", year, common, records=500)
    rec.metric("spending.rare", "R", "spending", "gbp", year, rare, records=records)
    spending = scale * (common + rare)
    for total in ("model.gov_spending", "model.household_benefits"):
        rec.metric(total, total, "model_totals", "gbp", year, spending)
    rec.metric("model.gov_tax", "gov_tax", "model_totals", "gbp", year, scale * tax)
    rec.metric(
        "model.gov_balance",
        "b",
        "model_totals",
        "gbp",
        year,
        scale * (tax - common - rare),
    )
    rec.metric("balance.receipts", "r", "balance", "gbp", year, tax)
    rec.metric("balance.spending", "s", "balance", "gbp", year, common + rare)
    rec.metric("balance.balance", "b", "balance", "gbp", year, tax - common - rare)
    rec.metric(
        "household.household_net_income",
        "n",
        "household_totals",
        "gbp",
        year,
        float(MARKET.sum()) + spending,
    )
    income, excludes = rebuild_protected(
        rec,
        partition,
        set(),
        suppressed_components(rec, partition, year),
        component_hh,
        HW,
        year,
        market_hh=market,
        pension_hh=None if market is None else np.zeros(2),
    )
    return rec, income, excludes


def _published(rec, year=2026):
    return {m: r["values"].get(str(year)) for m, r in rec.metrics.items()}


def test_a_total_is_rebuilt_without_its_suppressed_head():
    """Sol re-reviews 5 to 7 of #2335: each total holding a suppressed head is
    rebuilt from its other heads, never as the model's total less the head."""
    rec, _, _ = _rebuilt(common=7.3e10, rare=246.9)
    published = _published(rec)
    assert published["spending.rare"] is None
    for total in ("model.gov_spending", "model.household_benefits", "balance.spending"):
        assert published[total] == 7.3e10
        assert rec.metrics[total]["excludes"] == {"2026": {"spending.rare": 1}}
    # A spending head enters the balances negative.
    for total in ("balance.balance", "model.gov_balance"):
        assert published[total] == 5e11 - 7.3e10
        assert rec.metrics[total]["excludes"] == {"2026": {"spending.rare": -1}}
    # Household net income is rebuilt from market income and its parts.
    assert published["household.household_net_income"] == 50_000.0 + 7.3e10
    # A total with no suppressed head is the model's, and marked nothing.
    assert published["model.gov_tax"] == 5e11
    assert "excludes" not in rec.metrics["model.gov_tax"]
    # The raw value is kept off the record.
    assert all(246.9 not in r["values"].values() for r in rec.metrics.values())


@pytest.mark.parametrize("scale", [1.0001, 1.1])
def test_a_total_that_scales_its_heads_gives_nothing_back(scale):
    """Sol re-review 7 of #2335, P2 1: with a tiny uplift in benefits, total
    less head kept a residual of the head within the identity's £1
    tolerance. The rebuilt total is the published heads' sum, exactly."""
    rec, _, _ = _rebuilt(common=20_000.0, rare=1_000.0, scale=scale)
    published = _published(rec)
    assert published["model.household_benefits"] == 20_000.0
    assert published["model.gov_spending"] == 20_000.0
    # A total holding no suppressed head is still the model's own.
    assert published["model.gov_tax"] == scale * 5e11


@settings(max_examples=200, deadline=None)
@given(
    common=st.floats(1e3, 5e11),
    rare=st.floats(-1e10, 1e10),
    other=st.floats(-1e10, 1e10),
    scale=st.floats(0.5, 2.0),
)
def test_no_published_figure_depends_on_a_suppressed_head(common, rare, other, scale):
    """For all values: two datasets that differ only in a suppressed head
    publish exactly the same figures, whatever its size or sign and whatever
    the model's formulas do with it."""
    first, income_1, ex_1 = _rebuilt(common, rare, scale=scale)
    second, income_2, ex_2 = _rebuilt(common, other, scale=scale)
    assert _published(first) == _published(second)
    np.testing.assert_array_equal(income_1, income_2)
    assert ex_1 == ex_2


@settings(max_examples=100, deadline=None)
@given(
    commons=st.lists(st.floats(1e8, 5e11), min_size=2, max_size=6),
    rare=st.floats(0, 4.99e8),
)
def test_repeated_reports_say_nothing_about_a_suppressed_head(commons, rare):
    """Each published total is the published heads' sum in every report, so
    no sequence of reports narrows the suppressed head down."""
    for common in commons:
        published = _published(_rebuilt(common, rare)[0])
        assert published["model.gov_spending"] == published["spending.common"]
        assert published["balance.balance"] == (
            published["receipts.tax"] - published["spending.common"]
        )


def test_income_for_deciles_is_rebuilt_without_suppressed_heads():
    _, income, excludes = _rebuilt(common=900.0, rare=900.0)
    np.testing.assert_array_equal(income, [30_900.0, 20_000.0])
    assert excludes == {"spending.rare": 1}
    # With nothing suppressed, the model's own income is used.
    _, income, excludes = _rebuilt(common=900.0, rare=900.0, records=500)
    assert income is None and excludes == {}


def test_household_net_income_is_suppressed_when_it_cant_be_rebuilt():
    rec, income, excludes = _rebuilt(common=900.0, rare=900.0, market=None)
    assert income is None and excludes == {"spending.rare": 1}
    assert _published(rec)["household.household_net_income"] is None
    assert rec.metrics["household.household_net_income"]["suppressed"] == ["2026"]


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


def test_identities_leave_out_households_holding_a_suppressed_figure():
    """Sol re-review 7 of #2335: with a formula that scales its components,
    whether a holder's household differs, and by how much, depends on the
    suppressed figure. The verdict and detail come from the others only."""
    from policyengine_uk.utils.aggregate_impact.measure import _identity_check

    components = np.full(20, 100.0)
    holding = np.zeros(20, dtype=bool)
    holding[0] = True

    def detail(total, leave_out):
        rec = Recorder()
        _identity_check(
            rec,
            "identity:x",
            "x",
            components,
            total,
            2026,
            load_spec(),
            np.ones(20),
            leave_out=leave_out,
        )
        return rec.checks["identity:x"]

    # Only the holder differs: nothing to report about it.
    only_holder = components.copy()
    only_holder[0] = 5_000.0
    assert detail(only_holder, holding)["status"] == "pass"
    assert detail(only_holder, None)["status"] == "fail"
    # Every household differs: the holder isn't counted or summed.
    scaled = components * 1.1
    (text,) = detail(scaled, holding)["details"]
    assert "19 households differ" in text and "£-190" in text
    assert "aren't checked this year" in text


class StubSim:
    """Every variable household-level, and zero unless given."""

    def __init__(self, values, n=N):
        self.values, self.n = values, n
        entity = SimpleNamespace(key="household")

        class Variables(dict):
            def __missing__(self, key):
                return SimpleNamespace(entity=entity)

        names = set(values) | {
            "gov_tax",
            "gov_spending",
            "gov_balance",
            "household_tax",
            "household_benefits",
            "pre_budget_change_household_tax",
            "household_market_income",
            "household_net_income",
            "pension_contributions",
            "hbai_household_net_income",
            "hbai_household_net_income_before_reset_to_zero",
        }
        self.tax_benefit_system = SimpleNamespace(
            variables=Variables({v: SimpleNamespace(entity=entity) for v in names}),
            parameters=SimpleNamespace(),
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable.endswith("_weight"):
            return np.ones(self.n)
        if variable == "household_id":
            return np.arange(self.n)
        return np.asarray(self.values.get(variable, np.zeros(self.n)), dtype=float)


def _measured_year(values, partition=None):
    from policyengine_uk.utils.aggregate_impact.measure import measure_year
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    rec, households = Recorder(), {}
    rec.scope = "2026"
    measure_year(
        StubSim(values),
        partition or load_partition(default_partition_path()),
        load_spec(),
        2026,
        rec,
        households,
    )
    return rec, households


def _corporate_sdlt_double_counted():
    """The shipped partition in its shape before the #2159 fix: expected_sdlt
    carries corporate SDLT, declared as a double count rather than a head.
    The fix left the model with no double counts, so the tests of how a
    declared one is measured use this."""
    import yaml

    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        parse_partition,
    )

    with open(default_partition_path()) as f:
        raw = yaml.safe_load(f)
    totals = next(h for h in raw["tax_heads"] if h["id"] == "sdlt_corporate")["totals"]
    raw["tax_heads"] = [h for h in raw["tax_heads"] if h["id"] != "sdlt_corporate"]

    def repoint(ids):
        return list(
            dict.fromkeys("sdlt_household" if i == "sdlt_corporate" else i for i in ids)
        )

    for exclusion in raw["exclusions"]:
        if exclusion.get("spans"):
            exclusion["spans"] = repoint(exclusion["spans"])
        if exclusion.get("head") == "sdlt_corporate":
            exclusion["head"] = "sdlt_household"
    for guard in raw["overlap_guards"]:
        guard["heads"] = repoint(guard.get("heads") or [])
    raw["model_double_counts"] = [
        {
            "variable": "corporate_sdlt",
            "contained_in": "expected_sdlt",
            "totals": totals,
        }
    ]
    return parse_partition(raw)


def _first(n, value):
    out = np.zeros(N)
    out[:n] = value
    return out


def test_a_double_count_from_few_records_is_suppressed_and_left_out():
    """Sol re-review 7 of #2335, P2 4: a corporate SDLT double count from one
    record was published, and gov_tax less receipts gave it back too. The
    model's totals here also scale their parts by 10%, so the identities fail
    with a gap that holds it."""
    sdlt = _first(10, 1_000.0)
    corporate = _first(1, 1_234.5)
    sdlt = sdlt + corporate  # expected_sdlt contains corporate_sdlt
    model_tax = 1.1 * (sdlt + corporate)
    rec, _ = _measured_year(
        {
            "expected_sdlt": sdlt,
            "corporate_sdlt": corporate,
            "gov_tax": model_tax,
            "household_tax": model_tax,
            "pre_budget_change_household_tax": model_tax,
            "gov_balance": model_tax,
        },
        _corporate_sdlt_double_counted(),
    )
    published = _published(rec)
    assert published["double_counts.corporate_sdlt"] is None
    assert published["model.gov_tax"] == published["balance.receipts"] == sdlt.sum()
    assert rec.metrics["model.gov_tax"]["excludes"]["2026"] == {
        "double_counts.corporate_sdlt": 1
    }
    assert published["model.gov_balance"] == sdlt.sum()
    assert rec.checks["identity:gov_tax"]["status"] == "fail"
    assert all("£" not in d for d in rec.checks["identity:gov_tax"]["details"])


def test_an_uprated_benefit_total_is_rebuilt_from_its_published_heads():
    """Sol re-review 7 of #2335, P2 1, through measure_year: ten £2,000
    pensions, one suppressed £1,000 DSA award and an uplift of 0.01% in the
    model's totals. The published totals are the pensions' sum exactly."""
    pension = _first(10, 2_000.0)
    dsa = np.zeros(N)
    dsa[10] = 1_000.0
    benefits = 1.0001 * (pension + dsa)
    market = np.full(N, 10_000.0)
    rec, households = _measured_year(
        {
            "state_pension": pension,
            "disabled_students_allowance": dsa,
            "gov_spending": benefits,
            "household_benefits": benefits,
            "gov_balance": -benefits,
            "household_market_income": market,
            "household_net_income": market + benefits,
        }
    )
    published = _published(rec)
    assert published["spending.disabled_students_allowance"] is None
    for total in ("model.gov_spending", "model.household_benefits"):
        assert published[total] == 20_000.0
    assert published["model.gov_balance"] == -20_000.0
    assert published["household.household_net_income"] == market.sum() + 20_000.0
    # The decile incomes leave it out too.
    np.testing.assert_array_equal(households["2026"]["income"], market + pension)
    assert list(households["2026"]["excludes"]) == [
        "spending.disabled_students_allowance"
    ]


AWARDS = st.floats(1.0, 1e6) | st.floats(-1e6, -1.0)


@settings(max_examples=30, deadline=None)
@given(award=AWARDS, other=AWARDS, uplift=st.floats(0.9, 1.1))
def test_no_figure_measure_year_publishes_depends_on_a_suppressed_award(
    award, other, uplift
):
    """For all awards, of either sign, and uplifts: two datasets that differ
    only in one suppressed DSA award publish the same figures, decile
    incomes, check statuses and check details."""

    def run(dsa_award):
        pension = _first(10, 2_000.0)
        dsa = np.zeros(N)
        dsa[10] = dsa_award
        benefits = uplift * (pension + dsa)
        market = np.full(N, 10_000.0)
        return _measured_year(
            {
                "state_pension": pension,
                "disabled_students_allowance": dsa,
                "gov_spending": benefits,
                "household_benefits": benefits,
                "gov_balance": -benefits,
                "household_market_income": market,
                "household_net_income": market + benefits,
            }
        )

    (rec_1, hh_1), (rec_2, hh_2) = run(award), run(other)
    first, second = _published(rec_1), _published(rec_2)
    # The model's own totals that hold the award are never published as such.
    # (A rate with no one in its group is NaN on both sides.)
    assert first.keys() == second.keys()
    for metric_id, value in first.items():
        assert value == second[metric_id] or (
            value is not None and np.isnan(value) and np.isnan(second[metric_id])
        ), metric_id
    np.testing.assert_array_equal(hh_1["2026"]["income"], hh_2["2026"]["income"])
    assert [(c["id"], c["status"], c["details"]) for c in rec_1.checks.values()] == [
        (c["id"], c["status"], c["details"]) for c in rec_2.checks.values()
    ]


class ArraySim:
    """Household arrays by variable for one year; gov_balance is income tax
    less the state pension unless given."""

    def __init__(self, values, n=N):
        self.values, self.n = values, n
        entity = SimpleNamespace(key="household")
        names = set(values) | {"gov_balance", "household_weight"}
        self.tax_benefit_system = SimpleNamespace(
            variables={v: SimpleNamespace(entity=entity) for v in names}
        )

    def calculate(self, variable, period, map_to=None, unweighted=True):
        if variable.endswith("_weight"):
            return np.ones(self.n)
        if variable == "gov_balance" and variable not in self.values:
            return self.values["income_tax"] - self.values["state_pension"]
        return np.asarray(self.values.get(variable, np.zeros(self.n)), dtype=float)


def _pension_partition():
    from policyengine_uk.utils.aggregate_impact.partition import parse_partition

    def head(i, totals):
        return {"id": i, "label": i, "variable": i, "totals": totals}

    return parse_partition(
        {
            "schema_version": 1,
            "totals": {"gov_tax": {}, "gov_spending": {}},
            "tax_heads": [head("income_tax", ["gov_tax"])],
            "spending_heads": [head("state_pension", ["gov_spending"])],
        }
    )


def _reform_run(base, reformed, target="state_pension", year=2026):
    """One reform measured against a baseline year, as measure() runs it."""
    from policyengine_uk.utils.aggregate_impact.measure import (
        _weighted_records,
        baseline_records,
        weighted_total,
    )

    partition = _pension_partition()
    base_sim = ArraySim(base)
    rec = Recorder()
    for head in partition.heads:
        section = "receipts" if head.kind == "tax" else "spending"
        rec.metric(
            f"{section}.{head.id}",
            head.label,
            section,
            "gbp",
            year,
            float(base[head.variable].sum()),
            records=_weighted_records(base[head.variable] != 0, np.ones(N)),
        )
    reform = parse_reforms(
        {
            "reforms": [
                {
                    "name": "Change it",
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
    measure_reforms(
        lambda reform=None: ArraySim(reformed if reform else base),
        None,
        {year: weighted_total(base_sim, "gov_balance", year)},
        {year: {target: weighted_total(base_sim, target, year)}},
        reform,
        [year],
        rec,
        baseline={year: baseline_records(base_sim, partition, rec, year, [target])},
        components=partition.component_variables(),
    )
    costing = rec.metrics["reforms.change_it"]["values"][str(year)]
    change = rec.metrics["reform_targets.change_it"]["values"][str(year)]
    return rec, costing, change


def _world(pensions, tax):
    return {
        "state_pension": np.asarray(pensions, dtype=float),
        "income_tax": np.asarray(tax, dtype=float),
    }


def test_cancelling_changes_to_suppressed_records_publish_nothing():
    """Sol re-review 7 of #2335, P2 2: two suppressed pensions move from
    £1,000 and £2,000 to £1,100 and £1,900, so their total stays £3,000, but
    the first recipient's 20% tax gave a £20 costing, and back the pension."""
    tax = _first(12, 100.0)
    tax[0] = 200.0
    base = _world(_first(2, 0.0) + np.r_[1_000.0, 2_000.0, np.zeros(N - 2)], tax)
    reformed_tax = tax.copy()
    reformed_tax[0] = 220.0
    reformed = _world(np.r_[1_100.0, 1_900.0, np.zeros(N - 2)], reformed_tax)
    rec, costing, change = _reform_run(base, reformed)
    assert costing is None and change is None
    detail = rec.checks["responsive:change_it"]["failing"]["2026"]
    assert "£" not in detail and "withheld" in detail


def test_a_tiny_change_to_a_suppressed_record_publishes_nothing():
    """Sol re-review 7 of #2335, P2 2: a £4 pension uplifted 10% published a
    £0.40 target change under the old £0.50 national threshold."""
    base = _world(_first(1, 4.0), _first(12, 100.0))
    reformed = _world(_first(1, 4.4), _first(12, 100.0))
    _, costing, change = _reform_run(base, reformed)
    assert costing is None and change is None


def test_a_reform_that_leaves_a_small_cell_publishes_nothing():
    """Sol re-review 7 of #2335, P2 3: nine people paying £46 and one £1,486
    of income tax; a £13,000 allowance leaves £1,400 on one record, which
    the −£500 change gave back."""
    tax = np.r_[np.full(9, 46.0), 1_486.0, np.zeros(N - 10)]
    reformed_tax = np.r_[np.zeros(9), 1_400.0, np.zeros(N - 10)]
    pension = np.full(N, 100.0)
    _, costing, change = _reform_run(
        _world(pension, tax), _world(pension, reformed_tax), target="income_tax"
    )
    assert costing is None and change is None


@pytest.mark.parametrize("changed, published", [(3, False), (9, False), (10, True)])
def test_a_reform_costing_from_fewer_than_10_changed_households_is_withheld(
    changed, published
):
    tax = np.full(N, 100.0)
    reformed_tax = tax.copy()
    reformed_tax[:changed] += 10.0
    pension = np.full(N, 100.0)
    _, costing, change = _reform_run(
        _world(pension, tax), _world(pension, reformed_tax), target="income_tax"
    )
    if published:
        assert costing == pytest.approx(10.0 * changed)
        assert change == pytest.approx(10.0 * changed)
    else:
        assert costing is None and change is None


@settings(max_examples=100, deadline=None)
@given(
    pensions=st.lists(st.floats(1.0, 1e5), min_size=1, max_size=9),
    index=st.integers(0, 8),
    change=st.floats(-1e4, 1e4).filter(lambda x: abs(x) > 1e-3),
    cancel=st.booleans(),
)
def test_a_reform_that_touches_a_suppressed_record_publishes_nothing(
    pensions, index, change, cancel
):
    """For all suppressed pensions and any change to one of them, cancelled
    nationally by another or not: neither costing nor target change is
    published."""
    base = _world(np.r_[pensions, np.zeros(N - len(pensions))], np.full(N, 100.0))
    moved = base["state_pension"].copy()
    i = index % len(pensions)
    moved[i] += change
    if cancel and len(pensions) > 1:
        moved[(i + 1) % len(pensions)] -= change
    _, costing, change_published = _reform_run(base, _world(moved, base["income_tax"]))
    assert costing is None and change_published is None


def test_a_reform_without_baseline_records_publishes_nothing():
    rec = Recorder()
    baseline = {2025: 0.0, 2026: 0.0}
    reform = parse_reforms({"reforms": [{"name": "Any", "parameters": {"a": 1}}]})
    measure_reforms(
        lambda reform=None: YearSim({2025: 5.0, 2026: 5.0} if reform else baseline),
        None,
        baseline,
        {},
        reform,
        YEARS,
        rec,
    )
    assert rec.metrics["reforms.any"]["values"] == {"2025": None, "2026": None}


def test_hbai_holds_a_component_only_when_it_is_one_of_its_parts():
    from policyengine_uk.utils.aggregate_impact.measure import hbai_holds_any

    assert not hbai_holds_any({"disabled_students_allowance": ("x", 1.0)})
    assert hbai_holds_any({"child_benefit": ("x", 1.0)})


class HbaiSim:
    """Household-level HBAI pieces: employment income, child benefit and
    council tax, and the model's HBAI income before its reset."""

    def __init__(self, before, council_tax=1_200.0):
        self.values = {
            "employment_income": np.array([20_000.0, 0.0]),
            "child_benefit": np.array([1_234.5, 100.0]),
            "council_tax": np.array([council_tax, 0.0]),
            "hbai_household_net_income_before_reset_to_zero": before,
            "hbai_household_net_income": np.maximum(0.0, before),
        }
        self.tax_benefit_system = SimpleNamespace(variables=self.values)

    def calculate(self, variable, period, map_to=None, unweighted=True):
        return self.values.get(variable, np.zeros(2))


HIDDEN_CB = {"child_benefit": ("spending.child_benefit", 1_334.5)}


def test_hbai_is_rebuilt_without_the_suppressed_component():
    from policyengine_uk.utils.aggregate_impact.measure import _hbai_without

    consistent = np.array([20_000.0 + 1_234.5 - 1_200.0, 100.0])
    values, excludes = _hbai_without(HbaiSim(consistent), 2026, HIDDEN_CB)
    np.testing.assert_array_equal(values, [18_800.0, 0.0])
    assert excludes == {"spending.child_benefit": 1}


@pytest.mark.parametrize("council_tax", [1_200.0, 0.5, 0.01])
def test_hbai_is_suppressed_where_its_lists_dont_reproduce_the_model(council_tax):
    """Sol re-reviews 6 and 7 of #2335: with council tax abolished the model
    leaves it out of HBAI. Even £0.50 of it passed the old £1 tolerance and
    came back in."""
    from policyengine_uk.utils.aggregate_impact.measure import _hbai_without

    abolished = np.array([20_000.0 + 1_234.5, 100.0])
    assert _hbai_without(HbaiSim(abolished, council_tax), 2026, HIDDEN_CB) == (
        None,
        None,
    )


def test_hbai_reproduction_is_not_judged_on_households_holding_the_figure():
    from policyengine_uk.utils.aggregate_impact.measure import _hbai_without

    # The model leaves council tax out for the first household only, which
    # holds the suppressed child benefit: its verdict would depend on it.
    before = np.array([20_000.0 + 1_234.5, 100.0 - 0.0])
    holding = np.array([True, False])
    values, excludes = _hbai_without(HbaiSim(before), 2026, HIDDEN_CB, holding)
    np.testing.assert_array_equal(values, [18_800.0, 0.0])
    assert _hbai_without(HbaiSim(before), 2026, HIDDEN_CB) == (None, None)


def test_a_suppressed_hbai_component_withholds_deciles_poverty_and_the_gini():
    """Households are ranked into deciles on HBAI income: with a suppressed
    child benefit award in it, which decile its holder lands in depends on
    the award."""
    child_benefit = np.zeros(N)
    child_benefit[0] = 1_234.5
    market = np.full(N, 10_000.0)
    rec, households = _measured_year(
        {
            "child_benefit": child_benefit,
            "gov_spending": child_benefit,
            "household_benefits": child_benefit,
            "gov_balance": -child_benefit,
            "household_market_income": market,
            "household_net_income": market + child_benefit,
        }
    )
    assert "2026" not in households
    for record in rec.metrics.values():
        if record["section"] in ("deciles", "poverty", "poverty_count", "inequality"):
            assert record["values"]["2026"] is None, record["id"]
            assert "2026" in record["suppressed"]


@settings(max_examples=100, deadline=None)
@given(award=st.floats(0, 1e5), other=st.floats(0, 1e5))
def test_rebuilt_hbai_never_depends_on_the_suppressed_component(award, other):
    from policyengine_uk.utils.aggregate_impact.measure import _hbai_without

    def rebuilt(cb):
        sim = HbaiSim(np.array([20_000.0 + cb - 1_200.0, 100.0]))
        sim.values["child_benefit"] = np.array([cb, 100.0])
        return _hbai_without(sim, 2026, HIDDEN_CB)[0]

    np.testing.assert_array_equal(rebuilt(award), rebuilt(other))


def test_a_suppressed_heads_sign_and_finite_checks_say_nothing_about_it():
    """Sol re-review 8 of #2335, P3 2: whether one of so few records is
    negative is about it alone, and a count of non-finite values under 10 is
    a small cell."""
    dsa = np.zeros(N)
    dsa[10] = -1_000.0
    rec, _ = _measured_year({"disabled_students_allowance": dsa})
    sign = rec.checks["sign:disabled_students_allowance"]
    assert sign["status"] == "skipped"
    assert "fewer than 10 records" in sign["details"][0]
    dsa[10] = np.nan
    rec, _ = _measured_year({"disabled_students_allowance": dsa})
    (detail,) = rec.checks["finite:disabled_students_allowance"]["details"]
    assert "fewer than 10 non-finite values" in detail


@pytest.mark.parametrize("corporate", [1_234.5, 1_000.0])
def test_the_overlap_guard_leaves_out_households_holding_a_suppressed_figure(
    corporate,
):
    """Sol re-review 8 of #2335, P3 3: a one-record corporate SDLT in a
    household also paying LBTT moved the count from 9 to 10 households."""
    sdlt = _first(10, 1_000.0)
    lbtt = _first(10, 500.0)
    holder_corporate = np.zeros(N)
    holder_corporate[0] = corporate
    # The holder's SDLT is all corporate when corporate is 1,000, so its own
    # SDLT nets to zero and it would not overlap.
    sdlt[0] = max(corporate, 1_000.0)
    rec, _ = _measured_year(
        {
            "expected_sdlt": sdlt,
            "expected_lbtt": lbtt,
            "corporate_sdlt": holder_corporate,
        }
    )
    check = rec.checks["overlap_guard:property_transaction_tax_geography"]
    (detail,) = check["details"]
    assert "fewer than 10 households have more than one" in detail
    assert "aren't checked this year" in detail


def test_the_published_guard_strips_a_few_unit_double_count_coefficient():
    """Sol re-review 8 of #2335, P3 4."""
    from policyengine_uk.utils.aggregate_impact.measure import publishable_guard

    def guard(units):
        return {
            "components": [
                {"variable": "corporate_sdlt", "units": units, "status": "pass"}
            ],
            "double_counts": [
                {
                    "variable": "corporate_sdlt",
                    "contained_in": "expected_sdlt",
                    "coefficient": 0.4321,
                    "status": "fail",
                    "detail": "expected_sdlt moves by 0.4321 per unit of corporate_sdlt",
                }
            ],
        }

    (few,) = publishable_guard(guard(3))["double_counts"]
    assert few["coefficient"] is None and "0.4321" not in few["detail"]
    assert "fewer than 10 units" in few["detail"]
    (many,) = publishable_guard(guard(500))["double_counts"]
    assert many["coefficient"] == 0.4321 and "0.4321" in many["detail"]
    # Sol delta review 9 of #2335, P2: the comment must render it.
    from policyengine_uk.utils.aggregate_impact.render import _guard

    for units, shown in (
        (3, "coefficient not shown, fewer than 10 units"),
        (500, "coefficient 0.432"),
    ):
        published = {
            "status": "ran",
            "year": 2026,
            "components": [],
            **publishable_guard(guard(units)),
        }
        published["double_counts"][0]["issue"] = "#2159"
        text = _guard({"head": {"guard": published}})
        assert shown in text and "NO LONGER contained" in text
        if units == 3:
            assert "0.43" not in text


def test_certified_guard_failure_message_excludes_private_fields():
    """A failed invariant stays failed, with no raw survey detail in its message."""
    from policyengine_uk.tests.aggregate_impact import test_aggregate_impact_certified
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    partition = load_partition(default_partition_path())
    row = {
        "variable": partition.tax_heads[0].variable,
        "status": "fail",
        "problems": [
            {
                "total": "gov_tax",
                "head": "income_tax",
                "kind": "own_head",
                "households": 3,
                "where": np.array([True, False]),
                "share": 0.123456,
            }
        ],
        "detail": "SECRET_C4_household_amount",
        "household_id": "SECRET_C4_household_id",
        "responses": {"SECRET_C4_response": 1_234.5},
    }
    measured = (
        {
            "guard": {
                "status": "ran",
                "reset_reproduces_baseline": True,
                "components": [row],
            }
        },
        None,
        partition,
        None,
    )
    with pytest.raises(AssertionError) as error:
        test_aggregate_impact_certified.test_every_tax_component_is_counted_exactly_once(
            measured
        )
    message = str(error.value)
    assert "SECRET_C4" not in message
    assert "income_tax" in message and "own_head" in message
    assert "where" not in message and "share" not in message


@pytest.mark.parametrize(
    "slot", ["variable", "status", "total", "head", "kind", "households"]
)
def test_guard_component_diagnostic_rejects_untrusted_slot_values(slot):
    """An allowed key cannot smuggle an object or an arbitrary private string."""
    import json

    from policyengine_uk.utils.aggregate_impact.measure import (
        component_guard_diagnostic,
    )
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    class Unprintable:
        def __str__(self):
            raise AssertionError("SECRET_C4_str_was_called")

        __repr__ = __str__
        __hash__ = __str__

        def __eq__(self, other):
            raise AssertionError("SECRET_C4_eq_was_called")

        def __int__(self):
            raise AssertionError("SECRET_C4_int_was_called")

    class UntrustedString(str):
        def __str__(self):
            raise AssertionError("SECRET_C4_subclass_was_printed")

    partition = load_partition(default_partition_path())
    for value in ("SECRET_C4", Unprintable(), UntrustedString("income_tax")):
        problem = {
            "total": "gov_tax",
            "head": "income_tax",
            "kind": "own_head",
            "households": 10,
        }
        row = {"variable": "income_tax", "status": "fail", "problems": [problem]}
        if slot in ("variable", "status"):
            row[slot] = value
        else:
            problem[slot] = value
        diagnostic = component_guard_diagnostic(row, partition)
        rendered = json.dumps(diagnostic)
        assert "SECRET_C4" not in rendered
        field = (
            diagnostic[slot]
            if slot in ("variable", "status")
            else diagnostic["problems"][0][slot]
        )
        assert field == (None if slot == "households" else "unknown")


@pytest.mark.parametrize(
    "count,shown",
    [
        (0, 0),
        (3, None),
        (9, None),
        (10, 10),
        (100, 100),
        (None, None),
        (True, None),
        (3.5, None),
    ],
)
def test_guard_component_diagnostic_preserves_suppressed_counts(count, shown):
    from policyengine_uk.utils.aggregate_impact.measure import (
        component_guard_diagnostic,
    )
    from policyengine_uk.utils.aggregate_impact.partition import (
        default_partition_path,
        load_partition,
    )

    partition = load_partition(default_partition_path())
    row = {
        "variable": "income_tax",
        "status": "fail",
        "units": 100,
        "problems": [
            {
                "total": "gov_tax",
                "head": "income_tax",
                "kind": "own_head",
                "households": count,
            }
        ],
    }
    diagnostic = component_guard_diagnostic(row, partition)
    assert diagnostic == {
        "variable": "income_tax",
        "status": "fail",
        "problems": [
            {
                "total": "gov_tax",
                "head": "income_tax",
                "kind": "own_head",
                "households": shown,
            }
        ],
    }
