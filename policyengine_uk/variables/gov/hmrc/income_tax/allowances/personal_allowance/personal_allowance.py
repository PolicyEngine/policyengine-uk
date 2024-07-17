from policyengine_uk.model_api import *


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Individual's maximum Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        params = parameters(period)
        contrib = params.gov.contrib
        PA = params.gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = PA.amount
        sp_age = person("is_SP_age", period)
        pensioner_pa = contrib.conservatives.pensioner_personal_allowance
        if pensioner_pa != personal_allowance:
            personal_allowance = where(
                sp_age, pensioner_pa, personal_allowance
            )
        ANI = person("adjusted_net_income", period)
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        return max_(0, personal_allowance - reduction)