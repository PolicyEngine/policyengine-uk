from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_net_vat_liability(Variable):
    value_type = float
    entity = Firm
    label = "Net VAT liability"
    definition_period = YEAR
    unit = GBP
    documentation = "Net VAT liability (output VAT minus input VAT)"

    def formula(firm, period, parameters):
        output_vat = firm("firm_vat_on_sales", period)
        input_vat = firm("firm_vat_on_purchases", period)

        return output_vat - input_vat
