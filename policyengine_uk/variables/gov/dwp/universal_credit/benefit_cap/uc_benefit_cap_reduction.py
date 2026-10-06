from policyengine_uk.model_api import *


class uc_benefit_cap_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit benefit cap reduction"
    documentation = (
        "The amount the benefit cap removes from a Universal Credit award: "
        "the reg. 81 reduction (uc_benefit_cap_reduction_before_award_limit), "
        "up to the award before the cap, which the reduction can take to nil "
        "but not below (UC Regs 2013 reg. 81). Deductions from the award come "
        "after the cap (UC etc. (Claims and Payments) Regs 2013 Sch. 6), so "
        "under current law universal_credit is the award before the cap less "
        "this amount and uc_deductions. A protected floor reform limits this "
        "amount and deductions together in universal_credit; this variable is "
        "the reduction before that limit."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/81",
    )

    def formula(benunit, period, parameters):
        reduction = benunit("uc_benefit_cap_reduction_before_award_limit", period)
        award = max_(benunit("universal_credit_pre_benefit_cap", period), 0)
        return min_(reduction, award)
