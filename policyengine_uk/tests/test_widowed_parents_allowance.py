"""Widowed Parent's Allowance has its own variable, apart from bsp_reported.

FRS benefit code 6 is "Bereavement Support Payment / Widowed Parent's
Allowance", and datasets put it in bsp_reported. Bereavement Support Payment
is tax-free, is not Universal Credit unearned income and has frozen rates.
Widowed Parent's Allowance is taxable (ITEPA 2003 s.577), is UC unearned
income (UC Regs 2013 reg. 66(1)(b)(vi)) and rises with CPI. Once datasets
split code 6, the allowance needs its own CPI-projected input that counts
wherever Bereavement Support Payment counts, and in tax and UC as well.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from policyengine_uk import Microsimulation, Simulation, parameters
from policyengine_uk.data import UKSingleYearDataset

UPRATING_INDICES = Path(__file__).parents[1] / "data" / "uprating_indices.yaml"
CPI_GROWTH = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
CPI_INDEX = "gov.economic_assumptions.indices.obr.consumer_price_index"
CPI = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index
AGGREGATES_THAT_COUNT_BSP = (
    "household_benefits",
    "hbai_household_net_income",
    "gov_spending",
)
WEEKLY_RATE_2026 = 156.65


def test_widowed_parents_allowance_reported_is_projected_by_cpi():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    indices = sorted(
        index
        for index, variables in listed.items()
        if "widowed_parents_allowance_reported" in variables
    )
    assert indices == [CPI_GROWTH]


def test_widowed_parents_allowance_reported_declares_cpi_uprating():
    sim = Simulation(situation={"people": {"parent": {"age": 40}}})
    variable = sim.tax_benefit_system.variables["widowed_parents_allowance_reported"]
    assert variable.uprating == CPI_INDEX


def single_parent(inputs, **benunit):
    return Simulation(
        situation={
            "people": {
                "parent": {"age": 40, **{k: {2026: v} for k, v in inputs.items()}},
                "child": {"age": 5},
            },
            "benunits": {"benunit": {"members": ["parent", "child"], **benunit}},
            "households": {
                "household": {
                    "members": ["parent", "child"],
                    "country": "ENGLAND",
                    "tenure_type": "RENT_PRIVATELY",
                    "rent": 9_000,
                }
            },
        }
    )


@pytest.mark.parametrize("aggregate", AGGREGATES_THAT_COUNT_BSP)
def test_widowed_parents_allowance_counts_wherever_bsp_does(aggregate):
    # A £20,000 earner who does not claim Universal Credit gets no
    # means-tested benefit, so each aggregate moves by the payment. The
    # allowance is taxable at the basic rate here, so HBAI income gains 80%
    # of it; Bereavement Support Payment is untaxed.
    def value(inputs):
        sim = Simulation(
            situation={
                "people": {
                    "parent": {
                        "age": 40,
                        "employment_income": {2026: 20_000},
                        **{k: {2026: v} for k, v in inputs.items()},
                    }
                },
                "benunits": {
                    "benunit": {"members": ["parent"], "would_claim_uc": False}
                },
                "households": {
                    "household": {"members": ["parent"], "country": "ENGLAND"}
                },
            }
        )
        return sim.calculate(aggregate, 2026).sum()

    base = value({})
    amount = WEEKLY_RATE_2026 * 52
    assert value({"bsp_reported": amount}) - base == pytest.approx(amount, abs=0.01)
    expected = amount * (0.8 if aggregate == "hbai_household_net_income" else 1)
    assert value({"widowed_parents_allowance_reported": amount}) - base == (
        pytest.approx(expected, abs=0.01)
    )


def test_universal_credit_falls_by_the_allowance_and_not_by_bsp():
    amount = WEEKLY_RATE_2026 * 52

    def uc(inputs):
        return single_parent(inputs).calculate("universal_credit", 2026).sum()

    base = uc({})
    assert base > amount
    assert uc({"widowed_parents_allowance_reported": amount}) - base == (
        pytest.approx(-amount, abs=0.01)
    )
    assert uc({"bsp_reported": amount}) == pytest.approx(base, abs=0.01)


def test_projected_widowed_parents_allowance_grows_with_cpi():
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
                "widowed_parents_allowance_reported": [8_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1.0],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "rent": [0.0],
                "council_tax": [0.0],
            }
        ),
        fiscal_year=2024,
    )
    sim = Microsimulation(dataset=dataset)
    expected = 8_000.0 * np.prod([1 + CPI(str(year)) for year in range(2025, 2030)])
    assert sim.calculate("widowed_parents_allowance", 2029).iloc[0] == (
        pytest.approx(expected)
    )
    assert expected > 8_000.0
