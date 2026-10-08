from policyengine_uk.model_api import *


class housing_benefit_owned_household_capital(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit owned household capital"
    documentation = "Claimant/partner beneficial share of valued capital in the configured household sources, excluding person-level LISA capital. Include only their legal beneficial shares, applying joint-owner counts including owners outside the household; exclude dependants' holdings. This replaces the household proxy when known, rather than adding to it. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
