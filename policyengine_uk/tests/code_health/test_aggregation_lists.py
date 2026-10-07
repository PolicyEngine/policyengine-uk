"""Lists of variable names must not repeat an entry.

policyengine-core's add() and the adds/subtracts attributes sum every entry in
a list, so a name listed twice is counted twice. HOUSEHOLD_BENEFIT_VARIABLES
listed "jsa_contrib" twice, which counted contributory JSA twice in
household_benefits, household_net_income and household_gross_income. A
duplicate in a membership list (such as a qualifying-benefits parameter) is
harmless today but becomes a double count as soon as the list is summed.

These tests cover every such list in the package: the named aggregation
constants, every variable's adds and subtracts (including those given as a
parameter path), every list literal of variable names in the package source,
and every list-valued parameter of strings.
"""

import ast
from collections import Counter
from pathlib import Path

import pytest
from policyengine_core.parameters import Parameter

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.variables.contrib.policyengine.pre_budget_change_household_benefits import (
    PRE_BUDGET_CHANGE_HOUSEHOLD_BENEFIT_VARIABLES,
)
from policyengine_uk.variables.gov.gov_spending import GOV_SPENDING_VARIABLES
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
    HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS,
)
from policyengine_uk.variables.household.income.household_benefits import (
    HOUSEHOLD_BENEFIT_VARIABLES,
)

PACKAGE = Path(__file__).parents[2]
SYSTEM = CountryTaxBenefitSystem()


def duplicates(names):
    return sorted(name for name, count in Counter(names).items() if count > 1)


@pytest.mark.parametrize(
    "name, names",
    [
        ("HOUSEHOLD_BENEFIT_VARIABLES", HOUSEHOLD_BENEFIT_VARIABLES),
        (
            "PRE_BUDGET_CHANGE_HOUSEHOLD_BENEFIT_VARIABLES",
            PRE_BUDGET_CHANGE_HOUSEHOLD_BENEFIT_VARIABLES,
        ),
        ("GOV_SPENDING_VARIABLES", GOV_SPENDING_VARIABLES),
        ("HBAI_HOUSEHOLD_NET_INCOME_ADDS", HBAI_HOUSEHOLD_NET_INCOME_ADDS),
        ("HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS", HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS),
    ],
)
def test_named_aggregation_lists_have_no_duplicates(name, names):
    assert not duplicates(names), f"{name} repeats {duplicates(names)}"
    unknown = sorted(set(names) - set(SYSTEM.variables))
    assert not unknown, f"{name} names unknown variables {unknown}"


def test_variable_adds_and_subtracts_have_no_duplicates():
    offenders = []
    for name, variable in SYSTEM.variables.items():
        for attribute in ("adds", "subtracts"):
            listed = getattr(variable, attribute, None)
            if listed is None:
                continue
            if isinstance(listed, str):
                # A parameter path: check every value the list has taken.
                parameter = SYSTEM.parameters.get_child(listed)
                for value in parameter.values_list:
                    repeated = duplicates(value.value)
                    if repeated:
                        offenders.append(
                            f"{name}.{attribute} ({value.instant_str}): {repeated}"
                        )
            elif duplicates(listed):
                offenders.append(f"{name}.{attribute}: {duplicates(listed)}")
    assert not offenders, "\n".join(offenders)


def _string_list_literals(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and len(node.elts) > 1:
            if all(
                isinstance(element, ast.Constant) and isinstance(element.value, str)
                for element in node.elts
            ):
                yield node.lineno, [element.value for element in node.elts]


def test_variable_name_list_literals_have_no_duplicates():
    # Catches lists that are not attached to a variable, such as the list
    # passed to add() in a formula or a module-level constant.
    offenders = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if "tests" in path.relative_to(PACKAGE).parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for lineno, names in _string_list_literals(tree):
            if not set(names) <= set(SYSTEM.variables):
                continue
            if duplicates(names):
                relative = path.relative_to(PACKAGE.parent)
                offenders.append(f"{relative}:{lineno}: {duplicates(names)}")
    assert not offenders, "\n".join(offenders)


def test_string_list_parameters_have_no_duplicates():
    offenders = []
    for parameter in SYSTEM.parameters.get_descendants():
        if not isinstance(parameter, Parameter):
            continue
        for value in parameter.values_list:
            listed = value.value
            if not isinstance(listed, list):
                continue
            if not all(isinstance(item, str) for item in listed):
                continue
            if duplicates(listed):
                offenders.append(
                    f"{parameter.name} ({value.instant_str}): {duplicates(listed)}"
                )
    assert not offenders, "\n".join(offenders)
