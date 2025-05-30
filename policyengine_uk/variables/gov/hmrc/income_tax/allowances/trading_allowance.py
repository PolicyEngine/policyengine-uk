from policyengine_uk.model_api import *


class trading_allowance(Variable):
    value_type = float
    entity = Person
    label = "Trading Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.trading_allowance
