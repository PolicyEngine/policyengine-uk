from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import (
    category_maximum,
    MONTHS_IN_YEAR,
    MONTHLY_MAXIMUM_FIRST_YEAR,
)

warnings.filterwarnings("ignore")


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate"
    documentation = "Local Housing Allowance rate, capped at the national maximum"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        """The published Housing Benefit rate.

        Rates are the lower of the Broad Rental Market Area percentile and the
        weekly national maximum for the category (Rent Officers (Housing
        Benefit Functions) Order 1997, Schedule 3B). Universal Credit has its
        own monthly maximum: see ``uc_LHA_cap``.
        """
        rate = benunit("uncapped_BRMA_LHA_rate", period)
        maximum = category_maximum(benunit, period, "maximum")
        return min_(rate, maximum * 52)
