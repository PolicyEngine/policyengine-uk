"""WTC worker conditions stay with their person and benefit unit.

These controls use genuine work/claim inputs and literal final-award oracles.
They exercise composition and parameter hooks, rather than duplicate the
production predicate. Disability retains the model's existing generic proxy.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation


YEAR = 2024


def situation(families, reverse=False):
    people, benunits, households = {}, {}, {}
    for i, (adults, children) in enumerate(families):
        names = []
        for j, inputs in enumerate(adults + children):
            name = f"person_{i}_{j}"
            people[name] = {key: {YEAR: value} for key, value in inputs.items()}
            people[name]["is_claimant_or_partner"] = {YEAR: j < len(adults)}
            names.append(name)
        if reverse:
            names.reverse()
        benunits[f"family_{i}"] = {"members": names}
        households[f"household_{i}"] = {"members": names}
    if reverse:
        people = dict(reversed(list(people.items())))
    return {"people": people, "benunits": benunits, "households": households}


def worker(age, hours, earnings=5_000, **inputs):
    return {
        "age": age,
        "hours_worked": hours * 52,
        "employment_income": earnings if hours else 0,
        **inputs,
    }


@pytest.mark.parametrize("reverse", [False, True])
def test_worker_conditions_do_not_move_between_people_or_families(reverse):
    families = [
        ([worker(40, 0, working_tax_credit_reported=1), worker(24, 30)], []),
        ([worker(40, 0, working_tax_credit_reported=1), worker(25, 30)], []),
        (
            [
                worker(30, 16, is_parent=True, working_tax_credit_reported=1),
                worker(28, 0, is_parent=True),
            ],
            [worker(15, 8, earnings=1_000)],
        ),
        (
            [
                worker(
                    30,
                    16,
                    earnings=3_000,
                    is_parent=True,
                    working_tax_credit_reported=1,
                ),
                worker(28, 8, earnings=2_000, is_parent=True),
            ],
            [{"age": 10}],
        ),
    ]
    simulation = Simulation(situation=situation(families, reverse))
    # Request the final award first, so an eligibility-only cache cannot hide
    # a cross-person or cross-family error in the cash consumer.
    np.testing.assert_allclose(
        simulation.calculate("working_tax_credit", YEAR),
        [0, 5_950, 0, 4_935],
        atol=0.01,
        rtol=0,
    )
    np.testing.assert_array_equal(
        simulation.calculate("is_WTC_eligible", YEAR), [False, True, False, True]
    )


@pytest.mark.parametrize(
    "age,hours,disabled,parameter,value,baseline_cash",
    [
        (25, 30, False, "min_age_without_children_or_disability", 26, 3_450),
        (16, 16, True, "min_age", 17, 6_370),
        (60, 16, False, "min_hours.old_age", 61, 2_435),
    ],
)
def test_worker_age_parameters_change_actual_cash_awards(
    age, hours, disabled, parameter, value, baseline_cash
):
    inputs = situation(
        [
            (
                [
                    worker(
                        age,
                        hours,
                        is_disabled_for_benefits=disabled,
                        working_tax_credit_reported=1,
                    )
                ],
                [],
            )
        ]
    )
    baseline = Simulation(situation=inputs)
    reform = Simulation(
        situation=inputs,
        reform={f"gov.dwp.tax_credits.working_tax_credit.{parameter}": value},
    )
    assert baseline.calculate("working_tax_credit", YEAR)[0] == baseline_cash
    assert reform.calculate("working_tax_credit", YEAR)[0] == 0
