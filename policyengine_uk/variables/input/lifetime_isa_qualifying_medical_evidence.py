from policyengine_uk.model_api import *


class lifetime_isa_qualifying_medical_evidence(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Lifetime ISA manager holds qualifying medical evidence"
    documentation = "The account manager has received written evidence from a registered medical practitioner that the investor is expected to live for less than one year. A diagnosis or general disability alone does not qualify. False unless supplied."
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/4"
