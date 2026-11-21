from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_partial_exemption_recovery_share(Variable):
    label = "Share of input VAT recoverable"
    documentation = (
        "Share of the firm's input VAT it can recover under the partial "
        "exemption standard method: taxable supplies over taxable plus exempt "
        "supplies. A firm with no supplies recovers all of its input VAT. The "
        "de minimis limits and special methods are not modelled; supply a "
        "value to override the default."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/101"

    def formula(firm, period, parameters):
        taxable = firm("firm_vat_taxable_turnover", period)
        exempt = firm("firm_exempt_supplies", period)
        total = taxable + exempt
        has_supplies = total > 0
        share = np.ones_like(total)
        share[has_supplies] = taxable[has_supplies] / total[has_supplies]
        return np.clip(share, 0, 1)
