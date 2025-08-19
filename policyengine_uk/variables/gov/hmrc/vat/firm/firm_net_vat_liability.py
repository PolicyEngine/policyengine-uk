from policyengine_uk.model_api import *


class firm_net_vat_liability(Variable):
    value_type = float
    entity = Firm
    label = "Net VAT liability"
    definition_period = YEAR
    unit = GBP
    documentation = "Net VAT liability (output VAT minus input VAT)"

    def formula(firm, period, parameters):
        vat_registered = firm("firm_vat_registered", period)
        output_vat = firm("firm_vat_on_sales", period)
        input_vat = firm("firm_vat_on_purchases", period)

        net_vat = output_vat - input_vat

        # Only registered firms pay/reclaim VAT
        return net_vat * vat_registered
