from policyengine_uk.model_api import *


class housing_benefit_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit tariff income from capital"
    documentation = "Weekly Housing Benefit tariff income from capital annualised to the model period."
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        capital = benunit("housing_benefit_assessable_capital", period)
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        # Guarantee Credit passport: SI 2006/214 reg 26 (NI: SR 2006/406
        # reg 24) disregards the whole of the capital and income of a
        # claimant "in receipt, or whose partner is in receipt, of a
        # guarantee credit". By reg 2(5) (NI: reg 2(5)), that includes a
        # person who would be in receipt but for SPC Regs 2002 reg 13 (NI:
        # SPC Regs (NI) 2003 reg 13), the small-amounts rule, which
        # PolicyEngine does not model.
        passported = any_over_SP_age & benunit("in_receipt_of_guarantee_credit", period)
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        threshold = where(
            any_over_SP_age,
            p.pension_age.tariff_income.threshold,
            p.working_age.tariff_income.threshold,
        )
        step = where(
            any_over_SP_age,
            p.pension_age.tariff_income.step,
            p.working_age.tariff_income.step,
        )
        amount = where(
            any_over_SP_age,
            p.pension_age.tariff_income.amount,
            p.working_age.tariff_income.amount,
        )
        excess_capital = max_(0, capital - threshold)
        steps = np.ceil(excess_capital / step)
        tariff_income = steps * amount * WEEKS_IN_YEAR
        # Redundant with the zero assessable capital of a passported
        # family, but kept for parallelism with reg 26's "capital and
        # income".
        return where(passported, 0, tariff_income)
