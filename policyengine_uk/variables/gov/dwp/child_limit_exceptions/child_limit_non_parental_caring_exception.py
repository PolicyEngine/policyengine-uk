from policyengine_uk.model_api import *


class child_limit_non_parental_caring_exception(Variable):
    value_type = bool
    entity = Person
    label = "Two-child limit non-parental caring arrangements exception"
    documentation = (
        "Whether the non-parental caring arrangements exception to the "
        "Universal Credit and Child Tax Credit child limit applies to this "
        "child or qualifying young person: the claimant, who is not the "
        "child's parent or step-parent, is a friend or family carer (for "
        "example under a child arrangements order, special guardianship, "
        "guardian's allowance or kinship care order, or caring for a child "
        "who would otherwise be looked after by a local authority), or is "
        "responsible for a child who is this child's parent."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/paragraph/4/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/12/2025-04-06",
    )
