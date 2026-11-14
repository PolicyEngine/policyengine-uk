from policyengine_uk.model_api import *
import numpy as np


class income_support_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support tariff income from capital"
    documentation = (
        "Weekly tariff income from capital under IS Regs 1987 reg 53 (NI: SR "
        "1987/459 reg 53), over 52 weeks: £1 for each complete £250 of capital "
        "above the lower threshold and £1 for any part left over. DWP and "
        "Northern Ireland's Department for Communities use a lower threshold of "
        "£6,000, or £10,000 where "
        "legacy_prescribed_accommodation_capital_exception is true, and stop "
        "counting capital at £16,000. Above that amount this variable continues "
        "the same arithmetic, which the regulation doesn't prescribe. "
        "income_support_applicable_income adds this variable in full, and the "
        "model pays no IS through income_support_entitlement while "
        "income_support_eligible finds capital above the configured capital limit "
        "(reg 45, £16,000), so while the limit stays at £16,000 the arithmetic "
        "above it changes no award. Under a reform that raises the limit, the "
        "model subtracts the continued tariff from awards."
    )
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
        # Under reg 53(1)-(1C), DWP and the Department for Communities use a
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
