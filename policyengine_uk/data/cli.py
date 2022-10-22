from policyengine_core.data import openfisca_data_cli
from policyengine_uk.data.datasets import DATASETS


def cli():
    openfisca_data_cli(DATASETS)
