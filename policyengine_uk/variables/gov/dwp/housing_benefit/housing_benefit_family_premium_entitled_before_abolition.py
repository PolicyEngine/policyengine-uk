from policyengine_uk.model_api import *


class housing_benefit_family_premium_entitled_before_abolition(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit family premium entitled before abolition"
    documentation = "Claimant was entitled to HB and had a child or young person in the family on 30 April 2016 (GB) or 4 September 2016 (NI)."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
