import numpy as np
import pandas as pd
import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset


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
        {"gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {"2026": float("inf")}},
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


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize("income", [59_999, 60_000, 60_001])
@pytest.mark.parametrize("opts_out", [False, True])
@pytest.mark.parametrize("taper_end", [50_000, 60_000])
def test_cliff_charge_has_no_division_warnings(income, opts_out, taper_end):
    """Degenerate taper reforms charge fully only above their start threshold."""
    simulation = Simulation(
        situation={
            "people": {
                "parent": {"age": {2026: 40}, "adjusted_net_income": {2026: income}},
                "child": {"age": {2026: 5}},
            },
            "benunits": {
                "family": {
                    "members": ["parent", "child"],
                    "child_benefit_opts_out": {2026: opts_out},
                }
            },
            "households": {"home": {"members": ["parent", "child"]}},
        },
        reform={
            "gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {"2026": taper_end}
        },
    )
    with np.errstate(divide="raise", invalid="raise"):
        payment = simulation.calculate("child_benefit", 2026)[0]
        charge = simulation.calculate("CB_HITC", 2026).sum()
    entitlement = simulation.calculate("child_benefit_entitlement", 2026)[0]
    assert payment == (0 if opts_out and income > 60_000 else entitlement)
    assert charge == (payment if income > 60_000 else 0)


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize(
    "reform, payment, charge",
    [
        (None, 0, 0),
        (abolish_child_benefit_charge, 2_337.40, 0),
        (
            {
                "gov.hmrc.income_tax.charges.CB_HITC.phase_out_start": {
                    "2026": 200_000
                },
                "gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {"2026": 220_000},
            },
            2_337.40,
            0,
        ),
        (
            {
                "gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {
                    "2026": float("inf")
                }
            },
            2_337.40,
            0,
        ),
        (
            {"gov.hmrc.income_tax.charges.CB_HITC.phase_out_end": {"2026": 10_000_000}},
            2_337.40,
            2_337.40 * 40_000 / 9_940_000,
        ),
    ],
)
def test_dataset_opted_out_claimants_resume_but_nonclaimants_do_not(
    reform, payment, charge
):
    """Microcosm #1089 stores claim-and-not-opted-out in its would-claim column."""
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2, 3, 4, 5, 6],
                "person_benunit_id": [1, 1, 1, 2, 2, 2],
                "person_household_id": [1, 1, 1, 2, 2, 2],
                "age": [40, 8, 5, 40, 8, 5],
                "adjusted_net_income": [100_000, 0, 0, 100_000, 0, 0],
            }
        ),
        benunit=pd.DataFrame(
            {
                "benunit_id": [1, 2],
                "would_claim_child_benefit": [False, False],
                "child_benefit_opts_out": [True, False],
            }
        ),
        household=pd.DataFrame(
            {"household_id": [1, 2], "region": ["SOUTH_EAST", "SOUTH_EAST"]}
        ),
        fiscal_year=2026,
    )
    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[dataset]), reform=reform
    )
    assert simulation.calculate("child_benefit_entitlement", 2026) == pytest.approx(
        [2_337.40, 2_337.40], abs=0.01
    )
    assert simulation.baseline.calculate("child_benefit", 2026) == pytest.approx([0, 0])
    assert simulation.calculate("child_benefit", 2026) == pytest.approx(
        [payment, 0], abs=0.01
    )
    assert simulation.calculate("CB_HITC", 2026) == pytest.approx(
        [charge, 0, 0, 0, 0, 0], abs=0.01
    )
    assert simulation.baseline.calculate("child_benefit", 2026) == pytest.approx([0, 0])
