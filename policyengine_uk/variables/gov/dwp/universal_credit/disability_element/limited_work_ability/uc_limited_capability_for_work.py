from policyengine_uk.model_api import *


class uc_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work"
    documentation = (
        "Whether this person has limited capability for work (UC Regs 2013 "
        "reg 39), which the work allowance (reg 22), the reduced minimum age "
        "(reg 8(1)(a)), the partner's exception to the childcare work "
        "condition (reg 32(1)(b)(i)) and the work preparation group (Welfare "
        "Reform Act 2012 s.21(1)(a)) need. Limited capability for work and "
        "work-related activity (uc_limited_capability_for_WRA) includes it, "
        "and otherwise it defaults to is_disabled_for_benefits. An ESA award "
        "without the support component therefore removes limited capability for "
        "work-related activity but not for work. Universal Credit also takes "
        "an ESA determination of limited capability for work (reg 39(1)(a)), "
        "so any ESA award of the person's own would imply it; the model does "
        "not infer that yet, because the work allowance still reads every "
        "member of the benefit unit, not only the claimants."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/39",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/8",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/21",
    )

    def formula(person, period, parameters):
        return person("uc_limited_capability_for_WRA", period) | person(
            "is_disabled_for_benefits", period
        )
