from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_childcare_parental_pay_end(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare parental pay end"
    documentation = "Last day of entitlement to the prescribed statutory parental payment, maternity allowance or qualifying support. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    default_value = date(9999, 1, 1)
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
