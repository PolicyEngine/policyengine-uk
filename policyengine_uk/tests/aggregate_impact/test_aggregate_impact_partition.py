"""The fiscal partition against the model's own component lists.

These run without data. The partition was written from the receipts
classification and each variable's formula; closure compares it with
GOV_TAX_VARIABLES and its siblings, which are a second, independent statement
of the same totals.
"""

import copy

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.aggregate_impact.partition import (
    PartitionError,
    closure_problems,
    default_partition_path,
    group_label,
    load_partition,
    parse_partition,
    read_model_lists,
    structural_problems,
)

PATH = default_partition_path()


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.fixture(scope="module")
def shipped():
    return load_partition(PATH)


@pytest.fixture(scope="module")
def raw():
    with open(PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def model_lists(shipped):
    lists, problems = read_model_lists(shipped)
    assert not problems
    return lists


def test_shipped_partition_is_found_and_loads(shipped):
    assert PATH is not None and PATH.name == "fiscal_partition.yaml"
    assert shipped.schema_version == 1
    assert shipped.tax_heads and shipped.spending_heads


def test_every_model_total_is_exactly_its_heads_and_declared_double_counts(
    shipped, model_lists, system
):
    assert set(model_lists) == {
        "gov_tax",
        "household_tax",
        "pre_budget_change_household_tax",
        "gov_spending",
        "household_benefits",
    }
    assert closure_problems(shipped, model_lists, system.variables) == []


def test_every_head_is_a_money_variable_with_its_declared_entity(shipped, system):
    for head in shipped.heads:
        variable = system.variables[head.variable]
        assert variable.value_type is float, head.id
        assert variable.definition_period in ("year", "month"), head.id
        assert head.entity == variable.entity.key, head.id


def test_receipts_and_spending_are_separate(shipped):
    for head in shipped.tax_heads:
        assert not set(head.totals) & {"gov_spending", "household_benefits"}
    for head in shipped.spending_heads:
        assert not set(head.totals) & {"gov_tax", "household_tax"}


def test_spending_exclusions_name_known_variables_and_spending_heads(raw, system):
    spending_heads = {head["id"] for head in raw["spending_heads"]}
    head_variables = {
        head["variable"] for head in raw["tax_heads"] + raw["spending_heads"]
    }
    exclusions = raw["exclusions"] + raw["spending_exclusions"]
    excluded_variables = [entry["variable"] for entry in exclusions]
    assert len(excluded_variables) == len(set(excluded_variables))
    assert not head_variables & set(excluded_variables)
    for entry in raw["spending_exclusions"]:
        assert entry["variable"] in system.variables, entry
        assert entry["head"] in spending_heads, entry
        assert entry["kind"] in {"component", "assessment"}, entry
        assert entry["note"], entry


def test_budget_and_energy_support_variables_have_fiscal_classifications(raw):
    # These tax, earnings and payment helpers must have an explicit owner;
    # adding a head for a component would count the same receipt twice.
    variables = {
        "carers_allowance_weekly_earnings_above_limit",
        "pension_tax_allowance",
        "household_energy_payment",
        "miscellaneous_income_trading_allowance_deduction",
        "uses_trading_allowance",
        "miscellaneous_income_before_trading_allowance",
        "income_not_otherwise_charged",
        "income_tax_charges",
        "income_tax_reductions",
        "machine_games_standard_rate_higher_stake_net_takings",
        "ebr_alternative_fuel_payment",
        "monthly_ebr_alternative_fuel_payment",
    }
    classified = [
        entry["variable"]
        for section in (
            "tax_heads",
            "spending_heads",
            "exclusions",
            "spending_exclusions",
        )
        for entry in raw[section]
    ]
    assert variables <= set(classified)
    assert all(classified.count(variable) == 1 for variable in variables)


def test_dropped_when_matches_the_council_tax_abolition_formulas(shipped):
    switch = "gov.contrib.abolish_council_tax"
    assert shipped.dropped("gov_tax", [switch]) == {
        "council_tax",
        "high_value_council_tax_surcharge",
    }
    assert shipped.dropped("gov_spending", [switch]) == {"council_tax_benefit"}
    assert shipped.dropped("gov_tax") == set()
    assert set(shipped.components("gov_tax")) - set(
        shipped.components("gov_tax", [switch])
    ) == {"council_tax", "high_value_council_tax_surcharge"}


def test_group_labels_read_as_sentence_case():
    assert group_label("excise_duties") == "Excise duties"
    assert group_label("Income tax and NICs") == "Income tax and NICs"


def _remove_head(raw, head_id):
    """The partition without one head and every reference to it."""
    out = copy.deepcopy(raw)
    removed = next(
        h for h in raw["tax_heads"] + raw["spending_heads"] if h["id"] == head_id
    )
    for key in ("tax_heads", "spending_heads"):
        out[key] = [h for h in out[key] if h["id"] != head_id]
        for head in out[key]:
            if head.get("reads"):
                head["reads"] = [r for r in head["reads"] if r.get("head") != head_id]
    out["exclusions"] = [
        e
        for e in out.get("exclusions") or []
        if e.get("head") != head_id and head_id not in (e.get("spans") or [])
    ]
    out["model_double_counts"] = [
        d
        for d in out.get("model_double_counts") or []
        if d["contained_in"] != removed["variable"]
    ]
    for guard in out.get("overlap_guards") or []:
        if isinstance(guard, dict) and guard.get("heads"):
            guard["heads"] = [h for h in guard["heads"] if h != head_id]
            if (
                guard.get("kind") == "geographic_exclusivity"
                and len(guard["heads"]) < 2
            ):
                guard["kind"] = "removed_with_head"
    for spec in (out.get("totals") or {}).values():
        for parameter, variables in ((spec or {}).get("dropped_when") or {}).items():
            spec["dropped_when"][parameter] = [
                v for v in variables if v != removed["variable"]
            ]
    return out


def _mutations(raw):
    """Each yields a partition dict that a check must reject, and which check."""
    out = []
    a = copy.deepcopy(raw)
    a["tax_heads"][1]["variable"] = a["tax_heads"][0]["variable"]
    out.append(("duplicate head variable", a, "structural"))
    out.append(
        ("missing head", _remove_head(raw, raw["tax_heads"][0]["id"]), "closure")
    )
    c = copy.deepcopy(raw)
    c["spending_heads"].append(
        {
            "id": "not_a_model_component",
            "label": "x",
            "variable": "employment_income",
            "totals": ["gov_spending"],
        }
    )
    out.append(("extra component", c, "closure"))
    d = copy.deepcopy(raw)
    if d.get("model_double_counts"):
        d["model_double_counts"][0]["contained_in"] = "vat"
        out.append(("double count in a total its container is not in", d, "structural"))
    e = copy.deepcopy(raw)
    e["tax_heads"][0]["totals"] = list(e["tax_heads"][0]["totals"]) + ["gov_spending"]
    out.append(("tax head in a spending total", e, "structural"))
    f = copy.deepcopy(raw)
    f["tax_heads"][0]["id"] = f["tax_heads"][1]["id"]
    out.append(("duplicate head id", f, "structural"))
    return out


def test_each_kind_of_broken_partition_is_rejected(raw, model_lists, system):
    for name, mutated, check in _mutations(raw):
        if check == "structural":
            with pytest.raises(PartitionError):
                parse_partition(mutated)
        else:
            partition = parse_partition(mutated)
            assert closure_problems(partition, model_lists, system.variables), name


@settings(max_examples=30, deadline=None)
@given(data=st.data())
def test_component_sets_do_not_depend_on_head_order(raw, data):
    shuffled = copy.deepcopy(raw)
    shuffled["tax_heads"] = data.draw(st.permutations(shuffled["tax_heads"]))
    shuffled["spending_heads"] = data.draw(st.permutations(shuffled["spending_heads"]))
    a, b = parse_partition(raw), parse_partition(shuffled)
    for total in a.totals:
        assert sorted(a.components(total)) == sorted(b.components(total))


@settings(max_examples=30, deadline=None)
@given(data=st.data())
def test_removing_any_head_breaks_closure_of_each_total_it_was_in(
    raw, model_lists, data
):
    heads = raw["tax_heads"] + raw["spending_heads"]
    removed = heads[data.draw(st.integers(0, len(heads) - 1))]
    problems = closure_problems(
        parse_partition(_remove_head(raw, removed["id"])), model_lists
    )
    for total in removed["totals"]:
        assert any(total in p and removed["variable"] in p for p in problems)


def test_structural_checks_pass_on_the_shipped_file(shipped):
    assert structural_problems(shipped) == []


def test_a_geographic_guard_must_name_two_known_heads(raw):
    for heads in ([], ["council_tax"], ["council_tax", "no_such_head"]):
        mutated = copy.deepcopy(raw)
        mutated["overlap_guards"] = [
            {"id": "g", "kind": "geographic_exclusivity", "heads": heads}
        ]
        with pytest.raises(PartitionError):
            parse_partition(mutated)
