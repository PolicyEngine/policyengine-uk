from policyengine_uk.model_api import *


class is_in_approved_training(Variable):
    value_type = bool
    entity = Person
    label = "In approved training"
    documentation = (
        "Whether this person is in approved training for child and qualifying "
        "young person benefit rules. This is dataset-supplied where observed."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/5"
