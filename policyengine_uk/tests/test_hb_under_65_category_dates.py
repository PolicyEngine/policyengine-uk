"""The historical under-65 pension-age Housing Benefit category ends on the same
day in both jurisdictions.

Great Britain: SI 2017/1187 regs 1(2)(b) and 7(7). Northern Ireland: SR 2017/242
regs 1(2)(b) and 7(7). Each removes the under-65 rows of the personal allowance
table from 6 December 2018. The model samples annual parameters at 30 April, so
the date moves no annual result; this test pins the statutory dates in the
parameter files.
"""

import datetime
from pathlib import Path

import pytest
import yaml

ALLOWANCES = (
    Path(__file__).parents[1]
    / "parameters"
    / "gov"
    / "dwp"
    / "housing_benefit"
    / "allowances"
)
END = datetime.date(2018, 12, 6)


@pytest.mark.parametrize("category", ["single", "couple", "lone_parent"])
@pytest.mark.parametrize(
    "jurisdiction, instrument",
    [("great_britain", "uksi/2017/1187"), ("northern_ireland", "nisr/2017/242")],
)
def test_under_65_category_ends_on_6_december_2018(category, jurisdiction, instrument):
    data = yaml.safe_load((ALLOWANCES / category / "aged_under_65.yaml").read_text())
    values = data[f"age_limit_{jurisdiction}"]["values"]
    dates = sorted(values)
    assert dates[-1] == END
    assert values[dates[-2]] == 65
    end = values[END]
    assert end["value"] == 0
    assert any(instrument in reference["href"] for reference in end["reference"])
