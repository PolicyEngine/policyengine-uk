from policyengine_uk.model_api import *


class receives_limited_capability_for_work_credits(Variable):
    value_type = bool
    entity = Person
    label = "entitled to National Insurance credits for incapacity or limited capability for work"
    documentation = (
        "Whether this person is entitled to National Insurance credits on the "
        "grounds of incapacity for work or limited capability for work under "
        "regulation 8B of the Social Security (Credits) Regulations 1975. "
        "Tax-Free Childcare and the extended childcare entitlement treat these "
        "credits like the benefits that let a partner qualify without working. "
        "Not in the survey data, so false unless supplied."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/1975/556/regulation/8B"
