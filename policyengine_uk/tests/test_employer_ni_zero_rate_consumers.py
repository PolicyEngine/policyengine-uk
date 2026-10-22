"""The employer cost and salary sacrifice variables apply the employer NI
zero rates.

ni_class_1_employer zero-rates earnings up to the upper secondary threshold
for an earner under 21 (SSCBA 1992 s.9A) and up to the apprentice upper
secondary threshold for an apprentice under 25 (s.9B). The variables that
recompute employer NI themselves (baseline_employer_cost,
adjusted_employer_cost, employer_ni_fixed_employer_cost_change and
salary_sacrifice_pension_ni_employer) must apply the same schedule.

Case 1 (2026): pay of £30,000, no pension contributions, employer rate raised
from 15% to 16% with the default fixed-cost incidence. Earnings are below the
UST and AUST (£50,270), so an earner aged 20 or an apprentice aged 24 pays no
employer NI before or after the rise, and pay does not change. An earner aged
21, or an apprentice aged 25, is charged on earnings above the secondary
threshold (£5,000): employer cost 30,000 + 0.15 x 25,000 = £33,750, and pay
at fixed cost solves P + 0.16 x (P - 5,000) = 33,750, so
P = (33,750 + 800) / 1.16 = £29,784.48, a cut of £215.52.

Case 2 (2029): pay of £30,000 with a £5,000 salary sacrifice against the
£2,000 cap, so the £3,000 excess enters NIC earnings only (total £33,000;
pay stays £30,000), and a £2,000 employer pension contribution. For an
earner aged 20 or an apprentice aged 24 all of it is below the UST and AUST,
so the excess bears no employer NI and employer cost is 30,000 + 2,000 =
£32,000. At age 21 the £3,000 excess sits above the secondary threshold and
bears 0.15 x 3,000 = £450.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

RATE_RISE = {
    "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {"2026": 0.16}
}
PAY = 30_000
CASES = {
    # name: (age, is_apprentice, zero_rated)
    "aged 20": (20, False, True),
    "aged 21": (21, False, False),
    "apprentice aged 24": (24, True, True),
    "apprentice aged 25": (25, True, False),
}


def situation(people, year):
    return {
        "people": {
            name: {
                "age": {year: age},
                "is_apprentice": {year: apprentice},
                **inputs,
            }
            for name, (age, apprentice, inputs) in people.items()
        },
        "benunits": {f"benunit_{name}": {"members": [name]} for name in people},
        "households": {f"household_{name}": {"members": [name]} for name in people},
    }


def values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


@pytest.mark.parametrize("case", CASES)
def test_rate_rise_leaves_zero_rated_pay_unchanged(case):
    age, apprentice, zero_rated = CASES[case]
    people = {"person": (age, apprentice, {"employment_income": {2026: PAY}})}
    simulation = Simulation(situation=situation(people, 2026), reform=RATE_RISE)

    pay = values(simulation, "employment_income", 2026)[0]
    change = values(simulation, "employer_ni_fixed_employer_cost_change", 2026)[0]
    baseline_cost = values(simulation, "baseline_employer_cost", 2026)[0]
    adjusted_cost = values(simulation, "adjusted_employer_cost", 2026)[0]
    employer_ni = values(simulation, "ni_class_1_employer", 2026)[0]

    if zero_rated:
        assert change == pytest.approx(0, abs=0.01)
        assert pay == pytest.approx(PAY, abs=0.01)
        assert baseline_cost == pytest.approx(PAY, abs=0.01)
        assert adjusted_cost == pytest.approx(PAY, abs=0.01)
        assert employer_ni == pytest.approx(0, abs=0.01)
    else:
        new_pay = (PAY + 0.15 * (PAY - 5_000) + 0.16 * 5_000) / 1.16
        assert pay == pytest.approx(new_pay, abs=0.01)
        assert change == pytest.approx(new_pay - PAY, abs=0.01)
        assert change == pytest.approx(-215.52, abs=0.01)
        assert baseline_cost == pytest.approx(33_750, abs=0.01)
        # Fixed employer cost: the reformed cost equals the baseline cost.
        assert adjusted_cost == pytest.approx(33_750, abs=0.01)
        assert employer_ni == pytest.approx(0.16 * (new_pay - 5_000), abs=0.01)


def test_rate_rise_with_mixed_ages_in_one_simulation():
    # Per-person thresholds must not break the no-change shortcut for a
    # population of more than one person.
    people = {
        case.replace(" ", "_"): (age, apprentice, {"employment_income": {2026: PAY}})
        for case, (age, apprentice, _) in CASES.items()
    }
    simulation = Simulation(situation=situation(people, 2026), reform=RATE_RISE)
    change = values(simulation, "employer_ni_fixed_employer_cost_change", 2026)
    expected = [0 if zero_rated else -215.52 for (_, _, zero_rated) in CASES.values()]
    np.testing.assert_allclose(change, expected, atol=0.01)


@pytest.mark.parametrize("case", CASES)
def test_salary_sacrifice_excess_is_zero_rated(case):
    age, apprentice, zero_rated = CASES[case]
    inputs = {
        "employment_income": {2029: PAY},
        "pension_contributions_via_salary_sacrifice": {2029: 5_000},
        "employer_pension_contributions": {2029: 2_000},
    }
    people = {"person": (age, apprentice, inputs)}
    simulation = Simulation(
        situation=situation(people, 2029),
        reform={
            "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate": {
                "2029": 0
            },
        },
    )

    returned = values(simulation, "salary_sacrifice_returned_to_income", 2029)[0]
    excess = values(simulation, "salary_sacrifice_pension_ni_excess", 2029)[0]
    nic_earnings = values(simulation, "ni_class_1_income", 2029)[0]
    pay = values(simulation, "employment_income", 2029)[0]
    extra_ni = values(simulation, "salary_sacrifice_pension_ni_employer", 2029)[0]
    adjusted_cost = values(simulation, "adjusted_employer_cost", 2029)[0]
    employer_ni = values(simulation, "ni_class_1_employer", 2029)[0]

    # The excess enters NIC earnings only; it is not returned to pay.
    assert returned == pytest.approx(0, abs=0.01)
    assert excess == pytest.approx(3_000, abs=0.01)
    assert nic_earnings == pytest.approx(33_000, abs=0.01)
    assert pay == pytest.approx(PAY, abs=0.01)
    if zero_rated:
        assert extra_ni == pytest.approx(0, abs=0.01)
        assert employer_ni == pytest.approx(0, abs=0.01)
        assert adjusted_cost == pytest.approx(32_000, abs=0.01)
    else:
        assert extra_ni == pytest.approx(0.15 * 3_000, abs=0.01)
