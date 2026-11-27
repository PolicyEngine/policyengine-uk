from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_applies_partial_exemption_de_minimis(Variable):
    label = "Partial exemption de minimis tests applied"
    documentation = (
        "Whether the partial exemption de minimis tests are applied to the "
        "firm (SI 1995/2518 regs 105A and 106). Where they are met, the "
        "firm's exempt input tax is treated as attributable to taxable "
        "supplies, so all its input VAT is recoverable. The tests are "
        "mandatory in law, but this defaults to false so that existing "
        "results are unchanged; with it unset, VAT is overstated for small "
        "partly exempt firms, so a data builder should set it."
    )
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = bool
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/106"
