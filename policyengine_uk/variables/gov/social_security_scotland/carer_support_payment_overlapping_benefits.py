from policyengine_uk.model_api import *


class carer_support_payment_overlapping_benefits(Variable):
    value_type = float
    entity = Person
    label = "Benefits that overlap with Carer Support Payment"
    documentation = (
        "Overlapping benefits by which regulation 16(2) of the Carer's "
        "Assistance (Carer Support Payment) (Scotland) Regulations 2023 "
        "reduces Carer Support Payment."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ssi/2023/302/regulation/16"
    adds = "gov.social_security_scotland.carer_support_payment.overlapping_benefits"
