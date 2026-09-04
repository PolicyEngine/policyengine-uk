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


class uc_LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA under Universal Credit"
    documentation = "Rent covered by the Local Housing Allowance for Universal Credit"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        """Universal Credit applies a monthly national maximum.

        The monthly figures in Schedule 1 to the Rent Officers (Universal
        Credit Functions) Order 2013 are set independently of the weekly
        Housing Benefit maxima and are slightly higher, so annualising the
        weekly figure would impose a ceiling below the statutory one.
        """
        rent = benunit("benunit_rent", period)

        if period.start.year < MONTHLY_MAXIMUM_FIRST_YEAR:
            # Before the monthly series begins, fall back to the weekly
            # Housing Benefit rate, as the model did previously.
            return min_(rent, benunit("BRMA_LHA_rate", period))

        rate = benunit("uncapped_BRMA_LHA_rate", period)
        maximum = category_maximum(benunit, period, "maximum_monthly")
        return min_(rent, min_(rate, maximum * MONTHS_IN_YEAR))
