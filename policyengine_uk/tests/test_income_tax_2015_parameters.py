"""Statutory 2015-16 parameters and the 6 April 2016 transition (#2865).

Sources: ITA 2007 ss.8, 10(5) and 13 as at 6 April 2015; Finance
(No. 2) Act 2015 s.6(a); Finance Act 2016 ss.4(17) and 5(3), (5), (10).
https://www.legislation.gov.uk/ukpga/2007/3/section/10/2015-04-06
https://www.legislation.gov.uk/ukpga/2007/3/section/13/2015-04-06
https://www.legislation.gov.uk/ukpga/2015/33/section/6/enacted
https://www.legislation.gov.uk/ukpga/2016/24/section/4/enacted
https://www.legislation.gov.uk/ukpga/2016/24/section/5/enacted

The official 2015-16/2016-17 rates table independently lists these figures:
https://www.gov.uk/government/publications/tax-and-tax-credit-rates-and-thresholds-for-2016-17/tax-and-tax-credit-rates-and-thresholds-for-2016-17

These are nominal statutory parameter tests, not a certification of cash
dividend liability before 2016. That regime also needs the historical
gross-up and tax credit (ITTOIA 2005 ss.397-398; HMRC SAIM5100).
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
        ("rates/dividends.yaml", 1, "threshold", 31_785, 32_000),
        ("rates/dividends.yaml", 0, "rate", 0.1, 0.075),
        ("rates/dividends.yaml", 1, "rate", 0.325, 0.325),
        ("rates/dividends.yaml", 2, "rate", 0.375, 0.381),
        # The technical extra bracket must repeat the additional rate.
        ("rates/dividends.yaml", 3, "rate", 0.375, 0.381),
        ("allowances/dividend_allowance.yaml", None, None, 0, 5_000),
        ("allowances/personal_savings_allowance/basic.yaml", None, None, 0, 1_000),
        ("allowances/personal_savings_allowance/higher.yaml", None, None, 0, 500),
        ("allowances/personal_savings_allowance/additional.yaml", None, None, 0, 0),
    ],
    ids=[
        "UK-basic-limit",
        "dividend-upper-threshold",
        "dividend-ordinary-rate",
        "dividend-upper-rate",
        "dividend-additional-rate",
        "dividend-extra-rate",
        "dividend-allowance",
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
    "year,basic_limit,dividend_rates,dividend_allowance,savings_allowances",
    [
        (2015, 31_785, [0.1, 0.325, 0.375, 0.375], 0, [0, 0, 0]),
        (2016, 32_000, [0.075, 0.325, 0.381, 0.381], 5_000, [1_000, 500, 0]),
    ],
)
def test_processed_annual_parameters_preserve_both_tax_years(
    system, year, basic_limit, dividend_rates, dividend_allowance, savings_allowances
):
    income_tax = system.parameters(f"{year}-01-01").gov.hmrc.income_tax
    assert income_tax.rates.uk.thresholds[1] == basic_limit
    assert income_tax.rates.dividends.thresholds[1] == basic_limit
    assert income_tax.rates.dividends.rates == dividend_rates
    assert income_tax.allowances.dividend_allowance == dividend_allowance
    psa = income_tax.allowances.personal_savings_allowance
    assert [psa.basic, psa.higher, psa.additional] == savings_allowances
