"""MOCK regressions for pension relief in adjusted net income (#2243).

ITA 2007 s.58 deducts gross relieved relief-at-source contributions from
adjusted net income. They restore the personal allowance and reduce HICBC,
while entering the income tax rate-band base only once. All populations are
synthetic situations; these tests never load or download a survey dataset.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation


@pytest.fixture(scope="module")
def template():
    return Simulation(situation={"people": {"template": {"age": {2024: 45}}}})


def simulate(
    template,
    year,
    cases,
    *,
    with_child=False,
    gift_aid=0,
    supplied_ani=None,
    person_inputs=None,
):
    """Give each taxpayer a separate London household and optional child."""
    people, benunits, households, adult_indices = {}, {}, {}, []
    for index, (wages, contributions) in enumerate(cases):
        adult = f"adult_{index}"
        adult_indices.append(len(people))
        people[adult] = {
            "age": {year: 45},
            "employment_income": {year: wages},
            "personal_pension_contributions": {year: contributions},
            "employee_pension_contributions": {year: 0},
            "employer_pension_contributions": {year: 0},
            "gift_aid": {year: gift_aid},
        }
        if supplied_ani is not None:
            people[adult]["adjusted_net_income"] = {year: supplied_ani}
        for name, value in (person_inputs or {}).items():
            people[adult][name] = {year: value}
        members = [adult]
        if with_child:
            child = f"child_{index}"
            people[child] = {"age": {year: 8}}
            members.append(child)
        benunits[f"family_{index}"] = {"members": members}
        if with_child:
            # Hold actual Child Benefit received fixed to isolate its charge,
            # including the statutory whole-percentage and pound rounding.
            benunits[f"family_{index}"]["child_benefit"] = {year: 1_200}
        households[f"household_{index}"] = {
            "members": members,
            "region": {year: "LONDON"},
        }

    simulation = template.clone(clone_tax_benefit_system=False)
    simulation.build_from_situation(
        {"people": people, "benunits": benunits, "households": households}
    )
    simulation.input_variables = simulation.get_known_variables()
    simulation.calculated_periods = []
    variables = (
        "pension_contributions_relief",
        "pension_annual_allowance",
        "net_income",
        "adjusted_net_income",
        "personal_allowance",
        "earned_taxable_income",
        "income_tax",
        "CB_HITC",
        "student_loan_repayment",
    )
    return {
        name: np.asarray(simulation.calculate(name, year), dtype=float)[adult_indices]
        for name in variables
    }


def test_150000_pay_and_60000_ras_restore_full_personal_allowance(template):
    values = simulate(template, 2024, [(150_000, 60_000)])
    expected = {
        "pension_contributions_relief": 60_000,
        "net_income": 150_000,
        "adjusted_net_income": 90_000,
        "personal_allowance": 12_570,
        "earned_taxable_income": 77_430,
        # £37,700 at 20% plus £39,730 at 40%; relief is deducted once.
        "income_tax": 37_700 * 0.2 + 39_730 * 0.4,
    }
    for name, amount in expected.items():
        assert values[name][0] == pytest.approx(amount, abs=0.01), name


@pytest.mark.parametrize(
    "year,wages,threshold", [(2023, 60_000, 50_000), (2024, 70_000, 60_000)]
)
def test_ras_reduces_income_to_hicbc_threshold(template, year, wages, threshold):
    values = simulate(template, year, [(wages, 0), (wages, 10_000)], with_child=True)
    assert values["adjusted_net_income"][1] == threshold
    assert values["CB_HITC"][0] > 0
    assert values["CB_HITC"][1] == 0


@pytest.mark.parametrize("gift_aid", [0, 1_600])
@pytest.mark.parametrize(
    "wages,contributions,expected_relief,expected_annual_allowance",
    [
        (70_000, 10_000, 10_000, 60_000),
        (150_000, 60_000, 60_000, 60_000),
        (300_000, 60_000, 60_000, 40_000),
        (340_000, 60_000, 60_000, 20_000),
        (400_000, 60_000, 60_000, 10_000),
        (300_000, 5_000, 5_000, 40_000),
    ],
)
def test_supplied_ani_preserves_pension_relief_and_annual_allowance(
    template,
    wages,
    contributions,
    expected_relief,
    expected_annual_allowance,
    gift_aid,
):
    # The 2024 model's AA is £60,000, tapering at 50% above £260,000
    # of its net-income base, with a £10,000 floor. Direct ANI inputs
    # must reconstruct that base. Contribution relief follows the independent
    # earnings limit; input above the AA instead attracts a separate charge.
    expected_ani = wages - expected_relief - gift_aid / 0.8
    ordinary = simulate(template, 2024, [(wages, contributions)], gift_aid=gift_aid)
    supplied = simulate(
        template,
        2024,
        [(wages, contributions)],
        gift_aid=gift_aid,
        supplied_ani=expected_ani,
    )
    for name, expected in {
        "net_income": wages,
        "adjusted_net_income": expected_ani,
        "pension_contributions_relief": expected_relief,
        "pension_annual_allowance": expected_annual_allowance,
    }.items():
        assert ordinary[name][0] == pytest.approx(expected, abs=0.01), name
        assert supplied[name][0] == pytest.approx(expected, abs=0.01), name
    for name in ordinary:
        np.testing.assert_allclose(
            supplied[name], ordinary[name], atol=0.01, err_msg=name
        )


def test_supplied_ani_preserves_explicit_annual_allowance_and_student_loan(template):
    person_inputs = {
        "pension_annual_allowance": 20_000,
        "student_loan_plan": "PLAN_2",
        "student_loan_balance": 100_000,
    }
    ordinary = simulate(
        template, 2024, [(150_000, 60_000)], person_inputs=person_inputs
    )
    supplied = simulate(
        template,
        2024,
        [(150_000, 60_000)],
        person_inputs=person_inputs,
        supplied_ani=ordinary["adjusted_net_income"][0],
    )
    for name in ordinary:
        np.testing.assert_allclose(
            supplied[name], ordinary[name], atol=0.01, err_msg=name
        )
    # Section 190 relief is independent of AA after #2240: the £40,000
    # excess attracts a separate charge. An explicit AA must not make the
    # supplied-ANI inverse invent income or increase Plan 2 repayments.
    for name, expected in {
        "pension_annual_allowance": 20_000,
        "pension_contributions_relief": 60_000,
        "adjusted_net_income": 90_000,
        "net_income": 150_000,
        # (150,000 - 27,295) * 9%.
        "student_loan_repayment": 11_043.45,
    }.items():
        assert ordinary[name][0] == pytest.approx(expected, abs=0.01), name
        assert supplied[name][0] == pytest.approx(expected, abs=0.01), name


@settings(max_examples=30, deadline=None, derandomize=True, database=None)
@given(
    year=st.sampled_from([2023, 2024]),
    wages=st.integers(40_000, 180_000),
    lower_contribution=st.integers(0, 20_000),
    increase=st.integers(200, 20_000),
)
def test_increasing_relieved_ras_never_lowers_pa_or_raises_hicbc(
    template, year, wages, lower_contribution, increase
):
    higher_contribution = lower_contribution + increase
    hicbc_start, hicbc_end = (50_000, 60_000) if year == 2023 else (60_000, 80_000)
    # The two witnesses cross a statutory taper boundary in every example.
    # Monotonicity alone would pass even if pensions never changed ANI.
    pa_wages = 100_000 + higher_contribution
    hicbc_wages = hicbc_start + higher_contribution
    cases = [
        (pay, contribution)
        for pay in (wages, pa_wages, hicbc_wages)
        for contribution in (lower_contribution, higher_contribution)
    ]
    values = simulate(template, year, cases, with_child=True)

    expected_ani = np.array([pay - contribution for pay, contribution in cases])
    expected_pa = np.maximum(
        0, np.ceil(12_570 - np.maximum(0, expected_ani - 100_000) / 2)
    )
    charge_percentage = np.clip(
        np.floor(100 * (expected_ani - hicbc_start) / (hicbc_end - hicbc_start)),
        0,
        100,
    )
    expected_hicbc = np.floor(1_200 * charge_percentage / 100)
    np.testing.assert_allclose(values["adjusted_net_income"], expected_ani, atol=0.01)
    np.testing.assert_allclose(values["personal_allowance"], expected_pa, atol=0.01)
    np.testing.assert_allclose(values["CB_HITC"], expected_hicbc, atol=0.01)

    pa = values["personal_allowance"].reshape(-1, 2)
    hicbc = values["CB_HITC"].reshape(-1, 2)
    assert np.all(pa[:, 1] >= pa[:, 0])
    assert np.all(hicbc[:, 1] <= hicbc[:, 0])
    assert pa[1, 1] > pa[1, 0]
    assert hicbc[2, 1] < hicbc[2, 0]
