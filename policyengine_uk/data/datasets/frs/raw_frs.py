from policyengine_core.data import Dataset
from pathlib import Path
import pandas as pd
from pandas import DataFrame
import warnings
from ..utils import (
    sum_to_entity,
    categorical,
    sum_from_positive_fields,
    sum_positive_variables,
    fill_with_mean,
    STORAGE_FOLDER,
)
from typing import Dict
import numpy as np
from numpy import maximum as max_, where
from typing import Type


class RawFRS(Dataset):
    """A `Survey` instance for the Family Resources Survey."""

    name = "raw_frs"
    label = "Family Resources Survey"
    data_format = Dataset.TABLES
    tab_folder = None

    @staticmethod
    def from_folder(
        folder: str,
        new_name: str = None,
        new_label: str = None,
        new_time_period: int = None,
        new_url: str = None,
    ):
        class RawFRSFromFolder(RawFRS):
            tab_folder = folder
            name = new_name
            label = new_label
            file_path = STORAGE_FOLDER / f"{new_name}.h5"
            time_period = new_time_period
            url = new_url

        return RawFRSFromFolder

    def generate(self):
        """Generate the survey data from the original TAB files.

        Args:
            tab_folder (Path): The folder containing the original TAB files.
        """

        tab_folder = self.tab_folder

        if isinstance(tab_folder, str):
            tab_folder = Path(tab_folder)

        # Load the data
        tables = {}
        for tab_file in tab_folder.glob("*.tab"):
            table_name = tab_file.stem
            if "frs" in table_name:
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tables[table_name] = pd.read_csv(
                    tab_file, delimiter="\t"
                ).apply(pd.to_numeric, errors="coerce")

            sernum = (
                "sernum"
                if "sernum" in tables[table_name].columns
                else "SERNUM"
            )  # FRS inconsistently users sernum/SERNUM in different years

            if "PERSON" in tables[table_name].columns:
                tables[table_name]["person_id"] = (
                    tables[table_name][sernum] * 1e2
                    + tables[table_name].BENUNIT * 1e1
                    + tables[table_name].PERSON
                ).astype(int)

            if "BENUNIT" in tables[table_name].columns:
                tables[table_name]["benunit_id"] = (
                    tables[table_name][sernum] * 1e2
                    + tables[table_name].BENUNIT * 1e1
                ).astype(int)

            if sernum in tables[table_name].columns:
                tables[table_name]["household_id"] = (
                    tables[table_name][sernum] * 1e2
                ).astype(int)
            if table_name in ("adult", "child"):
                tables[table_name].set_index(
                    "person_id", inplace=True, drop=False
                )
            elif table_name == "benunit":
                tables[table_name].set_index(
                    "benunit_id", inplace=True, drop=False
                )
            elif table_name == "househol":
                tables[table_name].set_index(
                    "household_id", inplace=True, drop=False
                )
        tables["benunit"] = tables["benunit"][
            tables["benunit"].benunit_id.isin(tables["adult"].benunit_id)
        ]
        tables["househol"] = tables["househol"][
            tables["househol"].household_id.isin(tables["adult"].household_id)
        ]

        # Save the data
        self.save_dataset(tables)


RawFRS_2019_20 = RawFRS.from_folder(
    "/Users/nikhil/ukda/frs_2019_20",
    "raw_frs_2019",
    "FRS 2019-20",
    2019,
    new_url="release://policyengine/non-public-microdata/2023-q2-calibration/raw_frs_2019.h5",
)

RawFRS_2018_19 = RawFRS.from_folder(
    "/Users/nikhil/ukda/frs_2018_19",
    "raw_frs_2018",
    "FRS 2018-19",
    2018,
    new_url="release://policyengine/non-public-microdata/2023-q2-calibration/raw_frs_2018.h5",
)

RawFRS_2020_21 = RawFRS.from_folder(
    "/Users/nikhil/ukda/frs_2020_21",
    "raw_frs_2020",
    "FRS 2020-21",
    2020,
    new_url="release://policyengine/non-public-microdata/2023-q2-calibration/raw_frs_2020.h5",
)
