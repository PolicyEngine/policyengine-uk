import pytest

from policyengine_uk import Simulation


YEAR_2024 = 2024
YEAR_2025 = 2025


def _situation(year: int, **person_overrides):
    person = {
        "age": {year: 35},
        "care_hours": {year: 40},
    }
    person.update(person_overrides)
    return {
        "people": {
            "person": person,
        },
        "benunits": {
            "benunit": {
                "members": ["person"],
            }
        },
        "households": {
            "household": {
                "members": ["person"],
                "country": {year: "SCOTLAND"},
            }
        },
    }


def test_scottish_carers_allowance_remains_in_place_for_2024():
    sim = Simulation(situation=_situation(YEAR_2024))

    assert sim.calculate("carers_allowance", YEAR_2024)[0] > 0
    assert sim.calculate("carer_support_payment", YEAR_2024)[0] == 0


def test_scottish_carers_move_to_csp_in_2025():
    sim = Simulation(situation=_situation(YEAR_2025))

    assert sim.calculate("carers_allowance", YEAR_2025)[0] == 0
    assert sim.calculate("carer_support_payment", YEAR_2025)[0] > 0


def test_csp_counts_for_pension_credit_carer_additions():
    # A person's own carer benefit does not bar their severe disability
    # addition: SPC Regs 2002 Sch I para 1(1)(a)(iii) bars it only where a
    # carer benefit is paid to someone "in respect of caring for him".
    sim = Simulation(
        situation=_situation(
            YEAR_2025,
            attendance_allowance={YEAR_2025: 1},
        )
    )
    parameters = sim.tax_benefit_system.parameters(str(YEAR_2025))
    guarantee_credit = parameters.gov.dwp.pension_credit.guarantee_credit

    expected_carer_addition = float(guarantee_credit.carer.addition) * 52
    expected_severe_disability_addition = (
        float(guarantee_credit.severe_disability.addition) * 52
    )

    assert sim.calculate("carer_minimum_guarantee_addition", YEAR_2025)[0] == (
        expected_carer_addition
    )
    assert sim.calculate("severe_disability_minimum_guarantee_addition", YEAR_2025)[
        0
    ] == pytest.approx(expected_severe_disability_addition)


def _couple_situation(year: int, claimant: dict, partner: dict):
    return {
        "people": {
            "claimant": {"age": {year: 35}, **claimant},
            "partner": {"age": {year: 35}, **partner},
        },
        "benunits": {"benunit": {"members": ["claimant", "partner"]}},
        "households": {
            "household": {
                "members": ["claimant", "partner"],
                "country": {year: "SCOTLAND"},
            }
        },
    }


def test_partner_csp_for_caring_gives_couple_severe_disability_single_rate_or_nil():
    # Sch I para 1(1)(b): a couple qualifies only if both partners get a
    # qualifying benefit; reg 6(5) then pays the single amount where a carer
    # benefit is paid for one of them. Where only one partner qualifies and the
    # other is not blind, para 1(1)(c) gives nothing.
    both_qualify = _couple_situation(
        YEAR_2025,
        claimant={"attendance_allowance": {YEAR_2025: 1}},
        partner={
            "attendance_allowance": {YEAR_2025: 1},
            "care_hours": {YEAR_2025: 40},
        },
    )
    one_qualifies = _couple_situation(
        YEAR_2025,
        claimant={"attendance_allowance": {YEAR_2025: 1}},
        partner={"care_hours": {YEAR_2025: 40}},
    )
    sim = Simulation(situation=both_qualify)
    parameters = sim.tax_benefit_system.parameters(str(YEAR_2025))
    single_amount = (
        float(
            parameters.gov.dwp.pension_credit.guarantee_credit.severe_disability.addition
        )
        * 52
    )
    assert sim.calculate("carer_support_payment", YEAR_2025)[1] > 0
    assert sim.calculate("severe_disability_minimum_guarantee_addition", YEAR_2025)[
        0
    ] == pytest.approx(single_amount)

    sim = Simulation(situation=one_qualifies)
    assert sim.calculate("carer_support_payment", YEAR_2025)[1] > 0
    assert sim.calculate("severe_disability_minimum_guarantee_addition", YEAR_2025)[
        0
    ] == pytest.approx(0)


def test_csp_counts_for_uc_non_dep_exemption_and_housing_benefit_income():
    situation = _situation(YEAR_2025)
    # Not claiming Universal Credit: on it, the whole of the Housing Benefit
    # income would be disregarded (SI 2006/213 Sch 5 para 4).
    situation["benunits"]["benunit"]["would_claim_uc"] = {YEAR_2025: False}
    sim = Simulation(situation=situation)

    csp_amount = sim.calculate("carer_support_payment", YEAR_2025)[0]
    hb_disregard = sim.calculate(
        "housing_benefit_applicable_income_disregard", YEAR_2025
    )[0]
    hb_income = sim.calculate("housing_benefit_applicable_income", YEAR_2025)[0]

    assert sim.calculate("uc_non_dep_deduction_exempt", YEAR_2025)[0]
    assert hb_income == max(0, csp_amount - hb_disregard)


def test_csp_earnings_limit_is_independent_of_carers_allowance_limit():
    year = 2026
    inputs = _situation(year, employment_income={year: 11_000})
    baseline = Simulation(situation=inputs)
    csp_reform = Simulation(
        situation=inputs,
        reform={
            "gov.social_security_scotland.carer_support_payment.earnings_limit": 1_000
        },
    )
    ca_reform = Simulation(
        situation=inputs,
        reform={"gov.dwp.carers_allowance.earnings_limit": 1_000},
    )
    assert baseline.calculate("carer_support_payment", year)[0] == 0
    assert csp_reform.calculate("carer_support_payment", year)[0] == pytest.approx(
        4_495.40, abs=0.01
    )
    assert ca_reform.calculate("carer_support_payment", year)[0] == 0

    # A CSP parameter reform cannot change the existing England CA route.
    inputs["households"]["household"]["country"] = {year: "ENGLAND"}
    england = Simulation(
        situation=inputs,
        reform={
            "gov.social_security_scotland.carer_support_payment.earnings_limit": 1_000
        },
    )
    assert england.calculate("carers_allowance", year)[0] == 0


def test_csp_statutory_dates_and_annual_model_coverage():
    from pathlib import Path

    from policyengine_core.parameters.helpers import load_parameter_file
    from policyengine_uk import CountryTaxBenefitSystem

    parameter_file = (
        Path(__file__).resolve().parents[1]
        / "parameters/gov/social_security_scotland/carer_support_payment/earnings_limit.yaml"
    )
    raw = load_parameter_file(str(parameter_file), name="earnings_limit")
    for date, expected in [
        ("2023-11-19", 139),
        ("2024-04-06", 139),
        ("2024-04-07", 151),
        ("2025-04-05", 151),
        ("2025-04-06", 196),
        ("2026-04-04", 196),
        ("2026-04-05", 204),
    ]:
        assert raw(date) == expected
    system = CountryTaxBenefitSystem()
    for year, expected in [(2024, 151), (2025, 196), (2026, 204)]:
        assert (
            system.parameters(
                str(year)
            ).gov.social_security_scotland.carer_support_payment.earnings_limit
            == expected
        )
    # The statutory pilot start does not expand the existing model coverage.
    for year in [2023, 2024]:
        sim = Simulation(situation=_situation(year))
        assert sim.calculate("carer_support_payment", year)[0] == 0


def test_csp_first_excluded_penny_in_the_actual_holder_dtype(record_property):
    import json

    import numpy as np

    year = 2026
    critical = Simulation(
        situation=_situation(year, employment_income={year: 10_608.52})
    )
    earnings = critical.calculate("carers_allowance_earnings", year)
    encoded_boundary = np.asarray(10_608.52, dtype=earnings.dtype)
    assert critical.calculate("carer_support_payment", year)[0] == 0
    observations = []
    # These neighbours check the model's encoded legal penny boundary, rather
    # than claim that arbitrary binary fractions are a separate statutory rule.
    for pay, expected in [
        (np.nextafter(encoded_boundary, -np.inf, dtype=earnings.dtype), 4_495.40),
        (encoded_boundary, 0),
        (np.nextafter(encoded_boundary, np.inf, dtype=earnings.dtype), 0),
    ]:
        sim = Simulation(
            situation=_situation(year, employment_income={year: float(pay)})
        )
        counted = sim.calculate("carers_allowance_earnings", year)
        actual = sim.calculate("carer_support_payment", year)[0]
        assert actual == pytest.approx(expected, abs=0.01)
        observations.append(
            {
                "pay": float(pay),
                "counted_annual": float(counted[0]),
                "dtype": str(counted.dtype),
                "CSP": float(actual),
                "expected": expected,
            }
        )
    record_property("CSP_holder_boundary", json.dumps(observations, sort_keys=True))


@pytest.mark.parametrize("reverse", [False, True])
def test_csp_earnings_are_personal_and_request_order_independent(reverse):
    year = 2026
    people, benunits, households = {}, {}, {}
    for family, pay in [("low", 8_000), ("high", 40_000)]:
        names = [family + suffix for suffix in ["_carer", "_partner", "_caree"]]
        people[names[0]] = {
            "age": {year: 45},
            "care_hours": {year: 40},
            "employment_income": {year: pay},
            "is_parent": {year: True},
        }
        people[names[1]] = {
            "age": {year: 43},
            "employment_income": {year: 40_000 if family == "low" else 0},
            "is_parent": {year: True},
        }
        people[names[2]] = {"age": {year: 18}, "pip_dl_category": {year: "STANDARD"}}
        benunits[family] = {"members": list(reversed(names)) if reverse else names}
        households[family] = {
            "members": list(reversed(names)) if reverse else names,
            "country": {year: "SCOTLAND"},
        }
    if reverse:
        people = dict(reversed(list(people.items())))
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    if reverse:
        sim.calculate("is_entitled_to_carer_benefit", year)
    values = sim.calculate("carer_support_payment", year)
    by_name = dict(zip(sim.populations["person"].ids, values))
    assert by_name["low_carer"] == pytest.approx(4_495.40, abs=0.01)
    assert by_name["high_carer"] == 0
    assert all(
        value == 0 for name, value in by_name.items() if not name.endswith("_carer")
    )
