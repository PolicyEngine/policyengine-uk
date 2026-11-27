"""The worked examples in docs/book/usage/firm-reforms.md.

Each fixture runs the code from one section of the page, and each test checks
a figure the page states. Keep the two in step: a change here needs the same
change on the page.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2026


def values(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR))


# Raise the corporation tax main rate


@pytest.fixture(scope="module")
def main_rate_sim():
    firms = {
        "large_company": {"firm_taxable_trading_profit": {2026: 2_000_000}},
        "mid_company": {"firm_taxable_trading_profit": {2026: 150_000}},
        "small_company": {"firm_taxable_trading_profit": {2026: 40_000}},
        "sole_trader": {
            "firm_legal_form": "SOLE_TRADER",
            "firm_taxable_trading_profit": {2026: 80_000},
        },
    }
    reform = {"gov.hmrc.corporation_tax.main_rate": {"2026-01-01.2100-12-31": 0.27}}

    return Simulation(situation={"firms": firms}, reform=reform)


def test_main_rate_baseline(main_rate_sim):
    # 25% x 2,000,000; 25% x 150,000 - 3/200 x 100,000; 19% x 40,000; none.
    assert values(main_rate_sim.baseline, "corporation_tax") == pytest.approx(
        [500_000, 36_000, 7_600, 0], abs=0.01
    )


def test_main_rate_reform(main_rate_sim):
    # 27% x 2,000,000; 27% x 150,000 - 1,500; small profits rate; none.
    assert values(main_rate_sim, "corporation_tax") == pytest.approx(
        [540_000, 39_000, 7_600, 0], abs=0.01
    )


def test_main_rate_leaves_marginal_relief_unchanged(main_rate_sim):
    for simulation in (main_rate_sim, main_rate_sim.baseline):
        assert values(simulation, "firm_marginal_relief") == pytest.approx(
            [0, 1_500, 0, 0], abs=0.01
        )


# Change the main-pool writing-down allowance


@pytest.fixture(scope="module")
def wda_sim():
    firms = {
        "manufacturer": {
            "firm_taxable_trading_profit": {2026: 1_000_000},
            "firm_main_pool_brought_forward": {2026: 500_000},
        },
        "workshop": {
            "firm_taxable_trading_profit": {2026: 100_000},
            "firm_main_pool_brought_forward": {2026: 200_000},
        },
    }
    reform = {
        "gov.hmrc.corporation_tax.capital_allowances.writing_down_allowance.main_rate": {
            "2026-01-01.2100-12-31": 0.18
        }
    }

    return Simulation(situation={"firms": firms}, reform=reform)


WDA_EXPECTED = {
    # 14% and 18% of 500,000 and 200,000.
    "firm_main_pool_writing_down_allowance": ([70_000, 28_000], [90_000, 36_000]),
    "firm_taxable_profit": ([930_000, 72_000], [910_000, 64_000]),
    # Manufacturer: 25% of taxable profit. Workshop: 25% x 72,000 -
    # 3/200 x 178,000 = 15,330; 25% x 64,000 - 3/200 x 186,000 = 13,210.
    "corporation_tax": ([232_500, 15_330], [227_500, 13_210]),
    "firm_main_pool_carried_forward": ([430_000, 172_000], [410_000, 164_000]),
}


@pytest.mark.parametrize("variable", sorted(WDA_EXPECTED))
def test_wda(wda_sim, variable):
    baseline, reformed = WDA_EXPECTED[variable]
    assert values(wda_sim.baseline, variable) == pytest.approx(baseline, abs=0.01)
    assert values(wda_sim, variable) == pytest.approx(reformed, abs=0.01)


def test_wda_tax_change(wda_sim):
    change = values(wda_sim, "corporation_tax") - values(
        wda_sim.baseline, "corporation_tax"
    )
    # 25% x 20,000 and 26.5% x 8,000.
    assert change == pytest.approx([-5_000, -2_120], abs=0.01)


# Cut the Employment Allowance and allocate the change to households


@pytest.fixture(scope="module")
def allowance_sim():
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [30, 50],
                "employment_income": [25_000.0, 75_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "household_weight": [1_000.0, 1_000.0],
                "region": "LONDON",
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 0.0,
                "corporate_sector_wealth": [0.0, 100_000.0],
                "consumption": [20_000.0, 30_000.0],
            }
        ),
        firm=pd.DataFrame(
            {
                "firm_id": [1, 2, 3],
                "firm_weight": [100.0, 300.0, 50.0],
                "firm_paybill": [2_000_000.0, 150_000.0, 60_000.0],
                "firm_employees": [40.0, 5.0, 2.0],
            }
        ),
        fiscal_year=2026,
    )
    reform = {
        "gov.hmrc.national_insurance.employment_allowance.amount": {
            "2026-01-01.2100-12-31": 5_000
        },
        "gov.contrib.policyengine.firm_incidence.capital": {
            "2026-01-01.2100-12-31": 0.5
        },
        "gov.contrib.policyengine.firm_incidence.consumer": {
            "2026-01-01.2100-12-31": 0.25
        },
        "gov.contrib.policyengine.firm_incidence.labour": {
            "2026-01-01.2100-12-31": 0.25
        },
    }

    return Microsimulation(dataset=dataset, reform=reform)


HOUSEHOLD_WEIGHT = 1_000


def test_allowance_employer_ni_before_allowance(allowance_sim):
    # 15% x (pay - 5,000 per employee): 1,800,000; 125,000; 50,000.
    assert values(allowance_sim, "firm_employer_ni_before_allowance") == pytest.approx(
        [270_000, 18_750, 7_500], abs=0.01
    )


def test_allowance_amounts(allowance_sim):
    assert values(allowance_sim.baseline, "employment_allowance") == pytest.approx(
        [10_500, 10_500, 7_500], abs=0.01
    )
    assert values(allowance_sim, "employment_allowance") == pytest.approx(
        [5_000, 5_000, 5_000], abs=0.01
    )


def test_allowance_change_total(allowance_sim):
    # 100 x 5,500 + 300 x 5,500 + 50 x 2,500.
    assert values(allowance_sim, "firm_tax_change_total") == pytest.approx(
        [2_325_000, 2_325_000], abs=0.01
    )


def test_allowance_incidence_keys(allowance_sim):
    assert values(allowance_sim, "shareholding") == pytest.approx([0, 0.001])
    assert values(allowance_sim, "consumption_shareholding") == pytest.approx(
        [0.0004, 0.0006]
    )


def test_allowance_incidence(allowance_sim):
    incidence = values(allowance_sim, "firm_tax_incidence")
    # 2,325,000 x (0.25 x 0.0004 + 0.25 x 0.00025) and
    # 2,325,000 x (0.5 x 0.001 + 0.25 x 0.0006 + 0.25 x 0.00075).
    assert incidence == pytest.approx([377.81, 1_947.19], abs=0.005)
    assert (incidence * HOUSEHOLD_WEIGHT).sum() == pytest.approx(2_325_000)


@pytest.mark.parametrize("variable", ["household_tax", "gov_tax"])
def test_allowance_leaves_household_totals_unchanged(allowance_sim, variable):
    assert values(allowance_sim, variable) == pytest.approx(
        values(allowance_sim.baseline, variable)
    )
