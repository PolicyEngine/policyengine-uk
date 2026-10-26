"""Tax-benefit systems share their variables' code, and nothing else.

Each Simulation builds a new tax-benefit system. From 3.33.12,
policyengine-core compiles each variable file once per process and every
system runs that code (PolicyEngine/policyengine-core#608). Coverage's
sys.monitoring core, which CI uses, keeps every code object it has seen alive,
so code compiled again for every system used to fill the CI shards' memory.
Until core shared it, the test conftest did the sharing itself.

Systems must still get their own modules, classes and functions, and compute
the same results.
"""

import sys

from policyengine_uk import Simulation

# A variable with a formula. income_tax itself adds this and the winter fuel
# payment charge, so it has no formula of its own.
FORMULA_VARIABLE = "income_tax_before_winter_fuel_payment_charge"
SITUATION = {
    "people": {"adult": {"age": {2026: 40}, "employment_income": {2026: 30_000}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}


def _formula(simulation):
    variable = simulation.tax_benefit_system.variables[FORMULA_VARIABLE]
    return variable.get_formula()


def test_systems_share_code_but_not_modules_classes_or_functions():
    first = Simulation(situation=SITUATION)
    second = Simulation(situation=SITUATION)
    first_class = type(first.tax_benefit_system.variables[FORMULA_VARIABLE])
    second_class = type(second.tax_benefit_system.variables[FORMULA_VARIABLE])
    first_formula = _formula(first)
    second_formula = _formula(second)

    assert first_class is not second_class
    assert (
        sys.modules[first_class.__module__]
        is not (sys.modules[second_class.__module__])
    )
    assert first_formula is not second_formula
    assert first_formula.__globals__ is not second_formula.__globals__
    assert first_formula.__code__ is second_formula.__code__
    assert first.calculate("income_tax", 2026) == second.calculate("income_tax", 2026)
