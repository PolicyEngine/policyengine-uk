from policyengine_uk.model_api import *


class housing_benefit_family_premium_new_claim_since_abolition(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit family premium new claim since abolition"
    documentation = "A new Housing Benefit claim has been made since the applicable family-premium abolition date; this ends transitional protection."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
