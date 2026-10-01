from policyengine_uk.model_api import *


class uc_is_foster_parent_or_new_friend_or_family_carer(Variable):
    value_type = bool
    entity = Person
    label = "Foster parent, or friend or family carer in their first 12 months, for Universal Credit"
    documentation = (
        "Whether the Universal Credit Regulations 2013 reg. 91(2) puts the "
        "claimant in the group subject to the work-focused interview "
        "requirement only: the responsible foster parent of a child aged at "
        "least 1; a foster parent of a child or qualifying young person "
        "whose care needs make a work search requirement unreasonable; a "
        "foster parent between placements for up to 8 weeks; or a friend or "
        "family carer who took on a child within the past 12 months and is "
        "the responsible carer for that child. An input: the model has no "
        "fostering or kinship care data."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/91"
    definition_period = YEAR
    default_value = False
