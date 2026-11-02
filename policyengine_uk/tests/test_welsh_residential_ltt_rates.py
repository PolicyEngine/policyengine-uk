"""Welsh residential LTT dates and the existing annual sampling convention.

WSI 2022/1027 reg 7 replaces the main table from 10 October 2022;
WSI 2024/1311 reg 6 replaces the higher table from 11 December 2024.
Annual purchase inputs cannot select transaction dates or protected contracts.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml
from policyengine_core.parameters import ParameterScale

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem

PATH = "gov.wra.land_transaction_tax.residential"
DIRECTORY = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/wra/land_transaction_tax/residential"
)
OLD_THRESHOLDS = [0, 180_000, 250_000, 400_000, 750_000, 1_500_000]
MAIN_THRESHOLDS = [0, 225_000, 400_000, 750_000, 1_500_000]
OLD_MAIN_RATES = [0, 0.035, 0.05, 0.075, 0.1, 0.12]
MAIN_RATES = [0, 0.06, 0.075, 0.1, 0.12]
OLD_HIGHER_RATES = [0.04, 0.075, 0.09, 0.115, 0.14, 0.16]
HIGHER_RATES = [0.05, 0.085, 0.1, 0.125, 0.15, 0.17]


def raw_scale(name):
    file = DIRECTORY / f"{name}.yaml"
    data = yaml.safe_load(file.read_text())
    for bracket in data["brackets"]:
        for component in ["threshold", "rate"]:
            bracket[component] = {
                str(date): value for date, value in bracket[component].items()
            }
    return ParameterScale(f"{PATH}.{name}", data=data, file_path=str(file))


@pytest.mark.parametrize(
    "date,thresholds,rates",
    [
        ("2018-04-01", OLD_THRESHOLDS, OLD_MAIN_RATES),
        (
            "2020-07-27",
            [0, 250_000, 400_000, 750_000, 1_500_000],
            [0, 0.05, 0.075, 0.1, 0.12],
        ),
        ("2021-07-01", OLD_THRESHOLDS, OLD_MAIN_RATES),
        ("2022-10-09", OLD_THRESHOLDS, OLD_MAIN_RATES),
        ("2022-10-10", MAIN_THRESHOLDS, MAIN_RATES),
    ],
)
def test_raw_main_table_preserves_history_and_october_change(date, thresholds, rates):
    raw = raw_scale("primary")
    assert raw(date).thresholds == thresholds
    assert raw(date).rates == rates
    assert not raw.metadata.get("fiscal_year_blend", False)
    assert not raw.metadata.get("preserve_calendar_dates", False)


@pytest.mark.parametrize(
    "date,rates",
    [
        ("2018-04-01", [0.03, 0.065, 0.08, 0.105, 0.13, 0.15]),
        ("2020-12-21", [0.03, 0.065, 0.08, 0.105, 0.13, 0.15]),
        ("2020-12-22", OLD_HIGHER_RATES),
        ("2024-12-10", OLD_HIGHER_RATES),
        ("2024-12-11", HIGHER_RATES),
    ],
)
def test_raw_higher_table_preserves_history_and_december_change(date, rates):
    raw = raw_scale("higher_rate")
    assert raw(date).thresholds == OLD_THRESHOLDS
    assert raw(date).rates == rates


@pytest.mark.parametrize(
    "name,date,expected",
    [
        (
            "primary",
            "2022-10-10",
            [0, 0, 0, 1_500, 4_500, 10_500, 18_000, 36_750, 41_750, 111_750, 171_750],
        ),
        (
            "higher_rate",
            "2024-12-11",
            [
                0,
                9_000,
                12_825,
                14_950,
                19_950,
                29_950,
                42_450,
                73_700,
                81_200,
                186_200,
                271_200,
            ],
        ),
    ],
)
def test_new_tables_apply_marginal_rates_across_all_bands(name, date, expected):
    prices = np.array(
        [
            0,
            180_000,
            225_000,
            250_000,
            300_000,
            400_000,
            500_000,
            750_000,
            800_000,
            1_500_000,
            2_000_000,
        ]
    )
    np.testing.assert_allclose(
        raw_scale(name)(date).calc(prices), expected, rtol=0, atol=1e-8
    )


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "name,year,thresholds,rates",
    [
        ("primary", 2022, OLD_THRESHOLDS, OLD_MAIN_RATES),
        ("primary", 2023, MAIN_THRESHOLDS, MAIN_RATES),
        ("higher_rate", 2024, OLD_THRESHOLDS, OLD_HIGHER_RATES),
        ("higher_rate", 2025, OLD_THRESHOLDS, HIGHER_RATES),
    ],
)
def test_annual_tables_keep_april30_transactional_sampling(
    system, name, year, thresholds, rates
):
    scale = system.parameters.get_child(f"{PATH}.{name}")(f"{year}-01-01")
    assert scale.thresholds == thresholds
    assert scale.rates == rates
