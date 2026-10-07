from policyengine_uk.model_api import *


class uc_has_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "Has limited capability for work, for Universal Credit"
    documentation = (
        "Whether the claimant has limited capability for work. A claimant "
        "who has it, and does not also have limited capability for "
        "work-related activity, is subject to the work preparation "
        "requirement. An input: the model identifies limited capability for "
        "work-related activity only (uc_limited_capability_for_WRA)."
    )
    reference = "https://www.legislation.gov.uk/ukpga/2012/5/section/21"
    definition_period = YEAR
    default_value = False
