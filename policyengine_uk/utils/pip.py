"""Shared logic for the PIP component categories."""

import numpy as np
from policyengine_core.periods import Period

from policyengine_uk.model_api import select
from policyengine_uk.utils.supplied_inputs import (
    supplied_input,
    supplied_input_periods,
)
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory

# The default of the points inputs: the person was not assessed. Zero is an
# assessment that scored no points.
NOT_ASSESSED = -1


def pip_category(person, period: Period, thresholds, component: str):
    """The PIP category for ``component`` ("dl" or "m") in ``period``.

    A category supplied for the period is an input, so this only runs when
    there is none. Each person's evidence is then the more recent of their
    points and the category supplied for an earlier year, which carries
    forward as it would for an input-only variable:

    - a person's points come from the latest year up to ``period`` for
      which they were assessed (points other than ``NOT_ASSESSED``);
    - they decide the category if they are for a later year than the latest
      earlier category, or if there is no earlier category;
    - otherwise the earlier category carries forward. With neither, the
      category is NONE.

    Points are decided per person: one person's points for a year leave
    another person's carried category alone. A category supplied for a year
    is stored for the whole population, so it applies to everyone that year,
    with NONE for anyone not given one, as before the points existed.
    """
    category_variable = f"pip_{component}_category"
    points_variable = f"pip_{component}_points"

    earlier_categories = [
        p
        for p in supplied_input_periods(person, category_variable)
        if p.start < period.start
    ]
    category_period = earlier_categories[-1] if earlier_categories else None

    points = np.full(person.count, NOT_ASSESSED)
    # Whether the person's latest points are for a later year than the
    # latest earlier category (always, if there is no such category).
    points_are_newer = np.zeros(person.count, dtype=bool)
    for points_period in supplied_input_periods(person, points_variable):
        if points_period.start > period.start:
            break
        values = supplied_input(person, points_variable, points_period)
        assessed = values != NOT_ASSESSED
        points = np.where(assessed, values, points)
        points_are_newer = np.where(
            assessed,
            category_period is None or points_period.start > category_period.start,
            points_are_newer,
        )

    from_points = select(
        [points >= thresholds.enhanced, points >= thresholds.standard],
        [PIPCategory.ENHANCED.index, PIPCategory.STANDARD.index],
        default=PIPCategory.NONE.index,
    )
    if category_period is None:
        return from_points
    carried = np.asarray(supplied_input(person, category_variable, category_period))
    return np.where(points_are_newer, from_points, carried)
