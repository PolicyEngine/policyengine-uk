from policyengine_uk.model_api import *


class cannot_reasonably_share_bedroom_due_to_disability(Variable):
    value_type = bool
    entity = Person
    label = "not reasonably able to share a bedroom because of disability"
    documentation = (
        "Whether the decision maker (Universal Credit) or the local authority "
        "(Housing Benefit) is satisfied that, because of their disability, "
        "this person is not reasonably able to share a bedroom: for a child "
        "under 16, with another child; for a member of a couple, with the "
        "other member of the couple. With a qualifying disability benefit, "
        "this gives the child or the couple a bedroom of their own in the LHA "
        "size criteria (see is_child_who_cannot_share_bedroom and "
        "is_member_of_couple_who_cannot_share_bedroom). The survey data do "
        "not record this judgement, so it is false unless supplied."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
    )
