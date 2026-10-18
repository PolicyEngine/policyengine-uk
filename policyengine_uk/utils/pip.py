"""Shared logic for the PIP component categories."""

from policyengine_core.periods import Period

from policyengine_uk.model_api import select
from policyengine_uk.utils.supplied_inputs import (
    supplied_input,
    supplied_input_periods,
)
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


def pip_category(person, period: Period, thresholds, component: str):
    """The PIP category for ``component`` ("dl" or "m") in ``period``.

    A category supplied for the period is an input, so this only runs when
    there is none. Points supplied for the period are then the evidence. If
    they are not, the most recent earlier input decides: a category supplied
    in an earlier year carries forward, as it would for an input-only
    variable, unless points were supplied in a later year than that
    category. Points, like other inputs, carry forward from the latest year
    they were supplied. Points default to zero, below the standard
    threshold, so with neither input the category is NONE.

    Inputs are stored for the whole population, so "supplied" is decided
    per year, not per person. If points are supplied for a year for anyone,
    everyone's category that year comes from points, and a person given
    only an earlier category reads the default of zero points (NONE). Give
    such a person their points or category for that year as well.
    """
    category_variable = f"pip_{component}_category"
    points_variable = f"pip_{component}_points"
    if supplied_input(person, points_variable, period) is None:
        earlier_categories = [
            p
            for p in supplied_input_periods(person, category_variable)
            if p.start < period.start
        ]
        earlier_points = [
            p
            for p in supplied_input_periods(person, points_variable)
            if p.start < period.start
        ]
        if earlier_categories and (
            not earlier_points
            or earlier_categories[-1].start >= earlier_points[-1].start
        ):
            return supplied_input(person, category_variable, earlier_categories[-1])
    points = person(points_variable, period)
    return select(
        [points >= thresholds.enhanced, points >= thresholds.standard],
        [PIPCategory.ENHANCED, PIPCategory.STANDARD],
        default=PIPCategory.NONE,
    )
