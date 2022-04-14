from openfisca_uk.data.datasets.frs import (
    FRS,
    RawFRS,
    ExtendedFRS,
    CalibratedFRS,
    EnhancedFRS,
    SynthFRS,
)
from openfisca_uk.data.datasets.was import RawWAS, WAS
from openfisca_uk.data.datasets.lcfs import RawLCFS, LCFS
from openfisca_uk.data.datasets.spi import RawSPI, SPI

DATASETS = [
    RawFRS,
    FRS,
    RawWAS,
    RawLCFS,
    RawSPI,
    SPI,
    ExtendedFRS,
    CalibratedFRS,
    LCFS,
    WAS,
    EnhancedFRS,
    SynthFRS,
]
