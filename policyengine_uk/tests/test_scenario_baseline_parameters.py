"""A Scenario's parameter changes must not leak into ``parameters.baseline``.

``Simulation.apply_parameter_changes`` reloads and reprocesses the parameter
tree. Before #2188 it cloned the baseline child from the already reformed
tree, so ``baseline_vat`` and ``adjust_budgets`` compared a reform with
itself.
"""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
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
    assert _vat_change(sim) == pytest.approx(526.32, abs=0.01)
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
