from openfisca_uk.microdata import (
    RawFRS,
    RawWAS,
    FRS,
    FRSEnhanced,
)
from openfisca_uk.microdata.datasets.lcf.raw_lcf import RawLCF
import logging

logging.basicConfig(level=logging.INFO)

logging.info("Downloading WAS (2016)")
RawWAS.download(2016)
logging.info("Downloading WAS (2019)")
RawLCF.download(2019)

for year in (2018, 2019):
    logging.info(f"Downloading raw FRS ({year})")
    RawFRS.download(year)
    logging.info(f"Generating FRS ({year})")
    FRS.generate(year)
    logging.info(f"Uploading FRS ({year})")
    FRS.upload(year)

logging.info(f"Generating enhanced FRS (2019)")
FRSEnhanced.generate(2019)
logging.info(f"Uploading enhanced FRS (2019)")
FRSEnhanced.upload(2019)
