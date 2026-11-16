"""Share earnings-tax counterfactuals across PC and UC housing calculations."""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.tests.test_uc_non_dep_pension_credit import YEAR, mixed_families


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

# SPC Regs 2002 reg. 17A(2)(h) and (i) make statutory sick, maternity and
# paternity pay earnings of an employed earner, so the tax on them is tax on
# employed earnings and both counterfactuals remove them with wages.
EMPLOYED_EARNINGS = (
    "employment_income",
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
)


def earnings_families():
    situation = mixed_families()
    for name, wages, profit in (
        ("tenant", 18_000, 1_000),
        ("pc_older", 1_000, 2_000),
        ("pc_younger", 0, 100),
        ("working_non_dep", 10_000, 0),
        ("renter_older", 1_000, 1_000),
        ("renter_younger", 0, 0),
    ):
        situation["people"][name]["employment_income"] = {YEAR: wages}
        situation["people"][name]["self_employment_income"] = {YEAR: profit}
    situation["people"]["pc_older"]["statutory_sick_pay"] = {YEAR: 500}
    return situation


def count_counterfactuals(monkeypatch, sim):
    variable = sim.tax_benefit_system.variables[
        "pension_credit_income_tax_without_earnings"
    ]
    namespace = variable.get_formula(YEAR).__globals__
    original = namespace["income_tax_with_inputs_zeroed"]
    calls = []

    def counted(simulation, period, variables):
        calls.append((simulation.branch_name, tuple(variables)))
        return original(simulation, period, variables)

    monkeypatch.setitem(namespace, "income_tax_with_inputs_zeroed", counted)
    return calls


@pytest.mark.parametrize("first", ["pension_credit", "household_net_income"])
def test_full_calculation_reuses_two_earnings_tax_counterfactuals(monkeypatch, first):
    sim = Simulation(situation=earnings_families())
    calls = count_counterfactuals(monkeypatch, sim)
    sim.calculate(first, YEAR)
    sim.calculate("household_net_income", YEAR)
    sim.calculate("pension_credit", YEAR)
    # Employed earnings (wages and statutory sick pay) and self-employment
    # are present. The UC housing non-dependant check shares the two
    # counterfactuals with ordinary PC.
    assert calls == [
        ("default", EMPLOYED_EARNINGS),
        ("default", EMPLOYED_EARNINGS + ("self_employment_income",)),
    ]
    assert sim.branches == {}


def test_earnings_tax_reuse_preserves_calculation_order_and_changed_inputs():
    pc_first = Simulation(situation=earnings_families())
    income_first = Simulation(situation=earnings_families())
    pc_first.calculate("pension_credit", YEAR)
    income_first.calculate("household_net_income", YEAR)
    outputs = (
        "household_net_income",
        "pension_credit",
        "pension_credit_income",
        "pension_credit_employment_income_tax",
        "pension_credit_self_employment_income_tax",
        "uc_non_dep_receives_pension_credit",
        "universal_credit",
    )
    for name in outputs:
        np.testing.assert_allclose(
            pc_first.calculate(name, YEAR),
            income_first.calculate(name, YEAR),
            atol=0.01,
            rtol=0,
        )
    wages = [18_000, 50_000, 0, 10_000, 1_000, 0]
    pc_first.set_input("employment_income", YEAR, wages)
    pc_first.drop_computed_arrays()
    changed_situation = earnings_families()
    changed_situation["people"]["pc_older"]["employment_income"] = {YEAR: 50_000}
    fresh = Simulation(situation=changed_situation)
    for name in outputs:
        np.testing.assert_allclose(
            pc_first.calculate(name, YEAR),
            fresh.calculate(name, YEAR),
            atol=0.01,
            rtol=0,
        )
    assert not pc_first.calculate("uc_non_dep_receives_pension_credit", YEAR)[1]
    assert pc_first.branches == {}
