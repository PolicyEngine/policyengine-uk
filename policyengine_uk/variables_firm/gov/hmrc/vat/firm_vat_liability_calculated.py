from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_liability_calculated(Variable):
    value_type = float
    entity = Firm
    label = "Calculated VAT liability"
    definition_period = YEAR
    unit = GBP
    documentation = "Calculated VAT liability based on supplies and parameters"

    def formula(firm, period, parameters):
        # This calculates VAT based on supplies and rates
        # Compare with vat_liability_k from the dataset
        return firm("firm_net_vat_liability", period)
