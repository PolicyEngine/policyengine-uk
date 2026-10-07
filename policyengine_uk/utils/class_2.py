"""Class 2 National Insurance rules shared by ni_class_2 and by the notional
Class 2 that the Universal Credit minimum income floor deducts.

Both charge a whole tax year of self-employment, so they share the s.11(2)
liability test and the number of contribution weeks in the year.
"""

import datetime

import numpy as np


def class_2_contribution_weeks(year: int) -> int:
    """Contribution weeks in the tax year that starts on 6 April of ``year``.

    A contribution week is "a period of seven days beginning with midnight
    between Saturday and Sunday" (SI 2001/1004 reg. 1(2)), and the first week
    of a contribution year starts on the first Sunday after 5 April (HMRC
    NIM70200). A year therefore has one week for each Sunday from 6 April to
    the following 5 April: 53 in 2019-20 and 2025-26, 52 in the other years
    from 2015-16 to 2026-27. NIM70200: "a person who is self-employed for the
    full year will be liable for all 53 weeks."
    """
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 5)
    # date.weekday() is 6 on a Sunday.
    first_sunday = start + datetime.timedelta(days=(6 - start.weekday()) % 7)
    return (end - first_sunday).days // 7 + 1


def class_2_liable(relevant_profits, class_2):
    """Whether s.11(2) SSCBA 1992 makes an earner with these relevant profits
    liable to Class 2 for the year.

    From 2022-23 only relevant profits that exceed the lower profits threshold
    are liable; those from the small profits threshold up to it are treated as
    paid (s.11(5A)-(5B)) and cost nothing. Before then liability started at
    the small profits threshold ("of, or exceeding"). ``class_2`` is the
    gov.hmrc.national_insurance.class_2 parameter node for the year.
    """
    return np.where(
        class_2.lower_profits_threshold_applies,
        relevant_profits > class_2.lower_profits_threshold,
        relevant_profits >= class_2.small_profits_threshold,
    )
