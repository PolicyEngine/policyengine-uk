import pandas as pd
from openfisca_uk.microdata import FRS
import h5py
import pytest

TEST_YEAR = 2018

FRS.generate(2018)

with h5py.File(FRS.file(TEST_YEAR)) as f:
    VARIABLES = list(f.keys())


@pytest.mark.parametrize("variable", VARIABLES)
def test_not_nan(variable):
    assert pd.Series(FRS.load(TEST_YEAR, variable)).isna().mean() == 0
