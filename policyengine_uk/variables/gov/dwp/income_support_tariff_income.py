from policyengine_uk.model_api import *
import numpy as np


class income_support_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/53",
        "https://www.legislation.gov.uk/nisr/1996/93/regulation/11/made",
    )

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        capital = benunit("income_support_assessable_capital", period)
        mt = IS.means_test.capital
        # IS Regs 1987 reg 53(1A)-(1C) (NI: the same regulation of SR
        # 1987/459): for a claimant who lives permanently in prescribed
        # accommodation the lower threshold is £10,000, not £6,000. The
        # capital limit (reg 45) bars the award above the upper limit, so no
        # award turns on tariff income there.
        threshold = where(
            benunit("legacy_prescribed_accommodation_capital_exception", period),
            mt.residential_threshold,
            mt.tariff_income.threshold,
        )
        excess_capital = max_(0, capital - threshold)
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
