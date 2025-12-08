from policyengine_uk.model_api import *


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 35, s. 58",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/35",
    )

    def formula(person, period, parameters):
        params = parameters(period)
        PA = params.gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = PA.amount
        ANI = person("adjusted_net_income", period)
        # Per ITA 2007 s.58, deduct grossed-up Gift Aid from ANI
        # when calculating Personal Allowance taper
        gift_aid_grossed_up = person("gift_aid_grossed_up", period)
        ANI_for_taper = ANI - gift_aid_grossed_up
        excess = max_(0, ANI_for_taper - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        return max_(0, personal_allowance - reduction)
