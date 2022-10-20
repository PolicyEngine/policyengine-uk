from openfisca_tools.data import openfisca_data_cli
from openfisca_uk.data.datasets import DATASETS


def cli():
    openfisca_data_cli(DATASETS)
