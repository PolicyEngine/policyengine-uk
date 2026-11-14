from policyengine_uk.model_api import *


class child_limit_non_consensual_conception_exception(Variable):
    value_type = bool
    entity = Person
    label = "Two-child limit non-consensual conception exception"
    documentation = (
        "Whether the non-consensual conception exception to the Universal "
        "Credit and Child Tax Credit child limit applies to this child or "
        "qualifying young person: DWP or HMRC has determined that the child "
        "is likely to have been conceived as a result of non-consensual sex, "
        "including in a controlling or coercive relationship, and the "
        "claimant parent does not live with the other party."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/paragraph/5/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/13/2025-04-06",
    )
