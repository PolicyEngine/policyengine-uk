from policyengine_uk.model_api import *


class housing_benefit_capital_repairs_funds_retained(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital repairs funds retained"
    documentation = "Retained loan, grant or insurance funds specifically for essential repairs/alterations to the home under the applicable schedule. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
