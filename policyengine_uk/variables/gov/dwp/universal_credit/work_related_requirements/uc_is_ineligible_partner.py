from policyengine_uk.model_api import *


class uc_is_ineligible_partner(Variable):
    value_type = bool
    entity = Person
    label = "Partner who cannot be a joint Universal Credit claimant"
    documentation = (
        "Whether this person is the member of a couple whose partner claims "
        "Universal Credit as a single person under the Universal Credit "
        "Regulations 2013 reg. 3(3): this person is under 18 and cannot claim "
        "at that age, is not in Great Britain, is a prisoner, is excluded by "
        "reg. 19, or is subject to immigration control. They are in no work-related group and the "
        "minimum income floor never applies to them, but their earned income "
        "counts as their partner's, and they add the pay for 35 hours at "
        "the national living wage to the couple threshold (reg. 90(3)(b)). "
        "An input. The model does not yet give such a couple the single "
        "claimant's standard allowance of reg. 36(3)."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/3"
    definition_period = YEAR
    default_value = False
