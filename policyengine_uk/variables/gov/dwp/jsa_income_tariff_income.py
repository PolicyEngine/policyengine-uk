from policyengine_uk.model_api import *
import numpy as np


class jsa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-based JSA tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/116",
        "https://www.legislation.gov.uk/nisr/1996/356/regulation/10/made",
    )

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA.income
        capital = benunit("jsa_income_assessable_capital", period)
        mt = JSA.capital
        # JSA Regs 1996 reg 116(1A)-(1C) (NI: the same regulation of SR
        # 1996/198): for a claimant who lives permanently in prescribed
        # accommodation the lower threshold is £10,000, not £6,000. The
        # capital limit (reg 107) bars the award above the upper limit, so no
        # award turns on tariff income there.
        threshold = where(
            benunit("legacy_prescribed_accommodation_capital_exception", period),
            mt.residential_threshold,
            mt.tariff_income.threshold,
        )
        excess_capital = max_(0, capital - threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
