from policyengine_uk.model_api import *


class trading_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the trading allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        trading_allowance = parameters(
            period
        ).gov.hmrc.income_tax.allowances.trading_allowance
        return min_(
            trading_allowance,
            person("self_employment_income", period),
        )
