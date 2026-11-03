"""Household cash and stocks-and-shares ISA totals sum per-person balances.

Datasets built before the per-person balances existed store only the
household totals. Those totals must keep their stored values, projected with
savings, rather than fall to the sum of balances the dataset does not have.
Every means test counts both kinds of ISA at their withdrawal value, without
the 10% for expenses of sale.
"""

import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset


def _dataset(person_columns, household_columns):
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 1],
            "person_household_id": [1, 1],
            "age": [30, 28],
            **person_columns,
        }
    )
    household = pd.DataFrame(
        {
            "household_id": [1],
            "household_weight": [1.0],
            "region": ["LONDON"],
            "tenure_type": ["RENT_PRIVATELY"],
            "council_tax": [1_500.0],
            "rent": [12_000.0],
            "savings": [1_000.0],
            **household_columns,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=household,
        fiscal_year=2025,
    )


def _growth(simulation, year):
    growth = simulation.calculate("savings", year).values[0] / 1_000.0
    assert growth != pytest.approx(1.0)
    return growth


def test_stored_household_totals_without_person_balances_project_with_savings():
    simulation = Microsimulation(
        dataset=_dataset(
            {}, {"cash_isa": [3_000.0], "stocks_and_shares_isa": [2_000.0]}
        )
    )
    growth = _growth(simulation, 2027)
    cash = simulation.calculate("cash_isa", 2027).values[0]
    shares = simulation.calculate("stocks_and_shares_isa", 2027).values[0]
    assert cash == pytest.approx(3_000.0 * growth)
    assert shares == pytest.approx(2_000.0 * growth)
    # Savings, the cash ISA and the stocks-and-shares ISA all reach the
    # capital pool at their value: an ISA is valued at what its holder would
    # get by withdrawing it, with no deduction for expenses of sale (ADM
    # H1656), so the itemised ISA sits in the part of share_like_capital
    # without them.
    without = simulation.calculate("share_like_capital_without_sale_expenses", 2027)
    with_expenses = simulation.calculate("share_like_capital_with_sale_expenses", 2027)
    assert without.values[0] == pytest.approx(2_000.0 * growth)
    assert with_expenses.values[0] == 0
    capital = simulation.calculate("uc_assessable_capital", 2027).values[0]
    expected = (1_000.0 + 3_000.0 + 2_000.0) * growth
    assert capital == pytest.approx(expected, rel=1e-5)


def test_household_totals_sum_the_person_balances_in_every_year():
    simulation = Microsimulation(
        dataset=_dataset(
            {
                "cash_isa_balance": [4_000.0, 1_000.0],
                "stocks_and_shares_isa_balance": [0.0, 2_500.0],
            },
            {},
        )
    )
    growth = _growth(simulation, 2027)
    for year, factor in ((2025, 1.0), (2027, growth)):
        cash = simulation.calculate("cash_isa_balance", year).values
        shares = simulation.calculate("stocks_and_shares_isa_balance", year).values
        assert list(cash) == pytest.approx([4_000.0 * factor, 1_000.0 * factor])
        assert list(shares) == pytest.approx([0.0, 2_500.0 * factor])
        household_cash = simulation.calculate("cash_isa", year).values[0]
        household_shares = simulation.calculate("stocks_and_shares_isa", year)
        assert household_cash == pytest.approx(cash.sum())
        assert household_shares.values[0] == pytest.approx(shares.sum())


def _isa_situation(age, period, **person):
    """One adult with £1,000 of savings and the given person-level balances."""
    return {
        "people": {
            "person": {
                "age": {period: age},
                **{name: {period: value} for name, value in person.items()},
            }
        },
        "benunits": {
            "benunit": {"members": ["person"], "would_claim_uc": {period: False}}
        },
        "households": {
            "household": {"members": ["person"], "savings": {period: 1_000.0}}
        },
    }


@pytest.mark.parametrize(
    "variable, age, period",
    [
        ("uc_assessable_capital", 30, 2026),
        ("housing_benefit_assessable_capital", 30, 2026),
        # Income Support's capital list applies to a working-age claimant
        # before Universal Credit replaced it.
        ("income_support_assessable_capital", 30, 2021),
        ("jsa_income_assessable_capital", 30, 2026),
        ("esa_income_assessable_capital", 40, 2026),
        ("pension_credit_assessable_capital", 70, 2026),
    ],
)
def test_person_isa_balances_count_in_full_in_every_means_test(variable, age, period):
    """Neither a cash ISA nor a stocks-and-shares ISA takes the 10% for
    expenses of sale: each is valued at its withdrawal value (ADM H1656; DMG
    29662, 52662, 84748). £1,000 + £3,000 + £2,000 = £6,000, where the 10%
    on the stocks-and-shares ISA would give £5,800."""
    simulation = Simulation(
        situation=_isa_situation(
            age,
            period,
            cash_isa_balance=3_000.0,
            stocks_and_shares_isa_balance=2_000.0,
        )
    )
    assert simulation.calculate("stocks_and_shares_isa", period)[0] == 2_000
    assert simulation.calculate("share_like_capital_without_sale_expenses", period)[
        0
    ] == pytest.approx(2_000)
    assert simulation.calculate("share_like_capital_with_sale_expenses", period)[0] == 0
    if variable == "housing_benefit_assessable_capital":
        assert not simulation.calculate(
            "housing_benefit_on_passporting_benefit", period
        )[0]
    assert simulation.calculate(variable, period)[0] == pytest.approx(6_000, abs=0.01)
