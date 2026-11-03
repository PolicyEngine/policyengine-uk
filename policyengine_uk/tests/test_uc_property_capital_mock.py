"""UC financial and property capital through a local MOCK dataset.

These are synthetic post-ingestion tables, never survey records. The upstream
uk-data blocker exercises FRS B4/B3 selection and then the real engine. Here
we pin its engine-facing boundary: ``benunit_reported_capital`` is the selected
financial total (including zero or the missing sentinel), while the property
columns arrive separately after imputation. No uk-data dependency or network
access is needed to exercise their valuation and allocation in the engine.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025


def _mock_year(
    reported=(0,),
    *,
    adults=None,
    household_inputs=None,
    person_inputs=None,
    overrides=None,
    year=YEAR,
    age=30,
):
    """One MOCK household, with an explicit claimant/partner ownership set."""
    adults = adults or [1] * len(reported)
    benunit_ids = np.arange(1, len(reported) + 1)
    person_benunit_ids = np.repeat(benunit_ids, adults)
    person_count = len(person_benunit_ids)
    person = pd.DataFrame(
        {
            "person_id": np.arange(1, person_count + 1),
            "person_benunit_id": person_benunit_ids,
            "person_household_id": np.ones(person_count, dtype=int),
            "age": age,
            "is_claimant_or_partner": True,
            "employment_income": 0.0,
            **(person_inputs or {}),
        }
    )
    benunit = pd.DataFrame(
        {
            "benunit_id": benunit_ids,
            "benunit_reported_capital": np.array(reported, dtype=float),
            "would_claim_uc": True,
        }
    )
    if overrides is not None:
        benunit["uc_reported_capital"] = overrides
    household = pd.DataFrame(
        {
            "household_id": [1],
            "household_weight": [1.0],
            "region": ["LONDON"],
            "tenure_type": ["OWNED_OUTRIGHT"],
            "rent": [0.0],
            "council_tax": [0.0],
            "savings": [0.0],
            "corporate_wealth": [0.0],
            "other_residential_property_value": [0.0],
            "non_residential_property_value": [0.0],
            **{name: [value] for name, value in (household_inputs or {}).items()},
        }
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=year
    )


def _load_mock(tmp_path, *years):
    """Round-trip the actual H5 schema before calculating the real formulas."""
    path = tmp_path / "MOCK_uc_property_capital.h5"
    UKMultiYearDataset(datasets=list(years)).save(str(path))
    return Simulation(dataset=path)


@pytest.mark.parametrize(
    "property_variable",
    ["other_residential_property_value", "non_residential_property_value"],
)
def test_mock_zero_financial_total_preserves_countable_property(
    tmp_path, property_variable
):
    """The data PR's age-30 B4=0 / £50,000 property reproducer."""
    simulation = _load_mock(
        tmp_path,
        _mock_year(household_inputs={property_variable: 50_000}),
    )

    assert simulation.calculate("benunit_reported_capital", YEAR)[0] == 0
    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 45_000
    assert not simulation.calculate("is_uc_eligible", YEAR)[0]
    assert simulation.calculate("universal_credit", YEAR)[0] == 0


@pytest.mark.parametrize(
    "reported, household_inputs, expected_capital, tariff_steps",
    [
        (6_000, {"other_residential_property_value": 10_000}, 15_000, 36),
        (
            6_000,
            {
                "other_residential_property_value": 3_000,
                "non_residential_property_value": 7_000,
            },
            15_000,
            36,
        ),
        (0, {}, 0, 0),
        (6_000, {"savings": 50_000, "corporate_wealth": 30_000}, 6_000, 0),
        (
            -1,
            {"savings": 6_000, "other_residential_property_value": 10_000},
            15_000,
            36,
        ),
    ],
    ids=[
        "financial-plus-property",
        "both-property-components",
        "zero-financial-no-property",
        "financial-proxies-not-counted-twice",
        "missing-financial-keeps-proxy-and-property",
    ],
)
def test_mock_financial_and_property_pools(
    tmp_path, reported, household_inputs, expected_capital, tariff_steps
):
    simulation = _load_mock(
        tmp_path,
        _mock_year((reported,), household_inputs=household_inputs),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == expected_capital
    assert simulation.calculate("is_uc_eligible", YEAR)[0]
    annual_tariff = tariff_steps * 4.35 * 12
    assert simulation.calculate("uc_tariff_income", YEAR)[0] == pytest.approx(
        annual_tariff
    )
    allowance = simulation.calculate("uc_standard_allowance", YEAR)[0]
    assert allowance > 0
    assert simulation.calculate("universal_credit", YEAR)[0] == pytest.approx(
        allowance - annual_tariff
    )


def test_mock_complete_override_zero_consumes_its_whole_capital_share(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (6_000,),
            overrides=[0.0],
            household_inputs={
                "savings": 50_000,
                "other_residential_property_value": 50_000,
            },
            person_inputs={"lifetime_isa_balance": 30_000.0},
        ),
    )

    assert simulation.calculate("uc_reported_capital", YEAR)[0] == 0
    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 0
    assert simulation.calculate("is_uc_eligible", YEAR)[0]
    assert simulation.calculate("universal_credit", YEAR)[0] == pytest.approx(
        simulation.calculate("uc_standard_allowance", YEAR)[0]
    )


def test_mock_owner_override_consumes_its_company_holding_once(tmp_path):
    year = 2026
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (-1, -1),
            overrides=[10_000.0, -1.0],
            household_inputs={"savings": 20_000, "corporate_wealth": 10_000},
            person_inputs={
                "stands_as_sole_owner_or_partner_of_company": [True, False],
                "owned_company_carries_on_property_business": [True, False],
                "owned_company_holding_value": [10_000.0, 0.0],
                "owned_company_capital": [0.0, 0.0],
            },
            year=year,
        ),
    )

    # The owner's override already contains the holding. The other unit keeps
    # the £20k residual and is ineligible for UC after the H5 input round trip.
    np.testing.assert_allclose(
        simulation.calculate("uc_assessable_capital", year), [0, 20_000]
    )
    assert simulation.calculate("universal_credit", year)[1] == 0


@pytest.mark.parametrize("layout", ["two-overrides", "override-and-dependant"])
def test_mock_company_holding_routes_share_one_corporate_budget(tmp_path, layout):
    """The two review regressions preserve £20k savings after real H5 loading."""
    year = 2026
    dependant = layout == "override-and-dependant"
    holdings = [6_000.0, 4_000.0, 0.0, 0.0] if dependant else [6_000.0, 4_000.0, 0.0]
    flags = [holding > 0 for holding in holdings]
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (-1, 0 if dependant else -1, -1),
            adults=[2, 1, 1] if dependant else [1, 1, 1],
            overrides=[0.0, -1.0 if dependant else 0.0, -1.0],
            household_inputs={"savings": 20_000, "corporate_wealth": 4_000},
            person_inputs={
                "age": [30, 10, 30, 30] if dependant else [30, 30, 30],
                "is_claimant_or_partner": [True, False, True, True]
                if dependant
                else [True, True, True],
                "stands_as_sole_owner_or_partner_of_company": flags,
                "owned_company_carries_on_property_business": flags,
                "owned_company_holding_value": holdings,
                "owned_company_capital": [0.0] * len(holdings),
            },
            year=year,
        ),
    )

    np.testing.assert_allclose(
        simulation.calculate("uc_assessable_capital", year), [0, 0, 20_000]
    )
    assert not simulation.calculate("is_uc_eligible", year)[2]
    assert simulation.calculate("universal_credit", year)[2] == 0


def test_mock_financial_total_already_covers_lifetime_isa(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (6_000,),
            household_inputs={"household_lifetime_isa_balance": 30_000},
            person_inputs={"lifetime_isa_balance": 30_000.0},
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 6_000
    assert simulation.calculate("uc_tariff_income", YEAR)[0] == 0


def test_mock_main_home_is_excluded_and_cash_has_no_sale_deduction(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (-1,),
            household_inputs={"main_residence_value": 500_000, "savings": 6_001},
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 6_001
    assert simulation.calculate("uc_tariff_income", YEAR)[0] == pytest.approx(4.35 * 12)


def test_mock_property_allocation_pools_claimant_and_partner_shares(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (0, 0),
            adults=[2, 1],
            household_inputs={"other_residential_property_value": 12_000},
        ),
    )

    assessed = simulation.calculate("uc_assessable_capital", YEAR)
    assert assessed.tolist() == pytest.approx([7_200, 3_600])
    assert assessed.sum() == pytest.approx(12_000 * 0.9)


@pytest.mark.parametrize(
    "property_variable, debt_variable",
    [
        (
            "other_residential_property_value",
            "other_residential_property_secured_debt",
        ),
        (
            "non_residential_property_value",
            "non_residential_property_secured_debt",
        ),
    ],
)
@pytest.mark.parametrize("secured_debt, expected", [(2_000, 7_000), (9_500, 0)])
def test_mock_property_deducts_sale_expenses_before_secured_debt(
    tmp_path, property_variable, debt_variable, secured_debt, expected
):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            household_inputs={
                property_variable: 10_000,
                debt_variable: secured_debt,
            },
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == expected


def test_mock_property_type_debt_does_not_reduce_another_property_pool(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            household_inputs={
                "other_residential_property_value": 10_000,
                "other_residential_property_secured_debt": 20_000,
                "non_residential_property_value": 10_000,
            },
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 9_000


@pytest.mark.parametrize("other_financial", [-1, 0, 6_000])
def test_mock_mixed_household_keeps_override_and_property_pools_separate(
    tmp_path, other_financial
):
    """An override's property share is consumed, never redistributed."""
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (-1, other_financial, -1),
            adults=[1, 2, 1],
            overrides=[100_000.0, -1.0, -1.0],
            household_inputs={"other_residential_property_value": 12_000},
        ),
    )

    assessed = simulation.calculate("uc_assessable_capital", YEAR)
    financial = max(0, other_financial)
    assert assessed.tolist() == pytest.approx([100_000, financial + 5_400, 2_700])
    # Add the override unit's consumed conventional share back only for this
    # conservation assertion. Its unknown financial/property split is not an
    # observed component of either allocation pool.
    assert assessed[1:].sum() - financial + 2_700 == pytest.approx(12_000 * 0.9)


def test_mock_property_valuation_uses_the_assessment_year(tmp_path):
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (6_000,), household_inputs={"other_residential_property_value": 10_000}
        ),
        _mock_year(
            (6_000,),
            household_inputs={"other_residential_property_value": 20_000},
            year=2026,
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 15_000
    assert simulation.calculate("uc_assessable_capital", 2026)[0] == 24_000


@pytest.mark.parametrize("reported, expected", [(6_000, 6_000), (0, 0), (-1, 56_000)])
def test_mock_pension_credit_keeps_its_existing_reported_capital_contract(
    tmp_path, reported, expected
):
    """Changing UC's financial boundary does not change Pension Credit."""
    simulation = _load_mock(
        tmp_path,
        _mock_year(
            (reported,),
            overrides=[0.0],
            age=75,
            household_inputs={
                "savings": 6_000,
                "other_residential_property_value": 50_000,
            },
        ),
    )

    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 0
    assert simulation.calculate("pension_credit_reported_capital", YEAR)[0] == reported
    assert (
        simulation.calculate("pension_credit_assessable_capital", YEAR)[0] == expected
    )
