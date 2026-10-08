from policyengine_uk.model_api import *


class housing_benefit_childcare_parental_pay_entitled(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare parental pay entitled"
    documentation = "The person is entitled to one of the statutory payments or qualifying support expressly listed in regulation 28(14). Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
