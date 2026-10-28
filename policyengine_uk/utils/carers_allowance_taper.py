"""Carer's Allowance before and under the Budget 2026 earnings taper.

Budget 2026 replaces the cliff edge at the earnings limit with a taper in
England and Wales from a date within 2030-31. Before the taper starts, a carer
above the limit gets nothing; once it applies, they get the rate less the
earnings above the limit. In the year it starts, each rule covers part of the
year. The couple restriction and the overlapping-benefit rule work week by
week, so each part gets them on its own award, and the parts are then weighted
by their share of the year.
"""

import numpy as np


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
