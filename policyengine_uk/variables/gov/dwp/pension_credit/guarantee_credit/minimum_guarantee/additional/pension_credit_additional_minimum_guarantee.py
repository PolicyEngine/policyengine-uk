from policyengine_uk.model_api import *


class pension_credit_additional_minimum_guarantee(Variable):
    label = "Pension Credit additional minimum guarantee"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6"

    adds = "gov.dwp.pension_credit.guarantee_credit.additions"
