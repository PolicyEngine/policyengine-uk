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
        "excess (UC Regs 2013 reg. 81). Housing Benefit counts as nil in the "
        "welfare benefits (reg. 80(2A)). The cap reduces an award of Universal "
        "Credit (reg. 78(1)), so there is no reduction without one. This is the "
        "amount reg. 81 takes off, which can exceed the award before the cap; "
        "the award goes no lower than nil, so the amount actually removed, "
        "uc_benefit_cap_reduction_after_floor, is the smaller of the two, and "
        "that is the Universal Credit part of benefit_cap_reduction."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/81",
    )

    def formula(benunit, period, parameters):
        # Reg 80(2A): where the welfare benefit is Housing Benefit, "the
        # amount to be used is nil". benefit_cap_welfare_benefits counts it
        # for the Housing Benefit cap (HB Regs 2006 reg 75C(2)(b)), so it is
        # taken out here; a family paid both is capped on its other benefits.
        welfare_benefits = benunit("benefit_cap_welfare_benefits", period) - benunit(
            "housing_benefit_pre_benefit_cap", period
        )
        excess = max_(welfare_benefits - benunit("uc_benefit_cap", period), 0)
        reduction = max_(excess - benunit("uc_childcare_element", period), 0)
        has_award = benunit("universal_credit_pre_benefit_cap", period) > 0
        return where(has_award, reduction, 0)
