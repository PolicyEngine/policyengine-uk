from policyengine_uk.model_api import *
import numpy as np


class esa_income_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income-related ESA tariff income from capital"
    documentation = (
        "Weekly tariff income from capital under ESA Regs 2008 reg 118 (NI: SR "
        "2008/280 reg 118), over 52 weeks: £1 for each complete £250 of capital "
        "above the lower threshold and £1 for any part left over. DWP and "
        "Northern Ireland's Department for Communities use a lower threshold of "
        "£6,000, or £10,000 where "
        "legacy_prescribed_accommodation_capital_exception is true, and stop "
        "counting capital at £16,000. Above that amount this variable continues "
        "the same arithmetic, which the regulation doesn't prescribe. The model "
        "pays no ESA through esa_income_eligible or the own-right claims in "
        "esa_income while capital exceeds the configured capital limit (reg 110, "
        "£16,000), so while the limit stays at £16,000 the arithmetic above it "
        "changes no award. Under a reform that raises the limit, the model "
        "subtracts the continued tariff from awards."
    )
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
        # Under reg 118(1)-(4), DWP and the Department for Communities use a
        # lower threshold of £6,000, or £10,000 for a claimant who lives
        # permanently in prescribed accommodation. Each branch subtracts its
        # own scalar threshold, so both keep the stored capital's float32
        # precision.
        ordinary_excess = max_(0, capital - mt.tariff_income.threshold)
        residential_excess = max_(0, capital - mt.residential_threshold)
        excess_capital = where(
            benunit("legacy_prescribed_accommodation_capital_exception", period),
            residential_excess,
            ordinary_excess,
        )
        tariff_units = np.ceil(excess_capital / mt.tariff_income.step)
        return tariff_units * mt.tariff_income.amount * WEEKS_IN_YEAR
