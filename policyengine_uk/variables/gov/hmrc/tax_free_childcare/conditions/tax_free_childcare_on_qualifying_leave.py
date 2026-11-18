from policyengine_uk.model_api import *


class tax_free_childcare_on_qualifying_leave(Variable):
    value_type = bool
    entity = Person
    label = "on qualifying leave for tax-free childcare"
    documentation = (
        "Legacy reported sickness, parenting or annual-leave fact, retained "
        "for caller compatibility. This input alone no longer satisfies the "
        "Tax-Free Childcare paid-work or minimum-income eligibility conditions. "
        "Regulation 14 concerns the connection between childcare costs and "
        "work, not qualifying paid work for eligibility. Ordinary employed "
        "leave uses the person's factual in_work and expected income. For a "
        "regulation 12 temporary absence, use "
        "tax_free_childcare_qualifying_temporary_absence only when its "
        "prior-work and applicable child/account conditions are satisfied."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/12",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/14",
    ]
