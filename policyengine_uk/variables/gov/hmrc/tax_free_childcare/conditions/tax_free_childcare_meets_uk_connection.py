from policyengine_uk.model_api import *


class tax_free_childcare_meets_uk_connection(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets the Tax-Free Childcare UK connection requirement"
    documentation = (
        "Whether the family satisfies the Tax-Free Childcare requirement to be "
        "treated as being in the United Kingdom."
    )
    definition_period = YEAR
    default_value = True
    reference = "The Childcare Payments (Eligibility) Regulations 2015 regs. 6-8"
