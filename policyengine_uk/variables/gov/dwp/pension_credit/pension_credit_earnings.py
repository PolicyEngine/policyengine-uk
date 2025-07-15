from policyengine_uk.model_api import *


class pension_credit_earnings(Variable):
    label = "earnings for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A"
    adds = "gov.dwp.pension_credit.guarantee_credit.earnings_sources"
