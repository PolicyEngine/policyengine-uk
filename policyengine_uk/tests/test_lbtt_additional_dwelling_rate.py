"""ADS statutory date and the existing annual transactional-tax convention.

SSI 2024/367 arts1–3 changes6% to8% from5December2024, with protection
for contracts entered on/before4December. Annual purchase inputs have no
contract/effective date; processed parameters sample30April, so these
annual readings cannot select protected contracts or late2024 purchases.
"""

from pathlib import Path

import pytest
import yaml
from policyengine_core.parameters import Parameter

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem

PATH = "gov.revenue_scotland.lbtt.residential.additional_residence_surcharge"
FILE = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/revenue_scotland/lbtt/residential/additional_residence_surcharge.yaml"
)


def test_raw_ads_rate_keeps_history_and_changes_on_5_december_2024():
    data = yaml.safe_load(FILE.read_text())
    data["values"] = {str(date): value for date, value in data["values"].items()}
    raw = Parameter(PATH, data=data, file_path=str(FILE))
    for date, expected in [
        ("2016-04-01", 0.03),
        ("2019-01-25", 0.04),
        ("2022-12-16", 0.06),
        ("2024-12-04", 0.06),
        ("2024-12-05", 0.08),
    ]:
        assert raw(date) == expected, date
    assert not raw.metadata.get("fiscal_year_blend", False)
    assert not raw.metadata.get("preserve_calendar_dates", False)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize("year,expected", [(2024, 0.06), (2025, 0.08), (2026, 0.08)])
def test_annual_ads_rate_preserves_april30_sampling(system, year, expected):
    assert system.parameters.get_child(PATH)(f"{year}-01-01") == expected
