"""Dated dividend limits and preserved rate/reform interfaces.

ITA 2007 s.13 uses the corresponding UK taxable-income bands. Earlier
unchanged values below are regression controls, not a pre-2016 law audit.
"""

from pathlib import Path

import pytest
import yaml
from policyengine_core.parameters import Parameter

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem

PATH = "gov.hmrc.income_tax.rates.dividends"
FILE = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/hmrc/income_tax/rates/dividends.yaml"
)


@pytest.mark.parametrize(
    "bracket,before,after,old,new",
    [
        (1, "2016-04-05", "2016-04-06", 37_500, 32_000),
        (1, "2017-04-05", "2017-04-06", 32_000, 33_500),
        (1, "2018-04-05", "2018-04-06", 33_500, 34_500),
        (1, "2019-04-05", "2019-04-06", 34_500, 37_500),
        (1, "2021-04-05", "2021-04-06", 37_500, 37_700),
        (2, "2023-04-05", "2023-04-06", 150_000, 125_140),
    ],
)
def test_raw_dividend_limits_change_on_the_statutory_tax_year_date(
    bracket, before, after, old, new
):
    data = yaml.safe_load(FILE.read_text())["brackets"][bracket]["threshold"]
    data["values"] = {str(date): value for date, value in data["values"].items()}
    raw = Parameter(f"{PATH}[{bracket}].threshold", data=data, file_path=str(FILE))
    assert raw(before) == old
    assert raw(after) == new


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "year,basic_limit,additional_limit",
    [
        (2016, 32_000, 150_000),
        (2017, 33_500, 150_000),
        (2018, 34_500, 150_000),
        (2019, 37_500, 150_000),
        (2020, 37_500, 150_000),
        (2021, 37_700, 150_000),
        (2023, 37_700, 125_140),
        (2025, 37_700, 125_140),
        (2026, 37_700, 125_140),
    ],
)
def test_annual_dividend_limits_include_restoration_and_current_years(
    system, year, basic_limit, additional_limit
):
    scale = system.parameters.get_child(PATH)(f"{year}-01-01")
    assert scale.thresholds == [0, basic_limit, additional_limit, 10_000_000]


def test_2026_dividend_rates_and_optional_extra_bracket_are_unchanged(system):
    scale = system.parameters.get_child(PATH)("2026-01-01")
    assert scale.rates == [0.1075, 0.3575, 0.3935, 0.3935]
    assert scale.thresholds == [0, 37_700, 125_140, 10_000_000]
