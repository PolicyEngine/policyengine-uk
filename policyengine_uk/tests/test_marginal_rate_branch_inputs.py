"""Marginal rate branches recalculate every value the pay rise can change.

The marginal tax rate formulas raise an input in a branch and recalculate.
They used to keep, in the branch, every variable stored at load
(``simulation.input_variables``) for any period. A dataset column such as
``student_loan_repayment`` is entered through 2030 and calculated after, so for
a later year the branch read the value calculated before the branch existed,
and the rate depended on calculation order: eFRS 2032 marginal_tax_rate
differed for 1,723 people between a fresh run and one that calculated 2031
first.

Invariants:

1. The rate for a year does not depend on what was calculated first.
2. Entering a variable for another year does not change the rate for a year
   in which it is calculated.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation


def graduate(entered_repayment_years=()):
    """A Plan 2 graduate earning above the repayment threshold in 2025-2026,
    with ``student_loan_repayment`` entered (as 0) for the given years."""
    years = (2025, 2026)
    return {
        "people": {
            "graduate": {
                "age": {year: 30 for year in years},
                "employment_income": {year: 50_000 for year in years},
                "student_loan_plan": {year: "PLAN_2" for year in years},
                "student_loan_repayment": {year: 0 for year in entered_repayment_years},
            }
        },
        "benunits": {"benunit": {"members": ["graduate"]}},
        "households": {
            "household": {
                "members": ["graduate"],
                "region": {year: "LONDON" for year in years},
            }
        },
    }


RATES = ("marginal_tax_rate", "marginal_tax_rate_wrt_employer_cost")


@pytest.mark.parametrize("rate", RATES)
@pytest.mark.parametrize(
    "first",
    [
        (),
        (("household_net_income", 2026),),
        (("marginal_tax_rate", 2025),),
        (("marginal_tax_rate_wrt_employer_cost", 2025),),
        (("marginal_tax_rate", 2025), ("household_net_income", 2026)),
    ],
)
def test_rates_past_the_entered_years_do_not_depend_on_order(rate, first):
    reference = Simulation(situation=graduate()).calculate(rate, 2026)
    simulation = Simulation(situation=graduate(entered_repayment_years=(2025,)))
    for variable, year in first:
        simulation.calculate(variable, year)
    assert np.array_equal(simulation.calculate(rate, 2026), reference)


def test_the_rate_includes_the_student_loan_repayment():
    # 9% of the pay rise goes to the Plan 2 repayment once it is recalculated.
    with_loan = Simulation(situation=graduate(entered_repayment_years=(2025,)))
    with_loan.calculate("household_net_income", 2026)
    without = graduate()
    without["people"]["graduate"]["student_loan_plan"] = {2025: "NONE", 2026: "NONE"}
    difference = (
        with_loan.calculate("marginal_tax_rate", 2026)[0]
        - Simulation(situation=without).calculate("marginal_tax_rate", 2026)[0]
    )
    assert difference == pytest.approx(0.09, abs=1e-3)


def test_an_entered_year_keeps_its_entered_value():
    # In the entered year the branch keeps the input (the repayment entered
    # as 0 does not move with the pay rise), whatever was calculated first.
    rates = []
    for first in [(), (("marginal_tax_rate", 2026),)]:
        simulation = Simulation(situation=graduate(entered_repayment_years=(2025,)))
        for variable, year in first:
            simulation.calculate(variable, year)
        rates.append(simulation.calculate("marginal_tax_rate", 2025))
        assert simulation.calculate("student_loan_repayment", 2025)[0] == 0
    assert np.array_equal(rates[0], rates[1])
