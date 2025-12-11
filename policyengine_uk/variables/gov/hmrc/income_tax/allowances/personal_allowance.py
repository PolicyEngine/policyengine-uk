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
        p = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = p.amount
        ani = person("adjusted_net_income", period)
        # Per ITA 2007 s.58, deduct grossed-up Gift Aid from ANI
        # when calculating Personal Allowance taper
        gift_aid_grossed_up = person("gift_aid_grossed_up", period)
        ani_for_taper = ani - gift_aid_grossed_up
        excess = max_(0, ani_for_taper - p.maximum_ani)
        reduction = excess * p.reduction_rate
        return max_(0, personal_allowance - reduction)
