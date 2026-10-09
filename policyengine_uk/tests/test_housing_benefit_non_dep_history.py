"""Complete historical HB scale, separate from deduction eligibility rules."""

from pathlib import Path

import numpy as np
import pytest
from policyengine_core.parameters.helpers import load_parameter_file

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
    ],
)
def test_all_historical_scale_cells(year, thresholds, amounts):
    # SI 2015/457 art 18(3); SI 2016/242 reg 5; SI 2017/260 art 22(4).
    # Test the parameter itself, not the separate #2007 eligibility/banding fix.
    scale = load_parameter_file(str(PATH), "hb_non_dep_scale")(f"{year}-04-30")
    assert scale.thresholds == thresholds
    assert scale.amounts == amounts
    np.testing.assert_allclose(
        scale.calc(np.array(thresholds)), amounts, rtol=0, atol=0
    )
