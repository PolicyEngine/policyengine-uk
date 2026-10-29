"""Carer's Allowance before and under the Budget 2026 earnings taper.

Budget 2026 replaces the cliff edge at the earnings limit with a taper in
England and Wales from a date within 2030-31. Before the taper starts, a carer
above the limit gets nothing; once it applies, they get the rate less the
earnings above the limit. In the year it starts, each rule covers part of the
year. The couple restriction and the overlapping-benefit rule work week by
week, so each part gets them on its own award, weighted by its share of the
year.

A person's weekly award is the same in every part of the year in which it is
positive: the full rate wherever they are within the earnings limit, and the
tapered rate, which only the part under the taper pays, where they are above
it. So the annual amounts carry the parts as shares of the year: the
pre-overlap award is the candidate award scaled by the share the couple
restriction keeps, and the overlapping benefits come off for that share.

The shares describe an annual award only where the model's own formulas
calculate it from the parts of the year. An award that an input supplies, or
that a reform neutralizes or calculates with a formula of its own, carries no
dates, even where it equals the model's: it gets the whole-year treatment, and
so does every stage after it.
"""

import numpy as np
from policyengine_core.commons.formulas import WEEKS_IN_YEAR

from policyengine_uk.utils.couple_carer_award import limit_carer_benefit_to_one_partner
from policyengine_uk.utils.formula_origin import calculated_by
from policyengine_uk.utils.supplied_inputs import supplied_input


def carers_allowance_weekly_by_part_of_year(person, period, parameters):
    """The weekly award, before the couple and overlap restrictions, in each
    part of the year, as (share of the year, weekly award) pairs. A part with
    no share of the year is left out, so outside the year the taper starts in
    there is one part."""
    ca = parameters(period).gov.dwp.carers_allowance
    in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
    csp_replaces_ca = period.start.year >= 2025
    receives_ca = person("carers_allowance_reported", period) > 0
    meets_age_condition = person("age", period) >= ca.min_age
    meets_work_condition = person("care_hours", period) >= ca.min_hours
    would_claim = person("would_claim_carers_allowance", period)
    eligible = (
        ~(in_scotland & csp_replaces_ca)
        & (meets_work_condition | receives_ca)
        & would_claim
        & meets_age_condition
    )
    # SSCBA 1992 s. 70(1)(b): no allowance for anyone gainfully employed,
    # which reg. 8 of the 1976 Regulations defines by an earnings limit.
    # It applies to reported recipients too.
    gainfully_employed = person("is_gainfully_employed_for_carers_allowance", period)
    # Budget 2026 (para 6.13) replaces that cliff edge in England and Wales
    # with a taper: the weekly allowance less taper.rate for each pound of
    # weekly earnings above the limit.
    taper = ca.earnings_taper
    country = person.household("country", period).decode_to_str()
    excess = person("carers_allowance_weekly_earnings_above_limit", period)
    tapered = np.isin(country, list(taper.countries)) * np.maximum(
        0, ca.rate - taper.rate * excess
    )
    parts = (
        (1 - taper.applies, np.where(gainfully_employed, 0, ca.rate)),
        (taper.applies, np.where(gainfully_employed, tapered, ca.rate)),
    )
    return [(share, eligible * weekly) for share, weekly in parts if share > 0]


def carers_allowance_annual_award(parts):
    """The annual award the parts of the year add up to."""
    return sum(share * weekly * WEEKS_IN_YEAR for share, weekly in parts)


def carers_allowance_shares_of_year(person, period, parts):
    """From carers_allowance_weekly_by_part_of_year's parts: the share of the
    year in which the person has an award before the couple restriction, and
    the share in which the restriction leaves it with them."""
    candidate = kept = 0
    for share, weekly in parts:
        selected = limit_carer_benefit_to_one_partner(person, period, weekly)
        candidate = candidate + share * (weekly > 0)
        kept = kept + share * (selected > 0)
    return candidate, kept


def calculated_from_parts_of_year(person, period, model_variable):
    """Whether the simulation calculates model_variable, a stage before the
    payment, with the model's own formula, and so from the parts of the
    year: no input supplies it, and no reform neutralizes it or puts a
    formula of its own in place of the model's."""
    name = model_variable.__name__
    variable = person.simulation.tax_benefit_system.get_variable(name)
    return (
        supplied_input(person, name, period) is None
        and not variable.is_neutralized
        and calculated_by(person, name, period, model_variable)
    )
