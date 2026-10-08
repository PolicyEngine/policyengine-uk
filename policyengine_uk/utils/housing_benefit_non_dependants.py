"""Claimant-specific Housing Benefit non-dependant change histories.

The input is factual award history, not a user-selected exemption. Core's
existing person/family/household entities have no claimant/non-dependant
relationship entity, so the sparse relationship records are JSON strings on
each claimant's benefit unit. Parsing is separate from the date/amount rule.
"""

import json
from datetime import date

import numpy as np


def _day(value):
    if not isinstance(value, str):
        raise ValueError("Non-dependant history dates must be ISO calendar dates")
    try:
        return np.datetime64(date.fromisoformat(value), "D")
    except ValueError as error:
        raise ValueError(
            "Non-dependant history dates must be ISO calendar dates"
        ) from error


def postponed_non_dep_increases(
    benunit, period, current_deductions, full_student_exemption, student, applies, weeks
):
    """Return only positive increases still postponed, before rent allocation.

    SI 2006/214 reg 59(10)-(13); SR 2006/406 reg 57(12)-(15).
    First qualifying increase starts the clock. An uprating is not an arrival
    or a change in the person's circumstances. Existing deductions, decreases
    and exemptions remain effective.
    """
    person = benunit.members
    histories = benunit("housing_benefit_non_dep_increase_history", period)
    now = benunit("housing_benefit_assessment_date", period)
    award_start = benunit("housing_benefit_continuous_award_start", period)
    weekdays = benunit("housing_benefit_benefit_week_start", period)
    if np.any((weekdays < 0) | (weekdays > 6)):
        raise ValueError("Housing Benefit benefit-week weekday must be 0 through 6")
    person_indices = {
        str(identifier): index for index, identifier in enumerate(person.ids)
    }
    household_of_person = person.household.members_entity_id
    household_of_claim = benunit.max(household_of_person)
    claim_indices, indices, previous_amounts, last_dates = [], [], [], []
    event_records, event_dates, event_kinds = [], [], []
    for claim, encoded in enumerate(histories):
        if not applies[claim] or encoded in ("", "[]"):
            continue
        try:
            records = json.loads(encoded)
        except (ValueError, TypeError) as error:
            raise ValueError(
                "Housing Benefit non-dependant history must be a JSON array"
            ) from error
        if not isinstance(records, list):
            raise ValueError(
                "Housing Benefit non-dependant history must be a JSON array"
            )
        seen = set()
        for record in records:
            if not isinstance(record, dict) or set(record) != {
                "person_id",
                "previous_weekly_deduction",
                "last_effective_date",
                "increases",
            }:
                raise ValueError(
                    "Non-dependant history has missing or unexpected fields"
                )
            identifier = record["person_id"]
            if (
                not isinstance(identifier, str)
                or identifier not in person_indices
                or identifier in seen
            ):
                raise ValueError(
                    "Non-dependant history needs unique existing person IDs"
                )
            seen.add(identifier)
            index = person_indices[identifier]
            if household_of_person[index] != household_of_claim[claim]:
                raise ValueError(
                    "Non-dependant history person must be in the claimant's household"
                )
            previous = record["previous_weekly_deduction"]
            if (
                isinstance(previous, bool)
                or not isinstance(previous, (int, float))
                or not np.isfinite(previous)
                or previous < 0
            ):
                raise ValueError(
                    "Previous non-dependant deduction must be a finite nonnegative weekly amount"
                )
            last = _day(record["last_effective_date"])
            events = record["increases"]
            if not isinstance(events, list):
                raise ValueError(
                    "Non-dependant increases must be an array of dated events"
                )
            record_index = len(claim_indices)
            claim_indices.append(claim)
            indices.append(index)
            previous_amounts.append(previous)
            last_dates.append(last)
            for event in events:
                if not isinstance(event, dict) or set(event) != {"date", "kind"}:
                    raise ValueError("Each non-dependant increase needs date and kind")
                event_date = _day(event["date"])
                if event["kind"] not in ("arrival", "circumstances", "uprating"):
                    raise ValueError("Unknown non-dependant increase kind")
                event_records.append(record_index)
                event_dates.append(event_date)
                event_kinds.append(event["kind"] != "uprating")
    # The loops above only decode and validate sparse relationship records.
    # Apply the policy rule to arrays, including multiple claims per person.
    claims = np.asarray(claim_indices, dtype=int)
    people = np.asarray(indices, dtype=int)
    records = np.asarray(event_records, dtype=int)
    dates = np.asarray(event_dates, dtype="datetime64[D]")
    last = np.asarray(last_dates, dtype="datetime64[D]")
    since = np.maximum(award_start[claims], last)
    valid = (
        np.asarray(event_kinds, dtype=bool)
        & (dates > since[records])
        & (dates <= now[claims[records]])
    )
    first = np.full(len(claims), "9999-01-01", dtype="datetime64[D]")
    np.minimum.at(first, records[valid], dates[valid])
    due = first + np.timedelta64(int(weeks * 7), "D")
    weekday = (due - np.datetime64("1970-01-05", "D")).astype(int) % 7
    due += ((weekdays[claims] - weekday) % 7).astype("timedelta64[D]")
    current = np.where(
        full_student_exemption[claims] & student[people], 0, current_deductions[people]
    )
    pending = (first < np.datetime64("9999-01-01")) & (now[claims] < due)
    difference = np.maximum(0, current - np.asarray(previous_amounts) * 52) * pending
    return np.bincount(claims, weights=difference, minlength=benunit.count)
