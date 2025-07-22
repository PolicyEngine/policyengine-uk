from policyengine_uk.model_api import *


class dividend_allowance(Variable):
    value_type = float
    entity = Person
    label = "Dividend allowance for the person"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13A"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.dividend_allowance
