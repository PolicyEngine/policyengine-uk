from policyengine_uk.model_api import *
import numpy as np


class jsa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-based JSA tariff income from capital"
    documentation = (
        "Weekly tariff income from capital under JSA Regs 1996 reg 116 (NI: SR "
        "1996/198 reg 116), over 52 weeks: £1 for each complete £250 of "
        "capital above the lower threshold and £1 for any part left over. The "
        "lower threshold is £6,000, or £10,000 where "
        "legacy_prescribed_accommodation_capital_exception is true. The "
        "regulation counts capital only up to £16,000. Above that amount this "
        "variable continues the same arithmetic, which the regulation does "
        "not prescribe. jsa_income_eligible and the own-right claims in "
        "jsa_income pay nothing while capital exceeds the configured capital "
        "limit (reg 107, £16,000), so at that limit no award depends on the "
        "continuation. A reform that raises the limit lets awards read it."
    )
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
        # Reg 116(1)-(1C): the lower threshold is £6,000, or £10,000 for a
        # claimant who lives permanently in prescribed accommodation. Each
        # branch subtracts its own scalar threshold, so both keep the stored
        # capital's float32 precision.
        ordinary_excess = max_(0, capital - mt.tariff_income.threshold)
        residential_excess = max_(0, capital - mt.residential_threshold)
        excess_capital = where(
            benunit("legacy_prescribed_accommodation_capital_exception", period),
            residential_excess,
            ordinary_excess,
        )
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
