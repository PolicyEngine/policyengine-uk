"""Spousal maintenance is gross income for non-dependant deductions.

HB Regs 2006 reg 74(2), (9), pension-age HB reg 55(2), (10), and
SI 2012/2885 Sch 1 para 8(2), (9) do not disregard spousal maintenance.
It remains exempt from income tax under ITTOIA 2005 s 727.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation

YEAR = 2026


@pytest.fixture(scope="module")
def non_dependants():
    # Separate benefit units isolate each non-dependant's own gross income.
    cases = [
        ("earnings_only", 7_800, 0),
        ("maintenance_100", 7_800, 5_200),
        ("maintenance_150", 7_800, 7_800),
        ("same_gross_earnings", 13_000, 0),
    ]
    people, benunits, households = {}, {}, {}
    for name, earnings, maintenance in cases:
        people[name] = {
            "age": {YEAR: 30},
            "weekly_hours": {YEAR: 16},
            "employment_income": {YEAR: earnings},
            "spousal_maintenance_income": {YEAR: maintenance},
            "housing_benefit_individual_non_dep_deduction_eligible": {YEAR: True},
            "council_tax_reduction_individual_non_dep_deduction_eligible": {YEAR: True},
        }
        benunits[name] = {
            "members": [name],
            "universal_credit": {YEAR: 0},
            "pension_credit": {YEAR: 0},
        }
        households[name] = {
            "members": [name],
            "country": {YEAR: "ENGLAND"},
            "local_authority": {YEAR: "MERTON"},
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


def values(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR), dtype=float)


def test_housing_benefit_non_dependant_band_counts_spousal_maintenance(non_dependants):
    # HB reg 74(2): £150/week is below £192; £150 + £100 = £250 is
    # in the £192–278.99 band. SI 2026/148 art 23(3) sets £20.40 and
    # £46.85 weekly deductions: £1,060.80 and £2,436.20 a year.
    np.testing.assert_allclose(
        values(non_dependants, "household_benefits_individual_non_dep_deduction")[:2],
        [1_060.80, 2_436.20],
        atol=0.01,
    )


def test_national_ctr_non_dependant_band_counts_spousal_maintenance(non_dependants):
    # SI 2012/2885 Sch 1 para 8(2), (9): £150 earnings plus £100
    # maintenance and £250 earnings have the same normal gross weekly income.
    # Compare bands without endorsing the pre-existing shared HB rate scale
    # in the national CTR formula (#2007).
    deductions = values(
        non_dependants, "council_tax_reduction_individual_non_dep_deduction"
    )
    assert deductions[1] == pytest.approx(deductions[3], abs=0.01)
    assert deductions[1] > deductions[0]


def test_local_ctr_non_dependant_band_counts_spousal_maintenance(non_dependants):
    # Merton's 2026 scheme para 30(1), (2), (9), pp 58–61:
    # £150 + £150 = £300/week falls in £279–484.99, with £10.60/week
    # deducted (£551.20/year), rather than £5.20 (£270.40/year).
    np.testing.assert_allclose(
        values(
            non_dependants, "merton_council_tax_reduction_individual_non_dep_deduction"
        )[:3],
        [270.40, 270.40, 551.20],
        atol=0.01,
    )


def test_non_dependant_spousal_maintenance_stays_exempt_from_income_tax(non_dependants):
    # ITTOIA 2005 s 727: maintenance leaves taxable income at £7,800.
    # The £13,000 earnings comparator is taxable above the £12,570 allowance:
    # (£13,000 - £12,570) × 20% = £86.
    np.testing.assert_allclose(
        values(non_dependants, "total_income"),
        [7_800, 7_800, 7_800, 13_000],
        atol=0.01,
    )
    np.testing.assert_allclose(
        values(non_dependants, "income_tax"), [0, 0, 0, 86], atol=0.01
    )
