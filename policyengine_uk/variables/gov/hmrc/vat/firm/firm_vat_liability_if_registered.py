from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_liability_if_registered(Variable):
    label = "VAT liability if registered"
    documentation = (
        "VAT the firm would owe if registered: the flat rate liability if it "
        "elects the flat rate scheme and is eligible, otherwise output VAT "
        "less recoverable input VAT."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(firm, period, parameters):
        # Keep in step with _vat_under_reform_rules_at_baseline_rates in
        # policyengine_uk/variables/contrib/policyengine/firm/firm_tax_change_total.py.
        uses_frs = firm("firm_uses_flat_rate_scheme", period)
        eligible = firm("firm_flat_rate_scheme_eligible", period)
        flat_rate = firm("firm_vat_flat_rate_liability", period)
        normal = firm("firm_vat_normal_liability", period)
        return where(uses_frs & eligible, flat_rate, normal)
