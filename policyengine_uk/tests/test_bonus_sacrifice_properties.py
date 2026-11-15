"""Bonus sacrifice is scored exactly as salary sacrifice of the same amount.

The NICs exemption cap (NICs Act 2026 s. 1) covers salary-sacrificed and
bonus-sacrificed pension contributions together, and FA 2004 s. 228ZA(5)(b)
adds both back to annual allowance threshold income.
pension_contributions_via_bonus_sacrifice is a separate input only because
sources measure the two routes apart, so moving any part of a sacrifice from
one input to the other must change no result, before or after the cap.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

YEARS = (2028, 2029, 2030)
HAIRCUT = "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate"
# age, cash pay, salary sacrifice, bonus sacrifice, employer contributions
CASES = [
    (40, 80_000, 0, 10_000, 0),
    (40, 40_000, 1_500, 1_500, 0),
    # Crosses the upper earnings limit.
    (40, 49_000, 2_000, 3_000, 2_000),
    # Crosses the primary threshold.
    (40, 11_000, 0, 5_000, 0),
    # Over State Pension age: no employee NICs.
    (70, 45_000, 1_000, 5_000, 0),
    # Tapered annual allowance.
    (45, 190_000, 10_000, 30_000, 80_000),
    # No pay, so nothing to sacrifice.
    (40, 0, 0, 27_000, 0),
]
OUTPUTS = (
    "pension_contributions_via_salary_sacrifice_from_pay",
    "pension_contributions_via_salary_sacrifice_adjusted",
    "salary_sacrifice_pension_ni_excess",
    "ni_class_1_income",
    "national_insurance",
    "ni_class_1_employer",
    "salary_sacrifice_pension_ni_employee",
    "salary_sacrifice_pension_ni_employer",
    "income_tax",
    "pension_contributions_for_annual_allowance",
    "pension_annual_allowance_threshold_income",
    "pension_annual_allowance_adjusted_income",
    "pension_annual_allowance",
    "household_net_income",
    "hbai_household_net_income",
)


def simulation(route):
    """route maps a case to its (salary, bonus) sacrifice inputs."""
    people = {}
    for i, case in enumerate(CASES):
        age, pay, _, _, employer = case
        salary, bonus = route(case)
        people[f"p{i}"] = {
            name: {str(year): value for year in YEARS}
            for name, value in {
                "age": age,
                "employment_income": pay,
                "employer_pension_contributions": employer,
                "pension_contributions_via_salary_sacrifice": salary,
                "pension_contributions_via_bonus_sacrifice": bonus,
            }.items()
        }
    return Simulation(
        situation={
            "people": people,
            "benunits": {f"b{i}": {"members": [name]} for i, name in enumerate(people)},
            "households": {
                f"h{i}": {"members": [name], "region": "LONDON"}
                for i, name in enumerate(people)
            },
        },
        reform={HAIRCUT: {"2028-01-01.2030-12-31": 0}},
    )


@pytest.fixture(scope="module")
def simulations():
    return {
        "split": simulation(lambda c: (c[2], c[3])),
        "all_salary": simulation(lambda c: (c[2] + c[3], 0)),
        "all_bonus": simulation(lambda c: (0, c[2] + c[3])),
        "none": simulation(lambda c: (0, 0)),
    }


def values(sim, variable, year):
    return np.asarray(sim.calculate(variable, year), dtype=float)


@pytest.mark.parametrize("year", YEARS)
@pytest.mark.parametrize("route", ("split", "all_bonus"))
def test_bonus_sacrifice_scores_like_salary_sacrifice(simulations, route, year):
    for name in OUTPUTS:
        np.testing.assert_allclose(
            values(simulations[route], name, year),
            values(simulations["all_salary"], name, year),
            atol=0.01,
            err_msg=name,
        )


@pytest.mark.parametrize("year", (2029, 2030))
def test_cap_charges_nics_on_bonus_sacrifice_above_threshold(simulations, year):
    # £80,000 of pay and a £10,000 bonus sacrifice: £8,000 above the £2,000
    # threshold, all above the upper earnings limit, so employee NICs rise by
    # 2% of it and employer NICs by 15%.
    split, none = simulations["split"], simulations["none"]
    assert values(split, "salary_sacrifice_pension_ni_excess", year)[0] == 8_000
    employee_rise = (
        values(split, "national_insurance", year)[0]
        - values(none, "national_insurance", year)[0]
    )
    employer_rise = (
        values(split, "ni_class_1_employer", year)[0]
        - values(none, "ni_class_1_employer", year)[0]
    )
    assert employee_rise == pytest.approx(160, abs=0.01)
    assert employer_rise == pytest.approx(1_200, abs=0.01)


def test_bonus_sacrifice_is_free_of_nics_before_the_cap(simulations):
    split, none = simulations["split"], simulations["none"]
    for name in ("national_insurance", "ni_class_1_employer"):
        np.testing.assert_allclose(
            values(split, name, 2028), values(none, name, 2028), err_msg=name
        )
