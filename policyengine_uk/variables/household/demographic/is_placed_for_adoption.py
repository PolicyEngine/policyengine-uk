from policyengine_uk.model_api import *


class is_placed_for_adoption(Variable):
    value_type = bool
    entity = Person
    label = "placed for adoption"
    documentation = (
        "Whether this child is placed for adoption with the claimant or "
        "partner of their benefit unit (an adopter), or placed with them "
        "prior to adoption. Put the child in the adopter's benefit unit and "
        "leave is_looked_after_by_local_authority false: under Universal "
        "Credit the adopter is responsible for the child (UC Regs 2013 reg "
        "4A(1)(c)) and satisfies the foster parent condition for an "
        "additional bedroom (Sch 4 para 12(4)(b)); under Housing Benefit and "
        "the other legacy schemes the child is not a member of the "
        "claimant's household (HB Regs 2006 reg 21(3)(b)-(c))."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4A",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
    )
