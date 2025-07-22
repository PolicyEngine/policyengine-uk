from policyengine_uk.model_api import *


class property_allowance(Variable):
    value_type = float
    entity = Person
    label = "Property Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783BF"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.property_allowance
