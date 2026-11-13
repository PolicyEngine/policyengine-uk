"""2015-16 non-dividend parameters and held dividend compatibility (#2865).

Sources: ITA 2007 ss.8, 10(5) and 13 as at 6 April 2015; Finance
(No. 2) Act 2015 s.6(a); Finance Act 2016 ss.4(17) and 5(3), (5), (10).
https://www.legislation.gov.uk/ukpga/2007/3/section/10/2015-04-06
https://www.legislation.gov.uk/ukpga/2007/3/section/13/2015-04-06
https://www.legislation.gov.uk/ukpga/2015/33/section/6/enacted
https://www.legislation.gov.uk/ukpga/2016/24/section/4/enacted
https://www.legislation.gov.uk/ukpga/2016/24/section/5/enacted

The official 2015-16/2016-17 rates table independently lists these figures:
https://www.gov.uk/government/publications/tax-and-tax-credit-rates-and-thresholds-for-2016-17/tax-and-tax-credit-rates-and-thresholds-for-2016-17

The statutory assertions cover the UK basic-rate limit and Personal Savings
Allowance. The separately named dividend controls preserve the pre-backfill
model approximation; they do not certify cash-dividend liability before 2016.
That regime still needs the historical gross-up and tax credit
(ITTOIA 2005 ss.397-398; HMRC SAIM5100).
Raw parameters retain the actual April boundary. Processed model year Y
uses the fiscal-year value sampled at 30 April Y, including for January.
"""

from pathlib import Path

import pytest
import yaml
from policyengine_core.parameters import Parameter

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem

PARAMETER_DIR = Path(policyengine_uk.__file__).parent / "parameters/gov/hmrc/income_tax"


def raw_parameter(relative, bracket, field):
    """Read an unprocessed leaf using Core, as test_dividend_band_dates does."""
    file = PARAMETER_DIR / relative
    data = yaml.safe_load(file.read_text())
    if bracket is not None:
        data = data["brackets"][bracket][field]
    data["values"] = {str(date): value for date, value in data["values"].items()}
    return Parameter(f"historical_2015.{relative}.{bracket}.{field}", data=data)


@pytest.mark.parametrize(
    "relative,bracket,field,before,after",
    [
        ("rates/uk.yaml", 1, "threshold", 31_785, 32_000),
        ("allowances/personal_savings_allowance/basic.yaml", None, None, 0, 1_000),
        ("allowances/personal_savings_allowance/higher.yaml", None, None, 0, 500),
        ("allowances/personal_savings_allowance/additional.yaml", None, None, 0, 0),
    ],
    ids=[
        "UK-basic-limit",
        "PSA-basic",
        "PSA-higher",
        "PSA-additional",
    ],
)
def test_raw_parameters_change_on_6_april_2016(relative, bracket, field, before, after):
    raw = raw_parameter(relative, bracket, field)
    assert raw("2015-04-06") == before
    assert raw("2016-04-05") == before
    assert raw("2016-04-06") == after


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "year,basic_limit,savings_allowances",
    [
        (2015, 31_785, [0, 0, 0]),
        (2016, 32_000, [1_000, 500, 0]),
    ],
)
def test_processed_annual_parameters_preserve_both_tax_years(
    system, year, basic_limit, savings_allowances
):
    income_tax = system.parameters(f"{year}-01-01").gov.hmrc.income_tax
    assert income_tax.rates.uk.thresholds[1] == basic_limit
    psa = income_tax.allowances.personal_savings_allowance
    assert [psa.basic, psa.higher, psa.additional] == savings_allowances


def test_held_2015_dividend_parameters_preserve_pre_backfill_approximation(system):
    # Frozen from pre-backfill parent b8b383cd. These are compatibility
    # values, not the statutory 2015 nominal rates or dividend allowance.
    income_tax = system.parameters("2015-01-01").gov.hmrc.income_tax
    assert income_tax.rates.dividends.rates == [0.075, 0.325, 0.381, 0.381]
    assert income_tax.rates.dividends.thresholds == [0, 37_500, 150_000, 10_000_000]
    assert income_tax.allowances.dividend_allowance == 5_000


def test_held_dividend_allowance_keeps_its_first_stated_2016_entry():
    # The processed model backdates the first value. Raw YAML does not
    # state that the 5,000 allowance legally applied before 6 April 2016.
    data = yaml.safe_load(
        (PARAMETER_DIR / "allowances/dividend_allowance.yaml").read_text()
    )
    values = {str(date): value for date, value in data["values"].items()}
    assert min(values) == "2016-04-06"
    assert values["2016-04-06"]["value"] == 5_000


@pytest.mark.parametrize(
    "year,rates,thresholds,dividend_allowance",
    [
        (2016, [0.075, 0.325, 0.381, 0.381], [0, 32_000, 150_000, 10_000_000], 5_000),
        (2026, [0.1075, 0.3575, 0.3935, 0.3935], [0, 37_700, 125_140, 10_000_000], 500),
    ],
)
def test_modern_dividend_parameters_remain_unchanged(
    system, year, rates, thresholds, dividend_allowance
):
    income_tax = system.parameters(f"{year}-01-01").gov.hmrc.income_tax
    assert income_tax.rates.dividends.rates == rates
    assert income_tax.rates.dividends.thresholds == thresholds
    assert income_tax.allowances.dividend_allowance == dividend_allowance
