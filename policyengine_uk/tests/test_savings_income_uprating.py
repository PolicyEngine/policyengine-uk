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
A dataset that declares the obr_savings_income_2022_2025 projection (an H5
root attribute, savings_income_projection.py) grows savings_interest_income,
non_cash_isa_cash_interest, other_investment_income and additive ISA interest
by the per-person series from 2022 to 2025 and by obr.per_capita.gdp in other
years: after 2025, and before 2022, where the series has no source and the
parameter only repeats its first value. A dataset that declares nothing, as
every dataset built before the declaration existed, grows them by GDP per
head in every year, as before.
"""

from copy import deepcopy
from types import SimpleNamespace

import h5py
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.savings_income_projection import (
    DEFAULT_SAVINGS_INCOME_PROJECTION,
    GDP_PER_HEAD,
    OBR_SAVINGS_INCOME_2022_2025,
    SAVINGS_INCOME_PROJECTION_KEY,
    core_dataset_savings_income_projection,
    read_savings_income_projection,
    write_savings_income_projection,
)
from policyengine_uk.data.economic_assumptions import (
    GDP_PER_HEAD_GROWTH,
    SAVINGS_INCOME_GROWTH,
    SAVINGS_INCOME_GROWTH_FIRST_YEAR,
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


def test_the_savings_window_runs_from_the_first_sourced_year_to_2025_26():
    assert (SAVINGS_INCOME_GROWTH_FIRST_YEAR, SAVINGS_INCOME_GROWTH_LAST_YEAR) == (
        min(OBR_SAVINGS_INCOME_GROWTH),
        2025,
    )


@pytest.mark.parametrize("rule", [OBR_SAVINGS_INCOME_2022_2025, GDP_PER_HEAD])
@pytest.mark.parametrize("year", range(2015, 2041))
def test_growth_rate_uses_gdp_per_head_outside_2022_23_to_2025_26(year, rule):
    series = (
        YOY.obr.per_capita.savings_income
        if rule == OBR_SAVINGS_INCOME_2022_2025 and 2022 <= year <= 2025
        else YOY.obr.per_capita.gdp
    )
    assert growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, str(year), rule) == at(
        series, year
    )
    # Every other series reads its own values.
    for name in (
        GDP_PER_HEAD_GROWTH,
        "gov.economic_assumptions.yoy_growth.ons.population",
    ):
        assert growth_rate(PARAMETERS, name, str(year), rule) == PARAMETERS.get_child(
            name
        )(str(year))


@pytest.mark.parametrize("year", range(2015, 2041))
def test_growth_rate_defaults_to_gdp_per_head_in_every_year(year):
    assert DEFAULT_SAVINGS_INCOME_PROJECTION == GDP_PER_HEAD
    assert growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, str(year)) == at(
        YOY.obr.per_capita.gdp, year
    )


def test_growth_rate_refuses_an_unknown_rule():
    with pytest.raises(ValueError, match="unknown rule"):
        growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, "2024", "cpi")


def dataset(year, contract, people, rule=OBR_SAVINGS_INCOME_2022_2025):
    """One household per person, each holding every savings input, declaring
    ``rule`` (None declares nothing)."""
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
        savings_income_projection=rule,
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


@pytest.mark.parametrize("contract", [LEGACY, ADDITIVE], ids=["legacy", "additive"])
def test_projection_before_2022_23_follows_gdp_per_head(contract):
    """The series starts in 2022-23, so a 2020-21 dataset grows by GDP per
    head into 2021-22, not by a backdated 2022-23 rate, then by the series."""
    gdp_2021 = at(YOY.obr.per_capita.gdp, 2021)
    savings_2022 = at(YOY.obr.per_capita.savings_income, 2022)
    assert gdp_2021 != pytest.approx(savings_2022)
    projected = extend_single_year_dataset(
        dataset(2020, contract, PEOPLE), PARAMETERS, end_year=2022
    )
    for year, growth in ((2021, gdp_2021), (2022, savings_2022)):
        for name in SAVINGS_INPUTS:
            before = projected.datasets[year - 1].person[name].values
            after = projected.datasets[year].person[name].values
            np.testing.assert_allclose(after, before * (1 + growth), rtol=1e-12)


@pytest.mark.parametrize("contract", [LEGACY, ADDITIVE], ids=["legacy", "additive"])
def test_undeclared_data_grows_savings_income_by_gdp_per_head_every_year(contract):
    """Data built before the declaration existed projects as it did before
    the OBR series was added: by GDP per head in every year, 2023-24 to
    2025-26 included. Legacy ISA interest stays flat."""
    undeclared = dataset(2020, contract, PEOPLE, rule=None)
    assert undeclared.savings_income_projection == GDP_PER_HEAD
    projected = extend_single_year_dataset(undeclared, PARAMETERS, end_year=2027)
    assert projected.savings_income_projection == GDP_PER_HEAD
    names = list(SAVINGS_INPUTS)
    if contract == ADDITIVE:
        names.append("individual_savings_account_interest_income")
    for year in range(2021, 2028):
        growth = at(YOY.obr.per_capita.gdp, year)
        for name in names:
            before = projected.datasets[year - 1].person[name].values
            after = projected.datasets[year].person[name].values
            np.testing.assert_allclose(after, before * (1 + growth), rtol=1e-12)


@settings(max_examples=60, deadline=None)
@given(
    year=st.integers(min_value=2015, max_value=2031),
    rule=st.sampled_from([None, GDP_PER_HEAD, OBR_SAVINGS_INCOME_2022_2025]),
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
def test_each_year_grows_every_savings_input_by_the_same_rate(
    year, rule, additive, amounts
):
    """One year of projection multiplies each savings input by 1 + growth.

    The rate is growth_rate's for the year projected into under the declared
    rule (GDP per head when none is declared), the same for the
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
    previous = dataset(year, contract, people, rule=rule)
    current = previous.copy()
    current.time_period = str(year + 1)
    apply_single_year_uprating(current, previous, PARAMETERS)
    factor = 1 + growth_rate(
        PARAMETERS,
        SAVINGS_INCOME_GROWTH,
        str(year + 1),
        rule or DEFAULT_SAVINGS_INCOME_PROJECTION,
    )
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


# The declaration travels with the data.


@pytest.mark.parametrize("rule", [GDP_PER_HEAD, OBR_SAVINGS_INCOME_2022_2025])
def test_a_single_year_file_keeps_its_rule(tmp_path, rule):
    path = tmp_path / "single.h5"
    dataset(2023, ADDITIVE, PEOPLE, rule=rule).save(str(path))
    with h5py.File(path, "r") as file:
        assert file.attrs[SAVINGS_INCOME_PROJECTION_KEY] == rule
    assert read_savings_income_projection(path) == rule
    assert UKSingleYearDataset(str(path)).savings_income_projection == rule


def test_a_file_without_the_attribute_reads_as_gdp_per_head(tmp_path):
    path = tmp_path / "old.h5"
    dataset(2023, ADDITIVE, PEOPLE).save(str(path))
    with h5py.File(path, "a") as file:
        del file.attrs[SAVINGS_INCOME_PROJECTION_KEY]
    assert read_savings_income_projection(path) is None
    assert UKSingleYearDataset(str(path)).savings_income_projection == GDP_PER_HEAD
    write_savings_income_projection(path, OBR_SAVINGS_INCOME_2022_2025)
    assert read_savings_income_projection(path) == OBR_SAVINGS_INCOME_2022_2025


def test_a_declaration_that_contradicts_the_file_is_refused(tmp_path):
    path = tmp_path / "obr.h5"
    dataset(2023, ADDITIVE, PEOPLE).save(str(path))
    with pytest.raises(ValueError, match="disagree"):
        UKSingleYearDataset(str(path), savings_income_projection=GDP_PER_HEAD)
    # Repeating the file's own rule is not a contradiction.
    assert (
        UKSingleYearDataset(
            str(path), savings_income_projection=OBR_SAVINGS_INCOME_2022_2025
        ).savings_income_projection
        == OBR_SAVINGS_INCOME_2022_2025
    )


def test_an_unknown_rule_is_refused(tmp_path):
    with pytest.raises(ValueError, match="unknown rule"):
        dataset(2023, ADDITIVE, PEOPLE, rule="cpi")
    path = tmp_path / "bad.h5"
    dataset(2023, ADDITIVE, PEOPLE).save(str(path))
    with h5py.File(path, "a") as file:
        file.attrs[SAVINGS_INCOME_PROJECTION_KEY] = "cpi"
    with pytest.raises(ValueError, match="unknown rule"):
        UKSingleYearDataset(str(path))


@pytest.mark.parametrize("rule", [GDP_PER_HEAD, OBR_SAVINGS_INCOME_2022_2025])
def test_projection_copies_and_multi_year_files_keep_the_rule(tmp_path, rule):
    projected = extend_single_year_dataset(
        dataset(2023, ADDITIVE, PEOPLE, rule=rule), PARAMETERS, end_year=2026
    )
    assert {projected[year].savings_income_projection for year in projected.years} == {
        rule
    }
    assert projected.copy().savings_income_projection == rule
    path = tmp_path / "multi.h5"
    projected.save(str(path))
    with h5py.File(path, "r") as file:
        assert file.attrs[SAVINGS_INCOME_PROJECTION_KEY] == rule
    reloaded = UKMultiYearDataset(str(path))
    assert {reloaded[year].savings_income_projection for year in reloaded.years} == {
        rule
    }


def test_a_multi_year_dataset_refuses_mixed_rules():
    first = dataset(2023, ADDITIVE, PEOPLE, rule=GDP_PER_HEAD)
    second = dataset(2024, ADDITIVE, PEOPLE, rule=OBR_SAVINGS_INCOME_2022_2025)
    with pytest.raises(ValueError, match="different rules"):
        UKMultiYearDataset(datasets=[first, second])


def test_core_datasets_declare_through_an_attribute_or_their_file(tmp_path):
    assert (
        core_dataset_savings_income_projection(
            SimpleNamespace(savings_income_projection=OBR_SAVINGS_INCOME_2022_2025)
        )
        == OBR_SAVINGS_INCOME_2022_2025
    )
    assert core_dataset_savings_income_projection(SimpleNamespace()) == GDP_PER_HEAD
    path = tmp_path / "core.h5"
    dataset(2023, ADDITIVE, PEOPLE).save(str(path))
    assert (
        core_dataset_savings_income_projection(SimpleNamespace(file_path=str(path)))
        == OBR_SAVINGS_INCOME_2022_2025
    )


@pytest.mark.parametrize("rule", [None, OBR_SAVINGS_INCOME_2022_2025])
def test_a_simulation_projects_by_and_exports_the_rule(rule):
    """A simulation built from the data projects by its rule, and its clones,
    exported datasets and input frames declare the same rule."""
    sim = Microsimulation(dataset=dataset(2023, ADDITIVE, PEOPLE, rule=rule))
    expected = rule or GDP_PER_HEAD
    assert sim._savings_income_projection == expected
    assert sim.clone()._savings_income_projection == expected
    assert sim.to_input_dataframe().attrs[SAVINGS_INCOME_PROJECTION_KEY] == expected
    exported = UKSingleYearDataset.from_simulation(sim, fiscal_year=2025)
    assert exported.savings_income_projection == expected
    factor = (1 + growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, "2024", expected)) * (
        1 + growth_rate(PARAMETERS, SAVINGS_INCOME_GROWTH, "2025", expected)
    )
    before = sim.dataset[2023].person.other_investment_income.values
    after = sim.dataset[2025].person.other_investment_income.values
    np.testing.assert_allclose(after, before * factor, rtol=1e-12)
