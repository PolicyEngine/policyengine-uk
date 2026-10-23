"""PC notional Class 2 uses CER chargeable income, before actual NI reliefs.

CER 1996 reg. 14(2)(a), (3), at 6 April 2023:
https://www.legislation.gov.uk/uksi/1996/2745/regulation/14/2023-04-06
SSCBA 1992 s. 11(2), (4), at 6 April 2023:
https://www.legislation.gov.uk/ukpga/1992/4/section/11/2023-04-06
"""

import pytest

from policyengine_uk import Simulation


@pytest.mark.parametrize(
    "profit, expected_deductions",
    [(12_570, 0), (13_000, 304.10)],
)
def test_notional_class2_ignores_actual_trading_allowance(profit, expected_deductions):
    simulation = Simulation(
        situation={
            "people": {
                "adult": {
                    "age": {2023: 60},
                    "self_employment_income": {2023: profit},
                    "self_employment_gross_receipts": {2023: profit},
                }
            }
        }
    )
    # Known receipts trigger the £1,000 trading allowance for actual NI.
    assert simulation.calculate("ni_class_2", 2023)[0] == 0
    # CER chargeable income is profit before that allowance. At £13,000:
    # tax = (£13,000 - £12,570) * 20% = £86;
    # Class 4 = (£13,000 - £12,570) * 9% = £38.70;
    # Class 2 = 52 * £3.45 = £179.40. Total = £304.10.
    # At exactly £12,570 CER 14(2)(a) expressly excludes Class 2, and the
    # personal allowance/lower profits limit make tax/Class 4 zero too.
    assert simulation.calculate("pension_credit_self_employment_deductions", 2023)[
        0
    ] == pytest.approx(expected_deductions, abs=0.01)


def test_other_trade_loss_keeps_protected_couple_notional_class2():
    results = []
    for loss in (0, 20_000):
        simulation = Simulation(
            situation={
                "people": {
                    "claimant": {
                        "age": {2023: 70},
                        "attendance_allowance": {2023: 3_000},
                        "marital_status": {2023: "MARRIED"},
                        "would_claim_marriage_allowance": {2023: False},
                    },
                    "partner": {
                        "age": {2023: 60},
                        "marital_status": {2023: "MARRIED"},
                        "would_claim_marriage_allowance": {2023: False},
                        "dla_sc_category": {2023: "MIDDLE"},
                        "self_employment_income": {2023: 20_000},
                        "trading_loss": {2023: loss},
                    },
                },
                "benunits": {
                    "couple": {
                        "members": ["claimant", "partner"],
                        "is_married": {2023: True},
                        "has_mixed_age_couple_pension_credit_saving": {2023: True},
                        "would_claim_pc": {2023: True},
                    }
                },
                "households": {"home": {"members": ["claimant", "partner"]}},
            }
        )
        assert simulation.calculate("is_pension_credit_eligible", 2023)[0]
        actual_class2 = simulation.calculate("ni_class_2", 2023)[1]
        assert actual_class2 == pytest.approx(0 if loss else 179.40, abs=0.01)
        # CER 13(12) prohibits another employment's loss reducing the
        # £20,000 positive profit. Notional deductions are therefore
        # (£20,000 - £12,570 PA) * 20% = £1,486 tax, with Marriage Allowance
        # takeup explicitly off to isolate the notional-Class-2 property;
        # plus £668.70 Class 4 and £179.40 Class 2 = £2,334.10.
        deductions = simulation.calculate(
            "pension_credit_self_employment_deductions", 2023
        )[1]
        assert deductions == pytest.approx(2_334.10, abs=0.01)
        results.append(
            (
                deductions,
                simulation.calculate("pension_credit_income", 2023)[0],
                simulation.calculate("pension_credit", 2023)[0],
            )
        )
    # SI 2023/316 art.30(2)(a), (d): the couple guarantee plus the higher
    # severe-disability addition is (£306.85 + £152.80) * 52 = £23,901.80.
    # https://www.legislation.gov.uk/uksi/2023/316/article/30/made
    # PC income = £20,000 - £2,334.10 deductions - £1,040 disregard =
    # £16,625.90; the award is £23,901.80 - £16,625.90 = £7,275.90.
    assert results[0] == pytest.approx((2_334.10, 16_625.90, 7_275.90), abs=0.01)
    assert results[1] == pytest.approx(results[0], abs=0.01)


@pytest.mark.parametrize("year, age", [(2023, 70), (2024, 60)])
def test_notional_class2_respects_pension_age_and_abolition(year, age):
    simulation = Simulation(
        situation={
            "people": {
                "adult": {
                    "age": {year: age},
                    "self_employment_income": {year: 13_000},
                    "self_employment_gross_receipts": {year: 13_000},
                }
            }
        }
    )
    # SSCBA s.11(7)(b) excludes pension-age earners, while SI 2024/377
    # reg.8(7) omits CER 14(2)(a) from 6 April 2024. Neither case has a
    # notional Class 2 deduction. Class 4 is £25.80 at 2024's 6% main rate.
    expected = 86 if year == 2023 else 86 + 25.80
    assert simulation.calculate("pension_credit_self_employment_deductions", year)[
        0
    ] == pytest.approx(expected, abs=0.01)
