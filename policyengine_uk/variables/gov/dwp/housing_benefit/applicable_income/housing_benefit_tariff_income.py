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
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        lower_threshold = where(
            any_over_SP_age,
            p.pension_age.lower_threshold,
            p.working_age.lower_threshold,
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
        excess_capital = max_(0, capital - lower_threshold)
        steps = np.ceil(excess_capital / step)
        return steps * amount * WEEKS_IN_YEAR
