from policyengine_uk.model_api import *


class council_tax_reduction_working_age_universal_credit_award(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit award for working-age council tax reduction"
    documentation = (
        "The Universal Credit award after any benefit cap reduction and before "
        "deductions from payment, such as advance or third-party deductions. "
        "The benefit cap reduces the award (UC Regs 2013 reg 81), while "
        "deductions from payment do not."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
    )

    def formula(benunit, period, parameters):
        award_before_cap = benunit("universal_credit_pre_benefit_cap", period)
        cap_reduction = benunit("benefit_cap_reduction", period)
        return max_(0, award_before_cap - cap_reduction)
