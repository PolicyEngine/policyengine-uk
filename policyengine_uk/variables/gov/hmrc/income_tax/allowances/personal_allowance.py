from policyengine_uk.model_api import *


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = p.amount
        ani = person("adjusted_net_income", period)
        excess = max_(0, ani - p.maximum_ani)
        reduction = excess * p.reduction_rate
        return max_(0, personal_allowance - reduction)
