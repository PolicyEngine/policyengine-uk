from policyengine_uk.model_api import *


class housing_benefit_capital_business_disposal_steps(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital business disposal steps"
    documentation = "Reasonable steps are being taken to dispose of the former business assets. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
