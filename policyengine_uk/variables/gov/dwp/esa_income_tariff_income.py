from policyengine_uk.model_api import *
import numpy as np


class esa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-related ESA tariff income from capital"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        capital = benunit("esa_income_assessable_capital", period)
        mt = ESA.capital
        excess_capital = max_(0, capital - mt.lower_threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
