"""The UC qualifying young person test follows the family's tax credit closure.

The model pays tax credits to the family, on every member's reports, and
ends them when the claimant's and partner's legacy awards close
(legacy_benefits_closed, read by is_CTC_eligible and is_WTC_eligible).
Nobody is entitled to an award the model has ended, so the predicate reads a
young person's own tax credit report only while the family's legacy awards
stay open (SI 2014/1230 reg. 28).

In the baseline the family's legacy awards close only once a benefit has
closed, and tax credits close first (gov.dwp.tax_credits.active turns false
on 6 April 2025, Income Support on 1 April 2026), so the year gate already
covers every closed tax credit report. These tests keep tax credits paying
in 2026 by a parameter reform, so the family's closure decides.

The household: a parent aged 45 and a 17-year-old on a non-advanced course,
North East, owned outright, no income, in 2026. The parent claims Universal
Credit as a single claimant over 25: £424.90 a month (standard_allowance
SINGLE_OLD) and £351.88 a month for a qualifying young person (child element
first higher amount), so 12 x (424.90 + 351.88) = £9,321.36 with the child
element and 12 x 424.90 = £5,098.80 without it.
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2026
TAX_CREDITS_PAYING = {"gov.dwp.tax_credits.active": {"2020-01-01.2100-12-31": True}}


def household(young_report, parent_report=None):
    parent = {
        "age": {YEAR: 45},
        "is_parent": {YEAR: True},
        "is_claimant_or_partner": {YEAR: True},
    }
    if parent_report:
        parent[parent_report] = {YEAR: 3_000}
    return {
        "people": {
            "parent": parent,
            "young_person": {
                "age": {YEAR: 17},
                "current_education": {YEAR: "POST_SECONDARY"},
                "is_claimant_or_partner": {YEAR: False},
                young_report: {YEAR: 1_000},
            },
        },
        "benunits": {"benunit": {"members": ["parent", "young_person"]}},
        "households": {
            "household": {
                "members": ["parent", "young_person"],
                "region": {YEAR: "NORTH_EAST"},
                "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
            }
        },
    }


def outcome(situation, reform):
    sim = Simulation(situation=situation, reform=reform)
    return (
        sim.calculate("legacy_benefits_closed", YEAR).tolist(),
        sim.calculate("is_qualifying_young_person_for_universal_credit", YEAR).tolist(),
        round(float(sim.calculate("universal_credit", YEAR)[0]), 2),
    )


@pytest.mark.parametrize(
    "report", ["child_tax_credit_reported", "working_tax_credit_reported"]
)
def test_a_young_persons_tax_credit_report_excludes_while_the_family_stays_open(
    report,
):
    # Tax credits pay in 2026 under the reform, and nothing closes the
    # family's legacy awards, so the young person's own report excludes them.
    assert outcome(household(report), TAX_CREDITS_PAYING) == (
        [False],
        [False, False],
        5_098.80,
    )


@pytest.mark.parametrize(
    "report", ["child_tax_credit_reported", "working_tax_credit_reported"]
)
def test_the_parents_closed_legacy_award_ends_the_young_persons_tax_credits(
    report,
):
    # The parent's own Income Support report in 2026, after Income Support
    # closed, closes the family's legacy awards, which ends the family's tax
    # credits, the young person's report included.
    situation = household(report, "income_support_reported")
    assert outcome(situation, TAX_CREDITS_PAYING) == (
        [True],
        [False, True],
        9_321.36,
    )
