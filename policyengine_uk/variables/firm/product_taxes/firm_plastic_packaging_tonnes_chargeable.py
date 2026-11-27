from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_plastic_packaging_tonnes_chargeable(Variable):
    label = "Chargeable plastic packaging tonnes"
    documentation = "Tonnes of chargeable plastic packaging components, with less than 30% recycled plastic, that the firm manufactures in or imports into the UK in the year (Finance Act 2021 ss.43 and 47). Defaults to 0."
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    reference = "https://www.legislation.gov.uk/ukpga/2021/26/section/43"
