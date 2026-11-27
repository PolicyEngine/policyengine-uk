from policyengine_uk.model_api import *


class firm_psa_chargeable_earnings(Variable):
    value_type = float
    entity = Firm
    label = "Firm PAYE settlement agreement chargeable earnings"
    documentation = "General earnings included in the firm's PAYE settlement agreements that would otherwise bear secondary Class 1 or Class 1A contributions (SSCBA 1992 s.10A(1)(a), (4)). Do not also include them in firm_paybill or firm_class_1a_benefits. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/10A"
