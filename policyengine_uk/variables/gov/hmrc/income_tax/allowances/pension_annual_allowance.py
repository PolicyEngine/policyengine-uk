from policyengine_uk.model_api import *


class pension_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Annual Allowance for pension contributions"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        allowance = parameters(
            period
        ).gov.hmrc.income_tax.allowances.annual_allowance
        ANI = person("adjusted_net_income", period)
        reduction = max_(0, ANI - allowance.taper) * allowance.reduction_rate
        return max_(allowance.minimum, allowance.default - reduction)
