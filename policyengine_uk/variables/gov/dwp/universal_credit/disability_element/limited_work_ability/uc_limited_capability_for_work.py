from policyengine_uk.model_api import *


class uc_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work"
    documentation = (
        "Whether this person has limited capability for work (UC Regs 2013 "
        "reg 39), which the work allowance (reg 22) and the reduced minimum "
        "age (reg 8(1)(a)) need. Limited capability for work and work-related "
        "activity includes it (uc_limited_capability_for_WRA). So does an ESA "
        "award of the person's own (has_own_esa_award), however it is made "
        "up: Universal Credit takes an ESA determination of limited capability "
        "for work (reg 39(1)(a)). Someone still in the ESA assessment phase "
        "has not yet been assessed, but the model counts them too."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/39",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/8",
    )

    def formula(person, period, parameters):
        return person("uc_limited_capability_for_WRA", period) | person(
            "has_own_esa_award", period
        )
