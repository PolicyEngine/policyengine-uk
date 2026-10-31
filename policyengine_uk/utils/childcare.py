"""Internal term budgets for England's funded childcare entitlements.

The existing annual model gives equal weight to terms beginning in April,
September and January. DfE guidance effective 1 April 2026, A1.2/A1.7 and
SI 2014/2147 reg 3 start the base entitlements after the relevant birthday;
A1.4 keeps targeted provision until the universal term begins. A1.11 counts
the first base hours within working-parent provision in those same terms.

The national-average age-group funding table remains an annual valuation
proxy, sampled once for the model year, not a provider fee or term calendar.
The qualifying age band is shared by all hours funded in a term. Annual
working-parent hours/rollout and family eligibility/take-up stay annual.

Existing explicitly supplied annual shares or amounts have no term identity.
Their complete original calculation remains authoritative; these helpers do
not infer timing for them or introduce a consumer-facing term input schema.

https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026
https://www.legislation.gov.uk/uksi/2014/2147/regulation/3
"""

import numpy as np
from policyengine_core.model_api import MONTHS_IN_YEAR

from policyengine_uk.utils.dates import add_months_to_yyyymmdd, birth_day, term_starts
from policyengine_uk.utils.supplied_inputs import supplied_input


LEGACY_CHILDCARE_INPUTS = (
    "early_years_term_share_before_school",
    "extended_childcare_entitlement_term_share",
    "universal_childcare_entitlement",
    "targeted_childcare_entitlement",
    "extended_childcare_entitlement_total_per_child",
)


def uses_legacy_childcare_inputs(person, period) -> bool:
    """Recognise genuine stored inputs, including zero, never calculated caches."""
    return any(
        supplied_input(person, name, period) is not None
        for name in LEGACY_CHILDCARE_INPUTS
    )


def _school_terms(person, period, starts):
    # Only the native calculated route calls this: its before-school share is
    # a count of whole terms, with float32 rounding. Opaque inputs use legacy.
    count = np.rint(
        person("early_years_term_share_before_school", period) * len(starts)
    )
    return tuple(index < count for index in range(len(starts)))


def _scale_in_term(scale, born, start):
    """Apply an existing age scale from the term after each threshold birthday."""
    result = np.zeros(born.shape, dtype=np.asarray(scale.amounts).dtype)
    for threshold, amount in zip(scale.thresholds, scale.amounts):
        if np.isneginf(threshold):
            result = np.full(born.shape, amount)
        elif not np.isposinf(threshold):
            reaches = add_months_to_yyyymmdd(born, MONTHS_IN_YEAR * threshold)
            result = np.where(reaches < start, amount, result)
    return result


def universal_childcare_terms(person, period, parameters) -> tuple:
    """Native age/school term intersection; upper-age guards remain in eligibility."""
    starts = term_starts(period.start.year)
    born = birth_day(person, period)
    minimum = parameters(period).gov.dfe.universal_childcare_entitlement.age.min
    reaches = add_months_to_yyyymmdd(born, MONTHS_IN_YEAR * minimum)
    return tuple(
        (reaches < start) & school
        for start, school in zip(starts, _school_terms(person, period, starts))
    )


def targeted_childcare_terms(person, period, parameters) -> tuple:
    """Native targeted age-scale and before-school term intersection."""
    starts = term_starts(period.start.year)
    born = birth_day(person, period)
    scale = parameters(period).gov.dfe.targeted_childcare_entitlement.age_eligibility
    return tuple(
        _scale_in_term(scale, born, start).astype(bool) & school
        for start, school in zip(starts, _school_terms(person, period, starts))
    )


def childcare_term_value(person, period, parameters, component: str):
    """Compute one native component without adding unrelated award dependencies."""
    p = parameters(period).gov.dfe
    starts = term_starts(period.start.year)
    count = len(starts)
    born = birth_day(person, period)
    age = person("age", period)
    school = _school_terms(person, period, starts)
    participating = person.benunit("extended_childcare_entitlement_eligible", period)
    child_hours = person("max_free_entitlement_hours_used", period)
    used_annual = child_hours * p.weeks_per_year
    universal_hours = (
        np.minimum(used_annual, p.universal_childcare_entitlement.hours) / count
    )
    targeted_hours = (
        np.minimum(used_annual, p.targeted_childcare_entitlement.hours_entitlement)
        / count
    )
    working_hours = np.zeros(person.count)
    working_terms = tuple(np.zeros(person.count, dtype=bool) for _ in starts)
    # This is a scalar shortcut for a whole population, not an array branch.
    # As before, a non-participating family need not calculate child work rules.
    if np.any(participating):
        qualifying = person("extended_childcare_entitlement_qualifying_child", period)
        family_hours = person.benunit("maximum_extended_childcare_hours_usage", period)
        # Keep the existing annual hours/rollout schedule unchanged.
        hours_age = np.maximum(
            age, p.extended_childcare_entitlement.young_child_minimum_age
        )
        weekly_working = np.minimum(
            np.minimum(
                p.extended_childcare_entitlement.hours.calc(hours_age), child_hours
            ),
            family_hours,
        )
        working_hours = weekly_working * p.weeks_per_year / count
        working_count = np.rint(
            person("extended_childcare_entitlement_term_share", period) * count
        )
        working_terms = tuple(
            (index >= count - working_count)
            & school[index]
            & participating
            & qualifying
            for index in range(count)
        )

    universal_terms = tuple(np.zeros(person.count, dtype=bool) for _ in starts)
    targeted_terms = targeted_childcare_terms(person, period, parameters)
    universal_eligible = np.zeros(person.count, dtype=bool)
    targeted_eligible = np.zeros(person.count, dtype=bool)
    if component in ("universal", "extended"):
        universal_terms = universal_childcare_terms(person, period, parameters)
        universal_eligible = person("universal_childcare_entitlement_eligible", period)
    # A working-total calculation does not depend on either base programme.
    # A universal calculation needs targeted eligibility only if a hypothetical
    # reform makes their native terms overlap; baseline terms are disjoint.
    if component in ("targeted", "extended") or (
        component == "universal"
        and any(np.any(u & t) for u, t in zip(universal_terms, targeted_terms))
    ):
        targeted_eligible = person.benunit(
            "targeted_childcare_entitlement_eligible", period
        )
    claims_universal = (
        person.benunit("would_claim_universal_childcare", period)
        if component == "universal"
        else False
    )
    claims_targeted = (
        person.benunit("would_claim_targeted_childcare", period)
        if component == "targeted"
        else False
    )
    value = np.zeros(person.count, dtype=np.float64)
    for index, start in enumerate(starts):
        rate = _scale_in_term(p.childcare_funding_rate, born, start)
        target = targeted_terms[index] & targeted_eligible
        universal = universal_terms[index] & universal_eligible
        target_value = targeted_hours * target * rate
        universal_value = universal_hours * universal * rate
        working_value = working_hours * working_terms[index] * rate
        if component == "working":
            value += working_value
        elif component == "targeted":
            value += np.where(
                claims_targeted, target_value, np.minimum(target_value, working_value)
            )
        elif component == "universal":
            # Targeted funding has priority if a reform overlaps the age bands.
            common = np.minimum(
                universal_value,
                np.maximum(working_value - np.minimum(target_value, working_value), 0),
            )
            value += np.where(claims_universal, universal_value, common)
        elif component == "extended":
            value += np.maximum(working_value - target_value - universal_value, 0)
    return np.round(value, 2) if component == "extended" else value
