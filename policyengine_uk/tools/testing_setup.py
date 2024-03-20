from policyengine_uk.data import EnhancedFRS, SynthFRS
from policyengine_uk.initial_setup import set_default

EnhancedFRS.download(2022)
SynthFRS.download(2022)
set_default(EnhancedFRS)
