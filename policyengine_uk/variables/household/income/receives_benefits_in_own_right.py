from policyengine_uk.model_api import *


class receives_benefits_in_own_right(Variable):
    value_type = bool
    entity = Person
    label = "Receives benefits in own right"
    documentation = (
        "Whether this person receives Universal Credit, Employment and Support "
        "Allowance, or Jobseeker's Allowance in their own right. This is a "
        "person-level input because household benefit receipt does not identify "
        "which person is claiming independently."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/5"
