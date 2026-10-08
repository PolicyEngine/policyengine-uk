from policyengine_uk.model_api import *


class housing_benefit_capital_home_funds_retained(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital home funds retained"
    documentation = "Retained sale proceeds/acquisition loan or grant intended for another home, satisfying the applicable schedule's specified-use condition. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
