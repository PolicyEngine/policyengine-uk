from openfisca_uk.microdata.datasets import *
from pathlib import Path
from openfisca_uk.microdata.utils import VERSION

REPO = Path(__file__).parent


DATASETS = (
    RawFRS,
    FRS,
    SynthFRS,
    RawSPI,
    SPI,
    RawWAS,
    RawLCF,
    FRSEnhanced,
)
