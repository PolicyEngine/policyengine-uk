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
