from datetime import date

from policyengine_uk.model_api import *


class lifetime_isa_medical_evidence_received_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    default_value = date(9999, 1, 1)
    label = "Date Lifetime ISA manager received qualifying medical evidence"
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/4"
