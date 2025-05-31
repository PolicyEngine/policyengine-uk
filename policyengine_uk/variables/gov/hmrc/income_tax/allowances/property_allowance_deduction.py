from policyengine_uk.model_api import *


class property_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the property allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        return min_(
            person("property_income", period),
            person("property_allowance", period),
        )
