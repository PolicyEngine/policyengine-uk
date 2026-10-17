"""gov.contrib.policyengine.disable_simulated_benefits counts a carer's
reported Carer's Allowance once.

The survey reports Carer's Allowance (carers_allowance_reported) for every
respondent, Scotland included. From 2025 the model pays a carer in Scotland
Carer Support Payment in its place. The reform used to set carers_allowance
from the report in every country and leave carer_support_payment simulated,
so a Scottish carer was paid both from 2025. Invariants, for every person
and each of the reform's years:

1. Conservation: carers_allowance + carer_support_payment equals the
   person's reported Carer's Allowance, so the report is counted once in
   household income (both variables are in household_benefits once).
2. Placement: the report is carer_support_payment for a carer living in
   Scotland that year, from CARER_SUPPORT_PAYMENT_FROM, and
   carers_allowance otherwise. Where the carer lives is read in each year,
   so a carer who moves into or out of Scotland changes scheme with the move.
3. Differential: the reform places the report under the scheme the model
   itself pays with the reform off (the pre-overlap entitlements), and
   household_benefits exceeds that of the same dataset with no report by the
   report plus the Scottish Carer Supplement that Carer Support Payment
   brings.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.reforms.policyengine.disable_simulated_benefits import (
    BENEFITS,
    CARER_SUPPORT_PAYMENT_FROM,
    YEARS_IN_FUTURE,
    disable_simulated_benefits,
)
from policyengine_uk.utils.scenario import Scenario

REFORM_ON = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)
REGIONS = [
    "NORTH_EAST",
    "LONDON",
    "WALES",
    "SCOTLAND",
    "NORTHERN_IRELAND",
]
PROPERTY_SETTINGS = settings(
    max_examples=4,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def dataset(year, regions, reported_care, care_hours=None):
    """One adult of 40 per household, with a reported Carer's Allowance and
    weekly care hours (40 unless given)."""
    n = len(regions)
    ids = np.arange(1, n + 1)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": [40] * n,
            "care_hours": [float(x) for x in (care_hours or [40] * n)],
            "carers_allowance_reported": [float(x) for x in reported_care],
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


def moving_dataset(first_year, regions_by_year, reported_care, care_hours=None):
    """The same carers in each of the reform's years, living in each year
    where regions_by_year says. The reform reads the first year's reports."""
    return UKMultiYearDataset(
        datasets=[
            dataset(year, regions_by_year[year], reported_care, care_hours)
            for year in range(first_year, first_year + YEARS_IN_FUTURE)
        ]
    )


def check_care(simulation, regions, reported_care, first_year):
    """regions: each carer's region, the same in every year, or a dict of
    them by year."""
    reported = np.asarray(reported_care, dtype=float)
    for year in range(first_year, first_year + YEARS_IN_FUTURE):
        regions_in_year = regions[year] if isinstance(regions, dict) else regions
        in_scotland = np.asarray(regions_in_year) == "SCOTLAND"
        ca = values(simulation, "carers_allowance", year)
        csp = values(simulation, "carer_support_payment", year)
        np.testing.assert_allclose(ca + csp, reported, err_msg=str(year))
        paid_as_csp = in_scotland & (year >= CARER_SUPPORT_PAYMENT_FROM)
        np.testing.assert_allclose(
            csp, np.where(paid_as_csp, reported, 0), err_msg=str(year)
        )
        np.testing.assert_allclose(
            ca, np.where(paid_as_csp, 0, reported), err_msg=str(year)
        )


def test_carers_allowance_is_set_by_the_carer_split_alone():
    """carers_allowance is set with carer_support_payment from the one
    report. A generic BENEFITS entry as well would set it from the report in
    Scotland too, if it ran after the split."""
    assert "carers_allowance" not in BENEFITS
    assert "carer_support_payment" not in BENEFITS


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_a_scottish_carer_is_paid_the_report_once(simulation_class):
    """The case reported on #2075: two carers of 40 caring 40 hours a week,
    each reporting £4,000 of Carer's Allowance in 2025, one in Scotland and one
    in London. The Scottish carer was paid the report as Carer's Allowance
    and a simulated Carer Support Payment as well."""
    regions = ["SCOTLAND", "LONDON"]
    simulation = simulation_class(
        dataset=dataset(2025, regions, [4_000, 4_000]), scenario=REFORM_ON
    )
    for year in [2025, 2026]:
        np.testing.assert_allclose(
            values(simulation, "carers_allowance", year), [0, 4_000]
        )
        np.testing.assert_allclose(
            values(simulation, "carer_support_payment", year), [4_000, 0]
        )


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
@pytest.mark.parametrize("first_year", [2023, 2025])
def test_reported_care_is_counted_once(simulation_class, first_year):
    regions = ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
    reported_care = [4_000, 3_500, 4_200.5, 3_000, 0]
    simulation = simulation_class(
        dataset=dataset(first_year, regions, reported_care), scenario=REFORM_ON
    )
    check_care(simulation, regions, reported_care, first_year)


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_reform_set_after_the_data_load_counts_the_report_once(simulation_class):
    regions = ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
    reported_care = [4_000, 3_500, 4_200.5, 3_000, 0]
    simulation = simulation_class(
        dataset=dataset(2023, regions, reported_care),
        reform={"gov.contrib.policyengine.disable_simulated_benefits": True},
    )
    check_care(simulation, regions, reported_care, 2023)


def test_the_report_goes_to_the_scheme_the_model_pays():
    """With the reform off the model's pre-overlap entitlements say which
    scheme pays each carer: CARER_SUPPORT_PAYMENT_FROM must agree with them in
    every year, before and after the switch."""
    regions = ["SCOTLAND", "LONDON"]
    first_year = CARER_SUPPORT_PAYMENT_FROM - 3
    reported_care = [4_000, 4_000]
    off = Simulation(dataset=dataset(first_year, regions, reported_care))
    on = Simulation(
        dataset=dataset(first_year, regions, reported_care), scenario=REFORM_ON
    )
    for year in range(first_year, first_year + YEARS_IN_FUTURE):
        model_pays_csp = values(off, "carer_support_payment_pre_overlap", year) > 0
        model_pays_ca = values(off, "carers_allowance_pre_overlap", year) > 0
        # Each carer is entitled under exactly one scheme with the reform off.
        np.testing.assert_array_equal(model_pays_csp ^ model_pays_ca, True)
        np.testing.assert_array_equal(
            values(on, "carer_support_payment", year) > 0,
            model_pays_csp,
            err_msg=str(year),
        )
        np.testing.assert_array_equal(
            values(on, "carers_allowance", year) > 0, model_pays_ca, err_msg=str(year)
        )


def test_household_benefits_include_the_report_once():
    regions = ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND"]
    reported_care = [4_000, 3_500, 4_200.5, 3_000]
    with_report = Simulation(
        dataset=dataset(2023, regions, reported_care), scenario=REFORM_ON
    )
    without_report = Simulation(
        dataset=dataset(2023, regions, [0] * len(regions)), scenario=REFORM_ON
    )
    in_scotland = np.asarray(regions) == "SCOTLAND"
    for year in range(2023, 2023 + YEARS_IN_FUTURE):
        change = {
            name: values(with_report, name, year) - values(without_report, name, year)
            for name in [
                "household_benefits",
                "hbai_household_net_income",
                "scottish_carer_supplement",
            ]
        }
        # The Scottish Carer Supplement is paid with Carer Support Payment
        # (from March 2026), so only to the Scottish carer.
        supplement = change["scottish_carer_supplement"]
        np.testing.assert_allclose(supplement[~in_scotland], 0, err_msg=str(year))
        assert (supplement >= 0).all(), year
        for name in ["household_benefits", "hbai_household_net_income"]:
            np.testing.assert_allclose(
                change[name],
                np.asarray(reported_care) + supplement,
                err_msg=f"{name} {year}",
            )


@PROPERTY_SETTINGS
@given(
    first_year=st.sampled_from([2022, 2023, 2024, 2025, 2026]),
    carers=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.sampled_from([0, 100, 150.5, 3_000, 4_000, 4_331.6]),
            st.sampled_from([0, 20, 35, 40]),
        ),
        min_size=1,
        max_size=6,
    ),
)
def test_reported_care_is_conserved(first_year, carers):
    regions = [region for region, _, _ in carers]
    reported_care = [amount for _, amount, _ in carers]
    care_hours = [hours for _, _, hours in carers]
    simulation = Simulation(
        dataset=dataset(first_year, regions, reported_care, care_hours),
        scenario=REFORM_ON,
    )
    check_care(simulation, regions, reported_care, first_year)


def carer_situation(regions_by_year):
    """The case reported on #2075 at ab800e8bb: one carer, 40 in 2025, caring
    40 hours a week in every year, who reports £4,000 of Carer's Allowance in
    2025 and lives in each year where regions_by_year says. No earnings and
    no overlapping benefit."""
    years = list(regions_by_year)
    return {
        "people": {
            "carer": {
                "age": {year: 40 + year - years[0] for year in years},
                "care_hours": {year: 40 for year in years},
                "carers_allowance_reported": {years[0]: 4_000},
            }
        },
        "benunits": {"family": {"members": ["carer"]}},
        "households": {"home": {"members": ["carer"], "region": regions_by_year}},
    }


INCOME = [
    "carers_allowance",
    "carer_support_payment",
    "scottish_carer_supplement",
    "household_benefits",
    "hbai_household_net_income",
    "household_net_income",
]


@pytest.mark.parametrize(
    "before, after", [("LONDON", "SCOTLAND"), ("SCOTLAND", "LONDON")]
)
@pytest.mark.parametrize("route", ["scenario", "reform"])
def test_a_carer_who_moves_is_paid_under_each_years_scheme(before, after, route):
    """Reported on #2075 at ab800e8bb: the split read the country in the
    dataset year only, so a carer in London in 2025 and Scotland from 2026
    was paid Carer's Allowance in 2026 and lost the Scottish Carer
    Supplement. Each year's outputs now equal those of a carer who has lived
    in that year's country throughout."""
    first = 2025
    years = range(first, first + YEARS_IN_FUTURE)
    moved = {year: before if year == first else after for year in years}
    stayed = {year: after for year in years}
    switch = {"gov.contrib.policyengine.disable_simulated_benefits": True}

    def simulate(regions_by_year):
        if route == "scenario":
            return Simulation(
                situation=carer_situation(regions_by_year), scenario=REFORM_ON
            )
        return Simulation(situation=carer_situation(regions_by_year), reform=switch)

    simulation, control = simulate(moved), simulate(stayed)
    check_care(simulation, {year: [moved[year]] for year in years}, [4_000], first)
    for year in years[1:]:
        for name in INCOME:
            np.testing.assert_allclose(
                values(simulation, name, year),
                values(control, name, year),
                err_msg=f"{name} {year}",
            )
    supplement = values(simulation, "scottish_carer_supplement", first + 1)
    if after == "SCOTLAND":
        # The supplement comes with Carer Support Payment, and reaches
        # household income.
        assert supplement[0] > 0
    else:
        np.testing.assert_allclose(supplement, 0)
    for name in ["household_benefits", "hbai_household_net_income"]:
        np.testing.assert_allclose(
            values(simulation, name, first + 1), 4_000 + supplement, err_msg=name
        )


def test_a_reform_applied_after_a_move_is_set_reads_the_move():
    """The reform reads where each household lives when it is applied
    (review r11 on #2075). Switched on by the parameter, it is applied in the
    constructor, before a scenario's modifier applied after data load, so
    the amounts it sets do not follow a region that modifier or set_input
    changes later. Applied after the change, it reads the new region: a
    carer in London in the situation, moved to Scotland from 2026 by
    set_input, is paid Carer Support Payment from 2026."""
    first = 2025
    years = range(first, first + YEARS_IN_FUTURE)
    simulation = Simulation(
        situation=carer_situation({year: "LONDON" for year in years})
    )
    for year in years[1:]:
        simulation.set_input("region", year, ["SCOTLAND"])
    switched_on = SimpleNamespace(
        gov=SimpleNamespace(
            contrib=SimpleNamespace(
                policyengine=SimpleNamespace(disable_simulated_benefits=True)
            )
        )
    )
    simulation.apply_reform(disable_simulated_benefits(lambda _: switched_on, None))
    regions = {year: ["LONDON" if year == first else "SCOTLAND"] for year in years}
    check_care(simulation, regions, [4_000], first)
    assert values(simulation, "scottish_carer_supplement", first + 1)[0] > 0


@PROPERTY_SETTINGS
@given(
    first_year=st.sampled_from([2023, 2024, 2025, 2026]),
    carers=st.lists(
        st.tuples(
            st.lists(
                st.sampled_from(["SCOTLAND", "LONDON", "WALES"]),
                min_size=YEARS_IN_FUTURE,
                max_size=YEARS_IN_FUTURE,
            ),
            st.sampled_from([0, 150.5, 4_000]),
        ),
        min_size=1,
        max_size=4,
    ),
)
def test_reported_care_follows_each_years_country(first_year, carers):
    """Conservation and placement in every year, with each carer's region
    drawn afresh for each year (a multi-year dataset)."""
    years = range(first_year, first_year + YEARS_IN_FUTURE)
    regions_by_year = {
        year: [path[i] for path, _ in carers] for i, year in enumerate(years)
    }
    reported_care = [amount for _, amount in carers]
    simulation = Simulation(
        dataset=moving_dataset(first_year, regions_by_year, reported_care),
        scenario=REFORM_ON,
    )
    check_care(simulation, regions_by_year, reported_care, first_year)
