from policyengine_uk.model_api import *


class married_couples_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction from Married Couples' allowance for the year"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.income_tax.allowances.married_couples_allowance.deduction_rate
        return person("married_couples_allowance", period) * rate
