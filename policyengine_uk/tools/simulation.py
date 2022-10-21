import logging
from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.data import EnhancedFRS
from policyengine_uk.entities import entities
import numpy as np
import warnings
from policyengine_uk.entities import *
import numpy as np
import warnings
from policyengine_uk.initial_setup import REPO, set_default
from policyengine_uk.reforms.presets.current_date import use_current_parameters
from policyengine_uk.reforms.presets.average_parameters import (
    average_parameters as apply_parameter_averaging,
)
from policyengine_uk.tools.baseline_variables import (
    generate_baseline_variables,
)
from policyengine_uk.tools.parameters import backdate_parameters
from policyengine_core.reforms import Reform
from policyengine_uk.data import DATASETS, SynthFRS
from policyengine_core.simulations import (
    Microsimulation as GeneralMicrosimulation,
    IndividualSim as GeneralIndividualSim,
)
import yaml
from pathlib import Path
import h5py
import pandas as pd
from policyengine_core.parameters.operations import (
    interpolate_parameters,
    uprate_parameters,
    propagate_parameter_metadata,
)
from policyengine_core.model_api import Reform
from policyengine_uk.tools.tax_benefit_uprating import add_tax_benefit_uprating
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
        reform: Reform = (),
        dataset: type = EnhancedFRS,
        year: int = 2022,
        adjust_weights: bool = False,
        average_parameters: bool = False,
        add_baseline_values: bool = True,
        post_reform: Reform = None,
    ):
        if len(dataset.years) == 0:
            logging.warning(
                f"You are trying to run a microsimulation using the dataset: {dataset.label}, but no years of that dataset could be found. Attempting to download it."
            )
            try:
                dataset.download(year)
            except Exception as e:
                logging.warning(
                    f"Encountered an error when attempting to download the {dataset.label} (this is likely because your account could not be authenticated, if it is not a public dataset). Attempting to download the Synthetic FRS."
                )
                try:
                    SynthFRS.download(year)
                    dataset = SynthFRS
                except Exception as e:
                    logging.warning(
                        f"Encountered an error when attempting to download the synthetic FRS dataset: {e}"
                    )
                    raise e
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

        super().__init__(reform=reform, dataset=dataset, dataset_year=year)

        if (
            ("frs_enhanced" in dataset.name)
            and adjust_weights
            and year >= 2022
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

        if average_parameters:
            self.simulation.tax_benefit_system.parameters = (
                apply_parameter_averaging(
                    self.simulation.tax_benefit_system.parameters
                )
            )


class IndividualSim(GeneralIndividualSim):
    tax_benefit_system = CountryTaxBenefitSystem
    post_reform = backdate_parameters()

    default_roles = dict(
        benunit="adult",
        household="adult",
    )
    required_entities = [
        "benunit",
        "household",
    ]
