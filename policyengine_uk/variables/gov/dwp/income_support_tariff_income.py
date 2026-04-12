from policyengine_uk.model_api import *
import numpy as np


class income_support_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support tariff income from capital"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        capital = benunit("income_support_assessable_capital", period)
        mt = IS.means_test.capital
        excess_capital = max_(0, capital - mt.lower_threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
