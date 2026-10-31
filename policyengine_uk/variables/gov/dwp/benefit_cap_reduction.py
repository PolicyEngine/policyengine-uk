from policyengine_uk.model_api import *


class benefit_cap_reduction(Variable):
    label = "benefit cap reduction"
    documentation = (
        "The reduction the benefit cap actually makes to the family's "
        "Universal Credit (uc_benefit_cap_reduction_after_floor) or Housing "
        "Benefit (housing_benefit_benefit_cap_reduction, HB Regs 2006 reg. "
        "75D). Each scheme applies its own cap. A family receiving both is "
        "capped only through Universal Credit: Universal Credit counts its "
        "Housing Benefit as nil (UC Regs 2013 reg. 80(2A)) and the Housing "
        "Benefit cap does not apply to a claimant receiving Universal Credit "
        "(HB Regs 2006 reg. 75F(1)(g)). A family with neither award has no "
        "reduction. Neither part exceeds the award it reduces: the Universal "
        "Credit part is the reg. 81 amount (uc_benefit_cap_reduction) up to "
        "the award: an award cannot be reduced below nil, and WRA 2012 "
        "s. 96(2) allows a reduction smaller than the excess ('an amount up "
        "to or equalling the excess'). It is less "
        "where a protected floor reform binds; the Housing Benefit part "
        "leaves the reg. 75 minimum. This is the amount DWP's benefit cap "
        "statistics measure: for Universal Credit, the amount the payment "
        "has been capped by in the statement data; for Housing Benefit, the "
        "weekly amount the Housing Benefit has been capped by in the Single "
        "Housing Benefit Extract."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
        "https://www.gov.uk/government/publications/benefit-cap-statistics-background-information-and-methodology",
    )
    adds = [
        "uc_benefit_cap_reduction_after_floor",
        "housing_benefit_benefit_cap_reduction",
    ]
