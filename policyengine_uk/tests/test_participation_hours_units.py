"""Units regression tests for the participation dynamics module.

``hours_worked`` in policyengine-uk is an ANNUAL quantity: its label is
"Annual hours worked", it has a YEAR definition period, and ``weekly_hours``
derives from it as ``hours_worked / WEEKS_IN_YEAR``.

``impute_wages_for_nonworkers`` previously computed the hourly wage as
``employment_income / (hours_worked * 52)``, dividing by a year a second time.
That gave an implied hourly wage around £0.43 against a realistic £22, and
imputed roughly £194 of annual earnings for a non-worker entering part-time
work instead of about £21,600 — which collapses the extensive-margin response
to near-zero entrants.

These tests pin the units so a future change to ``hours_worked`` cannot
silently reintroduce the error.
"""

import numpy as np

from policyengine_uk.dynamics.participation import hourly_wage
from policyengine_uk.model_api import WEEKS_IN_YEAR


class FakeSimulation:
    """Minimal stand-in exposing only the variables ``hourly_wage`` reads."""

    def __init__(self, employment_income, hours_worked):
        self._values = {
            "employment_income": np.array(employment_income, dtype=float),
            "hours_worked": np.array(hours_worked, dtype=float),
        }

    def calculate(self, variable, period=None, **kwargs):
        return self._values[variable]


def test_hourly_wage_treats_hours_worked_as_annual():
    # A full-time worker: £40,000 over 37.5 hours a week for a full year.
    annual_hours = 37.5 * WEEKS_IN_YEAR
    sim = FakeSimulation([40_000.0], [annual_hours])

    _, wage, working = hourly_wage(sim, 2025)

    assert working[0]
    assert wage[0] == 40_000.0 / annual_hours
    # About £20.51. The pre-fix formula gave £0.39.
    assert 15 < wage[0] < 30


def test_imputed_entrant_earnings_are_a_plausible_part_time_wage():
    hours_for_new_entrants = 18.8
    annual_hours = 37.5 * WEEKS_IN_YEAR
    sim = FakeSimulation([40_000.0], [annual_hours])

    _, wage, _ = hourly_wage(sim, 2025)
    imputed = wage[0] * hours_for_new_entrants * WEEKS_IN_YEAR

    # Roughly £20,000 for 18.8 hours a week, not roughly £200.
    assert 15_000 < imputed < 25_000


def test_non_workers_and_zero_hours_get_no_wage():
    sim = FakeSimulation([0.0, 40_000.0, 0.0], [0.0, 2_000.0, 1_500.0])

    _, wage, working = hourly_wage(sim, 2025)

    assert not working[0] and wage[0] == 0
    assert working[1] and wage[1] == 20.0
    # Zero earnings with positive hours is not a worker for this purpose.
    assert not working[2] and wage[2] == 0


def test_zero_hours_does_not_divide_by_zero():
    sim = FakeSimulation([40_000.0, 0.0], [0.0, 0.0])

    _, wage, _ = hourly_wage(sim, 2025)

    assert np.isfinite(wage).all()
    assert (wage == 0).all()
