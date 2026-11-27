from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_sdil_litres_higher_rate(Variable):
    label = "Soft drinks levy litres at the higher rate"
    documentation = "Litres of chargeable soft drinks with 8 grams or more of sugar per 100 millilitres that the firm packages or imports in the year (Finance Act 2017 s.30). Defaults to 0."
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    reference = "https://www.legislation.gov.uk/ukpga/2017/10/section/30"
