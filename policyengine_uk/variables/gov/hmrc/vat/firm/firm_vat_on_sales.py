from policyengine_uk.model_api import *


class firm_vat_on_sales(Variable):
    value_type = float
    entity = Firm
    label = "VAT on sales"
    definition_period = YEAR
    unit = GBP
    documentation = "Total VAT charged on firm's sales (output VAT)"

    def formula(firm, period, parameters):
        vat_registered = firm("firm_vat_registered", period)

        if not vat_registered.any():
            return firm.empty_array()

        vat_params = parameters(period).gov.hmrc.vat

        standard_supplies = firm("firm_standard_rated_supplies", period)
        reduced_supplies = firm("firm_reduced_rated_supplies", period)
        zero_supplies = firm("firm_zero_rated_supplies", period)

        standard_vat = standard_supplies * vat_params.standard_rate
        reduced_vat = reduced_supplies * vat_params.reduced_rate
        zero_vat = zero_supplies * vat_params.zero_rate

        total_vat = standard_vat + reduced_vat + zero_vat

        return total_vat * vat_registered
