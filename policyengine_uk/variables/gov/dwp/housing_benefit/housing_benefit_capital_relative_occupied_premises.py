from policyengine_uk.model_api import *


class housing_benefit_capital_relative_occupied_premises(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital relative occupied premises"
    documentation = "Value of premises occupied as a home by a qualifying relative of the claimant/partner who has attained the prescribed age or is incapacitated, or by the former partner as a lone parent. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
