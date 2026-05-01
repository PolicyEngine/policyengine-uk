from policyengine_uk.model_api import *


class ealing_council_tax_reduction_care_leaver(Variable):
    value_type = bool
    entity = Person
    label = "Ealing CTR care leaver"
    definition_period = YEAR
    reference = "https://www.ealing.gov.uk/download/downloads/id/19657/council_tax_reduction_scheme_2026_to_2027.pdf"
