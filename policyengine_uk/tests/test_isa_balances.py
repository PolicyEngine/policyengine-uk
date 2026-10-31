"""Household cash and stocks-and-shares ISA totals sum per-person balances.

Datasets built before the per-person balances existed store only the
household totals. Those totals must keep their stored values, projected with
savings, rather than fall to the sum of balances the dataset does not have.
"""

import pandas as pd
import pytest

from policyengine_uk import Microsimulation
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
    # Savings and the cash ISA reach the capital pool at their value. The
    # stocks-and-shares ISA reaches it through share_like_capital, which
    # Universal Credit values less its sale-expense rate until the data
    # separate ISAs from shares.
    rate = simulation.tax_benefit_system.parameters(
        "2027-04-06"
    ).gov.dwp.universal_credit.means_test.capital.sale_expenses.rate
    capital = simulation.calculate("uc_assessable_capital", 2027).values[0]
    expected = (1_000.0 + 3_000.0 + 2_000.0 * (1 - rate)) * growth
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
