from policyengine_uk.model_api import *


class child_limit_continuation_exception(Variable):
    value_type = bool
    entity = Person
    label = "Two-child limit continuation of an existing exception"
    documentation = (
        "Whether the continuation exception to the Universal Credit and Child "
        "Tax Credit child limit applies to this child or qualifying young "
        "person: the claimant is the child's step-parent, no other exception "
        "applies, and a multiple births, adoption or non-consensual "
        "conception exception (for Child Tax Credit, any exception) applied "
        "to the child in an earlier joint award with the child's parent that "
        "has continued into this one. For Universal Credit the model treats "
        "it as continuing a multiple births or non-consensual conception "
        "exception, which keeps the child's place in the order of children; "
        "a continued adoption exception would not."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/paragraph/6/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/14/2025-04-06",
    )
