from policyengine_uk.model_api import *


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 35, s. 58",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/35",
        ),
        dict(
            title="Income Tax Act 2007 s. 55B(6)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
    ]

    def formula(person, period, parameters):
        params = parameters(period)
        PA = params.gov.hmrc.income_tax.allowances.personal_allowance
        personal_allowance = PA.amount
        ANI = person("adjusted_net_income", period)
        # adjusted_net_income includes the s.58 Gift Aid and pension relief.
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        allowance = max_(0, np.ceil(personal_allowance - reduction))
        # A Marriage Allowance election cuts the electing spouse's allowance
        # by the transferable amount (s. 55B(6)).
        relinquished = person("marriage_allowance_relinquished", period)
        return max_(0, allowance - relinquished)
