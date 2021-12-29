"""
This module tests the FRS dataset produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

import pandas as pd
from openfisca_uk_data import FRSEnhanced, UKMODOutput
from openfisca_uk import Microsimulation, REPO
import pytest
from microdf import MicroDataFrame
from openfisca_uk.reforms.presets.current_date import use_current_parameters
from openfisca_uk.tools.parameters import backdate_parameters
import yaml

TEST_YEAR = 2018
# Variable pairs to check for similarity
with open(
    REPO / "tests" / "microsimulation" / "frs" / "variable_ukmod_map.yml"
) as f:
    metadata = yaml.safe_load(f)

MAX_REL_ERROR = 0.05
MAX_MEAN_REL_ERROR = 0.05
MIN_NONZERO_AGREEMENT = 0.99

if TEST_YEAR not in UKMODOutput.years:
    raise FileNotFoundError("UKMOD FRS needed to run tests against.")
if TEST_YEAR not in FRSEnhanced.years:
    raise FileNotFoundError("FRS needed to run tests.")

baseline = Microsimulation(
    dataset=FRSEnhanced,
    year=TEST_YEAR,
)
ukmod = UKMODOutput.load(TEST_YEAR, "person")
ukmod_hh = ukmod.groupby("household_id").sum()
ukmod = MicroDataFrame(ukmod, weights=ukmod.person_weight)


def get_test_params(variable):
    test_params = dict(
        ukmod=metadata[variable],
        max_rel_error=MAX_MEAN_REL_ERROR,
        max_mean_rel_error=MAX_MEAN_REL_ERROR,
        min_nonzero_agreement=MIN_NONZERO_AGREEMENT,
        skip_household_matching=False,
    )
    if isinstance(metadata[variable], dict):
        test_params.update(**metadata[variable])
    else:
        test_params["ukmod"] = metadata[variable]
    return test_params


@pytest.mark.parametrize("variable", metadata.keys())
def test_aggregate(variable):
    test_params = get_test_params(variable)
    result = baseline.calc(variable, period=TEST_YEAR).sum()
    target = ukmod[test_params["ukmod"]].sum()

    assert abs(result / target - 1) < test_params["max_rel_error"]

    return result, target


@pytest.mark.parametrize("variable", metadata.keys())
def test_nonzero_count(variable):
    test_params = get_test_params(variable)
    result = (baseline.calc(variable, period=TEST_YEAR) > 0).sum()
    target = (ukmod[test_params["ukmod"]] > 0).sum()

    assert abs(result / target - 1) < test_params["max_rel_error"]

    return result, target


@pytest.mark.parametrize("variable", metadata.keys())
def test_average_error_among_nonzero(variable):
    test_params = get_test_params(variable)
    if test_params["skip_household_matching"]:
        return
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[test_params["ukmod"]]
    # Exclude the smallest 10% to avoid overweighting small errors
    mean_error_ukmod_nonzero = (
        (result / target - 1)[target > target[target > 0].quantile(0.1)]
        .abs()
        .mean()
    )

    assert mean_error_ukmod_nonzero < test_params["max_mean_rel_error"]

    return mean_error_ukmod_nonzero


@pytest.mark.parametrize("variable", metadata.keys())
def test_ukmod_nonzero_agreement(variable):
    test_params = get_test_params(variable)
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[test_params["ukmod"]]
    mean_error = ((result > 0) == (target == 0)).mean()

    assert mean_error < test_params["min_nonzero_agreement"]

    return mean_error
