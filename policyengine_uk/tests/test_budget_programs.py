"""The budget totals add exactly the budget terms in programs.yaml.

household_tax adds the programs.yaml terms flagged ``budget: tax`` and
household_benefits those flagged ``budget: benefit``, in ``budget_order``.
These tests read the YAML without policyengine_uk.programs and check:

1. Drift: the variables each total's formula reads are exactly the flagged
   terms, less those whose ``budget_dropped_when`` parameter is true, and
   household_tax reads them in ``budget_order``.
2. Differential: HOUSEHOLD_TAX_VARIABLES and HOUSEHOLD_BENEFIT_VARIABLES
   equal, in order, the lists the formula modules held as literals at commit
   2da212abcf2086337fc088a4a1236f4ae7b6af63, and the council tax and
   uprating rules match the ones those formulas applied.
3. budget_programs() returns the same records in a fresh interpreter,
   whichever module that interpreter imports first.
4. Properties (Hypothesis): every budget_programs() variable exists, none
   repeats, and each sign agrees with the list it came from; on generated
   registries, the loader keeps budget_order's order and refuses a registry
   whose flags and order disagree.
"""

import json
import subprocess
import sys

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.programs import (
    REGISTRY_PATH,
    BudgetProgram,
    RegistryError,
    build_budget_programs,
    budget_programs,
    budget_variables,
)
from policyengine_uk.variables.gov.hmrc.household_tax import HOUSEHOLD_TAX_VARIABLES
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

SYSTEM = CountryTaxBenefitSystem()
RAW = yaml.safe_load(REGISTRY_PATH.read_text())
ABOLISH_COUNCIL_TAX = "gov.contrib.abolish_council_tax"
LISTS = {"tax": HOUSEHOLD_TAX_VARIABLES, "benefit": HOUSEHOLD_BENEFIT_VARIABLES}
TOTALS = {"tax": "household_tax", "benefit": "household_benefits"}

# The lists as household_tax.py and household_benefits.py held them at
# commit 2da212ab, before the totals read programs.yaml.
MAIN_HOUSEHOLD_TAX_VARIABLES = [
    "isa_cash_interest_flat_rate_charge",
    "expected_sdlt",
    "expected_ltt",
    "expected_lbtt",
    "corporate_sdlt",
    "business_rates",
    "council_tax",
    "high_value_council_tax_surcharge",
    "domestic_rates",
    "fuel_duty",
    "alcohol_duty",
    "tobacco_duty",
    "gambling_duty",
    "vehicle_excise_duty",
    "tv_licence",
    "wealth_tax",
    "non_primary_residence_wealth_tax",
    "income_tax",
    "national_insurance",
    "LVT",
    "carbon_tax",
    "vat_change",
    "capital_gains_tax",
    "private_school_vat_change",
    "corporate_incident_tax_revenue_change",
    "consumer_incident_tax_revenue_change",
    "employer_ni_response_capital_incidence",
    "employer_ni_response_consumer_incidence",
    "student_loan_repayments",
]

MAIN_HOUSEHOLD_BENEFIT_VARIABLES = [
    "child_benefit",
    "council_tax_benefit",
    "esa_income",
    "esa_contrib",
    "housing_benefit",
    "income_support",
    "jsa_income",
    "jsa_contrib",
    "pension_credit",
    "universal_credit",
    "working_tax_credit",
    "child_tax_credit",
    "attendance_allowance",
    "afcs",
    "bsp",
    "war_widows_pension",
    "widowed_parents_allowance",
    "carers_allowance",
    "dla",
    "iidb",
    "incapacity_benefit",
    "pip",
    "sda",
    "state_pension",
    "maternity_allowance",
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
    "ssmg",
    "basic_income",
    "epg_subsidy",
    "cost_of_living_support_payment",
    "energy_bills_rebate",
    "household_energy_payment",
    "winter_fuel_allowance",
    "pawhp",
    "tax_free_childcare",
    "extended_childcare_entitlement",
    "universal_childcare_entitlement",
    "targeted_childcare_entitlement",
    "wales_childcare_offer",
    "care_to_learn",
    "childcare_grant",
    "parents_learning_allowance",
    "adult_dependants_grant",
    "travel_grant",
    "disabled_students_allowance",
    "bursary_fund_16_to_19",
    "nhs_spending",
    "dfe_education_spending",
    "dft_subsidy_spending",
    "healthy_start_vouchers",
    "two_child_limit_payment",
    "scottish_child_payment",
    "carer_support_payment",
    "scottish_carer_supplement",
    "disability_basic_income",
]

# The rules those formulas applied: abolishing council tax removed these
# terms, the non_sp uprating left out the State Pension, and neither uprating
# scaled basic income.
MAIN_DROPPED_WHEN_ABOLISHING_COUNCIL_TAX = {
    "council_tax",
    "high_value_council_tax_surcharge",
    "council_tax_benefit",
}
MAIN_UPRATING_EXCEPTIONS = {"state_pension": ("all",), "basic_income": ()}


def flagged(budget):
    """Variables the raw YAML flags with ``budget``, from both sections."""
    entries = RAW["programs"] + RAW["budget_terms"]
    return [entry["variable"] for entry in entries if entry.get("budget") == budget]


# 1. Drift


@pytest.mark.parametrize("budget", ["tax", "benefit"])
def test_registry_flags_are_the_listed_terms(budget):
    names = flagged(budget)
    assert len(names) == len(set(names))
    assert sorted(names) == sorted(LISTS[budget])
    assert RAW["budget_order"][budget] == LISTS[budget]


def read_by_formula(total, reform):
    """The variables ``total``'s formula reads, in the order it reads them."""
    year = 2026
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {year: 40}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {"household": {"members": ["adult"]}},
        },
        reform=reform or None,
    )
    sim.trace = True
    sim.calculate(total, year)
    (root,) = [tree for tree in sim.tracer.trees if tree.name == total]
    return [child.name for child in root.children]


@pytest.mark.parametrize("abolish", [False, True], ids=["current_law", "abolished"])
@pytest.mark.parametrize("budget", ["tax", "benefit"])
def test_totals_read_exactly_the_registry_terms(budget, abolish):
    reform = {ABOLISH_COUNCIL_TAX: True} if abolish else {}
    expected = [
        name
        for name in RAW["budget_order"][budget]
        if not (abolish and name in MAIN_DROPPED_WHEN_ABOLISHING_COUNCIL_TAX)
    ]
    read = read_by_formula(TOTALS[budget], reform)
    assert set(read) == set(expected)
    if budget == "tax":
        # household_tax makes one add() call, so the reads are its order.
        assert read == expected


# 2. Differential against main


def test_household_tax_variables_equal_main():
    assert HOUSEHOLD_TAX_VARIABLES == MAIN_HOUSEHOLD_TAX_VARIABLES
    assert budget_variables("tax") == MAIN_HOUSEHOLD_TAX_VARIABLES


def test_household_benefit_variables_equal_main():
    assert HOUSEHOLD_BENEFIT_VARIABLES == MAIN_HOUSEHOLD_BENEFIT_VARIABLES
    assert budget_variables("benefit") == MAIN_HOUSEHOLD_BENEFIT_VARIABLES


def test_council_tax_and_uprating_rules_equal_main():
    dropped = {p.variable for p in budget_programs() if p.dropped_when}
    assert dropped == MAIN_DROPPED_WHEN_ABOLISHING_COUNCIL_TAX
    assert {p.dropped_when for p in budget_programs() if p.dropped_when} == {
        ABOLISH_COUNCIL_TAX
    }
    for program in budget_programs():
        if program.is_tax:
            assert program.uprating == ()
        else:
            expected = MAIN_UPRATING_EXCEPTIONS.get(program.variable, ("all", "non_sp"))
            assert program.uprating == expected, program.variable


# 3. Fresh interpreter

FRESH_SCRIPT = """
import dataclasses, json, sys
if sys.argv[1] == "programs":
    from policyengine_uk.programs import budget_programs
elif sys.argv[1] == "household_tax":
    from policyengine_uk.variables.gov.hmrc.household_tax import HOUSEHOLD_TAX_VARIABLES
    from policyengine_uk.programs import budget_programs
else:
    import policyengine_uk
    budget_programs = policyengine_uk.programs.budget_programs
print(json.dumps([dataclasses.asdict(p) for p in budget_programs()]))
"""


@pytest.mark.parametrize("first_import", ["programs", "household_tax", "package"])
def test_budget_programs_in_a_fresh_interpreter(first_import):
    result = subprocess.run(
        [sys.executable, "-c", FRESH_SCRIPT, first_import],
        capture_output=True,
        text=True,
        check=True,
    )
    fresh = json.loads(result.stdout.strip().splitlines()[-1])
    here = [
        {**program.__dict__, "uprating": list(program.uprating)}
        for program in budget_programs()
    ]
    assert fresh == here


def test_budget_programs_have_labels_and_kinds():
    for program in budget_programs():
        assert isinstance(program, BudgetProgram)
        assert program.label.strip()
        assert program.kind in {
            "programme",
            "programme_measure",
            "reform_measure",
            "public_service",
        }
        if program.kind == "programme_measure":
            assert program.program is not None
    ids = {entry["id"] for entry in RAW["programs"]}
    non_programmes = [p for p in budget_programs() if not p.is_programme]
    assert {p.variable for p in non_programmes} >= {
        "vat_change",
        "employer_ni_response_capital_incidence",
        "employer_ni_response_consumer_incidence",
    }
    # A term that is not a programme never sits in the coverage list.
    coverage_variables = {entry.get("variable") for entry in RAW["programs"]}
    assert not {p.variable for p in non_programmes} & coverage_variables
    assert all(p.program in ids for p in budget_programs() if p.program)


# 4. Properties

PROGRAMS = budget_programs()


@settings(max_examples=50, deadline=None, derandomize=True)
@given(st.sampled_from(PROGRAMS))
def test_each_budget_program_exists_once_with_its_list_sign(program):
    assert program.variable in SYSTEM.variables
    assert [p.variable for p in PROGRAMS].count(program.variable) == 1
    assert program.budget in ("tax", "benefit")
    own, other = (
        (HOUSEHOLD_TAX_VARIABLES, HOUSEHOLD_BENEFIT_VARIABLES)
        if program.is_tax
        else (HOUSEHOLD_BENEFIT_VARIABLES, HOUSEHOLD_TAX_VARIABLES)
    )
    assert program.variable in own
    assert program.variable not in other


names = st.text(alphabet="abcdefghij_", min_size=1, max_size=8)


@st.composite
def registries(draw):
    """A registry with flagged terms in both sections and a shuffled order."""
    variables = draw(st.lists(names, min_size=1, max_size=12, unique=True))
    budgets = [draw(st.sampled_from(["tax", "benefit"])) for _ in variables]
    in_programs = [draw(st.booleans()) for _ in variables]
    programs, terms = [], []
    for variable, budget, listed in zip(variables, budgets, in_programs):
        entry = {"variable": variable, "name": variable.title(), "budget": budget}
        if listed:
            programs.append({"id": f"id_{variable}", **entry})
        else:
            terms.append({**entry, "kind": "reform_measure"})
    order = {
        budget: draw(
            st.permutations([v for v, b in zip(variables, budgets) if b == budget])
        )
        for budget in ("tax", "benefit")
    }
    return {"programs": programs, "budget_terms": terms, "budget_order": order}


@settings(max_examples=100, deadline=None, derandomize=True)
@given(registries())
def test_loader_keeps_budget_order_and_signs(registry):
    built = build_budget_programs(registry)
    for budget in ("tax", "benefit"):
        assert [p.variable for p in built if p.budget == budget] == list(
            registry["budget_order"][budget]
        )
    variables = [p.variable for p in built]
    assert len(variables) == len(set(variables))
    # Taxes come before benefits.
    kinds = [p.budget for p in built]
    assert kinds == sorted(kinds, key=["tax", "benefit"].index)


@settings(max_examples=100, deadline=None, derandomize=True)
@given(registries(), st.data())
def test_loader_refuses_order_that_disagrees_with_flags(registry, data):
    budget = data.draw(
        st.sampled_from([b for b in ("tax", "benefit") if registry["budget_order"][b]])
    )
    order = list(registry["budget_order"][budget])
    if data.draw(st.booleans()):
        order.pop(data.draw(st.integers(0, len(order) - 1)))
    else:
        order.append(data.draw(st.sampled_from(order)))
    broken = {**registry, "budget_order": {**registry["budget_order"], budget: order}}
    with pytest.raises(RegistryError):
        build_budget_programs(broken)
