from policyengine_uk.model_api import *


class is_looked_after_by_local_authority(Variable):
    value_type = bool
    entity = Person
    label = "looked after by a local authority"
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/4"
