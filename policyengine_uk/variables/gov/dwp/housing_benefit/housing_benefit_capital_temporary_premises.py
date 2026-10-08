from policyengine_uk.model_api import *


class housing_benefit_capital_temporary_premises(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital temporary premises"
    documentation = "Claimant/partner interest in premises being acquired, possessed, repaired or disposed of to satisfy an explicitly selected temporary property disregard, excluding the main home already omitted from sources. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
