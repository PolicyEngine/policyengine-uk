from policyengine_uk.model_api import *


class uc_is_temporarily_absent_from_claimant_household(Variable):
    value_type = bool
    entity = Person
    label = "Temporarily absent from the Universal Credit claimant's household"
    documentation = (
        "Whether this member of a couple is temporarily absent from the "
        "claimant's household. A couple stays a couple during a temporary "
        "absence unless it exceeds, or is expected to exceed, six months "
        "(regulation 3(6)). The absent member is unable to provide childcare "
        "for the childcare work condition (regulation 32(1)(b)(iii)). Survey "
        "data does not record it, so this defaults to false."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 32(1)(b)(iii)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 3(6)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
    ]
