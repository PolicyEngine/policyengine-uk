from policyengine_uk.model_api import *


class uc_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit tariff income from capital"
    documentation = "Monthly tariff income from capital annualised to the model period."
    definition_period = YEAR
    unit = GBP
    defined_for = "is_uc_eligible"

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        excess_capital = max_(0, capital - p.tariff_income.lower_threshold)
        steps = np.ceil(excess_capital / p.tariff_income.step)
        return steps * p.tariff_income.amount * MONTHS_IN_YEAR
