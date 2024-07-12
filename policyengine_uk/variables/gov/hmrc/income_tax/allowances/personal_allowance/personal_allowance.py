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
        contrib = params.gov.contrib
        pa = params.gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = pa.amount
        sp_age = person("is_SP_age", period)
        pensioner_pa = contrib.conservatives.pensioner_personal_allowance
        if pensioner_pa != personal_allowance:
            personal_allowance = where(
                sp_age, pensioner_pa, personal_allowance
            )
        ani = person("adjusted_net_income", period)
        excess = max_(0, ani - pa.maximum_ANI)
        reduction = excess * pa.reduction_rate
        return max_(0, personal_allowance - reduction)

class personal_allowance_max_value(Variable):
    value_type = float
    entity = Person
    label = "Maximum allowed Personal Allowance for an individual for the year, given their adjusted net income and age"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        params = parameters(period)
        contrib = params.gov.contrib
        pa = params.gov.hmrc.income_tax.allowances.personal_allowance
        pa_amount = pa.amount
        sp_age = person("is_SP_age", period)
        pensioner_pa = contrib.conservatives.pensioner_personal_allowance
        if pensioner_pa != pa_amount:
            pa_amount = where(
                sp_age, pensioner_pa, pa_amount
            )
        ani = person("adjusted_net_income", period)
        excess = max_(0, ani - pa.maximum_ANI)
        reduction = excess * pa.reduction_rate
        return max_(0, pa_amount - reduction)