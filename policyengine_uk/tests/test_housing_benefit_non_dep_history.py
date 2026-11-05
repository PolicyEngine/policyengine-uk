"""Complete historical HB scale, separate from deduction eligibility rules."""

from pathlib import Path

import numpy as np
import pytest
from policyengine_core.parameters.helpers import load_parameter_file

from policyengine_uk.system import system

PATH = (
    Path(__file__).resolve().parents[1]
    / "parameters/gov/dwp/housing_benefit/non_dep_deduction/amount.yaml"
)


@pytest.mark.parametrize(
    "year, thresholds, amounts",
    [
        (
            2015,
            [0, 129, 189, 246, 328, 408],
            [14.55, 33.40, 45.85, 75.05, 85.45, 93.80],
        ),
        (
            2016,
            [0, 133, 195, 253, 338, 420],
            [14.65, 33.65, 46.20, 75.60, 86.10, 94.50],
        ),
        (
            2017,
            [0, 136, 200, 259, 346, 430],
            [14.80, 34.00, 46.65, 76.35, 86.95, 95.45],
        ),
        (
            2018,
            [0, 139, 204, 265, 354, 439],
            [15.25, 35.00, 48.05, 78.65, 89.55, 98.30],
        ),
    ],
)
def test_all_historical_scale_cells(year, thresholds, amounts):
    # SI 2015/457 art 18(3); SI 2016/242 reg 5; SI 2017/260 art 22(4);
    # SI 2018/281 arts 1(2)(h), 23(3) and 24(3).
    # Test the parameter itself, not the separate #2007 eligibility/banding fix.
    scale = load_parameter_file(str(PATH), "hb_non_dep_scale")(f"{year}-04-30")
    assert scale.thresholds == thresholds
    assert scale.amounts == amounts
    np.testing.assert_allclose(
        scale.calc(np.array(thresholds)), amounts, rtol=0, atol=0
    )


@pytest.mark.parametrize("instant", ["2018", "2018-04-30"])
def test_processed_2018_scale_uses_april_commencement(instant):
    # The full processing pipeline backdates parameters to 2015 and samples
    # each fiscal year at 30 April. A June date incorrectly selects 2017 rates.
    scale = system.parameters(instant).gov.dwp.housing_benefit.non_dep_deduction.amount
    assert scale.thresholds == [0, 139, 204, 265, 354, 439]
    assert scale.amounts == [15.25, 35.00, 48.05, 78.65, 89.55, 98.30]
    # SI 2018/281 arts 23(3)(b) and 24(3)(b): £15.25 a week at £100 income.
    np.testing.assert_allclose(scale.calc(np.array([100])) * 52, [793], rtol=0, atol=0)
