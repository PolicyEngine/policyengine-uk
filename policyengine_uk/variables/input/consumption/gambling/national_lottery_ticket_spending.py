from policyengine_uk.model_api import *


class national_lottery_ticket_spending(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    default_value = 0
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.gambling_duty_bases.lottery"
    label = "Chargeable National Lottery ticket consideration"
    reference = "https://www.legislation.gov.uk/ukpga/1993/34/section/25"
