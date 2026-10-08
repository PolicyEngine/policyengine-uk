from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_childcare_sickness_start(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare sickness start"
    documentation = "First day of the sickness benefit or incapacity/LCW credits period after remunerative work. Supply the factual value when known; otherwise zero/false or an unobserved future date is used."
    default_value = date(9999, 1, 1)
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
