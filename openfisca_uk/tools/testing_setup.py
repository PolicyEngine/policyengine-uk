from openfisca_uk_data import UKMODOutput, FRSEnhanced
from openfisca_uk.initial_setup import set_default

FRSEnhanced.download(2018)
FRSEnhanced.download(2019)
UKMODOutput.download(2018)
set_default(FRSEnhanced)
