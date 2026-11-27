from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_trading_loss_surrendered(Variable):
    value_type = float
    entity = Firm
    label = "Firm trading loss surrendered as group relief"
    documentation = "Trading loss of the year that the firm surrenders to other group companies as group relief. It reduces the loss the firm can surrender for an SME R&D payable credit (CTA 2009 s.1056(2)(c)). Its effect on the claimant is entered there as firm_group_relief_claimed. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/section/1056"
