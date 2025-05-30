from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA"
    documentation = "Applicable amount for Local Housing Allowance"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        cap = benunit("BRMA_LHA_rate", period)
        return min_(rent, cap)
