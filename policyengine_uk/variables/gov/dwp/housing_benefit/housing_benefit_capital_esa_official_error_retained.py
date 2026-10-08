from policyengine_uk.model_api import *


class housing_benefit_capital_esa_official_error_retained(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital esa official error retained"
    documentation = "Retained payment rectifying an official error preventing or delaying contributory ESA assessment, under working-age Schedule 6 paragraph 9A. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
