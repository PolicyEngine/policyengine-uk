"""War Widow's Pension has its own variable, separate from bsp_reported (#2381).

Datasets built so far fill bsp_reported from FRS benefit codes 6 (Bereavement
Support Payment or Widowed Parent's Allowance) and 9 (War Widow's or Widower's
Pension). BSP rates have been frozen since April 2017, but war widow's pension
rises each April with September CPI under the Service Pensions (Amendment)
Orders, and in FRS 2024-25 it is about 90% of the combined value. Freezing
bsp_reported is only safe once datasets move code 9 into
war_widows_pension_reported, so that variable must exist, be projected by CPI
and count wherever BSP counts.
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

# Every aggregate that counts BSP must count war widow's pension too, or moving
# code 9 out of bsp_reported would drop it from income and spending.
AGGREGATES_THAT_COUNT_BSP = (
    "household_benefits",
    "hbai_household_net_income",
    "gov_spending",
)


def test_war_widows_pension_reported_is_projected_by_cpi():
    listed = yaml.safe_load(UPRATING_INDICES.read_text())
    indices = sorted(
        index
        for index, variables in listed.items()
        if "war_widows_pension_reported" in variables
    )
    assert indices == [CPI_GROWTH]


def test_war_widows_pension_reported_declares_cpi_uprating():
    sim = Simulation(situation={"people": {"widow": {"age": 70}}})
    variable = sim.tax_benefit_system.variables["war_widows_pension_reported"]
    assert variable.uprating == CPI_INDEX


@pytest.mark.parametrize("aggregate", AGGREGATES_THAT_COUNT_BSP)
def test_war_widows_pension_counts_wherever_bsp_does(aggregate):
    def value(person_inputs):
        sim = Simulation(
            situation={
                "people": {"widow": {"age": 70, **person_inputs}},
                "benunits": {"benunit": {"members": ["widow"]}},
                "households": {"household": {"members": ["widow"]}},
            }
        )
        return sim.calculate(aggregate, 2026).sum()

    base = value({})
    assert value({"bsp_reported": {2026: 5_000}}) - base == pytest.approx(5_000)
    assert value({"war_widows_pension_reported": {2026: 5_000}}) - base == (
        pytest.approx(5_000)
    )


def test_projected_war_widows_pension_grows_with_cpi():
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [70],
                "war_widows_pension_reported": [10_000.0],
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
    expected = 10_000.0 * np.prod([1 + CPI(str(year)) for year in range(2025, 2030)])
    assert sim.calculate("war_widows_pension", 2029).iloc[0] == pytest.approx(expected)
    assert expected > 10_000.0
