from policyengine_uk.model_api import *


class child_limit_multiple_birth_exception(Variable):
    value_type = bool
    entity = Person
    label = "Two-child limit multiple births exception"
    documentation = (
        "Whether the multiple births exception to the Universal Credit and "
        "Child Tax Credit child limit applies to this child or qualifying "
        "young person: the claimant is a parent (other than an adoptive "
        "parent) of a child born in a multiple birth, is responsible for at "
        "least two of the children from that pregnancy, and this child is not "
        "the first of them in the order of children. Set it on every child "
        "from the pregnancy except the first."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/paragraph/2/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/10/2025-04-06",
    )
