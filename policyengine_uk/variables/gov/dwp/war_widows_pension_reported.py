from policyengine_uk.model_api import *


class war_widows_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "War widow's or widower's pension (reported)"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/17"
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
