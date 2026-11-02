"""`fiscal_year` labelling on UKSingleYearDataset.

The year label is the year the financial year starts, so FRS 2024/25 data
is labelled 2024. A dataset loaded from a file takes its period from the
file; one built from DataFrames takes it from the argument.
"""

import os
import subprocess
import sys
import textwrap
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
    with pytest.warns(FutureWarning, match="fiscal_year was not given"):
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


# pytest.warns overrides the active filters, so the tests above would pass
# even if importing the package silenced warnings process-wide. Run a fresh
# interpreter under Python's default filters, as an ordinary caller would.
FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import sys
    import tempfile
    from pathlib import Path

    import pandas as pd

    import policyengine_uk  # noqa: F401  (import side effects are under test)
    from policyengine_uk.data.dataset_schema import UKSingleYearDataset

    frames = dict(
        person=pd.DataFrame(
            {"person_id": [1], "person_benunit_id": [1], "person_household_id": [1]}
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame({"household_id": [1]}),
    )
    UKSingleYearDataset(**frames)
    with tempfile.TemporaryDirectory() as directory:
        file_path = Path(directory) / "dataset.h5"
        UKSingleYearDataset(**frames, fiscal_year=2024).save(file_path)
        UKSingleYearDataset(file_path=file_path, fiscal_year=2030)
    """
)


def test_warnings_reach_a_fresh_process_under_default_filters():
    result = subprocess.run(
        [sys.executable, "-c", FRESH_PROCESS_SCRIPT],
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "PYTHONWARNINGS"},
    )
    assert result.returncode == 0, result.stderr
    assert "FutureWarning: fiscal_year was not given" in result.stderr
    assert "UserWarning: fiscal_year is ignored when loading" in result.stderr
