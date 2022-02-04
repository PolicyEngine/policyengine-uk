import logging
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_uk.entities import entities
import numpy as np
import warnings
from openfisca_uk.entities import *
import numpy as np
import warnings
from openfisca_uk.initial_setup import set_default
from openfisca_uk.tools.parameters import backdate_parameters
from openfisca_tools import ReformType
from openfisca_uk_data import DATASETS, SynthFRS
from openfisca_tools.microsimulation import (
    Microsimulation as GeneralMicrosimulation,
)
from openfisca_tools.hypothetical import IndividualSim as GeneralIndividualSim
import yaml
from pathlib import Path
import h5py
import pandas as pd


with open(Path(__file__).parent / "datasets.yml") as f:
    datasets = yaml.safe_load(f)
    DEFAULT_DATASET = list(
        filter(lambda ds: ds.name == datasets["default"], DATASETS)
    )[0]


warnings.filterwarnings("ignore")

np.random.seed(0)


class Microsimulation(GeneralMicrosimulation):
    tax_benefit_system = CountryTaxBenefitSystem
    entities = entities
    default_dataset = DEFAULT_DATASET
    post_reform = backdate_parameters()

    def __init__(
        self,
        reform: ReformType = (),
        dataset: type = None,
        year: int = None,
        duplicate_records: int = 2,
        adjust_weights: bool = True,
    ):
        if dataset is None:
            dataset = self.default_dataset
        else:
            dataset = dataset
        if year is None:
            year = self.default_year or max(dataset.years)
        else:
            year = year

        # Check if dataset is available

        if year not in dataset.years:
            download = input(
                f"\nYear {year} not available in dataset {dataset.name}: \n\t* Download the dataset [y]\n\t* Use the synthetic FRS (and set default) [n]\n\nChoice: "
            )
            if download == "y":
                dataset.download(year)
            else:
                set_default(SynthFRS)
                dataset = SynthFRS
                if year not in dataset.years:
                    logging.info(
                        f"Year {year} synthetic FRS not stored, downloading..."
                    )
                    dataset.download(year)

        if (dataset.name == "frs_enhanced") and (duplicate_records > 1):
            data = dataset.load(year)

            def duplicate(key, values):
                if "_id" in key:
                    return np.concatenate(
                        tuple([values] * duplicate_records)
                    ) * 10 + np.repeat(
                        list(range(1, 1 + duplicate_records)), len(values)
                    )
                elif "_weight" in key:
                    return (
                        np.concatenate(tuple([values] * duplicate_records))
                        / duplicate_records
                    )
                else:
                    return np.concatenate(tuple([values] * duplicate_records))

            class ProxyDataObject(dict):
                def close(self):
                    return None

            df = ProxyDataObject(
                {
                    key: duplicate(key, dataset.load(year, key))
                    for key in data.keys()
                }
            )

            df["claims_legacy_benefits"] = np.repeat(
                [True, False], len(df["benunit_id"]) / 2
            )

            class ProxyDataset:
                def load(year):
                    return df

                def close():
                    return None

                years = dataset.years
                name = "frs_enhanced_duplicated"

            dataset = ProxyDataset

        super().__init__(reform=reform, dataset=dataset, year=year)

        if (
            ("frs_enhanced" in dataset.name)
            and adjust_weights
            and year >= 2019
            and (duplicate_records > 1)
        ):
            weight_file = (
                Path(__file__).parent.parent / "calibration" / "frs_weights.h5"
            )
            if not weight_file.exists():
                raise FileNotFoundError("Weight adjustment file not found.")
            with h5py.File(weight_file, "r") as f:
                for year in f.keys():
                    self.simulation.set_input(
                        "household_weight", year, np.array(f[year])
                    )

                    self.simulation.set_input(
                        "person_weight",
                        year,
                        self.calc(
                            "household_weight", period=year, map_to="person"
                        ).values,
                    )


class IndividualSim(GeneralIndividualSim):
    tax_benefit_system = CountryTaxBenefitSystem
    post_reform = backdate_parameters()
