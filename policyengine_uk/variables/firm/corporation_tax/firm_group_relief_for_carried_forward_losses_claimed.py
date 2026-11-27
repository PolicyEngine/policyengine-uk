from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_relief_for_carried_forward_losses_claimed(Variable):
    value_type = float
    entity = Firm
    label = "Firm group relief for carried-forward losses claimed"
    documentation = "Carried-forward losses surrendered to the firm by other group companies that it claims for the year under CTA 2010 Part 5A, from 1 April 2017. The deduction is limited to the room left within the firm's relevant maximum after its own carried-forward losses, and is not given while its own carried-forward losses are unused. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/188CK"
