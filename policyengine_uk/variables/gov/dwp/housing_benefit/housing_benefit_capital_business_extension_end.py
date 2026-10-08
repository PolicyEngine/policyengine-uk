from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_capital_business_extension_end(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital business extension end"
    documentation = "Authority-accepted final day of the reasonable business-asset disposal period (including its initial period), or of an extension beyond the normal temporary-illness period. An unknown date does not establish reasonable ongoing disposal. Unobserved facts default to an unknown future date."
    default_value = date(9999, 1, 1)
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
