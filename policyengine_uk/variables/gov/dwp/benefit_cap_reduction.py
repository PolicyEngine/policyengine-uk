from policyengine_uk.model_api import *


class benefit_cap_reduction(Variable):
    label = "benefit cap reduction"
    documentation = (
        "The reduction the benefit cap makes to the family's Universal Credit "
        "(uc_benefit_cap_reduction, UC Regs 2013 reg. 81) or Housing Benefit "
        "(housing_benefit_benefit_cap_reduction, HB Regs 2006 reg. 75D). Each "
        "scheme applies its own cap; the model pays a family one or the "
        "other, never both. A family with neither award has no reduction. The "
        "Universal Credit part is the reg. 81 amount, which can exceed the "
        "award; the Housing Benefit part never exceeds the award less the "
        "reg. 75 minimum."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["uc_benefit_cap_reduction", "housing_benefit_benefit_cap_reduction"]
