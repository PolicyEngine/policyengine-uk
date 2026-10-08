from policyengine_uk.model_api import *


class housing_benefit_childcare_incapacity_but_for_determination(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit childcare incapacity but for determination"
    documentation = "The partner would meet the specified disability-premium/support-component/WRAG condition but for a statutory determination treating the person as capable of work or not having limited capability, under HB regulation 28(11)(b) or (ba)."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/29",
    )
