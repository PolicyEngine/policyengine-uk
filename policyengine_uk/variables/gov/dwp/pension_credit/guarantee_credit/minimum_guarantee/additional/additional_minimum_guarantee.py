from policyengine_uk.model_api import *


class additional_minimum_guarantee(Variable):
    label = "Additional Minimum Guarantee"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6"

    adds = "gov.dwp.pension_credit.guarantee_credit.additions"
