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
bears 0.15 x 3,000 = £450. The same holds with £5,000 of total employer pension
contributions (employer cost £35,000).
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

# The 2026 upper secondary and apprentice upper secondary thresholds as
# stored: £966.73 a week, £50,269.96 a year.
RELIEF_THRESHOLD = 966.73 * 52
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


# Total employer pension contributions with the £5,000 sacrifice: £2,000, and
# María's original case of £5,000 (the whole sacrifice). Employer cost is pay
# plus employer pension for a zero-rated earner: £32,000 or £35,000.
EMPLOYER_PENSIONS = {"£2,000 employer pension": 2_000, "£5,000 employer pension": 5_000}


@pytest.mark.parametrize("pension", EMPLOYER_PENSIONS)
@pytest.mark.parametrize("case", CASES)
def test_salary_sacrifice_excess_is_zero_rated(case, pension):
    age, apprentice, zero_rated = CASES[case]
    employer_pension = EMPLOYER_PENSIONS[pension]
    inputs = {
        "employment_income": {2029: PAY},
        "pension_contributions_via_salary_sacrifice": {2029: 5_000},
        "employer_pension_contributions": {2029: employer_pension},
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
        assert adjusted_cost == pytest.approx(PAY + employer_pension, abs=0.01)
    else:
        assert extra_ni == pytest.approx(0.15 * 3_000, abs=0.01)


# The fixed-cost equations must charge the sacrifice above the cap as NIC
# earnings, and count returned pay and the broad-base haircut as pay, as
# ni_class_1_employer and employer_cost do. baseline_employer_cost must equal
# the baseline simulation's employer_cost, and adjusted_employer_cost the
# reformed simulation's.
RATE_RISE_2029 = {
    "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {"2029": 0.16}
}
# No broad-base haircut in either population. A reform's baseline simulation
# is built from the situation under current law, so a reform setting the
# haircut rate to zero would remove it from the reformed population only. The
# haircut is an input here instead, which both populations share.
NO_HAIRCUT_2029 = {"salary_sacrifice_broad_base_haircut": {2029: 0}}


def assert_costs_match_employer_cost(simulation, year):
    baseline_cost = values(simulation, "baseline_employer_cost", year)
    adjusted_cost = values(simulation, "adjusted_employer_cost", year)
    np.testing.assert_allclose(
        baseline_cost, values(simulation.baseline, "employer_cost", year), atol=0.01
    )
    np.testing.assert_allclose(
        adjusted_cost, values(simulation, "employer_cost", year), atol=0.01
    )
    # Fixed employer cost: the reformed cost equals the baseline cost.
    np.testing.assert_allclose(adjusted_cost, baseline_cost, atol=0.01)


def test_rate_rise_charges_the_sacrifice_excess_at_fixed_cost():
    # María's 2029 case: aged 20, £49,000 pay, a £5,000 sacrifice against the
    # £2,000 cap and £2,000 of employer pension, no haircut in the baseline or
    # the reform. NIC earnings are 49,000 + 3,000 = £52,000, above the UST, so
    # the baseline cost is 51,000 + 0.15 x (52,000 - 50,269.96) = £51,259.51.
    # (With the 0.16% haircut in the baseline alone, pay there would be
    # £48,921.60 and the cost £51,169.35.) At 16% the charge
    # starts where pay plus pension reaches k = 2,000 + 50,269.96 - 3,000, so
    # pay plus pension is (51,259.51 + 0.16 x k) / 1.16 = 50,985.09 and pay
    # falls to £48,985.09, holding cost at £51,259.51.
    inputs = {
        "employment_income": {2029: 49_000},
        "pension_contributions_via_salary_sacrifice": {2029: 5_000},
        "employer_pension_contributions": {2029: 2_000},
        **NO_HAIRCUT_2029,
    }
    people = {"person": (20, False, inputs)}
    simulation = Simulation(situation=situation(people, 2029), reform=RATE_RISE_2029)

    assert values(simulation, "salary_sacrifice_pension_ni_excess", 2029)[
        0
    ] == pytest.approx(3_000, abs=0.01)
    assert values(simulation.baseline, "employment_income", 2029)[0] == pytest.approx(
        49_000, abs=0.01
    )
    baseline_cost = values(simulation, "baseline_employer_cost", 2029)[0]
    assert baseline_cost == pytest.approx(
        51_000 + 0.15 * (52_000 - RELIEF_THRESHOLD), abs=0.01
    )
    assert baseline_cost == pytest.approx(51_259.51, abs=0.01)
    k = 2_000 + RELIEF_THRESHOLD - 3_000
    new_pay = (baseline_cost + 0.16 * k) / 1.16 - 2_000
    assert new_pay == pytest.approx(48_985.09, abs=0.01)
    assert values(simulation, "employment_income", 2029)[0] == pytest.approx(
        new_pay, abs=0.01
    )
    assert values(simulation, "employer_ni_fixed_employer_cost_change", 2029)[
        0
    ] == pytest.approx(new_pay - 49_000, abs=0.01)
    assert_costs_match_employer_cost(simulation, 2029)


@pytest.mark.parametrize("case", CASES)
def test_rate_rise_with_sacrifice_excess_above_the_threshold(case):
    # The control above every threshold: £60,000 pay with the same sacrifice
    # and pension. The excess bears employer NI in both schedules.
    age, apprentice, _ = CASES[case]
    inputs = {
        "employment_income": {2029: 60_000},
        "pension_contributions_via_salary_sacrifice": {2029: 5_000},
        "employer_pension_contributions": {2029: 2_000},
        **NO_HAIRCUT_2029,
    }
    people = {"person": (age, apprentice, inputs)}
    simulation = Simulation(situation=situation(people, 2029), reform=RATE_RISE_2029)
    assert values(simulation, "employment_income", 2029)[0] < 60_000
    assert_costs_match_employer_cost(simulation, 2029)


@pytest.mark.parametrize("case", CASES)
def test_rate_rise_with_the_broad_base_haircut(case):
    # 2029 with the default haircut: pay before the reform is
    # 40,000 x (1 - 0.0016) = £39,936, and the cost equations must use it.
    age, apprentice, _ = CASES[case]
    inputs = {"employment_income": {2029: 40_000}}
    people = {"person": (age, apprentice, inputs)}
    baseline = Simulation(situation=situation(people, 2029))
    assert values(baseline, "employment_income", 2029)[0] == pytest.approx(
        39_936, abs=0.01
    )
    simulation = Simulation(situation=situation(people, 2029), reform=RATE_RISE_2029)
    assert_costs_match_employer_cost(simulation, 2029)


# The fixed-cost pay change must solve the employer cost equation on NIC
# earnings (pay plus statutory pay), piecewise around the reformed threshold,
# for earners whose pay alone is below their baseline threshold.
ZERO_RATED = {case: CASES[case] for case in CASES if CASES[case][2]}


@pytest.mark.parametrize("case", ZERO_RATED)
def test_rate_rise_with_statutory_pay_over_the_threshold(case):
    # 2026: £49,000 pay plus £2,000 statutory sick pay. Pay alone is below the
    # UST/AUST (£50,270), but NIC earnings of £51,000 are above it, so the 15%
    # to 16% rise raises employer NI and pay must fall to hold cost fixed.
    age, apprentice, _ = ZERO_RATED[case]
    inputs = {"employment_income": {2026: 49_000}, "statutory_sick_pay": {2026: 2_000}}
    people = {"person": (age, apprentice, inputs)}
    simulation = Simulation(situation=situation(people, 2026), reform=RATE_RISE)

    threshold = RELIEF_THRESHOLD
    baseline_cost = values(simulation, "baseline_employer_cost", 2026)[0]
    # 51,000 + 0.15 x (51,000 - 50,269.96) = 51,109.51
    assert baseline_cost == pytest.approx(
        51_000 + 0.15 * (51_000 - threshold), abs=0.01
    )
    assert baseline_cost == pytest.approx(51_109.51, abs=0.01)
    # Solve W + 2,000 + 0.16 x (W + 2,000 - T) = baseline cost for pay W.
    new_pay = (baseline_cost + 0.16 * threshold) / 1.16 - 2_000
    assert new_pay == pytest.approx(48_993.71, abs=0.01)
    pay = values(simulation, "employment_income", 2026)[0]
    assert pay == pytest.approx(new_pay, abs=0.01)
    adjusted_cost = values(simulation, "adjusted_employer_cost", 2026)[0]
    assert adjusted_cost == pytest.approx(baseline_cost, abs=0.01)


LOWER_RELIEF_THRESHOLDS = {
    f"gov.hmrc.national_insurance.class_1.thresholds.{name}": {"2026": 20_000 / 52}
    for name in ["upper_secondary_threshold", "apprentice_upper_secondary_threshold"]
}


@pytest.mark.parametrize("case", ZERO_RATED)
def test_lowered_relief_threshold_below_pay(case):
    # 2026: a reform lowers the UST and AUST to £20,000. Pay of £30,000 was
    # zero-rated (employer cost £30,000) and now crosses the reformed
    # threshold: P + 0.15 x (P - 20,000) = 30,000, so P = 33,000 / 1.15.
    age, apprentice, _ = ZERO_RATED[case]
    people = {"person": (age, apprentice, {"employment_income": {2026: PAY}})}
    simulation = Simulation(
        situation=situation(people, 2026), reform=LOWER_RELIEF_THRESHOLDS
    )

    pay = values(simulation, "employment_income", 2026)[0]
    assert pay == pytest.approx(33_000 / 1.15, abs=0.01)
    assert pay == pytest.approx(28_695.65, abs=0.01)
    assert values(simulation, "baseline_employer_cost", 2026)[0] == pytest.approx(
        PAY, abs=0.01
    )
    assert values(simulation, "adjusted_employer_cost", 2026)[0] == pytest.approx(
        PAY, abs=0.01
    )


@pytest.mark.parametrize("case", ZERO_RATED)
def test_raised_relief_threshold_above_pay(case):
    # The reverse crossing: pay of £60,000 bears 0.15 x (60,000 - 50,270) in
    # the baseline. Raising the UST and AUST to £70,000 removes the charge, so
    # pay rises by the whole saving to hold employer cost fixed.
    age, apprentice, _ = ZERO_RATED[case]
    people = {"person": (age, apprentice, {"employment_income": {2026: 60_000}})}
    reform = {name: {"2026": 70_000 / 52} for name in LOWER_RELIEF_THRESHOLDS}
    simulation = Simulation(situation=situation(people, 2026), reform=reform)

    baseline_cost = values(simulation, "baseline_employer_cost", 2026)[0]
    # 60,000 + 0.15 x (60,000 - 50,269.96) = 61,459.51
    assert baseline_cost == pytest.approx(
        60_000 + 0.15 * (60_000 - RELIEF_THRESHOLD), abs=0.01
    )
    assert baseline_cost == pytest.approx(61_459.51, abs=0.01)
    pay = values(simulation, "employment_income", 2026)[0]
    assert pay == pytest.approx(baseline_cost, abs=0.01)
    assert values(simulation, "adjusted_employer_cost", 2026)[0] == pytest.approx(
        baseline_cost, abs=0.01
    )
