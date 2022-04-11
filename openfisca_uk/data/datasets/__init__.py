from openfisca_uk.data.datasets.frs import FRS, RawFRS, ExtendedFRS, CalibratedFRS
from openfisca_uk.data.datasets.was import RawWAS
from openfisca_uk.data.datasets.lcfs import RawLCFS
from openfisca_uk.data.datasets.spi import RawSPI, SPI

DATASETS = [RawFRS, FRS, RawWAS, RawLCFS, RawSPI, SPI, ExtendedFRS, CalibratedFRS]