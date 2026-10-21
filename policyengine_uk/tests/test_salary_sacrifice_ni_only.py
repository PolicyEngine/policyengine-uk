"""The pension sacrifice cap changes NIC earnings, not pay or member payments.

NI Act 2026 ss1–2 and ITEPA 2003 s308 preserve the employer contribution.
FA 2004 ss188/190/191 make a synthetic member-payment offset unsafe at 75
and where relief is limited. Haircut zero isolates classification from the
separate, unchanged employer-incidence assumption. Cash pay is already net
of contractual sacrifice, as required by the existing UKSimulation adapter.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

YEARS = (2028, 2029, 2030)
CAP = "gov.hmrc.national_insurance.salary_sacrifice_pension_cap"
HAIRCUT = "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate"
# age, cash wages, employer sacrifice, actual net-pay member payment, gross RAS
CASES = [
    (80, 160_000, 30_000, 0, 0),
    (80, 100_000, 30_000, 0, 0),
    (75, 100_000, 30_000, 1_000, 0),
    (74, 1_500, 30_000, 0, 3_600),
    (40, 49_000, 5_000, 0, 0),
    (40, 0, 30_000, 0, 0),
    (40, 40_000, 2_000, 0, 0),
    (40, 40_000, 1_500, 0, 0),
    (40, 40_000, 5_000, 1_000, 2_000),
]


def simulations():
    people = {}
    for i, (age, wages, sacrifice, member, ras) in enumerate(CASES):
        people[f"p{i}"] = {
            name: {str(year): value for year in YEARS}
            for name, value in {
                "age": age,
                "employment_income": wages,
                "pension_contributions_via_salary_sacrifice": sacrifice,
                "employee_pension_contributions": member,
                "personal_pension_contributions": ras,
                "employer_pension_contributions": 2_000,
            }.items()
        }
    situation = {
        "people": people,
        "benunits": {f"b{i}": {"members": [name]} for i, name in enumerate(people)},
        "households": {
            f"h{i}": {"members": [name], "region": "LONDON"}
            for i, name in enumerate(people)
        },
    }
    isolated = {HAIRCUT: {"2028-01-01.2030-12-31": 0}}
    return (
        Simulation(situation=situation, reform=isolated),
        Simulation(
            situation=situation,
            reform={**isolated, CAP: {"2029-01-01.2030-12-31": float("inf")}},
        ),
    )


@pytest.fixture(scope="module")
def pair():
    return simulations()


def values(sim, variable, year):
    return np.asarray(sim.calculate(variable, year), dtype=float)


def ordinary_tax(sim, year):
    return values(sim, "income_tax", year) - values(
        sim, "personal_pension_contributions_tax", year
    )


@pytest.mark.parametrize("year", (2029, 2030))
def test_nic_cap_preserves_ordinary_tax_pay_member_payments_and_allowances(pair, year):
    capped, unlimited = pair
    # These reach existing final variables, so RED must be a numerical failure,
    # never a missing new variable or a forced final/intermediate value.
    np.testing.assert_allclose(
        ordinary_tax(capped, year), ordinary_tax(unlimited, year), atol=0.02, rtol=1e-6
    )
    for name in (
        "employment_income",
        "employee_pension_contributions",
        "adjusted_net_income",
        "personal_allowance",
        "pension_contributions_relief",
    ):
        np.testing.assert_allclose(
            values(capped, name, year),
            values(unlimited, name, year),
            atol=0.02,
            rtol=1e-6,
            err_msg=name,
        )
    np.testing.assert_allclose(
        values(capped, "employment_income", year), [c[1] for c in CASES]
    )
    np.testing.assert_allclose(
        values(capped, "employee_pension_contributions", year), [c[3] for c in CASES]
    )
    assert values(capped, "pension_contributions_relief", year)[3] == 3_600


def test_no_cap_before_2029_preserves_real_inputs(pair):
    capped, unlimited = pair
    np.testing.assert_allclose(
        ordinary_tax(capped, 2028), ordinary_tax(unlimited, 2028)
    )
    np.testing.assert_allclose(
        values(capped, "employment_income", 2028), [c[1] for c in CASES]
    )


@pytest.mark.parametrize("year", (2029, 2030))
def test_actual_class_1_curves_charge_the_excess_once(pair, year):
    capped, unlimited = pair
    excess = np.array([28_000, 28_000, 28_000, 28_000, 3_000, 0, 0, 0, 3_000])
    wages = np.array([c[1] for c in CASES])
    np.testing.assert_allclose(
        values(capped, "ni_class_1_income", year), wages + excess
    )
    np.testing.assert_allclose(values(unlimited, "ni_class_1_income", year), wages)
    p = capped.tax_benefit_system.parameters(year).gov.hmrc.national_insurance.class_1

    # Independent piecewise annual curves, not the approximate reporting helper.
    def employee(earnings):
        pt, uel = (
            p.thresholds.primary_threshold * 52,
            p.thresholds.upper_earnings_limit * 52,
        )
        liability = (
            np.minimum(np.maximum(earnings - pt, 0), uel - pt) * p.rates.employee.main
            + np.maximum(earnings - uel, 0) * p.rates.employee.additional
        )
        return np.where(
            np.array([False, False, False, False, True, True, True, True, True]),
            liability,
            0,
        )

    expected_employee = employee(wages + excess) - employee(wages)
    actual_employee = values(capped, "national_insurance", year) - values(
        unlimited, "national_insurance", year
    )
    np.testing.assert_allclose(actual_employee, expected_employee, atol=0.02, rtol=1e-6)
    st = p.thresholds.secondary_threshold * 52
    expected_employer = (
        np.maximum(wages + excess - st, 0) - np.maximum(wages - st, 0)
    ) * p.rates.employer
    np.testing.assert_allclose(
        values(capped, "ni_class_1_employer", year)
        - values(unlimited, "ni_class_1_employer", year),
        expected_employer,
        atol=0.02,
        rtol=1e-6,
    )
    # £49k crosses the UEL: each slice, rather than all £3k at one rate.
    assert 0 < expected_employee[4] < 3_000 * p.rates.employee.main


def test_dc_inputs_and_final_household_effect_conserve_real_payments(pair):
    capped, unlimited = pair
    for year in (2029, 2030):
        expected = [
            (member + ras if age < 75 else 0) + 2_000 + (sacrifice if wages > 0 else 0)
            for age, wages, sacrifice, member, ras in CASES
        ]
        np.testing.assert_allclose(
            values(capped, "pension_contributions_for_annual_allowance", year), expected
        )
        np.testing.assert_allclose(
            values(unlimited, "pension_contributions_for_annual_allowance", year),
            expected,
        )
        # At £49k there is no AA excess, no benefit entitlement and no relief:
        # the cap's only final household effect is actual employee NICs.
        i = 4
        ni_delta = (
            values(capped, "national_insurance", year)[i]
            - values(unlimited, "national_insurance", year)[i]
        )
        for name, sign in (
            ("household_tax", 1),
            ("household_net_income", -1),
            ("hbai_household_net_income", -1),
        ):
            actual = values(capped, name, year)[i] - values(unlimited, name, year)[i]
            assert actual == pytest.approx(sign * ni_delta, abs=0.02), name


def test_explicit_ordinary_return_input_remains_supported():
    sim = Simulation(
        situation={
            "people": {
                "p": {
                    "age": {"2026": 40},
                    "employment_income": {"2026": 40_000},
                    "employee_pension_contributions": {"2026": 1_000},
                    "salary_sacrifice_returned_to_income": {"2026": 500},
                }
            },
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )
    assert values(sim, "employment_income", 2026)[0] == 40_500
    assert values(sim, "employee_pension_contributions", 2026)[0] == 1_500


def test_ni_reporting_readers_retain_their_existing_approximation(pair):
    capped, _ = pair
    for year in (2029, 2030):
        # These reporting measures deliberately retain the known #2363
        # approximation, including no pension-age gate. Actual NICs above
        # are independently checked through national_insurance instead.
        p = capped.tax_benefit_system.parameters(
            year
        ).gov.hmrc.national_insurance.class_1
        assert values(capped, "salary_sacrifice_pension_ni_employee", year)[
            0
        ] == pytest.approx(28_000 * p.rates.employee.additional, abs=0.02)
        assert values(capped, "salary_sacrifice_pension_ni_employer", year)[
            0
        ] == pytest.approx(28_000 * p.rates.employer, abs=0.02)
        assert np.all(values(capped, "salary_sacrifice_returned_to_income", year) == 0)


# A supplied legacy return is actual pay plus an actual member payment. It
# must agree with entering those amounts directly, including in the merged
# annual-allowance readers. These are distinct from a computed NICs excess.
ACTUAL_RETURN_CASES = [
    dict(age=40, pay=40_000, member=1_000, returned=500),
    dict(age=75, pay=40_000, member=1_000, returned=500),
    dict(age=74, pay=1_500, member=0, returned=500, ras=3_600),
    dict(age=40, pay=40_000, member=1_000, returned=500, ani=39_000),
    dict(age=75, pay=40_000, member=1_000, returned=500, ani=40_500),
    dict(age=40, pay=200_000, member=5_000, returned=5_000, loss=400_000),
    dict(age=40, pay=40_000, member=1_000, returned=500, dc=90_000),
    dict(
        age=40,
        pay=200_000,
        member=5_000,
        returned=5_000,
        employer=30_000,
        sacrifice=30_000,
    ),
    dict(age=74, pay=40_000, member=1_000, returned=0, loss=100_000),
]
ACTUAL_RETURN_OUTPUTS = (
    "employment_income",
    "employee_pension_contributions",
    "pension_contributions",
    "pension_contributions_relief",
    "net_income",
    "adjusted_net_income",
    "personal_allowance",
    "pension_contributions_for_annual_allowance",
    "pension_annual_allowance_adjusted_income",
    "pension_annual_allowance_threshold_income",
    "pension_annual_allowance",
    "personal_pension_contributions_tax",
    "income_tax",
    "ni_class_1_income",
    "national_insurance",
    "household_tax",
    "household_net_income",
    "hbai_household_net_income",
)


def actual_return_simulations(cases):
    def situation(explicit_return):
        people = {}
        for i, case in enumerate(cases):
            returned = case["returned"]
            inputs = {
                "age": case["age"],
                "employment_income": case["pay"] + (0 if explicit_return else returned),
                "employee_pension_contributions": case["member"]
                + (0 if explicit_return else returned),
                "personal_pension_contributions": case.get("ras", 0),
                "employer_pension_contributions": case.get("employer", 0),
                "pension_contributions_via_salary_sacrifice": case.get("sacrifice", 0),
            }
            if explicit_return:
                inputs["salary_sacrifice_returned_to_income"] = returned
            for key, variable in (
                ("ani", "adjusted_net_income"),
                ("loss", "trading_loss"),
                ("dc", "pension_contributions_for_annual_allowance"),
            ):
                if key in case:
                    inputs[variable] = case[key]
            people[f"p{i}"] = {
                name: {"2026": amount} for name, amount in inputs.items()
            }
        return {
            "people": people,
            "benunits": {f"b{i}": {"members": [name]} for i, name in enumerate(people)},
            "households": {
                f"h{i}": {"members": [name], "region": "LONDON"}
                for i, name in enumerate(people)
            },
        }

    return tuple(
        Simulation(
            situation=situation(explicit_return),
            reform={HAIRCUT: {"2026-01-01.2026-12-31": 0}},
        )
        for explicit_return in (True, False)
    )


@pytest.fixture(scope="module")
def actual_return_pair():
    return actual_return_groups()


def actual_return_groups():
    # A supplied variable is stored for the whole Person array. Keep natural
    # cases separate from ANI and DC overrides so absent rows are not filled
    # with zero inputs that mask the very formulas under test.
    return [
        (indices, actual_return_simulations([ACTUAL_RETURN_CASES[i] for i in indices]))
        for indices in ([0, 1, 2, 5, 7, 8], [3, 4], [6])
    ]


def actual_return_values(groups, member, variable):
    result = np.empty(len(ACTUAL_RETURN_CASES))
    for indices, pair in groups:
        result[indices] = values(pair[member], variable, 2026)
    return result


@pytest.mark.parametrize("variable", ACTUAL_RETURN_OUTPUTS)
def test_explicit_actual_return_matches_actual_pay_and_member_inputs(
    actual_return_pair, variable
):
    np.testing.assert_allclose(
        actual_return_values(actual_return_pair, 0, variable),
        actual_return_values(actual_return_pair, 1, variable),
        atol=0.02,
        rtol=1e-6,
        err_msg=variable,
    )


def test_explicit_actual_return_has_independent_aa_and_final_charge_oracles(
    actual_return_pair,
):
    # 2026 actual pay205000/member10000, employer30000 and sacrifice30000:
    # DC70000; adjusted265000; threshold225000; taper(265000-260000)/2;
    # allowance57500; excess12500, charged at the unchanged45% marginal rate.
    expected = {
        "employment_income": 205_000,
        "employee_pension_contributions": 10_000,
        "pension_contributions_for_annual_allowance": 70_000,
        "pension_annual_allowance_adjusted_income": 265_000,
        "pension_annual_allowance_threshold_income": 225_000,
        "pension_annual_allowance": 57_500,
        "personal_pension_contributions_tax": 5_625,
    }
    for member in (0, 1):
        for variable, amount in expected.items():
            assert actual_return_values(actual_return_pair, member, variable)[
                7
            ] == pytest.approx(amount, abs=0.02), variable
        assert actual_return_values(actual_return_pair, member, "income_tax")[7] > 5_625


def test_explicit_actual_return_is_query_order_independent():
    groups = actual_return_groups()
    actual = {
        name: actual_return_values(groups, 0, name)
        for name in reversed(ACTUAL_RETURN_OUTPUTS)
    }
    for name in ACTUAL_RETURN_OUTPUTS:
        np.testing.assert_allclose(
            actual[name], actual_return_values(groups, 1, name), atol=0.02, rtol=1e-6
        )
