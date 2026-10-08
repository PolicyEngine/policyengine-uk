from policyengine_uk.model_api import *


class housing_benefit_childcare_wtc_in_payment_at_pay_end(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare wtc in payment at pay end"
    documentation = "The WTC childcare element was in payment on the statutory parental-pay entitlement end date. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
