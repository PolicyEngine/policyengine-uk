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
        self, reform: ReformType = (), dataset: type = None, year: int = None
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

        super().__init__(reform=reform, dataset=dataset, year=year)


class IndividualSim(GeneralIndividualSim):
    tax_benefit_system = CountryTaxBenefitSystem
    post_reform = backdate_parameters()
