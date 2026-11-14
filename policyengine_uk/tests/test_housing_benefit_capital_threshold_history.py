"""Ordinary pension-age HB capital history, before fiscal-year conversion."""

from pathlib import Path

import pytest
import yaml
from policyengine_core.parameters import Parameter

PARAMETER_PATH = (
    Path(__file__).resolve().parents[1]
    / "parameters/gov/dwp/housing_benefit/means_test/capital/pension_age"
    / "tariff_income/threshold.yaml"
)


@pytest.mark.parametrize(
    "instant, expected",
    [
        ("2006-04-10", 6000),
        ("2009-11-01", 6000),
        ("2009-11-02", 10000),
        ("2015-04-30", 10000),
        ("2026-04-30", 10000),
    ],
)
def test_ordinary_threshold_history(instant, expected):
    # Read the enacted calendar history: annual model conversion starts in 2015.
    # SI 2006/214 reg 29(2)(b), replaced by SI 2009/1676 regs 1 and 5.
    data = yaml.safe_load(PARAMETER_PATH.read_text())
    data["values"] = {str(date): value for date, value in data["values"].items()}
    threshold = Parameter("pension_age_tariff_threshold", data=data)
    assert threshold(instant) == expected
