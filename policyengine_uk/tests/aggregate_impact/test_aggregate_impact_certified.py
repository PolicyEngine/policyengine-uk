"""The aggregate-impact measurement on the certified dataset.

One year, the counted-once check on every tax component plus a few benefits.
Runs where microsimulation tests run (see conftest's data mode).
"""

import dataclasses

import numpy as np
import pytest

from policyengine_uk.utils.aggregate_impact.measure import measure
from policyengine_uk.utils.aggregate_impact.partition import (
    default_partition_path,
    load_partition,
)
from policyengine_uk.utils.aggregate_impact.reforms import load_reforms, parameter_node
from policyengine_uk.utils.aggregate_impact.spec import load_spec

pytestmark = pytest.mark.microsimulation

YEAR = 2026
# Components whose rise raises another benefit: a known model defect each.
# When one is fixed this test fails until its entry is removed. Empty since
# #2365 counted statutory sick, maternity and paternity pay as UC earnings.
KNOWN_RISING_WITH_INCOME: set = set()
# incapacity_benefit raises Universal Credit only through Carer's Allowance
# (#2424), which the check must report as mediated, not fail.
SPENDING_SAMPLE = {
    "state_pension",
    "universal_credit",
    "child_benefit",
    "statutory_sick_pay",
    "incapacity_benefit",
}


@pytest.fixture(scope="module")
def measured():
    from policyengine_uk import Microsimulation

    sim = Microsimulation()
    dataset = sim.dataset
    partition = load_partition(default_partition_path())
    spec = dataclasses.replace(
        load_spec(), first_year=YEAR, last_year=YEAR, guard_year=YEAR
    )
    tax_components = {h.variable for h in partition.tax_heads} | {
        d.variable for d in partition.double_counts
    }
    result, households = measure(
        sim,
        lambda reform=None: Microsimulation(dataset=dataset, reform=reform),
        partition,
        spec,
        label="test",
        reforms=[r for r in load_reforms() if r.scale],
        guard_variables=tax_components | SPENDING_SAMPLE,
    )
    return result, households, partition, Microsimulation(dataset=dataset)


def checks(result, prefix):
    return [c for c in result["checks"] if c["id"].startswith(prefix)]


def test_accounting_identities_and_closure_hold(measured):
    result, _, _, _ = measured
    assert result["status"] == "ok"
    for prefix in (
        "closure",
        "identity:",
        "finite:",
        "weights:",
        "bounds:",
        "determinism:",
    ):
        failing = [c for c in checks(result, prefix) if c["status"] != "pass"]
        assert failing == [], failing


def test_every_tax_component_is_counted_exactly_once(measured):
    result, _, partition, _ = measured
    guard = result["guard"]
    assert guard["status"] == "ran" and guard["reset_reproduces_baseline"]
    rows = {r["variable"]: r for r in guard["components"]}
    for head in partition.tax_heads:
        row = rows[head.variable]
        assert row["status"] == "pass", row
        for total, k in row["coefficients"].items():
            assert k == pytest.approx(1, abs=1e-3), (head.id, total)


def test_declared_double_counts_are_still_double_counted_by_the_model(measured):
    result, _, partition, _ = measured
    rows = {r["variable"]: r for r in result["guard"]["components"]}
    for declared in partition.double_counts:
        present = next(
            d
            for d in result["guard"]["double_counts"]
            if d["variable"] == declared.variable
        )
        assert present["status"] == "pass", present
        for total in declared.totals:
            assert rows[declared.variable]["model_coefficients"][
                total
            ] == pytest.approx(2, abs=1e-3)


def test_spending_never_rises_by_more_than_is_added_except_known_defects(measured):
    result, _, _, _ = measured
    rows = {r["variable"]: r for r in result["guard"]["components"]}
    for variable in SPENDING_SAMPLE:
        row = rows[variable]
        if variable in KNOWN_RISING_WITH_INCOME:
            assert (
                row["status"] == "fail"
                and 1 < row["coefficients"]["gov_spending"] < 1.05
            )
        else:
            assert row["status"] == "pass", row


def test_head_totals_agree_with_the_model_weighted_sums(measured):
    result, _, partition, sim = measured
    metrics = {m["id"]: m for m in result["metrics"]}
    for head in partition.heads:
        section = "receipts" if head.kind == "tax" else "spending"
        metric = metrics[f"{section}.{head.id}"]
        if str(YEAR) in metric.get("suppressed", ()):
            # Too few records to publish (privacy.py): only the count is checked.
            records = int(np.count_nonzero(sim.calculate(head.variable, YEAR).values))
            assert 0 < records < 10, head.id
            continue
        ours = metric["values"][str(YEAR)]
        theirs = float(sim.calculate(head.variable, YEAR).sum())
        assert ours == pytest.approx(theirs, rel=1e-6, abs=1e3), head.id
    receipts = metrics["balance.receipts"]["values"][str(YEAR)]
    model = metrics["model.gov_tax"]["values"][str(YEAR)]
    double_counted = sum(
        metrics[f"double_counts.{d.variable}"]["values"][str(YEAR)]
        for d in partition.double_counts
        if "gov_tax" in d.totals
    )
    assert receipts + double_counted == pytest.approx(model, rel=1e-9)


def test_household_detail_is_complete(measured):
    _, households, _, _ = measured
    columns = households[str(YEAR)]
    n = len(columns["household_id"])
    assert all(len(v) == n for v in columns.values())
    # Scalars only: a failing assertion on an array would print household
    # values into public CI logs.
    non_finite = int((~np.isfinite(columns["income"])).sum())
    assert non_finite == 0, f"{non_finite} households have a non-finite income"
    outside = int((~np.isin(columns["decile"], np.arange(-1, 11))).sum())
    assert outside == 0, f"{outside} households have a decile outside -1 to 10"


def test_relative_reforms_scale_their_parameters_and_move_their_targets(measured):
    result, _, _, sim = measured
    passing = {c["id"] for c in result["checks"] if c["status"] == "pass"}
    relative = [r for r in load_reforms() if r.scale]
    assert {r.id for r in relative} == {
        "uc_standard_allowance_plus_10pc",
        "state_pension_plus_10pc",
    }
    outcomes = {o["id"]: o for o in result["reforms"]}
    for reform in relative:
        assert f"reform_runs:{reform.id}" in passing
        assert f"responsive:{reform.id}" in passing
        for path, factor in reform.scale.items():
            baseline = parameter_node(sim.tax_benefit_system.parameters, path)(
                f"{YEAR}-01-01"
            )
            assert outcomes[reform.id]["parameters"][path][str(YEAR)] == pytest.approx(
                baseline * factor
            )


def test_the_published_result_holds_aggregates_only(measured):
    """result.json may be public: no household-length arrays, no single values."""
    result, households, _, _ = measured
    n_households = len(households[str(YEAR)]["household_id"])

    def numeric_lists(node):
        if isinstance(node, dict):
            for value in node.values():
                yield from numeric_lists(value)
        elif isinstance(node, list):
            if node and all(isinstance(v, (int, float)) for v in node):
                yield node
            for value in node:
                yield from numeric_lists(value)

    longest = max((len(values) for values in numeric_lists(result)), default=0)
    assert longest <= 50 < n_households
    details = " ".join(d for c in result["checks"] for d in c["details"])
    assert "minimum £" not in details and "largest gap" not in details


def test_geographic_guards_hold_once_declared_double_counts_are_netted(measured):
    """Council tax and domestic rates never meet; nor do SDLT, LTT and LBTT
    once corporate SDLT, which expected_sdlt carries while #2159 is open, is
    netted out of it as a declared double count."""
    result, _, _, _ = measured
    status = {c["id"]: c["status"] for c in result["checks"]}
    assert status["overlap_guard:local_tax_geography"] == "pass"
    assert status["overlap_guard:property_transaction_tax_geography"] == "pass"
