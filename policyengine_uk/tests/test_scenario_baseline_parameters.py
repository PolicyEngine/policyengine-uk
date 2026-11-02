"""A Scenario's parameter changes must not leak into ``parameters.baseline``.

``Simulation.apply_parameter_changes`` reloads and reprocesses the parameter
tree. Before #2188 it cloned the baseline child from the already reformed
tree, so ``baseline_vat`` and ``adjust_budgets`` compared a reform with
itself.
"""

import numpy as np
import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.reforms.policyengine.adjust_budgets import adjust_budgets
from policyengine_uk.system import system

VAT = "gov.hmrc.vat.standard_rate"

SITUATION = {
    "people": {"adult": {"age": {2026: 40}}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "full_rate_vat_consumption": {2026: 10_000},
            "reduced_rate_vat_consumption": {2026: 0},
        }
    },
}


def _vat_change(sim):
    return float(sim.calculate("vat", 2026)[0] - sim.calculate("baseline_vat", 2026)[0])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scenario": Scenario(parameter_changes={VAT: 0.22})},
        {"scenario": Scenario(parameter_changes={VAT: {"2026": 0.22}})},
        {"reform": {VAT: 0.22}},
        {
            "reform": Reform.from_dict(
                {VAT: {"2000-01-01.2100-12-31": 0.22}}, country_id="uk"
            )
        },
    ],
    ids=["scenario-scalar", "scenario-year", "reform-dict", "core-reform"],
)
def test_every_reform_route_scores_vat_against_the_unreformed_baseline(kwargs):
    sim = Simulation(situation=SITUATION, **kwargs)
    # All spending here is standard-rated, so raising the rate from 20% to
    # 22% raises VAT by a tenth, whatever the grossing factor (526.32 at the
    # current factor).
    unreformed_vat = float(Simulation(situation=SITUATION).calculate("vat", 2026)[0])
    assert _vat_change(sim) == pytest.approx(0.1 * unreformed_vat, abs=0.01)
    assert _vat_change(sim) > 0
    assert sim.tax_benefit_system.parameters.baseline.gov.hmrc.vat.standard_rate(
        "2026-06-01"
    ) == pytest.approx(0.2)


def test_no_reform_has_no_vat_change():
    assert _vat_change(Simulation(situation=SITUATION)) == 0


@pytest.mark.parametrize(
    "path, instant",
    [
        (VAT, "2026-06-01"),
        ("gov.hmrc.income_tax.allowances.personal_allowance.amount", "2028-06-01"),
        ("gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD", "2029-06-01"),
        ("gov.hmrc.fuel_duty.petrol_and_diesel", "2027-02-01"),
        ("gov.dfe.education_spending", "2027-01-01"),
    ],
)
def test_scenario_leaves_the_baseline_tree_identical_to_an_unreformed_system(
    path, instant
):
    changes = {
        VAT: 0.25,
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": 15_000,
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD": 500,
        "gov.hmrc.fuel_duty.petrol_and_diesel": 0.70,
        "gov.dfe.education_spending": 150,
    }
    sim = Simulation(situation=SITUATION, scenario=Scenario(parameter_changes=changes))
    reformed = sim.tax_benefit_system.parameters
    unreformed = system.parameters
    assert reformed.baseline.get_child(path)(instant) == pytest.approx(
        unreformed.baseline.get_child(path)(instant)
    )
    # The reform itself still reaches the processed tree.
    assert reformed.get_child(path)(instant) != pytest.approx(
        unreformed.get_child(path)(instant)
    )


def test_adjust_budgets_sees_a_scenario_spending_change():
    sim = Simulation(
        situation=SITUATION,
        scenario=Scenario(parameter_changes={"gov.dfe.education_spending": 150}),
    )
    assert adjust_budgets(sim.tax_benefit_system.parameters, 2026) is not None
    assert adjust_budgets(system.parameters, 2026) is None


# Juaristi22's review of #2193 (C1): once the baseline tree stayed unreformed,
# a before-load Scenario spending change registered the budget adjustment, and
# Simulation and Microsimulation stopped constructing because the adjustment
# read ``self.simulation`` from a tax-benefit system that never had one.

DFE = "gov.dfe.education_spending"
ALLOCATION = 1e9  # Synthetic £1bn allocation: routing only, not an estimate.

BUDGET_SITUATION = {
    "people": {
        "adult": {"age": {2026: 40}, "employment_income": {2026: 30_000}},
    },
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {
        "household": {
            "members": ["adult"],
            "region": {2026: "LONDON"},
            "dfe_education_spending": {2026: ALLOCATION},
            # Fixed weights, so the Microsimulation's weighted total equals
            # the allocation in every year.
            "household_weight": {year: 1.0 for year in range(2023, 2030)},
        }
    },
}

BEFORE_LOAD_DFE_150 = Scenario(
    parameter_changes={DFE: 150}, applied_before_data_load=True
)


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_before_load_spending_scenario_constructs(simulation_class):
    sim = simulation_class(situation=BUDGET_SITUATION, scenario=BEFORE_LOAD_DFE_150)
    net_income = np.asarray(sim.calculate("household_net_income", 2026))
    assert np.isfinite(net_income).all()
    assert np.isfinite(
        np.asarray(sim.baseline.calculate("household_net_income", 2026))
    ).all()


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_before_load_spending_scenario_scales_the_allocation(simulation_class):
    sim = simulation_class(situation=BUDGET_SITUATION, scenario=BEFORE_LOAD_DFE_150)
    parameters = sim.tax_benefit_system.parameters
    for year in range(2026, 2030):
        baseline_budget = parameters.baseline.gov.dfe.education_spending(year)
        assert parameters.gov.dfe.education_spending(year) == 150
        assert baseline_budget < 150
        # The allocation is scaled so its total rises by the budget change
        # (in £bn) for each year on its own, without carrying an earlier
        # year's change forward.
        expected = ALLOCATION + (150 - baseline_budget) * 1e9
        reformed = np.asarray(sim.calculate("dfe_education_spending", year))
        assert reformed[0] == pytest.approx(expected, rel=1e-6)
        baseline = np.asarray(sim.baseline.calculate("dfe_education_spending", year))
        assert baseline[0] == pytest.approx(ALLOCATION)
    # 2026: £150bn against the unreformed £107.28bn.
    assert np.asarray(sim.calculate("dfe_education_spending", 2026))[0] == (
        pytest.approx(43.7207e9, rel=1e-5)
    )
    # No allocation before 2026, so there is nothing to scale there.
    for year in range(2023, 2026):
        assert np.asarray(sim.calculate("dfe_education_spending", year))[0] == 0
    # Other budgets are untouched.
    for variable in ("nhs_spending", "dft_subsidy_spending"):
        assert np.asarray(sim.calculate(variable, 2026))[0] == pytest.approx(
            np.asarray(sim.baseline.calculate(variable, 2026))[0]
        )


def test_structural_reforms_can_read_the_simulation_they_are_applied_to():
    # adjust_budgets and disable_simulated_benefits read ``self.simulation``
    # inside Reform.apply, where ``self`` is the tax-benefit system.
    seen = []

    class reads_simulation(Reform):
        def apply(self):
            seen.append(self.simulation)

    sim = Simulation(situation=SITUATION)
    sim.apply_reform(reads_simulation)
    clone = sim.clone()
    clone.apply_reform(reads_simulation)
    assert seen == [sim, clone]


@pytest.mark.microsimulation
def test_before_load_spending_scenario_constructs_on_the_dataset():
    sim = Microsimulation(scenario=BEFORE_LOAD_DFE_150)
    year = 2026
    parameters = sim.tax_benefit_system.parameters
    budget_change = 150 - parameters.baseline.gov.dfe.education_spending(year)
    weights = np.asarray(sim.calculate("household_weight", year, unweighted=True))
    reformed = np.asarray(sim.calculate("dfe_education_spending", year))
    # ``sim.baseline`` is a plain Simulation, so weight its values here.
    baseline = np.asarray(sim.baseline.calculate("dfe_education_spending", year))
    reformed_total = (reformed * weights).sum() / 1e9
    baseline_total = (baseline * weights).sum() / 1e9
    assert baseline_total > 0
    assert reformed_total == pytest.approx(baseline_total + budget_change, rel=1e-4)
    assert np.isfinite(np.asarray(sim.calculate("household_net_income", year))).all()
