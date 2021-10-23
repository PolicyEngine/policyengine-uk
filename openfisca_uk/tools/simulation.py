from openfisca_uk import CountryTaxBenefitSystem
from openfisca_uk.entities import entities
import numpy as np
import warnings
from openfisca_uk.entities import *
import numpy as np
import warnings
from openfisca_uk.tools.parameters import backdate_parameters
from openfisca_uk_data import DATASETS
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


class IndividualSim(GeneralIndividualSim):
    tax_benefit_system = CountryTaxBenefitSystem
    post_reform = backdate_parameters()
