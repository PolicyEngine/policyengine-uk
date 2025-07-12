from policyengine_uk.model_api import *
import datetime
import numpy as np


class inflation_adjustment(Variable):
    label = (
        f"inflation multiplier to get {datetime.datetime.now().year} prices"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        cpi = (
            parameters.gov.economic_assumptions.indices.obr.consumer_price_index
        )
        current_period_cpi = cpi(period)
        now_cpi = cpi(datetime.datetime.now().strftime("%Y-01-01"))
        return now_cpi / current_period_cpi
