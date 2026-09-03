"""`fiscal_year` labelling on UKSingleYearDataset.

The year label is the year the financial year starts, so FRS 2024/25 data
is labelled 2024. A dataset loaded from a file takes its period from the
file; one built from DataFrames takes it from the argument.
"""

import warnings

import pandas as pd
import pytest

from policyengine_uk.data.dataset_schema import UKSingleYearDataset


@pytest.fixture
def frames():
    person = pd.DataFrame(
        {"person_id": [1], "person_benunit_id": [1], "person_household_id": [1]}
    )
    benunit = pd.DataFrame({"benunit_id": [1]})
    household = pd.DataFrame({"household_id": [1]})
    return person, benunit, household


def test_fiscal_year_sets_the_time_period(frames):
    person, benunit, household = frames
    dataset = UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2024
    )
    assert dataset.time_period == "2024"


def test_omitting_fiscal_year_warns(frames):
    person, benunit, household = frames
    with pytest.warns(DeprecationWarning, match="fiscal_year was not given"):
        dataset = UKSingleYearDataset(
            person=person, benunit=benunit, household=household
        )
    assert dataset.time_period == str(UKSingleYearDataset.DEFAULT_FISCAL_YEAR)


def test_fiscal_year_alongside_a_file_path_warns(tmp_path, frames):
    person, benunit, household = frames
    file_path = tmp_path / "dataset.h5"
    UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2024
    ).save(file_path)

    with pytest.warns(UserWarning, match="ignored when loading from a file"):
        dataset = UKSingleYearDataset(file_path=file_path, fiscal_year=2030)

    # The file's own period wins, so the ignored argument cannot mislabel it.
    assert dataset.time_period == "2024"


def test_loading_without_fiscal_year_does_not_warn(tmp_path, frames):
    person, benunit, household = frames
    file_path = tmp_path / "dataset.h5"
    UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2024
    ).save(file_path)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert UKSingleYearDataset(file_path=file_path).time_period == "2024"
