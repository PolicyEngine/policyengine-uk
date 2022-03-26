import logging
from openfisca_uk import CountryTaxBenefitSystem
from openfisca_uk.entities import entities
import numpy as np
import warnings
from openfisca_uk.entities import *
import numpy as np
import warnings
from openfisca_uk.initial_setup import REPO, set_default
from openfisca_uk.reforms.presets.current_date import use_current_parameters
from openfisca_uk.reforms.presets.average_parameters import (
    average_parameters as apply_parameter_averaging,
)
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
from openfisca_tools.parameters import (
    interpolate_parameters,
    uprate_parameters,
    propagate_parameter_metadata,
)
from openfisca_core.model_api import Reform
from openfisca_uk.tools.tax_benefit_uprating import add_tax_benefit_uprating
from functools import reduce


with open(Path(__file__).parent / "datasets.yml") as f:
    datasets = yaml.safe_load(f)
    DEFAULT_DATASET = list(
        filter(lambda ds: ds.name == datasets["default"], DATASETS)
    )[0]


warnings.filterwarnings("ignore")

np.random.seed(0)


def chain(*funcs):
    def f(parameters):
        for func in funcs:
            args = func(parameters)
        return args

    return f


class prepare_parameters(Reform):
    def apply(self):
        self.modify_parameters(
            chain(
                add_tax_benefit_uprating,
                propagate_parameter_metadata,
                interpolate_parameters,
                uprate_parameters,
            )
        )


class Microsimulation(GeneralMicrosimulation):
    tax_benefit_system = CountryTaxBenefitSystem
    entities = entities
    default_dataset = DEFAULT_DATASET
    post_reform = prepare_parameters, backdate_parameters()

    def __init__(
        self,
        reform: ReformType = (),
        dataset: type = None,
        year: int = None,
        duplicate_records: bool = False,
        adjust_weights: bool = True,
        average_parameters: bool = False,
        add_baseline_benefits: bool = True,
        post_reform: ReformType = None,
    ):
        if adjust_weights:
            duplicate_records = True
        if dataset is None:
            dataset = self.default_dataset
        else:
            dataset = dataset
        if post_reform is not None:
            self.post_reform = post_reform
        if year is None:
            year = self.default_year or max(dataset.years)
        else:
            year = year
        year = int(year)

        # Check if dataset is available

        if year not in dataset.years:
            print(
                f"Dataset {dataset.name} does not contain year {year} (but it does contain {dataset.years}"
            )
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

        if (dataset.name == "frs_enhanced") and duplicate_records:
            data = dataset.load(year)
            num_duplications = 2

            def duplicate(key, values):
                if "_id" in key:
                    return np.concatenate(
                        tuple([values] * num_duplications)
                    ) * 10 + np.repeat(
                        list(range(1, 1 + num_duplications)), len(values)
                    )
                elif "_weight" in key:
                    return (
                        np.concatenate(tuple([values] * num_duplications))
                        / duplicate_records
                    )
                else:
                    return np.concatenate(tuple([values] * num_duplications))

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

                    self.simulation.set_input(
                        "benunit_weight",
                        year,
                        self.calc(
                            "household_weight", period=year, map_to="benunit"
                        ).values,
                    )

            # Add baseline benefits

        if add_baseline_benefits:
            filepath = REPO / "data" / "baseline_variables.h5"
            if filepath.exists():
                with h5py.File(filepath, "r") as f:
                    for year in list(range(2019, 2026)):
                        for benefit in [
                            "universal_credit",
                            "pension_credit",
                            "working_tax_credit",
                            "child_tax_credit",
                            "income_support",
                            "housing_benefit",
                        ]:
                            self.simulation.set_input(
                                f"baseline_has_{benefit}",
                                year,
                                np.array(f[f"{year}/{benefit}"]) > 0,
                            )
                        for variable in ["hbai_excluded_income"]:
                            self.simulation.set_input(
                                f"baseline_{variable}",
                                year,
                                np.array(f[f"{year}/{variable}"]),
                            )

        if average_parameters:
            self.simulation.tax_benefit_system.parameters = (
                apply_parameter_averaging(
                    self.simulation.tax_benefit_system.parameters
                )
            )


class IndividualSim(GeneralIndividualSim):
    tax_benefit_system = CountryTaxBenefitSystem
    post_reform = backdate_parameters()
