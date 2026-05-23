from policyengine_uk.model_api import *


class ealing_council_tax_reduction_underlying_carers_allowance_entitlement(Variable):
    value_type = bool
    entity = Person
    label = "Ealing CTR underlying Carer's Allowance entitlement"
    definition_period = YEAR
    reference = "https://www.ealing.gov.uk/download/downloads/id/19657/council_tax_reduction_scheme_2026_to_2027.pdf"
