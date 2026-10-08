from policyengine_uk.model_api import *


class housing_benefit_childcare_listed_incapacity_benefit_payable(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare listed incapacity benefit payable"
    documentation = "A pension, allowance or payment expressly listed by HB regulation 28(11)(d) / pension-age regulation 31 is payable in respect of this partner, including the listed Scottish disability payments, section 104 disablement-pension increase or analogous war/industrial-injury increase. Does not mean any disability-related payment."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/29",
    )
