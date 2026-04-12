from policyengine_uk.model_api import *
import numpy as np


class jsa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-based JSA tariff income from capital"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA.income
        capital = benunit("jsa_income_assessable_capital", period)
        mt = JSA.capital
        excess_capital = max_(0, capital - mt.tariff_income.lower_threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
