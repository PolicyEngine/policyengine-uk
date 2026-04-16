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


def test_csp_counts_for_pension_credit_carer_additions_and_blocks_severe_disability():
    sim = Simulation(
        situation=_situation(
            YEAR_2025,
            attendance_allowance={YEAR_2025: 1},
        )
    )
    parameters = sim.tax_benefit_system.parameters(str(YEAR_2025))

    expected_carer_addition = (
        float(parameters.gov.dwp.pension_credit.guarantee_credit.carer.addition) * 52
    )

    assert sim.calculate("carer_minimum_guarantee_addition", YEAR_2025)[0] == (
        expected_carer_addition
    )
    assert (
        sim.calculate("severe_disability_minimum_guarantee_addition", YEAR_2025)[0]
        == 0
    )


def test_csp_counts_for_uc_non_dep_exemption_and_housing_benefit_income():
    sim = Simulation(situation=_situation(YEAR_2025))

    csp_amount = sim.calculate("carer_support_payment", YEAR_2025)[0]
    hb_disregard = sim.calculate("housing_benefit_applicable_income_disregard", YEAR_2025)[
        0
    ]
    hb_income = sim.calculate("housing_benefit_applicable_income", YEAR_2025)[0]

    assert sim.calculate("uc_non_dep_deduction_exempt", YEAR_2025)[0]
    assert hb_income == max(0, csp_amount - hb_disregard)
