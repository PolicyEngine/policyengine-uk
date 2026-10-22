from policyengine_uk.model_api import *


class receives_uc_with_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "receives Universal Credit with limited capability for work"
    documentation = (
        "Whether this person has limited capability for work (Universal "
        "Credit Regulations 2013 reg 39) and is in a benefit unit with a "
        "Universal Credit award. uc_limited_capability_for_work is the "
        "assessment alone, and defaults from disability, so it does not "
        "establish that Universal Credit is in payment."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/39"

    def formula(person, period, parameters):
        has_uc_award = person.benunit("universal_credit", period) > 0
        return person("uc_limited_capability_for_work", period) & has_uc_award
