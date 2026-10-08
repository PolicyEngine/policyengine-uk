from policyengine_uk.model_api import *


class housing_benefit_capital_business_active(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital business active"
    documentation = "The person is carrying on the trade/business to which the supplied assets belong. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
