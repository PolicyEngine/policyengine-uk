from policyengine_uk.model_api import *


class tax_free_childcare_on_carers_leave(Variable):
    value_type = bool
    entity = Person
    label = "on carer's leave for Tax-Free Childcare"
    documentation = (
        "Whether this person is absent from work on carer's leave under "
        "section 80J of the Employment Rights Act 1996, which regulation "
        "13(1)(c) of the Childcare Payments (Eligibility) Regulations 2015 "
        "treats like the caring and incapacity benefits from 6 April 2024."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/13"
