from policyengine_uk.model_api import *


class uc_benefit_cap_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit benefit cap reduction"
    documentation = (
        "The reduction the benefit cap makes to a Universal Credit award: the "
        "excess of the welfare benefits of the single person or couple over "
        "the Universal Credit cap, minus the childcare costs element, and "
        "nothing where the childcare costs element is greater than the "
        "excess (UC Regs 2013 reg. 81). The cap reduces an award of Universal "
        "Credit (reg. 78(1)), so there is no reduction without one. This is the "
        "amount reg. 81 takes off, which can exceed the award before the cap; "
        "universal_credit floors the award at nil, so the amount actually "
        "removed is the smaller of the two."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/81",
    )

    def formula(benunit, period, parameters):
        excess = max_(
            benunit("benefit_cap_welfare_benefits", period)
            - benunit("uc_benefit_cap", period),
            0,
        )
        reduction = max_(excess - benunit("uc_childcare_element", period), 0)
        has_award = benunit("universal_credit_pre_benefit_cap", period) > 0
        return where(has_award, reduction, 0)
