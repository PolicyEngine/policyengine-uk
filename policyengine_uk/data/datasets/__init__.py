from policyengine_uk.data.datasets.frs import (
    FRS,
    RawFRS,
    ExtendedFRS,
    CalibratedFRS,
    EnhancedFRS,
    SynthFRS,
)
from policyengine_uk.data.datasets.was import RawWAS, WAS
from policyengine_uk.data.datasets.lcfs import RawLCFS, LCFS
from policyengine_uk.data.datasets.spi import RawSPI, SPI

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
