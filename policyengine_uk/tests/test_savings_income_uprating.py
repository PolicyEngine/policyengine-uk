"""Savings income grows by the OBR's savings income forecast to 2025-26.

obr.savings_income is the "Savings income" row of the OBR's receipts table
"Self-employed income streams: growth rates" (percentage change on a year
earlier, pre-measures), fiscal year t-(t+1) stored at t-01-01, rounded to 4
decimals. Each year comes from the latest table that has it:

- 2024-2031: EFO October 2026, detailed forecast tables, receipts, Table 4.5
  (sha256 d115705716d77b11c190385d41cb1924f30080c9331a8a386c04d4e65a368e95);
- 2023: EFO March 2026, receipts Table 3.5 (sha256 f65b6cb7...766a28);
- 2022: EFO October 2024, receipts Table 3.5 (sha256 16d69c09...191991).

obr.per_capita.savings_income is that growth net of ons.population growth.
Dataset projection grows savings_interest_income, non_cash_isa_cash_interest,
other_investment_income and additive ISA interest by the per-person series to
2025 and by obr.per_capita.gdp after it.
"""

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    GDP_PER_HEAD_GROWTH,
    SAVINGS_INCOME_GROWTH,
    SAVINGS_INCOME_GROWTH_LAST_YEAR,
    apply_single_year_uprating,
    extend_single_year_dataset,
    growth_rate,
)
from policyengine_uk.system import system

PARAMETERS = system.parameters
YOY = PARAMETERS.gov.economic_assumptions.yoy_growth
INDICES = PARAMETERS.gov.economic_assumptions.indices
LEGACY = {"version": 1, "representation": "legacy_gross", "projection": "legacy_gross"}
ADDITIVE = {"version": 1, "representation": "additive", "projection": "additive"}

# The OBR's "Savings income" growth, per cent, as the workbooks store it.
OBR_SAVINGS_INCOME_GROWTH = {
    2022: 50.358,  # EFO October 2024, Table 3.5 (shown to 3 decimals)
    2023: 129.854,  # EFO March 2026, Table 3.5 (shown to 3 decimals)
    2024: 34.96108270919673,  # EFO October 2026, Table 4.5, from here on
    2025: 0.6496896187592638,
    2026: 0.6683540761534434,
    2027: 6.138376573221471,
    2028: 5.1434341752103485,
    2029: 4.936559409911245,
    2030: 5.559480586702126,
    2031: 5.893489202164259,
}
SAVINGS_INPUTS = (
    "savings_interest_income",
    "non_cash_isa_cash_interest",
    "other_investment_income",
)


def at(parameter, year):
    return parameter(f"{year}-01-01")


@pytest.mark.parametrize("year", sorted(OBR_SAVINGS_INCOME_GROWTH))
def test_savings_income_is_the_obr_row(year):
    expected = round(OBR_SAVINGS_INCOME_GROWTH[year] / 100, 4)
    assert at(YOY.obr.savings_income, year) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("year", sorted(OBR_SAVINGS_INCOME_GROWTH))
def test_per_capita_savings_income_divides_by_population(year):
    expected = round(
        (1 + at(YOY.obr.savings_income, year)) / (1 + at(YOY.ons.population, year)) - 1,
        4,
    )
    assert at(YOY.obr.per_capita.savings_income, year) == pytest.approx(
        expected, abs=1e-12
    )


def test_aggregate_index_carries_2023_24_to_2025_26_on_the_obr_path():
    """The level a 2023-24 figure reaches by 2025-26, as the OBR has it."""
    obr = (1 + OBR_SAVINGS_INCOME_GROWTH[2024] / 100) * (
        1 + OBR_SAVINGS_INCOME_GROWTH[2025] / 100
    )
    index = INDICES.obr.savings_income
    assert obr == pytest.approx(1.358379, abs=1e-6)
    assert at(index, 2025) / at(index, 2023) == pytest.approx(obr, abs=1e-4)
    assert at(index, 2024) / at(index, 2023) == pytest.approx(1.3496, abs=1e-5)
    assert at(index, 2023) / at(index, 2022) == pytest.approx(2.2985, abs=1e-5)


@pytest.mark.parametrize("year", range(2015, 2041))
def test_growth_rate_hands_over_to_gdp_per_head_after_2025_26(year):
    series = (
        YOY.obr.per_capita.savings_income
        if year <= SAVINGS_INCOME_GROWTH_LAST_YEAR
        else YOY.obr.per_capita.gdp
    )
    assert growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, str(year)) == at(series, year)
    # Every other series reads its own values.
    for name in (
        GDP_PER_HEAD_GROWTH,
        "gov.economic_assumptions.yoy_growth.ons.population",
    ):
        assert growth_rate(PARAMETERS, name, str(year)) == PARAMETERS.get_child(name)(
            str(year)
        )


def dataset(year, contract, people):
    """One household per person, each holding every savings input."""
    n = len(people)
    person = pd.DataFrame(
        {
            "person_id": np.arange(1, n + 1),
            "person_benunit_id": np.arange(1, n + 1),
            "person_household_id": np.arange(1, n + 1),
            "age": [45] * n,
            "employment_income": [30_000.0] * n,
            **{
                name: [float(amounts[name]) for amounts in people]
                for name in (
                    *SAVINGS_INPUTS,
                    "individual_savings_account_interest_income",
                )
            },
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": np.arange(1, n + 1)}),
        household=pd.DataFrame(
            {
                "household_id": np.arange(1, n + 1),
                "region": ["LONDON"] * n,
                "tenure_type": ["RENT_PRIVATELY"] * n,
                "council_tax": [1_500.0] * n,
                "rent": [12_000.0] * n,
                "household_weight": [1_000.0] * n,
            }
        ),
        fiscal_year=year,
        isa_income_contract=deepcopy(contract),
    )


PEOPLE = [
    {
        "savings_interest_income": 2_000,
        "non_cash_isa_cash_interest": 100,
        "other_investment_income": 300,
        "individual_savings_account_interest_income": 500,
    },
    {
        "savings_interest_income": 40_000,
        "non_cash_isa_cash_interest": 0,
        "other_investment_income": 9_000,
        "individual_savings_account_interest_income": 1_200,
    },
]


@pytest.mark.parametrize("contract", [LEGACY, ADDITIVE], ids=["legacy", "additive"])
def test_projection_from_2023_24_reaches_the_obr_level_in_2025_26(contract):
    """Weighted savings income in 2025-26 over 2023-24 is the OBR's growth.

    Weights grow by population and each person's income by the per-person
    series, so the total grows by the OBR's aggregate up to the 4-decimal
    rounding of the stored series. Under the legacy contract the stored
    amount is gross of ISA interest, which is what grows.
    """
    projected = extend_single_year_dataset(
        dataset(2023, contract, PEOPLE), PARAMETERS, end_year=2027
    )
    obr = (1 + OBR_SAVINGS_INCOME_GROWTH[2024] / 100) * (
        1 + OBR_SAVINGS_INCOME_GROWTH[2025] / 100
    )

    def total(year, name):
        data = projected.datasets[year]
        weight = data.household.household_weight.values
        return float((data.person[name].values * weight).sum())

    for name in SAVINGS_INPUTS:
        assert total(2025, name) / total(2023, name) == pytest.approx(obr, rel=2e-4)
    if contract == ADDITIVE:
        isa = "individual_savings_account_interest_income"
        assert total(2025, isa) / total(2023, isa) == pytest.approx(obr, rel=2e-4)
    # After 2025-26 the projection follows GDP per head, as before.
    for year in (2026, 2027):
        for name in SAVINGS_INPUTS:
            before = projected.datasets[year - 1].person[name].values
            after = projected.datasets[year].person[name].values
            np.testing.assert_allclose(
                after, before * (1 + at(YOY.obr.per_capita.gdp, year)), rtol=1e-12
            )


@settings(max_examples=60, deadline=None)
@given(
    year=st.integers(min_value=2022, max_value=2031),
    additive=st.booleans(),
    amounts=st.lists(
        st.tuples(
            st.floats(min_value=0, max_value=5e6, allow_nan=False),
            st.floats(min_value=0, max_value=5e5, allow_nan=False),
            st.floats(min_value=0, max_value=5e6, allow_nan=False),
            st.floats(min_value=0, max_value=5e4, allow_nan=False),
        ),
        min_size=1,
        max_size=4,
    ),
)
def test_each_year_grows_every_savings_input_by_the_same_rate(year, additive, amounts):
    """One year of projection multiplies each savings input by 1 + growth.

    The rate is growth_rate's for the year projected into, the same for the
    YAML-mapped inputs and the code paths for gross legacy interest and
    additive ISA interest (a differential check between them). Amounts stay
    non-negative, and legacy ISA interest stays flat.
    """
    contract = ADDITIVE if additive else LEGACY
    people = [
        {
            "savings_interest_income": gross + isa if not additive else gross,
            "non_cash_isa_cash_interest": min(noncash, isa),
            "other_investment_income": other,
            "individual_savings_account_interest_income": isa,
        }
        for gross, isa, other, noncash in amounts
    ]
    previous = dataset(year, contract, people)
    current = previous.copy()
    current.time_period = str(year + 1)
    apply_single_year_uprating(current, previous, PARAMETERS)
    factor = 1 + growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, str(year + 1))
    names = list(SAVINGS_INPUTS)
    if additive:
        names.append("individual_savings_account_interest_income")
    for name in names:
        before = previous.person[name].values
        after = current.person[name].values
        np.testing.assert_allclose(after, before * factor, rtol=1e-12, atol=1e-9)
        assert (after >= 0).all()
    if not additive:
        isa = "individual_savings_account_interest_income"
        np.testing.assert_array_equal(
            current.person[isa].values, previous.person[isa].values
        )
