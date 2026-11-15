from policyengine_uk.model_api import *


class uc_is_responsible_foster_parent_of_child_under_one(Variable):
    value_type = bool
    entity = Person
    label = "Responsible foster parent of a child under 1, for Universal Credit"
    documentation = (
        "Whether the claimant is the responsible foster parent of a child "
        "under the age of 1: the only foster parent, or the member of a "
        "fostering couple nominated as responsible. Such a claimant is "
        "subject to no work-related requirements. An input: a foster child "
        "is not a member of the benefit unit."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/89"
    definition_period = YEAR
    default_value = False
