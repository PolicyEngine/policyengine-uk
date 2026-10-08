from policyengine_uk.model_api import *


class housing_benefit_disabled_child_premium_before_death(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit disabled child premium before death"
    documentation = "A disabled child premium was included in the claimant's applicable amount immediately before this child's death, or ceased solely because of that death."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
