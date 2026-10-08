from policyengine_uk.model_api import *


class working_tax_credit_30_hour_element_in_award(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "working tax credit 30 hour element in award"
    documentation = "An actual Working Tax Credit award includes the 30-hour element under regulation 20(1)(c), for the claimant or partner. This is not inferred from age or a zero annual tax-credit payment."
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
    )
