from policyengine_uk.model_api import *


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        params = parameters(period)
        PA = params.gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = PA.amount
        ANI = person("adjusted_net_income", period)
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        return max_(0, personal_allowance - reduction)
