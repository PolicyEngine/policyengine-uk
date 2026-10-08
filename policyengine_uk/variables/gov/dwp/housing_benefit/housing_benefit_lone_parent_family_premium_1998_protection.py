from policyengine_uk.model_api import *


class housing_benefit_lone_parent_family_premium_1998_protection(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit lone parent family premium 1998 protection"
    documentation = "Award records establish continuing Schedule 3 paragraph 3(3)-(5) protection: HB/qualifying CTB entitlement from 5 April 1998 including permitted rent-free periods; continuous lone-parent status; required income-support/JSA/ESA receipt or nonreceipt continuity; and no disqualifying disability premium or ESA component. This is not ordinary lone-parent status."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
