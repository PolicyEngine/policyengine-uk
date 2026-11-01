from policyengine_uk.model_api import *
import numpy as np


class esa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-related ESA tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/118",
        "https://www.legislation.gov.uk/nisr/2008/280/regulation/118",
    )

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        capital = benunit("esa_income_assessable_capital", period)
        mt = ESA.capital
        # ESA Regs 2008 reg 118(2)-(4) (NI: SR 2008/280 reg 118(2)-(4)): for a
        # claimant who lives permanently in prescribed accommodation the lower
        # threshold is £10,000, not £6,000. The capital limit (reg 110) bars
        # the award above the upper limit, so no award turns on tariff income
        # there.
        threshold = where(
            benunit("legacy_prescribed_accommodation_capital_exception", period),
            mt.residential_threshold,
            mt.tariff_income.threshold,
        )
        excess_capital = max_(0, capital - threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
