from policyengine_uk.model_api import *


class firm_vat_on_sales(Variable):
    value_type = float
    entity = Firm
    label = "VAT on sales"
    definition_period = YEAR
    unit = GBP
    documentation = "Total VAT charged on firm's sales (output VAT)"
    defined_for = "firm_vat_registered"

    def formula(firm, period, parameters):
        vat_params = parameters(period).gov.hmrc.vat

        standard_supplies = firm("firm_standard_rated_supplies", period)
        reduced_supplies = firm("firm_reduced_rated_supplies", period)
        zero_supplies = firm("firm_zero_rated_supplies", period)

        standard_vat = standard_supplies * vat_params.standard_rate
        reduced_vat = reduced_supplies * vat_params.reduced_rate
        zero_vat = zero_supplies * vat_params.zero_rate

        return standard_vat + reduced_vat + zero_vat
