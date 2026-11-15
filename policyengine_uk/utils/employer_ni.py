import numpy as np
from policyengine_core.model_api import WEEKS_IN_YEAR, max_, where


def secondary_class_1_threshold(person, period, class_1):
    """Annual earnings above which the secondary percentage applies.

    The secondary threshold (SSCBA 1992 s.9), raised to the upper secondary
    threshold for an earner under 21 (s.9A) and to the apprentice upper
    secondary threshold for a relevant apprentice under 25 (s.9B). s.9A(1A)
    gives s.9B priority, and s.9A still zero-rates an under-21 apprentice's
    earnings above the apprentice threshold up to the under-21 one, so the
    higher threshold applies. Earnings above it bear the secondary percentage
    (s.9A(9)-(10), s.9B(7)).

    `class_1` is a Class 1 parameter node, so a variable can apply the
    baseline and the reformed schedule with the same function.
    """
    thresholds = class_1.thresholds
    age_limits = class_1.secondary_zero_rate_age_limits
    age = person("age", period)
    under_21_threshold = where(
        age < age_limits.under_21_group,
        thresholds.upper_secondary_threshold,
        0,
    )
    relevant_apprentice = person("is_apprentice", period) & (
        age < age_limits.relevant_apprentice
    )
    apprentice_threshold = where(
        relevant_apprentice,
        thresholds.apprentice_upper_secondary_threshold,
        0,
    )
    weekly = max_(
        class_1.employer_scale.components[1].threshold,
        max_(under_21_threshold, apprentice_threshold),
    )
    # In the earnings' float32, so that where no zero rate applies the charge
    # is computed exactly as with the scalar secondary threshold.
    return np.asarray(weekly * WEEKS_IN_YEAR, dtype=np.float32)


def salary_sacrifice_cost_terms(person, period):
    """The salary sacrifice terms in an employer's cost and NIC earnings.

    Employment income includes salary sacrifice returned to ordinary pay and
    the broad-base haircut, so both are pay. Class 1 earnings also include the
    sacrifice above the cap (salary_sacrifice_pension_ni_excess), which bears
    employer NI but is neither cash pay nor an actual pension payment.

    `person` is the Person population of either the reformed or the baseline
    simulation, so a variable can take each schedule's own terms. Returns the
    pay terms and the NIC-only earnings.
    """
    pay = person("salary_sacrifice_returned_to_income", period) + person(
        "salary_sacrifice_broad_base_haircut", period
    )
    return pay, person("salary_sacrifice_pension_ni_excess", period)
