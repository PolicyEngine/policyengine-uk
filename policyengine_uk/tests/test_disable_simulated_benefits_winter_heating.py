"""gov.contrib.policyengine.disable_simulated_benefits sets benefits to the
amounts the survey reports.

The reform could not run: policyengine_uk's Simulation never set
tax_benefit_system.simulation, through which a structural reform reaches the
simulation, and the benefit list named five <benefit>_reported variables
that no longer exist. These tests build small datasets and turn the reform on
before the data load, which is when structural reforms are created.

The survey reports one winter heating payment (FRS benefit code 62, in
winter_fuel_allowance_reported) for every respondent, Scotland included.
Invariants, for every household and each of the reform's years:

1. Conservation: winter_fuel_allowance + pawhp equals the household's
   reported winter heating payment, so the report is counted once in
   household income (both variables are in household_benefits once).
2. Placement: the report is pawhp in Scotland in the years PAWHP is paid
   (from the 2024 qualifying week) and winter_fuel_allowance otherwise.
3. Differential: household_benefits exceeds that of the same dataset with no
   reported winter heating payment by the report, plus the pensioner
   Cost-of-Living Payment it brings in 2022-23 and 2023-24.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.reforms.policyengine.disable_simulated_benefits import (
    BENEFITS,
    YEARS_IN_FUTURE,
)
from policyengine_uk.utils.scenario import Scenario

SYSTEM = CountryTaxBenefitSystem()
REFORM_ON = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)
REGIONS = [
    "NORTH_EAST",
    "NORTH_WEST",
    "YORKSHIRE",
    "EAST_MIDLANDS",
    "WEST_MIDLANDS",
    "EAST_OF_ENGLAND",
    "LONDON",
    "SOUTH_EAST",
    "SOUTH_WEST",
    "WALES",
    "SCOTLAND",
    "NORTHERN_IRELAND",
]
FIRST_PAWHP_YEAR = 2024
# Simulated benefits with a reported counterpart that the reform does not
# set from BENEFITS, and why.
NOT_IN_BENEFITS = {
    "winter_fuel_allowance": "set with pawhp from the one reported winter heating payment",
    "maternity_allowance": "already the reported amount (adds maternity_allowance_reported)",
    "employee_pension_contributions": "not a benefit",
    "tax": "not a benefit",
}
PROPERTY_SETTINGS = settings(
    max_examples=4,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def dataset(year, regions, winter_heating, pension_credit=None):
    """One pensioner per household, with a reported State Pension, winter
    heating payment and (optionally) Pension Credit."""
    n = len(regions)
    ids = np.arange(1, n + 1)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": [72] * n,
            "state_pension_reported": [10_000.0] * n,
            "winter_fuel_allowance_reported": [float(x) for x in winter_heating],
            "pension_credit_reported": [float(x) for x in (pension_credit or [0] * n)],
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "region": regions,
            "household_weight": [1.0] * n,
            "tenure_type": ["OWNED_OUTRIGHT"] * n,
            "council_tax": [0.0] * n,
            "rent": [0.0] * n,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=household,
        fiscal_year=year,
    )


def values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def check_winter_heating(simulation, regions, winter_heating, first_year):
    reported = np.asarray(winter_heating, dtype=float)
    in_scotland = np.asarray(regions) == "SCOTLAND"
    for year in range(first_year, first_year + YEARS_IN_FUTURE):
        wfa = values(simulation, "winter_fuel_allowance", year)
        pawhp = values(simulation, "pawhp", year)
        np.testing.assert_allclose(wfa + pawhp, reported, err_msg=str(year))
        paid_as_pawhp = in_scotland & (year >= FIRST_PAWHP_YEAR)
        np.testing.assert_allclose(
            pawhp, np.where(paid_as_pawhp, reported, 0), err_msg=str(year)
        )
        np.testing.assert_allclose(
            wfa, np.where(paid_as_pawhp, 0, reported), err_msg=str(year)
        )


def test_every_listed_benefit_has_a_reported_amount():
    missing = [name for name in BENEFITS if f"{name}_reported" not in SYSTEM.variables]
    assert not missing, missing


def test_every_simulated_benefit_with_a_reported_amount_is_set():
    reported = {
        name[: -len("_reported")]
        for name in SYSTEM.variables
        if name.endswith("_reported") and name[: -len("_reported")] in SYSTEM.variables
    }
    unlisted = reported - set(BENEFITS) - set(NOT_IN_BENEFITS)
    assert not unlisted, unlisted


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_reform_sets_reported_benefits(simulation_class):
    """The reform runs, and a listed benefit takes its reported amount."""
    simulation = simulation_class(
        dataset=dataset(2023, ["SCOTLAND", "LONDON"], [250, 300], [1_500, 0]),
        scenario=REFORM_ON,
    )
    for year in [2023, 2026, 2032]:
        np.testing.assert_allclose(
            values(simulation, "pension_credit", year), [1_500, 0]
        )
        np.testing.assert_allclose(
            values(simulation, "state_pension", year), [10_000, 10_000]
        )


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
@pytest.mark.parametrize("first_year", [2023, 2025])
def test_reported_winter_heating_is_counted_once(simulation_class, first_year):
    regions = ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
    winter_heating = [250, 300, 200, 100, 0]
    simulation = simulation_class(
        dataset=dataset(first_year, regions, winter_heating), scenario=REFORM_ON
    )
    check_winter_heating(simulation, regions, winter_heating, first_year)


def test_household_benefits_include_the_report_once():
    regions = ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND"]
    winter_heating = [250, 300, 200, 100]
    with_report = Simulation(
        dataset=dataset(2023, regions, winter_heating), scenario=REFORM_ON
    )
    without_report = Simulation(
        dataset=dataset(2023, regions, [0] * len(regions)), scenario=REFORM_ON
    )
    for year in range(2023, 2023 + YEARS_IN_FUTURE):
        change = {
            name: values(with_report, name, year) - values(without_report, name, year)
            for name in [
                "household_benefits",
                "hbai_household_net_income",
                "cost_of_living_support_payment",
            ]
        }
        # The pensioner Cost-of-Living Payment is £300 in 2023-24 and keyed
        # on the Winter Fuel Payment, which covered Scotland that winter.
        expected_col = 300 if year == 2023 else 0
        np.testing.assert_allclose(
            change["cost_of_living_support_payment"], expected_col
        )
        for name in ["household_benefits", "hbai_household_net_income"]:
            np.testing.assert_allclose(
                change[name], np.asarray(winter_heating) + expected_col, err_msg=name
            )


@PROPERTY_SETTINGS
@given(
    first_year=st.sampled_from([2022, 2023, 2024, 2025]),
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.sampled_from([0, 100, 150.5, 200, 250, 300, 600]),
        ),
        min_size=1,
        max_size=6,
    ),
)
def test_reported_winter_heating_is_conserved(first_year, households):
    regions = [region for region, _ in households]
    winter_heating = [amount for _, amount in households]
    simulation = Simulation(
        dataset=dataset(first_year, regions, winter_heating), scenario=REFORM_ON
    )
    check_winter_heating(simulation, regions, winter_heating, first_year)
