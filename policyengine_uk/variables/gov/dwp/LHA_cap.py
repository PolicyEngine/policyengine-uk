from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum rent (LHA)"
    documentation = (
        "The Housing Benefit maximum rent (LHA): the Local Housing Allowance "
        "rate for the benefit unit, or its rent where that is lower (SI "
        "2006/213 and 2006/214 reg 13D(5): where the LHA exceeds the cap "
        "rent, the maximum rent (LHA) is the cap rent)."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        cap = benunit("BRMA_LHA_rate", period)
        return min_(rent, cap)
