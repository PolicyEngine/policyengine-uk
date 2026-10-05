import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation


class abolish_child_benefit_charge(Reform):
    def apply(self):
        self.neutralize_variable("CB_HITC")


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize(
    "reform",
    [
        abolish_child_benefit_charge,
        {
            "gov.hmrc.income_tax.charges.CB_HITC.phase_out_start": {"2026": 100_000},
            "gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {"2026": 120_000},
        },
    ],
)
def test_removing_charge_restores_payment_without_changing_baseline(reform):
    situation = {
        "people": {
            "parent": {"age": {2026: 40}, "adjusted_net_income": {2026: 90_000}},
            "child": {"age": {2026: 5}},
        },
        "benunits": {
            "family": {
                "members": ["parent", "child"],
                "child_benefit_opts_out": {2026: True},
            }
        },
        "households": {"home": {"members": ["parent", "child"]}},
    }
    simulation = Simulation(situation=situation, reform=reform)
    entitlement = simulation.calculate("child_benefit_entitlement", 2026)[0]
    assert entitlement > 0
    assert simulation.baseline.calculate("child_benefit", 2026)[0] == 0
    assert simulation.calculate("child_benefit", 2026)[0] == entitlement
    assert simulation.calculate("CB_HITC", 2026).sum() == 0
    assert simulation.baseline.calculate("child_benefit", 2026)[0] == 0
