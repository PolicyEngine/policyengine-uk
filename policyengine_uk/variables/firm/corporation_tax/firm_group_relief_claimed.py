from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_relief_claimed(Variable):
    value_type = float
    entity = Firm
    label = "Firm group relief claimed"
    documentation = "Losses and other amounts surrendered to the firm by other group companies that it claims as group relief for the year under CTA 2010 Part 5. The firm's deduction, firm_group_relief, is capped at its total profits. Enter group relief for carried-forward losses (Part 5A) in firm_group_relief_for_carried_forward_losses_claimed instead, so that it is restricted with the firm's own carried-forward losses. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/137"
