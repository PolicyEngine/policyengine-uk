"""The company car benefit against HMRC's published rates, and its reforms.

1. Published rates: for every tax year from 2020-21 to 2029-30, the
   appropriate percentage at both ends of each band equals the rate HMRC
   publishes for it: HMRC 480 Appendix 2 for 2020-21 to 2026-27 (its
   2022-23 table holds to 2024-25), HMRC's future rates table for 2027-28,
   and the tables in Finance Act 2025 ss. 5 and 6 for 2028-29 and 2029-30.
   In 2020-21 and 2021-22 cars first registered before 6 April 2020 take
   the NEDC column and later cars the WLTP column (ITEPA 2003 s. 139A).
   A diesel car not meeting RDE2 adds 4 points, up to the maximum.
2. Budget 2026: the company_car_tax_rise_2030 scenario raises every
   appropriate percentage for 2030-31 by one point, to a maximum of 40%.
   With all three employer NI incidence shares set to zero, it changes a
   company car holder's income tax and their employer's Class 1A,
   nothing else (their student loan repayment included), and nobody else's
   tax; 2029-30 is unchanged. COMPANY_CAR_TAX_RISE_2030 passed as a reform
   dict gives the same results.
3. Employer NI: Class 1A follows the secondary percentage (SSCBA 1992
   s. 10(5)), so an employer rate reform moves it. The employer NI
   incidence can be disabled explicitly for static tax comparisons. The
   baseline_employer_cost and adjusted_employer_cost still equal each
   simulation's employer_cost for a company car holder, as they do for
   everyone else.

Comparisons allow float32 rounding.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.scenarios import company_car_tax_rise_2030
from policyengine_uk.scenarios.company_car_tax_rise_2030 import (
    COMPANY_CAR_TAX_RISE_2030,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

INCIDENCE = "gov.contrib.policyengine.employer_ni"
STATIC_INCIDENCE = {
    f"{INCIDENCE}.{channel}_incidence": {"2020-04-06.2100-12-31": 0}
    for channel in ["employee", "consumer", "capital"]
}
STATIC_SCENARIO = Scenario(parameter_changes=STATIC_INCIDENCE)

# Each table, in percentage points: the rate for 0 g/km; for 1 to 50 g/km by
# electric range (130 miles or more, 70-129, 40-69, 30-39, under 30); for
# 51-54, 55-59, 60-64, 65-69 and 70-74 g/km; and for each 5 g/km band from
# 75-79 to 165-169 g/km, then 170 g/km and above.
NEDC_2020 = (
    0,
    [2, 5, 8, 12, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37],
)
WLTP_2020 = (
    0,
    [0, 3, 6, 10, 12],
    [13, 14, 15, 16, 17],
    [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37],
)
NEDC_2021 = (
    1,
    [2, 5, 8, 12, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37],
)
WLTP_2021 = (
    1,
    [1, 4, 7, 11, 13],
    [14, 15, 16, 17, 18],
    [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37],
)
ALL_CARS_2022 = (
    2,
    [2, 5, 8, 12, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37],
)
ALL_CARS_2025 = (
    3,
    [3, 6, 9, 13, 15],
    [16, 17, 18, 19, 20],
    [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37, 37],
)
ALL_CARS_2026 = (
    4,
    [4, 7, 10, 14, 16],
    [17, 18, 19, 20, 21],
    [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37, 37],
)
ALL_CARS_2027 = (
    5,
    [5, 8, 11, 15, 17],
    [18, 19, 20, 21, 21],
    [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 37, 37, 37],
)
# Finance Act 2025 ss. 5 and 6: one rate for 1 to 50 g/km, a 65-74 g/km
# band, and from 75 g/km 22% (then 23%) plus one point for each 5 g/km, up
# to 38% (then 39%).
ALL_CARS_2028 = (
    7,
    [18] * 5,
    [19, 20, 21, 22, 22],
    [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 38, 38, 38],
)
ALL_CARS_2029 = (
    9,
    [19] * 5,
    [20, 21, 22, 23, 23],
    [23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 39, 39, 39],
)
# Budget 2026 for 2030-31: one point above 2029-30 in every band, up to 40%.
BUDGET_2026_2030 = (
    10,
    [20] * 5,
    [21, 22, 23, 24, 24],
    [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 40, 40, 40],
)

# (year, first registered on or after 6 April 2020, table)
PUBLISHED = [
    (2020, False, NEDC_2020),
    (2020, True, WLTP_2020),
    (2021, False, NEDC_2021),
    (2021, True, WLTP_2021),
    (2022, False, ALL_CARS_2022),
    (2022, True, ALL_CARS_2022),
    (2023, True, ALL_CARS_2022),
    (2024, False, ALL_CARS_2022),
    (2025, False, ALL_CARS_2025),
    (2026, True, ALL_CARS_2026),
    (2027, False, ALL_CARS_2027),
    (2028, False, ALL_CARS_2028),
    (2029, False, ALL_CARS_2029),
]

RANGE_BANDS = [(130, 300), (70, 129), (40, 69), (30, 39), (0, 29)]
CO2_BANDS = [(51, 54), (55, 59), (60, 64), (65, 69), (70, 74)]
GRADUATED_BANDS = [(low, low + 4) for low in range(75, 170, 5)] + [(170, 250)]


def band_points(table):
    """(CO2 g/km, electric range in miles, expected rate) at each band's ends."""
    zero, by_range, by_co2, graduated = table
    points = [(0, 0, zero)]
    for (low, high), rate in zip(RANGE_BANDS, by_range):
        for co2 in (1, 50):
            points += [(co2, low, rate), (co2, high, rate)]
    for bands, rates in ((CO2_BANDS, by_co2), (GRADUATED_BANDS, graduated)):
        for (low, high), rate in zip(bands, rates):
            points += [(low, 0, rate), (high, 0, rate)]
    return points


def situation(year, cars):
    """One person per car, each with the given company car inputs."""
    people = {
        f"person_{i}": {
            "age": {year: 40},
            "employment_income": {year: 40_000},
            **{name: {year: value} for name, value in car.items()},
        }
        for i, car in enumerate(cars)
    }
    return {
        "people": people,
        "benunits": {f"benunit_{name}": {"members": [name]} for name in people},
        "households": {f"household_{name}": {"members": [name]} for name in people},
    }


def values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def appropriate_percentages(year, cars, **kwargs):
    simulation = Simulation(situation=situation(year, cars), **kwargs)
    return values(simulation, "company_car_appropriate_percentage", year)


def cars_at(points, registered, fuel_type="PETROL"):
    return [
        {
            "company_car_list_price": 30_000,
            "company_car_co2_emissions": co2,
            "company_car_electric_range": electric_range,
            "company_car_registered_from_6_april_2020": registered,
            "company_car_fuel_type": fuel_type,
        }
        for co2, electric_range, _ in points
    ]


@pytest.mark.parametrize("year, registered, table", PUBLISHED)
def test_appropriate_percentages_match_published_rates(year, registered, table):
    points = band_points(table)
    actual = appropriate_percentages(year, cars_at(points, registered))
    expected = np.array([rate for *_, rate in points]) / 100
    np.testing.assert_allclose(actual, expected, atol=1e-6)


@pytest.mark.parametrize("year, registered, table", PUBLISHED)
def test_diesel_supplement_adds_four_points_up_to_the_maximum(year, registered, table):
    # HMRC 480 paragraph 12.29: a diesel car not meeting RDE2 adds 4 points,
    # subject to the overall maximum, which is the table's highest rate.
    points = [point for point in band_points(table) if point[0] > 0]
    maximum = max(table[3])
    actual = appropriate_percentages(
        year, cars_at(points, registered, "DIESEL_NON_RDE2")
    )
    expected = np.minimum(np.array([rate for *_, rate in points]) + 4, maximum) / 100
    np.testing.assert_allclose(actual, expected, atol=1e-6)


def test_figures_are_rounded_as_section_139_rounds_them():
    # s. 139(2): CO2 down to a whole number, electric range up; s. 139(4):
    # from 75 g/km, CO2 down to a multiple of 5. 2026-27 rates.
    cars = [
        {
            "company_car_list_price": 30_000,
            "company_car_co2_emissions": co2,
            "company_car_electric_range": electric_range,
        }
        for co2, electric_range in [(50.9, 130), (49, 29.1), (74.9, 0), (79.9, 0)]
    ]
    actual = appropriate_percentages(2026, cars)
    np.testing.assert_allclose(actual, [0.04, 0.14, 0.21, 0.21], atol=1e-6)


def test_2030_31_rise_sets_the_budget_2026_rates():
    points = band_points(BUDGET_2026_2030)
    cars = cars_at(points, registered=False)
    baseline = appropriate_percentages(2030, cars)
    reformed = appropriate_percentages(2030, cars, scenario=company_car_tax_rise_2030)
    expected = np.array([rate for *_, rate in points]) / 100
    np.testing.assert_allclose(reformed, expected, atol=1e-6)
    # The baseline keeps 2029-30's rates.
    expected_baseline = np.array([rate for *_, rate in band_points(ALL_CARS_2029)])
    np.testing.assert_allclose(baseline, expected_baseline / 100, atol=1e-6)


# A company car holder with private fuel and a Plan 2 student loan, and an
# employee without a car.
HOLDER = {
    "company_car_list_price": 40_000,
    "company_car_co2_emissions": 120,
    "company_car_private_fuel_provided": True,
    "student_loan_plan": "PLAN_2",
}
UNCHANGED_FOR_HOLDER = [
    "ni_class_1_employer",
    "ni_class_1_employee",
    "employment_income",
    "employer_ni_fixed_employer_cost_change",
    "student_loan_repayment",
    "plan_2_interest_rate",
]
TAX_AND_INCOME = [
    "income_tax",
    "ni_class_1a",
    "uc_individual_earned_income_before_mif",
] + UNCHANGED_FOR_HOLDER


@pytest.mark.parametrize("year", [2029, 2030, 2031])
def test_static_2030_31_rise_changes_only_holders_income_tax_and_class_1a(year):
    cars = [HOLDER, {}]
    baseline = Simulation(situation=situation(year, cars))
    reformed = Simulation(
        situation=situation(year, cars),
        scenario=company_car_tax_rise_2030 + STATIC_SCENARIO,
    )
    change = {
        variable: values(reformed, variable, year) - values(baseline, variable, year)
        for variable in TAX_AND_INCOME + ["benefits_in_kind", "gov_tax"]
    }
    benefit_change = change["benefits_in_kind"][0]
    if year == 2029:
        # The rise starts on 6 April 2030.
        for variable, difference in change.items():
            np.testing.assert_allclose(difference, 0, atol=1e-2, err_msg=variable)
        return
    # One point on the car (£40,000) and on the fuel multiplier.
    multiplier = baseline.tax_benefit_system.parameters(
        f"{year}-01-01"
    ).gov.hmrc.income_tax.benefits_in_kind.car_fuel.multiplier
    assert benefit_change == pytest.approx(0.01 * (40_000 + multiplier), abs=0.05)
    # Pay of £40,000 plus about £23,000 of car and fuel benefits is in the
    # higher rate band, and below the personal allowance taper.
    assert change["income_tax"][0] == pytest.approx(0.4 * benefit_change, abs=0.05)
    assert change["ni_class_1a"][0] == pytest.approx(0.15 * benefit_change, abs=0.05)
    assert change["gov_tax"][0] == pytest.approx(
        change["income_tax"][0] + change["ni_class_1a"][0], abs=0.05
    )
    # UC earnings lose the extra income tax and nothing else.
    assert change["uc_individual_earned_income_before_mif"][0] == pytest.approx(
        -change["income_tax"][0], abs=0.05
    )
    for variable in UNCHANGED_FOR_HOLDER:
        np.testing.assert_allclose(change[variable][0], 0, atol=1e-6, err_msg=variable)
    # Nothing changes for the employee without a car.
    for variable, difference in change.items():
        np.testing.assert_allclose(difference[1], 0, atol=1e-2, err_msg=variable)


def test_a_company_car_raises_gov_tax_by_its_income_tax_and_class_1a():
    # The same employee, with the same student loan, without the car.
    without_the_car = {
        name: value for name, value in HOLDER.items() if not name.startswith("company")
    }
    with_car = Simulation(situation=situation(2026, [HOLDER]))
    without_car = Simulation(situation=situation(2026, [without_the_car]))

    def change(variable):
        return (values(with_car, variable, 2026) - values(without_car, variable, 2026))[
            0
        ]

    assert change("ni_class_1a") > 0
    # Student loan repayments are in gov_tax but leave the benefit out.
    assert change("student_loan_repayment") == 0
    assert change("gov_tax") == pytest.approx(
        change("income_tax") + change("ni_class_1a"), abs=0.05
    )
    # The benefit is not cash: household income falls by the tax on it.
    assert change("household_net_income") == pytest.approx(
        -change("income_tax"), abs=0.05
    )


EMPLOYER_RATE = "gov.hmrc.national_insurance.class_1.employer_scale[1].rate"


def test_class_1a_follows_an_employer_rate_reform_with_static_incidence():
    reform = {
        EMPLOYER_RATE: {"2026-04-06.2100-12-31": 0.16},
        **STATIC_INCIDENCE,
    }
    cars = [HOLDER, {}]
    baseline = Simulation(situation=situation(2026, cars))
    reformed = Simulation(situation=situation(2026, cars), reform=reform)
    benefits = values(baseline, "benefits_in_kind", 2026)
    # SSCBA 1992 s. 10(5): the Class 1A percentage is the secondary
    # percentage for the year.
    np.testing.assert_allclose(
        values(reformed, "ni_class_1a", 2026), 0.16 * benefits, rtol=1e-6
    )
    # With all three incidence shares zero, pay is unchanged and employers
    # retain the whole liability increase, including Class 1A for the holder.
    pay_change = values(reformed, "employer_ni_fixed_employer_cost_change", 2026)
    np.testing.assert_allclose(pay_change, 0, atol=0, rtol=0)
    cost_change = values(reformed, "adjusted_employer_cost", 2026) - values(
        reformed, "baseline_employer_cost", 2026
    )
    assert cost_change[1] > 0
    assert cost_change[0] - cost_change[1] == pytest.approx(
        0.01 * benefits[0], abs=0.01
    )
    # Agreement: the incidence variables' costs equal employer_cost in each
    # simulation, for the holder too.
    np.testing.assert_allclose(
        values(reformed, "baseline_employer_cost", 2026),
        values(reformed.baseline, "employer_cost", 2026),
        atol=0.01,
    )
    np.testing.assert_allclose(
        values(reformed, "adjusted_employer_cost", 2026),
        values(reformed, "employer_cost", 2026),
        atol=0.01,
    )


@pytest.mark.parametrize("year", [2030, 2031, 2035])
def test_the_parameter_changes_as_a_reform_dict_match_the_scenario(year):
    cars = [HOLDER, {}]
    from_scenario = Simulation(
        situation=situation(year, cars), scenario=company_car_tax_rise_2030
    )
    from_dict = Simulation(
        situation=situation(year, cars), reform=COMPANY_CAR_TAX_RISE_2030
    )
    for variable in ["company_car_appropriate_percentage", "income_tax", "gov_tax"]:
        np.testing.assert_allclose(
            values(from_dict, variable, year),
            values(from_scenario, variable, year),
            atol=1e-6,
            err_msg=variable,
        )


def test_all_three_zero_shares_leave_the_2030_31_rise_static():
    # Disable every incidence channel explicitly. The cost replicas still
    # account for the Class 1A increase, which employers retain in this case.
    reform = {
        **COMPANY_CAR_TAX_RISE_2030,
        **STATIC_INCIDENCE,
    }
    simulation = Simulation(situation=situation(2030, [HOLDER]), reform=reform)
    class_1a_change = values(simulation, "ni_class_1a", 2030) - values(
        simulation.baseline, "ni_class_1a", 2030
    )
    assert class_1a_change[0] > 0
    for variable in ["employer_ni_fixed_employer_cost_change", "employment_income"]:
        np.testing.assert_allclose(
            values(simulation, variable, 2030),
            values(simulation.baseline, variable, 2030),
            atol=1e-6,
            err_msg=variable,
        )
    np.testing.assert_allclose(
        values(simulation, "adjusted_employer_cost", 2030)
        - values(simulation, "baseline_employer_cost", 2030),
        class_1a_change,
        atol=0.01,
    )
    for variable in [
        "employer_ni_response_consumer_incidence",
        "employer_ni_response_capital_incidence",
    ]:
        np.testing.assert_allclose(values(simulation, variable, 2030), 0, atol=0)
