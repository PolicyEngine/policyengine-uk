from openfisca_uk_data import FRS, UKMODOutput, FRSEnhanced
from openfisca_uk.initial_setup import set_default

FRS.download(2018)
FRS.download(2019)
FRSEnhanced.download(2019)
UKMODOutput.download(2018)
set_default(FRS)
