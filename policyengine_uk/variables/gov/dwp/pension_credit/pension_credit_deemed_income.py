from policyengine_uk.model_api import *
import numpy as np


class pension_credit_deemed_income(Variable):
    label = "Pension Credit deemed income from capital"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.income.capital
        capital = benunit("pension_credit_assessable_capital", period)
        excess = max_(0, capital - p.lower_threshold)
        steps = np.ceil(excess / p.tariff_income.step)
        return steps * p.tariff_income.amount * WEEKS_IN_YEAR
