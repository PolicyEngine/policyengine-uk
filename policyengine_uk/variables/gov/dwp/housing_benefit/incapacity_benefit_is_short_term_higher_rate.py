from policyengine_uk.model_api import *


class incapacity_benefit_is_short_term_higher_rate(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "incapacity benefit is short term higher rate"
    documentation = "Incapacity Benefit is actually payable at its short-term higher rate. A positive IB amount with unknown rate must not be treated as higher rate merely because the lower-rate flag is false."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/29",
    )
