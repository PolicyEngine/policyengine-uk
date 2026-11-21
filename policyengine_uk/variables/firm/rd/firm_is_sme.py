from policyengine_uk.model_api import *


class firm_is_sme(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is an SME for R&D relief"
    documentation = "Whether the firm, with its linked and partner enterprises, is a small or medium-sized enterprise for research and development relief: fewer than 500 staff and either turnover of no more than 100 million euros or a balance sheet of no more than 86 million euros."
    definition_period = YEAR
    default_value = False
