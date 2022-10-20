from openfisca_uk.data import EnhancedFRS, SynthFRS
from openfisca_uk.initial_setup import set_default

EnhancedFRS.download(2022)
SynthFRS.download(2022)
set_default(EnhancedFRS)
