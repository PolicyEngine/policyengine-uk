from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Cheltenham Council Tax Support claimant source non-dependant exemption"
    documentation = "Source input for claimant or partner non-dependant deduction exemptions not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"
    default_value = False
