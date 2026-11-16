"""Maintenance in the Income Support means test for continuing awards.

IS Regs 1987 reg 40 counts non-earnings income. Schedule 9 para 15(3)(a)
excludes former-partner maintenance from the voluntary-payment disregard;
para 73 disregards child maintenance. Reg 23 counts the claimant's and
partner's income, but not a child's or another benefit-unit member's income.

https://www.legislation.gov.uk/uksi/1987/1967/regulation/40
https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/15
https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/73
https://www.legislation.gov.uk/uksi/1987/1967/schedule/8/paragraph/5
https://www.legislation.gov.uk/uksi/1987/1967/schedule/8/paragraph/6
https://www.gov.uk/government/publications/benefit-and-pension-rates-2024-to-2025/benefit-and-pension-rates-2024-to-2025
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2024


def family(maintenance=None, partner=False, other_adult=False):
    people = {
        "claimant": {
            "age": {YEAR: 40},
            "is_parent": {YEAR: True},
            "is_claimant_or_partner": {YEAR: True},
            "income_support_reported": {YEAR: 100},
            "employment_income": {YEAR: 2_000},
            "hours_worked": {YEAR: 520},
        },
        "child": {
            "age": {YEAR: 4},
            "is_claimant_or_partner": {YEAR: False},
        },
    }
    if partner:
        people["partner"] = {
            "age": {YEAR: 38},
            "is_claimant_or_partner": {YEAR: True},
        }
    if other_adult:
        people["other_adult"] = {
            "age": {YEAR: 21},
            "is_claimant_or_partner": {YEAR: False},
            "current_education": {YEAR: "NOT_IN_EDUCATION"},
        }
    for person, variable, amount in maintenance or []:
        people[person][variable] = {YEAR: amount}
    members = list(people)
    return Simulation(
        situation={
            "people": people,
            "benunits": {"family": {"members": members}},
            "households": {"home": {"members": members, "region": "LONDON"}},
        }
    )


def amount(simulation, variable):
    return float(simulation.calculate(variable, YEAR)[0])


def test_spousal_maintenance_reduces_an_existing_income_support_award():
    baseline = family()
    maintained = family([("claimant", "spousal_maintenance_income", 1_200)])
    # 2024-25 lone-parent allowance: £90.50 * 52 = £4,706. Earnings of
    # £2,000 exceed the £20 * 52 = £1,040 earnings disregard, leaving £960.
    # Maintenance is counted in full: £960 + £1,200 = £2,160. The continuing
    # award therefore falls from £4,706 - £960 = £3,746 to £2,546.
    assert amount(baseline, "income_support_eligible") == 1
    assert amount(maintained, "income_support_eligible") == 1
    assert amount(baseline, "income_support_applicable_income") == pytest.approx(960)
    assert amount(maintained, "income_support_applicable_income") == pytest.approx(
        2_160
    )
    assert amount(baseline, "income_support") == pytest.approx(3_746, abs=0.01)
    assert amount(maintained, "income_support") == pytest.approx(2_546, abs=0.01)


@pytest.mark.parametrize("recipient", ["claimant", "partner"])
def test_either_partners_spousal_maintenance_counts(recipient):
    baseline = family(partner=True)
    maintained = family(
        [(recipient, "spousal_maintenance_income", 1_200)], partner=True
    )
    # Couple earnings disregard: £10 * 52 = £520. The claimant's £2,000
    # earnings leave £1,480; either partner's £1,200 raises it to £2,680.
    assert amount(baseline, "income_support_applicable_income") == pytest.approx(1_480)
    assert amount(maintained, "income_support_applicable_income") == pytest.approx(
        2_680
    )


def test_child_maintenance_and_other_members_income_remain_disregarded():
    baseline = family(other_adult=True)
    maintained = family(
        [
            ("claimant", "maintenance_income", 1_200),
            ("other_adult", "spousal_maintenance_income", 3_000),
            ("child", "spousal_maintenance_income", 2_000),
        ],
        other_adult=True,
    )
    # Only the claimant's £2,000 earnings count: £2,000 - £1,040 = £960.
    for simulation in (baseline, maintained):
        assert amount(simulation, "income_support_applicable_income") == pytest.approx(
            960
        )
        assert amount(simulation, "income_support") == pytest.approx(3_746, abs=0.01)
