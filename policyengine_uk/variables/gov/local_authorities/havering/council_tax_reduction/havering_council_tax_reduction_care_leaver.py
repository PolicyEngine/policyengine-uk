from policyengine_uk.model_api import *


class havering_council_tax_reduction_care_leaver(Variable):
    value_type = bool
    entity = Person
    label = "Havering CTS care leaver"
    definition_period = YEAR
    reference = "https://democracy.havering.gov.uk/documents/s83059/0-1%20-%20Budget%20report%20cabinet%202026%202.pdf"
